# AI助手模块

## 2.1 模块概述

**模块名称**：AI智能助手模块 (AI Assistant Module)

**功能描述**：

- 基于LangChain的智能问答助手
- 上下文感知：知道学生正在做什么实验
- RAG检索：从实验指导书中检索相关内容
- 对话记忆：支持多轮对话
- 对话管理：保存历史对话，支持会话切换

**核心价值**：

- 24/7 智能答疑，减轻教师负担
- 个性化指导，提升学习效率
- 知识库检索，精准定位问题
- 过程追溯，教师可查看学生提问记录

**技术栈**：

- LangChain：对话链管理
- OpenAI API：GPT-4 / GPT-3.5
- 向量数据库：ChromaDB / Pinecone
- Embedding：OpenAI text-embedding-ada-002

------

## 2.2 实体设计

### 2.2.1 对话会话实体 (ChatConversation)

**实体说明**：代表一次完整的对话会话，包含多条消息

**字段定义**：

| 字段名            | 类型         | 必填 | 说明                             | 示例值                                |
| ----------------- | ------------ | ---- | -------------------------------- | ------------------------------------- |
| id                | bigint       | 是   | 主键                             | 1                                     |
| session_id        | varchar(64)  | 是   | 会话唯一标识（UUID）             | "a1b2c3d4..."                         |
| title             | varchar(255) | 是   | 会话标题（自动生成或用户自定义） | "关于Linux用户管理的提问"             |
| user_id           | int          | 是   | 用户ID                           | 101                                   |
| context_type      | varchar(50)  | 否   | 上下文类型                       | experiment / vm / general             |
| context_id        | varchar(100) | 否   | 上下文对象ID                     | "1" (实验ID)                          |
| context_data      | json         | 否   | 上下文数据快照                   | {"experiment_title": "Linux用户管理"} |
| message_count     | int          | 否   | 消息数量                         | 15                                    |
| last_message_at   | datetime     | 否   | 最后消息时间                     | 2024-03-10 15:30:00                   |
| is_archived       | boolean      | 否   | 是否归档                         | false                                 |
| model_name        | varchar(50)  | 否   | AI模型名称                       | gpt-3.5-turbo / gpt-4                 |
| temperature       | decimal(3,2) | 否   | 模型温度参数                     | 0.7                                   |
| max_tokens        | int          | 否   | 最大token数                      | 2000                                  |
| created_by_id     | int          | 否   | 创建人ID                         | 1                                     |
| updated_by_id     | int          | 否   | 更新人ID                         | 1                                     |
| owner_organization_id| int       | 否   | 所属组织ID                       | 1                                     |
| is_deleted        | boolean      | 否   | 软删除标志                       | false                                 |
| remark            | varchar(255) | 否   | 备注                             | NULL                                  |
| created_at        | datetime     | 是   | 创建时间                         | 自动生成                              |
| updated_at        | datetime     | 是   | 更新时间                         | 自动更新                              |

**业务规则**：

- 每次打开AI助手创建新会话，或继续旧会话
- `session_id` 用于前端识别会话
- `context_type` 和 `context_id` 关联业务对象（实验、虚拟机等）
- 自动根据首条消息生成会话标题（由后端异步任务完成）

**索引设计**：

```sql
UNIQUE INDEX session_id (session_id)
INDEX idx_user_updated (user_id, updated_at)
INDEX idx_context (context_type, context_id)
```

------

### 2.2.2 对话消息实体 (ChatMessage)

**实体说明**：具体的对话消息记录

**字段定义**：

| 字段名            | 类型        | 必填 | 说明                   | 示例值                                |
| ----------------- | ----------- | ---- | ---------------------- | ------------------------------------- |
| id                | bigint      | 是   | 主键                   | 1                                     |
| conversation_id   | bigint      | 是   | 所属会话ID             | 1                                     |
| role              | varchar(20) | 是   | LangChain角色          | human / ai / system / function        |
| content           | text        | 是   | 消息内容               | "请问如何创建用户？"                  |
| content_type      | varchar(20) | 否   | 内容类型               | text / markdown / code                |
| sequence          | int         | 是   | 消息序号（会话内递增） | 1                                     |
| parent_message_id | bigint      | 否   | 父消息ID（支持消息树） | NULL                                  |
| prompt_tokens     | int         | 否   | 提示词token数          | 450                                   |
| completion_tokens | int         | 否   | 回复token数            | 120                                   |
| total_tokens      | int         | 否   | 总token数              | 570                                   |
| model_name        | varchar(50) | 否   | 使用的模型             | gpt-3.5-turbo                         |
| finish_reason     | varchar(50) | 否   | 完成原因               | stop / length / function_call         |
| function_call     | json        | 否   | 函数调用信息           | {"name": "search_doc", "args": {...}} |
| tool_calls        | json        | 否   | 工具调用列表           | [...]                                 |
| additional_kwargs | json        | 否   | 额外参数               | {...}                                 |
| error_message     | text        | 否   | 错误信息               | NULL                                  |
| retry_count       | int         | 否   | 重试次数               | 0                                     |
| feedback          | varchar(20) | 否   | 用户反馈               | helpful / not_helpful                 |
| feedback_detail   | text        | 否   | 反馈详情               | "回答很准确"                          |
| created_by_id     | int         | 否   | 创建人ID               | 1                                     |
| updated_by_id     | int         | 否   | 更新人ID               | 1                                     |
| owner_organization_id| int      | 否   | 所属组织ID             | 1                                     |
| is_deleted        | boolean     | 否   | 软删除标志             | false                                 |
| remark            | varchar(255)| 否   | 备注                   | NULL                                  |
| created_at        | datetime    | 是   | 创建时间               | 自动生成                              |

**业务规则**：

- 用户提问和AI回答交替出现
- `sequence` 确保消息顺序
- 记录token使用情况，用于成本控制
- 用户可对AI回答点赞/点踩

**角色说明**：

- `human`：用户消息
- `ai`：AI助手回复
- `system`：系统消息（如欢迎语）
- `function`：函数调用结果

**索引设计**：

```sql
INDEX idx_conversation_sequence (conversation_id, sequence)
INDEX idx_conversation_created (conversation_id, created_at)
INDEX idx_role_created (role, created_at)
```

------

### 2.2.3 实验上下文关联实体 (ChatExperimentContext)

**实体说明**：关联AI对话与实验业务对象

**字段定义**：

| 字段名              | 类型     | 必填 | 说明               | 示例值   |
| ------------------- | -------- | ---- | ------------------ | -------- |
| id                  | bigint   | 是   | 主键               | 1        |
| conversation_id     | bigint   | 是   | 会话ID             | 1        |
| experiment_id       | bigint   | 否   | 正在进行的实验ID   | 1        |
| submission_id       | bigint   | 否   | 正在编写的提交ID   | 10       |
| guidebook_id        | bigint   | 否   | 正在查看的指导书ID | 1        |
| indexed_content_ids | json     | 否   | 已索引的文档ID列表 | [1, 2]   |
| created_by_id       | int      | 否   | 创建人ID           | 1        |
| updated_by_id       | int      | 否   | 更新人ID           | 1        |
| owner_organization_id| int     | 否   | 所属组织ID         | 1        |
| is_deleted          | boolean  | 否   | 软删除标志         | false    |
| remark              | varchar(255)| 否 | 备注               | NULL     |
| created_at          | datetime | 是   | 创建时间           | 自动生成 |
| updated_at          | datetime | 是   | 更新时间           | 自动更新 |

**业务规则**：

- 一个会话只有一个上下文记录
- AI回答时自动检索 `guidebook_id` 对应的文档
- 上下文信息传递给LangChain，增强回答相关性

**索引设计**：

```sql
UNIQUE INDEX conversation_id (conversation_id)
INDEX idx_experiment (experiment_id)
```

------

### 2.2.4 会话摘要实体 (ChatConversationSummary)

**实体说明**：长对话自动总结，节省token

**字段定义**：

| 字段名              | 类型        | 必填 | 说明          | 示例值                                     |
| ------------------- | ----------- | ---- | ------------- | ------------------------------------------ |
| id                  | bigint      | 是   | 主键          | 1                                          |
| conversation_id     | bigint      | 是   | 会话ID        | 1                                          |
| summary_type        | varchar(20) | 是   | 摘要类型      | auto / manual                              |
| summary_content     | text        | 是   | 摘要内容      | "用户询问了Linux用户创建和权限设置问题..." |
| message_range_start | int         | 是   | 起始消息序号  | 1                                          |
| message_range_end   | int         | 是   | 结束消息序号  | 10                                         |
| tokens_saved        | int         | 否   | 节省的token数 | 1200                                       |
| created_by_id       | int         | 否   | 创建人ID      | 1                                          |
| updated_by_id       | int         | 否   | 更新人ID      | 1                                          |
| owner_organization_id| int        | 否   | 所属组织ID    | 1                                          |
| is_deleted          | boolean     | 否   | 软删除标志    | false                                      |
| remark              | varchar(255)| 否   | 备注          | NULL                                       |
| created_at          | datetime    | 是   | 创建时间      | 自动生成                                   |

**业务规则**：

- 当消息数超过20条时，自动总结前面的对话
- 总结后的内容作为上下文，替代原始消息
- 大幅减少token消耗

**索引设计**：

```sql
INDEX idx_conversation (conversation_id)
```

------

### 2.2.5 AI模型配置实体 (AIModelConfig)

**实体说明**：记录可用的AI模型配置及其参数

**字段定义**：

| 字段名              | 类型        | 必填 | 说明          | 示例值                                     |
| ------------------- | ----------- | ---- | ------------- | ------------------------------------------ |
| id                  | bigint      | 是   | 主键          | 1                                          |
| model_key           | varchar(50) | 是   | 模型标识        | gpt-3.5-turbo                              |
| model_name          | varchar(100)| 是   | 模型名称      | GPT-3.5 Turbo                              |
| provider            | varchar(50) | 是   | 提供商        | openai                                     |
| model_type          | varchar(50) | 是   | 模型类型      | gpt-3.5-turbo                              |
| is_enabled          | boolean     | 否   | 是否启用        | true                                       |
| is_default          | boolean     | 否   | 是否默认        | false                                      |
| max_tokens          | int         | 否   | 最大token数   | 4000                                       |
| temperature_default | decimal     | 否   | 默认温度        | 0.7                                        |
| temperature_min     | decimal     | 否   | 温度最小值      | 0.0                                        |
| temperature_max     | decimal     | 否   | 温度最大值      | 2.0                                        |
| cost_per_1k_input   | decimal     | 否   | 输入成本        | 0.0015                                     |
| cost_per_1k_output  | decimal     | 否   | 输出成本        | 0.0020                                     |
| rate_limit_rpm      | int         | 否   | RPM限制        | 60                                         |
| rate_limit_tpm      | int         | 否   | TPM限制        | 90000                                      |
| allowed_roles       | json        | 否   | 允许角色列表      | ["student", "teacher"]                     |
| created_by_id       | int         | 否   | 创建人ID      | 1                                          |
| updated_by_id       | int         | 否   | 更新人ID      | 1                                          |
| owner_organization_id| int        | 否   | 所属组织ID    | 1                                          |
| is_deleted          | boolean     | 否   | 软删除标志    | false                                      |
| remark              | varchar(255)| 否   | 备注          | NULL                                       |
| created_at          | datetime    | 是   | 创建时间      | 自动生成                                   |
| updated_at          | datetime    | 是   | 更新时间      | 自动更新                                   |

**索引设计**：

```sql
UNIQUE INDEX uk_model_key (model_key)
```

------

### 2.2.6 API Key管理实体 (AIApiKey)

**实体说明**：管理各AI提供商的API Key及其用量

**字段定义**：

| 字段名              | 类型        | 必填 | 说明          | 示例值                                     |
| ------------------- | ----------- | ---- | ------------- | ------------------------------------------ |
| id                  | bigint      | 是   | 主键          | 1                                          |
| provider            | varchar(50) | 是   | 提供商        | openai                                     |
| key_name            | varchar(100)| 是   | Key名称       | OpenAI-Default                             |
| api_key_encrypted   | text        | 是   | 加密后的API Key | sdfsf34234...                              |
| is_active           | boolean     | 否   | 是否启用        | true                                       |
| priority            | int         | 否   | 优先级        | 10                                         |
| daily_token_limit   | bigint      | 否   | 每日token限制 | 1000000                                    |
| monthly_token_limit | bigint      | 否   | 每月token限制 | 50000000                                   |
| daily_tokens_used   | bigint      | 否   | 今日已用token | 1500                                       |
| monthly_tokens_used | bigint      | 否   | 本月已用token | 45000                                      |
| total_tokens_used   | bigint      | 否   | 总计已用token | 9500000                                    |
| total_cost          | decimal     | 否   | 总花费($)       | 15.40                                      |
| last_used_at        | datetime    | 否   | 最后使用时间      | 2024-03-10 15:30:00                        |
| last_error          | text        | 否   | 最后错误信息      | Rate Limit Exceeded                        |
| error_count         | int         | 否   | 连续错误次数      | 0                                          |
| created_by_id       | int         | 否   | 创建人ID      | 1                                          |
| updated_by_id       | int         | 否   | 更新人ID      | 1                                          |
| owner_organization_id| int        | 否   | 所属组织ID    | 1                                          |
| is_deleted          | boolean     | 否   | 软删除标志    | false                                      |
| remark              | varchar(255)| 否   | 备注          | NULL                                       |
| created_at          | datetime    | 是   | 创建时间      | 自动生成                                   |
| updated_at          | datetime    | 是   | 更新时间      | 自动更新                                   |

**索引设计**：

```sql
INDEX idx_provider_active (provider, is_active)
```

------

### 2.2.7 用户配额实体 (AIUserQuota)

**实体说明**：管控用户每日/每月的API调用限额

**字段定义**：

| 字段名              | 类型        | 必填 | 说明          | 示例值                                     |
| ------------------- | ----------- | ---- | ------------- | ------------------------------------------ |
| id                  | bigint      | 是   | 主键          | 1                                          |
| user_id             | int         | 是   | 用户ID        | 101                                        |
| quota_type          | varchar(20) | 是   | 配额类型        | daily / monthly / total                    |
| token_limit         | bigint      | 是   | Token限制       | 10000                                      |
| tokens_used         | bigint      | 否   | 已使用token     | 1500                                       |
| reset_at            | datetime    | 否   | 重置时间        | 2024-03-11 00:00:00                        |
| is_active           | boolean     | 否   | 是否启用        | true                                       |
| created_at          | datetime    | 是   | 创建时间      | 自动生成                                   |
| updated_at          | datetime    | 是   | 更新时间      | 自动更新                                   |

**索引设计**：

```sql
UNIQUE INDEX uk_user_quota_type (user_id, quota_type)
INDEX idx_reset_at (reset_at)
```

------

### 2.2.8 智能体配置实体 (AIAgentConfig)

**实体说明**：管理不同上下文下的AI预设Prompt与配置

**字段定义**：

| 字段名              | 类型        | 必填 | 说明          | 示例值                                     |
| ------------------- | ----------- | ---- | ------------- | ------------------------------------------ |
| id                  | bigint      | 是   | 主键          | 1                                          |
| agent_key           | varchar(50) | 是   | Agent标识     | linux_assistant                            |
| agent_name          | varchar(100)| 是   | Agent名称     | Linux助理                                    |
| description         | text        | 否   | 描述          | 专门解答Linux相关问题的助手                        |
| system_prompt       | text        | 是   | 系统提示词        | 你是一个专业的Linux运维工程师...                    |
| context_type        | varchar(50) | 否   | 适用上下文        | experiment                                 |
| model_config_id     | bigint      | 否   | 默认模型ID      | 1                                          |
| temperature         | decimal     | 否   | 温度          | 0.7                                        |
| max_tokens          | int         | 否   | 最大token数   | 2000                                       |
| enable_rag          | boolean     | 否   | 是否启用RAG      | true                                       |
| rag_top_k           | int         | 否   | RAG检索数量     | 3                                          |
| enable_memory       | boolean     | 否   | 是否启用记忆      | true                                       |
| memory_window       | int         | 否   | 记忆窗口大小      | 20                                         |
| language            | varchar(10) | 否   | 语言          | zh-CN                                      |
| is_active           | boolean     | 否   | 是否启用        | true                                       |
| created_by_id       | int         | 否   | 创建人ID      | 1                                          |
| updated_by_id       | int         | 否   | 更新人ID      | 1                                          |
| owner_organization_id| int        | 否   | 所属组织ID    | 1                                          |
| is_deleted          | boolean     | 否   | 软删除标志    | false                                      |
| remark              | varchar(255)| 否   | 备注          | NULL                                       |
| created_at          | datetime    | 是   | 创建时间      | 自动生成                                   |
| updated_at          | datetime    | 是   | 更新时间      | 自动更新                                   |

**索引设计**：

```sql
UNIQUE INDEX uk_agent_key (agent_key)
```

------

### 2.2.9 知识库状态实体 (AIKnowledgeIndexStatus)

**实体说明**：记录各实验文档的RAG向量库构建状态

**字段定义**：

| 字段名              | 类型        | 必填 | 说明          | 示例值                                     |
| ------------------- | ----------- | ---- | ------------- | ------------------------------------------ |
| id                  | bigint      | 是   | 主键          | 1                                          |
| guidebook_id        | bigint      | 是   | 被索引文档ID    | 1                                          |
| experiment_id       | bigint      | 否   | 归属实验ID      | 1                                          |
| status              | varchar(20) | 是   | 状态          | pending / processing / completed / failed  |
| chunk_num           | int         | 否   | 文档分出总片数    | 150                                        |
| remark              | text        | 否   | 备注/错误原因     | PDF解析失败                                    |
| created_at          | datetime    | 是   | 创建时间      | 自动生成                                   |
| updated_at          | datetime    | 是   | 更新时间      | 自动更新                                   |

**索引设计**：

```sql
UNIQUE INDEX uk_knowledge_guidebook (guidebook_id)
INDEX idx_knowledge_sts (status)
```

------

### 2.2.10 AI使用记录实体 (AIUsageLog)

**实体说明**：明细记录每次API调用的Token和计费信息，用于报表和对账

**字段定义**：

| 字段名              | 类型        | 必填 | 说明          | 示例值                                     |
| ------------------- | ----------- | ---- | ------------- | ------------------------------------------ |
| id                  | bigint      | 是   | 主键          | 1                                          |
| user_id             | int         | 是   | 用户ID        | 101                                        |
| conversation_id     | bigint      | 否   | 会话ID        | 1                                          |
| message_id          | bigint      | 否   | 消息ID        | 10                                         |
| model_key           | varchar(50) | 是   | 模型表示        | gpt-3.5-turbo                              |
| api_key_id          | bigint      | 否   | 使用的API Key ID| 1                                          |
| prompt_tokens       | int         | 否   | 提问用量        | 120                                        |
| completion_tokens   | int         | 否   | 回复用量        | 350                                        |
| total_tokens        | int         | 否   | 总计用量        | 470                                        |
| cost                | decimal     | 否   | 估算计费($)       | 0.0012                                     |
| latency_ms          | int         | 否   | 响应延迟(毫秒)   | 1540                                       |
| status              | varchar(20) | 否   | 调用最终状态      | success / error                            |
| error_message       | text        | 否   | 错误详情        | NULL                                       |
| created_at          | datetime    | 是   | 创建时间      | 自动生成                                   |

**索引设计**：

```sql
INDEX idx_user_created (user_id, created_at)
INDEX idx_conversation (conversation_id)
INDEX idx_status (status, created_at)
```

------

## 2.3 后端API设计

### 2.3.1 对话会话API

**基础路径**：`/api/v1/chat/conversations/`

#### 1) 创建会话

```http
POST /api/v1/chat/conversations/
```

**请求体**：

```json
{
  "context_type": "experiment",
  "context_id": "1",
  "model_key": "gpt-4",
  "temperature": 0.8,
  "context_data": {
    "experiment_id": 1,
    "experiment_title": "Linux用户管理实验",
    "guidebook_id": 1
  }
}
```

**响应示例**：

```json
{
  "code": 201,
  "message": "会话创建成功",
  "data": {
    "id": 1,
    "session_id": "a1b2c3d4e5f6...",
    "title": "新对话",
    "message_count": 0,
    "created_at": "2024-03-10T15:00:00Z"
  }
}
```

*注：生成标题由后端在第一条消息发送后异步执行：*
```python
# 在 POST /messages/ 接口中
if conversation.message_count == 1:
    generate_conversation_title.delay(conversation.id)
```

#### 2) 获取我的会话列表

```http
GET /api/v1/chat/conversations/my/
```

**请求参数**：

```json
{
  "page": 1,
  "page_size": 20,
  "is_archived": false,
  "context_type": "experiment"   // 可选：筛选实验相关对话
}
```

**响应示例**：

```json
{
  "code": 200,
  "data": {
    "total": 8,
    "results": [
      {
        "id": 1,
        "session_id": "a1b2c3d4...",
        "title": "关于Linux用户管理的提问",
        "message_count": 15,
        "last_message_at": "2024-03-10T15:30:00Z",
        "last_message_preview": "chmod命令用于修改文件权限...",
        "context_data": {
          "experiment_title": "Linux用户管理实验"
        },
        "created_at": "2024-03-10T14:00:00Z"
      }
    ]
  }
}
```

#### 3) 获取会话详情

```http
GET /api/v1/chat/conversations/{id}/
```

**响应示例**：

```json
{
  "code": 200,
  "data": {
    "id": 1,
    "session_id": "a1b2c3d4...",
    "title": "关于Linux用户管理的提问",
    "context_type": "experiment",
    "context_data": {
      "experiment_id": 1,
      "experiment_title": "Linux用户管理实验",
      "guidebook_id": 1
    },
    "message_count": 15,
    "messages": [
      {
        "id": 1,
        "role": "human",
        "content": "请问如何创建一个新用户？",
        "sequence": 1,
        "created_at": "2024-03-10T14:05:00Z"
      },
      {
        "id": 2,
        "role": "ai",
        "content": "在Linux中创建新用户可以使用 `useradd` 命令...",
        "sequence": 2,
        "prompt_tokens": 450,
        "completion_tokens": 120,
        "total_tokens": 570,
        "created_at": "2024-03-10T14:05:05Z"
      }
    ],
    "created_at": "2024-03-10T14:00:00Z"
  }
}
```

#### 4) 删除会话

```http
DELETE /api/v1/chat/conversations/{id}/
```

**业务规则**：
- 执行**软删除**（设置 `is_deleted = true`）。
- 不会级联删除下属的 `ChatMessage` 和 `ChatConversationSummary`，但在应用层根据会话的 `is_deleted` 进行关联过滤。
- 若会话有正在生成的AI回复请求，应拒绝删除或标记该请求为失效。

#### 5) 归档会话

```http
POST /api/v1/chat/conversations/{id}/archive/
```

**业务规则**：
- 设置 `is_archived = true`。归档后的会话将从常规“我的会话列表”隐藏。
- 归档会话**设为只读**，无法继续发送消息。
- 目前不支持取消归档功能（留作未来扩展）。
- 可设置定时任务，将会话列表中超过30天未活跃的消息自动归档。


------

### 2.3.2 消息API

**基础路径**：`/api/v1/chat/messages/`

#### 1) 发送消息（核心接口）

```http
POST /api/v1/chat/conversations/{conversation_id}/messages/
```

**请求体**：

```json
{
  "content": "请问chmod 755是什么意思？"
}
```

**响应示例**（Server-Sent Events 流式响应）：

```text
HTTP/1.1 200 OK
Content-Type: text/event-stream
Cache-Control: no-cache
Connection: keep-alive

event: user_message
data: {"id": 10, "role": "human", "content": "请问chmod 755是什么意思？", "sequence": 19, "created_at": "2024-03-10T15:30:00Z"}

event: content_chunk
data: {"chunk": "chmod"}

event: content_chunk
data: {"chunk": " 755 "}

event: content_chunk
data: {"chunk": "是Linux"}

event: assistant_message
data: {"id": 11, "role": "ai", "content": "chmod 755 是Linux文件权限设置命令...", "sequence": 20, "sources": [{"guidebook_id": 1, "page": 3, "content_snippet": "chmod命令用于修改文件权限..."}], "created_at": "2024-03-10T15:30:05Z"}
```

**后端处理流程**：

1. 保存用户消息到数据库
2. 获取对话上下文（实验、指导书）
3. RAG检索相关文档片段
4. 构建LangChain提示词
5. 调用OpenAI API
6. 保存AI回复到数据库
7. 返回响应

#### 2) 消息反馈

```http
POST /api/v1/chat/messages/{id}/feedback/
```

**请求体**：

```json
{
  "feedback": "helpful",        // helpful / not_helpful
  "feedback_detail": "回答很准确，帮我解决了问题"
}
```

**响应示例**：

```json
{
  "code": 200,
  "message": "反馈成功",
  "data": null
}
```

------

### 2.3.3 管理端 - AI平台配置API

#### 1) 模型配置管理
```http
GET /api/v1/admin/ai/models/
```
**请求参数**： `?page=1&page_size=20&provider=openai`
**响应示例**：返回带有分页的 `ai_model_config` 列表树，见表设计。

```http
POST /api/v1/admin/ai/models/
PUT /api/v1/admin/ai/models/{id}/
```
**请求体**：包含 `model_key, model_name, provider...` 等全量配置。
**响应**：成功保存的模型结构体。

```http
POST /api/v1/admin/ai/models/{id}/toggle/
```
**说明**：批量/单独快捷切换 `is_enabled` 状态。

#### 2) API Key管理
```http
GET /api/v1/admin/ai/api-keys/
POST /api/v1/admin/ai/api-keys/
```
**安全说明**：保存将对传来的 key 通过 `AES-256` (结合环境 SECRET_KEY) 执行加密后落库。查询列表将**脱敏**隐藏真实的 `api_key_encrypted`，只显示后缀4位。

```http
GET /api/v1/admin/ai/api-keys/{id}/usage/
```
**说明**：返回该 Key 过去30天及每天详尽的 Token 开销日历。

```http
POST /api/v1/admin/ai/api-keys/{id}/rotate/
POST /api/v1/admin/ai/api-keys/{id}/disable/
```
**轮换逻辑**：当选择 rotate 时，系统支持录入新 Key 替换旧 Key，旧 Key 的状态标记为 `is_active=false` 进行安全降级。如果当前正在有连接池使用旧 Key，其生命周期结束前依然可通信，新的请求路由将调度至新 Key，实现可用性平滑切换。

#### 3) 用户配额管理 (单点及批量)
```http
GET /api/v1/admin/ai/quotas/?user_id={user_id}
POST /api/v1/admin/ai/quotas/
POST /api/v1/admin/ai/quotas/batch-set/
POST /api/v1/admin/ai/quotas/{id}/reset/
```
**时区逻辑**：`reset_at` 等日/月清零定时任务，全端严格使用 **UTC标准时间** 作为运算和对账基准，前端渲染根据浏览器时区自动 Localize。

#### 4) 智能体配置
```http
GET /api/v1/admin/ai/agents/
POST /api/v1/admin/ai/agents/
POST /api/v1/admin/ai/agents/{id}/test/
```
**响应**：对于 test 接口，后管直接发起沙盒评测返回对答耗时和分数。针对 `system_prompt` 的修改，提供内部的历史流转记录（如 `revision_id` 管理）。

#### 5) 知识库与全局统计 API
```http
# 知识库管理
GET /api/v1/admin/ai/knowledge/indexes/        # 查看全局文件索引队列
POST /api/v1/admin/ai/knowledge/indexes/rebuild/ # 重新触发异常文档构建

# 全局数据看板报表
GET /api/v1/admin/ai/stats/overview/           # 包含整体Token，API调用次数，总成本等
GET /api/v1/admin/ai/stats/usage-trend/        # 近30天每日使用趋势
```

### 2.3.4 用户端 - 模型选择与配额接口

#### 1) 获取可用模型列表
```http
GET /api/v1/chat/models/available/
```
**响应示例**：
```json
{
  "code": 200,
  "data": [
    {
      "model_key": "gpt-3.5-turbo",
      "model_name": "GPT-3.5 Turbo",
      "model_type": "gpt-3.5-turbo",
      "provider": "openai",
      "max_tokens": 4000,
      "requires_permission": false
    }
  ]
}
```
**业务逻辑**：后端仅返回开启了 `is_enabled=true` 且该用户的当前权限/角色数组位于配置 `allowed_roles` 交集以内的模型。如果用户通过接口恶意提交受限 `model_key`，服务端核心将在拦截器严格拦截。

#### 2) 查看我的配额使用情况
```http
GET /api/v1/chat/my-quota/
```
**响应示例**：返回用户的 daily 及 monthly 已用/总限额和下次重置 UTC 时间。

#### 3) 教师视角：旁路看护学生交互 (预留接口)
```http
GET /api/v1/chat/teacher/students/{student_id}/conversations/
GET /api/v1/chat/teacher/experiments/{experiment_id}/conversations/
```
**请求参数**： `?page=1&page_size=20&status=active`
**权限校验**：系统先反查该 `teacher_id` 当前是否有权查看参数中对应的学生或教授该实验节点。返回值等同于“获取对话详情” API 的结构，但在前端屏蔽 `回复` 与 `操作重试` 按钮。
**审计防范**：无论是教师还是管理员提取敏感的对话明细以及管理端的操作（增删配额，导出Token账单等），操作全链路通过系统拦截器写入 **系统操作审计表 (SystemAuditLog)**。

------

## 2.4 后端核心实现逻辑 (LangChain 及工具类)


### 2.4.1 RAG检索链与大模型调用组装

```python
# chat/langchain_service.py
from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings
from langchain.chat_models import ChatOpenAI
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from functools import lru_cache

@lru_cache(maxsize=10)
def get_cached_vectorstore(guidebook_id):
    embeddings = OpenAIEmbeddings()
    return Chroma(
        persist_directory=f"./chroma_db/guidebook_{guidebook_id}",
        embedding_function=embeddings
    )

class AIAssistantService:
    
    def __init__(self, user_id, model_key=None):
        self.user_id = user_id
        
        # 1. 前置配额检查（异常直接抛出，终止消耗）
        QuotaManager.check_quota(self.user_id, estimated_tokens=100)
        
        # 2. 获取防崩溃模型配置
        try:
            if not model_key:
                model_config = AIModelConfig.objects.get(is_default=True)
            else:
                model_config = AIModelConfig.objects.get(model_key=model_key, is_enabled=True)
                
            # 角色访问限制在此处可补权限校验逻辑验证 user 的 role
        except Exception:
            raise Exception("您请求的模型目前不存在或处于不可用状态！")
            
        self.model_config = model_config
        
        # 3. 动态获取防超限API Key
        self.api_key_id, api_key = APIKeyManager.get_available_key(
            provider=model_config.provider
        )
        
        # 4. 初始化健壮的大语言模型包装器
        self.llm = ChatOpenAI(
            model_name=model_config.model_type,
            temperature=model_config.temperature_default,
            openai_api_key=api_key,
            max_tokens=model_config.max_tokens,
            max_retries=2
        )
    
    def get_response(self, conversation_id, user_question):
        """获取AI回复"""
        
        # 1. 获取会话上下文
        conversation = ChatConversation.objects.get(id=conversation_id)
        context = ChatExperimentContext.objects.get(conversation_id=conversation_id)
        
        # 3. 如果没有关联实验指导书，则走普通对话
        if not context.guidebook_id:
            # 记录基础费用...
            return {
                'answer': self.llm.invoke(user_question).content,
                'sources': [],
                'tokens': {}
            }
            
        # 4. 加载向量数据库 (使用LRU缓存)
        vectorstore = get_cached_vectorstore(context.guidebook_id)
        
        # 4. 检索相关文档，加入严格的相关性过滤
        raw_docs = vectorstore.similarity_search_with_score(user_question, k=4)
        filtered_docs = [doc for doc, score in raw_docs if score > 0.5] # 根据距离算法设定合适的评分边界
        # 提取真实对象传递给链
        docs = [doc for doc, _ in filtered_docs[:3]]
        
        # 5. 获取对话历史（需要考虑已摘要的消息）
        summaries = ChatConversationSummary.objects.filter(
            conversation_id=conversation_id
        ).order_by('message_range_start')
        
        last_summarized_seq = summaries.last().message_range_end if summaries else 0
        messages = ChatMessage.objects.filter(
            conversation_id=conversation_id,
            sequence__gt=last_summarized_seq
        ).order_by('sequence')
        
        chat_history = []
        for msg in messages:
            chat_history.append((msg.role, msg.content))
        
        # 6. 构建检索链
        memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        
        # 将摘要作为历史指示注入
        if summaries:
            combined_summary = "\n".join([s.summary_content for s in summaries])
            memory.chat_memory.add_system_message(f"我们之前的对话摘要：{combined_summary}")
        
        # 填充历史记录
        for role, content in chat_history:
            if role == "human":
                memory.chat_memory.add_user_message(content)
            else:
                memory.chat_memory.add_ai_message(content)
        
        qa_chain = ConversationalRetrievalChain.from_llm(
            llm=self.llm,
            retriever=vectorstore.as_retriever(search_kwargs={"k": 3}),
            memory=memory,
            return_source_documents=True
        )
        
        # 7. 结合 Agent Config 提示词模板构建内容
        # AI 系统从 ai_agent_config 取回基于当前上下文的智能体 Prompt，如：
        experiment_title = context.experiment.title if context.experiment else "通用学习"
        current_step = context.submission.current_step if context.submission else "未知"
        
        # 8. 获取回复 & 记录额度及使用量日志
        try:
            result = qa_chain({
                "question": user_question,
                "chat_history": chat_history
            })
            
            answer = result['answer']
            sources = result['source_documents']
            prompt_tokens = result.get('prompt_tokens', 0)
            completion_tokens = result.get('completion_tokens', 0)
            tokens = result.get('total_tokens', 0)
            cost = tokens * 0.000001 # 简单折算例子

            # 扣除额度与计重
            APIKeyManager.record_usage(self.api_key_id, tokens, cost)
            QuotaManager.deduct_quota(self.user_id, tokens)
            
            AIUsageLog.objects.create(
                user_id=self.user_id,
                conversation_id=conversation_id,
                model_key=self.model_config.model_key,
                api_key_id=self.api_key_id,
                total_tokens=tokens,
                cost=cost,
                status='success'
            )
            
            return {
                'answer': answer,
                'sources': sources,
                'tokens': {
                    'prompt': prompt_tokens,
                    'completion': completion_tokens,
                    'total': tokens
                }
            }
        except Exception as e:
            APIKeyManager.record_error(self.api_key_id, str(e))
            raise e
```

### 2.4.2 文档索引构建与异步状态回控

```python
# chat/document_indexer.py
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings

def index_guidebook(guidebook_id):
    """为指导书建立向量索引"""
    guidebook = CourseGuidebook.objects.get(id=guidebook_id)
    
    # 1. 获取文本内容
    text_content = guidebook.text_content
    if not text_content:
        raise ValueError("文档未提取文本内容")
    
    # 2. 文本分块
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,           # 每块500字符
        chunk_overlap=50,         # 重叠50字符
        separators=["\n\n", "\n", "。", "！", "？", " "]
    )
    
    chunks = text_splitter.split_text(text_content)
    
    # 3. 构建元数据
    metadatas = []
    for i, chunk in enumerate(chunks):
        metadatas.append({
            'guidebook_id': guidebook_id,
            'chunk_index': i,
            'experiment_id': guidebook.experiment_id,
            'source': guidebook.file_name
        })
    
    # 4. 创建向量数据库
    embeddings = OpenAIEmbeddings()
    vectorstore = Chroma.from_texts(
        texts=chunks,
        embedding=embeddings,
        metadatas=metadatas,
        persist_directory=f"./chroma_db/guidebook_{guidebook_id}"
    )
    
    vectorstore.persist()
    
    # 5. 更新核心库索引总表状态，与该文档自身的统计联动
    AIKnowledgeIndexStatus.objects.update_or_create(
        guidebook_id=guidebook_id,
        defaults={
            'status': 'completed',
            'chunk_num': len(chunks),
            'experiment_id': guidebook.experiment_id,
        }
    )
    return len(chunks)
```

### 2.4.3 Celery异步通信与死信转移

```python
# chat/tasks.py
from celery import shared_task

@shared_task(bind=True, max_retries=3)
def index_guidebook_async(self, guidebook_id):
    """异步建立文档索引带重试"""
    try:
        AIKnowledgeIndexStatus.objects.update_or_create(guidebook_id=guidebook_id, defaults={'status': 'processing'})
        chunk_count = index_guidebook(guidebook_id)
        return f"索引完成，共{chunk_count}个分块"
    except Exception as e:
        try:
             # 如果遇到特定连接异常，通过指数退避触发重试
             self.retry(exc=e, countdown=2 ** self.request.retries)
        except MaxRetriesExceededError:
            # 死信状态更新
            AIKnowledgeIndexStatus.objects.update_or_create(guidebook_id=guidebook_id, defaults={'status': 'failed', 'remark': str(e)})
        raise e
```

------

## 2.5 前端设计

### 2.5.1 AI管理中心全局布局 (管理端)

**页面路由**： `/admin/ai/dashboard` 等关联子域。
**主要包含以下聚合Tab**：
1. **统一数据看板模块 (Dashboard)**:
    - 卡片：本月Token开销总和，活跃用户，调用总频率。
    - 图表：柱状图呈现不同模型与API Key用量的高低峰走势；响应时间监控报表。
2. **AI引擎与额度层**:
   - `模型配置表格`: 枚举模型名，单价，启停开关。配备新建/编辑长表单组件。
   - `API密匙收纳匣`: 脱敏明文显示。显示每个Key可用性的心跳状态、配额耗尽预警进度条和轮换(Rotate)按钮。
   - `用户策略下推表`: 利用虚拟滚动表格或带搜索的翻页功能，管理员可在此批量复选学生群体并通过组件实施“每月万字”Token下发。
3. **内容管控枢纽**:
   - `智能体配置台`: 挂载了对 System Prompt 微调版本的控制逻辑（包含应用哪个分支的提示词进行A/B对比体验）。
   - `知识库大盘`: 展示自实验模块接收过来异步处理中的知识文件总表，对于 `status=failed` 的数据行，直观抛出重建(`rebuild`)按钮一键派发新任务到 Celery。

### 2.5.2 全局助手浮动交互窗 (用户端)

**组件描述**：由于系统用户在阅读实验文档及调试虚拟环境时需要频发与 AI 对话，**单建页面不再适合**，因此将对话核心重构为悬浮至全局架构。
1. **固定锚位**：页面右下角恒定显示一个脉冲特效的 AI Robot 圆形图标，支持拖拽。
2. **气泡唤醒与路由守护**：
    - 点击图标向左上滑入弹出 350px 宽的悬浮抽屉交互面板。
    - 面板中的历史消息队列采用**前端框架的数据持久层技术（例如 Pinia 的 persist 插件，混合 LocalStorage 持久化）**存储关键的草稿与暂存ID，保证即使切换顶部大功能路由，AI界面及等待流回调仍旧保持。
    - 为面板配备未读红点数字角标（AI 返回了结果但用户抽屉被最小化时激活）。
3. **平滑演变**：对话过程中如果用户改变了侧边栏的模型选项（比如从基础模型转为高级模型）：
    - 界面提示用户模型即期生效。
    - 背景上下文历史无缝带入新引擎。而后台针对该次问答产生的算力明细账单，则实时切割按照新模型单据扣除额度和计入使用量表。

### 2.5.3 消息渲染窗细节剖析


```vue
<template>
  <div class="ai-chat-container">
    <!-- 会话列表（左侧侧边栏） -->
    <a-layout-sider :width="280" class="conversation-sidebar">
      <div class="sidebar-header">
        <h3>AI助手</h3>
        <a-button type="primary" @click="createNewConversation">
          <icon-plus /> 新对话
        </a-button>
      </div>
      
      <a-menu
        :selected-keys="[currentConversationId]"
        @menu-item-click="switchConversation"
      >
        <a-menu-item 
          v-for="conv in conversations" 
          :key="conv.id"
        >
          <div class="conversation-item">
            <div class="conv-title">{{ conv.title }}</div>
            <div class="conv-meta">
              <span>{{ conv.message_count }}条消息</span>
              <span>{{ formatTime(conv.last_message_at) }}</span>
            </div>
          </div>
        </a-menu-item>
      </a-menu>
    </a-layout-sider>
    
    <!-- 对话区域 -->
    <a-layout-content class="chat-content">
      <!-- 上下文提示 -->
      <div v-if="currentContext" class="context-banner">
        <icon-info-circle />
        <span>当前在 《{{ currentContext.experiment_title }}》 实验中提问</span>
      </div>
      
      <!-- 消息列表 -->
      <div ref="messageListRef" class="message-list">
        <div 
          v-for="message in messages" 
          :key="message.id"
          :class="['message-item', message.role]"
        >
          <!-- 用户消息 -->
          <div v-if="message.role === 'human'" class="user-message">
            <a-avatar :size="32">{{ username[0] }}</a-avatar>
            <div class="message-bubble">
              <div class="message-content">{{ message.content }}</div>
              <div class="message-time">{{ formatTime(message.created_at) }}</div>
            </div>
          </div>
          
          <!-- AI回复 -->
          <div v-else-if="message.role === 'ai'" class="assistant-message">
            <a-avatar :size="32" style="background-color: #165dff">
              <icon-robot />
            </a-avatar>
            <div class="message-bubble">
              <div class="message-content">
                <markdown-viewer :content="message.content" />
              </div>
              
              <!-- 引用来源 -->
              <div v-if="message.sources && message.sources.length" class="sources">
                <a-divider style="margin: 8px 0" />
                <div class="source-title">参考来源：</div>
                <div v-for="(source, idx) in message.sources" :key="idx" class="source-item">
                  <a-tag>{{ source.source }}</a-tag>
                  <span>{{ source.content_snippet }}</span>
                </div>
              </div>
              
              <div class="message-actions">
                <span class="message-time">{{ formatTime(message.created_at) }}</span>
                <a-space>
                  <a-button 
                    type="text" 
                    size="mini"
                    @click="() => feedbackMessage(message.id, 'helpful')"
                  >
                    <icon-thumb-up />
                  </a-button>
                  <a-button 
                    type="text" 
                    size="mini"
                    @click="() => feedbackMessage(message.id, 'not_helpful')"
                  >
                    <icon-thumb-down />
                  </a-button>
                  <a-button type="text" size="mini" @click="copyMessage(message.content)">
                    <icon-copy />
                  </a-button>
                </a-space>
              </div>
            </div>
          </div>
        </div>
        
        <!-- 加载中 -->
        <div v-if="isLoading" class="message-item assistant-message">
          <a-avatar :size="32" style="background-color: #165dff">
            <icon-robot />
          </a-avatar>
          <div class="message-bubble loading">
            <a-spin />
            <span>AI正在思考中...</span>
          </div>
        </div>
      </div>
      
      <!-- 输入框 -->
      <div class="input-area">
        <a-textarea
          v-model="inputMessage"
          placeholder="输入你的问题..."
          :auto-size="{ minRows: 1, maxRows: 4 }"
          @press-enter="handleSendMessage"
        />
        <a-button 
          type="primary" 
          :loading="isLoading"
          :disabled="!inputMessage.trim()"
          @click="sendMessage"
        >
          发送
        </a-button>
      </div>
    </a-layout-content>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { 
  getConversations, 
  getConversationMessages, 
  sendMessage as sendMessageAPI 
} from '@/api/chat'

const conversations = ref([])
const currentConversationId = ref(null)
const messages = ref([])
const inputMessage = ref('')
const isLoading = ref(false)
const messageListRef = ref(null)

const sendMessage = async () => {
  if (!inputMessage.value.trim()) return
  
  const userMessage = inputMessage.value
  inputMessage.value = ''
  
  const tempId = Date.now()
  // 立即显示用户消息
  messages.value.push({
    id: tempId,
    role: 'human',
    content: userMessage,
    created_at: new Date()
  })
  
  scrollToBottom()
  
  try {
    isLoading.value = true
    
    // 使用 fetch 获取 SSE 流式响应
    const response = await fetch(`/api/v1/chat/conversations/${currentConversationId.value}/messages/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content: userMessage })
    })
    
    if (!response.ok) {
      if (response.status === 429) throw new Error('请求过于频繁，请稍后再试')
      if (response.status === 402) throw new Error('使用配额已满，请联系管理员或下周期重试')
      throw new Error('网络连接失败')
    }
    
    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let aiMessageObj = null
    let buffer = ''
    
    while (true) {
      const { value, done } = await reader.read()
      if (done) break
      
      buffer += decoder.decode(value, { stream: true })
      const events = buffer.split('\n\n')
      buffer = events.pop() // 保留不完整的部分
      
      for (const eventBlock of events) {
        const lines = eventBlock.split('\n')
        let currentEvent = ''
        for (const line of lines) {
          if (line.startsWith('event: ')) {
            currentEvent = line.substring(7)
          } else if (line.startsWith('data: ')) {
            const data = JSON.parse(line.substring(6))
            if (currentEvent === 'user_message') {
              const tempIndex = messages.value.findIndex(m => m.id === tempId)
              if (tempIndex !== -1) messages.value[tempIndex] = data
            } else if (currentEvent === 'content_chunk') {
              if (!aiMessageObj) {
                aiMessageObj = { id: Date.now(), role: 'ai', content: '', created_at: new Date() }
                messages.value.push(aiMessageObj)
              }
              aiMessageObj.content += data.chunk
              scrollToBottom()
            } else if (currentEvent === 'assistant_message') {
               const index = aiMessageObj ? messages.value.findIndex(m => m.id === aiMessageObj.id) : -1
               if (aiMessageObj && index !== -1) {
                 messages.value[index] = data
               } else if (!aiMessageObj) {
                 messages.value.push(data)
               }
            }
          }
        }
      }
    }
  } catch (error) {
    Message.error(error.message || '发送失败')
  } finally {
    isLoading.value = false
  }
}

const scrollToBottom = () => {
  nextTick(() => {
    if (messageListRef.value) {
      messageListRef.value.scrollTop = messageListRef.value.scrollHeight
    }
  })
}

const feedbackMessage = async (messageId, feedback) => {
  try {
    await feedbackMessageAPI(messageId, { feedback })
    Message.success('感谢您的反馈')
  } catch (error) {
    Message.error('反馈失败')
  }
}

onMounted(() => {
  loadConversations()
})
</script>

<style scoped lang="scss">
.ai-chat-container {
  display: flex;
  height: 100vh;
  
  .conversation-sidebar {
    border-right: 1px solid var(--color-border);
    background: #fff;
    
    .sidebar-header {
      padding: 16px;
      border-bottom: 1px solid var(--color-border);
      
      h3 {
        margin-bottom: 12px;
      }
    }
  }
  
  .chat-content {
    display: flex;
    flex-direction: column;
    height: 100%;
    
    .context-banner {
      padding: 12px 16px;
      background: #f7f8fa;
      border-bottom: 1px solid var(--color-border);
      color: #4e5969;
    }
    
    .message-list {
      flex: 1;
      overflow-y: auto;
      padding: 24px;
      
      .message-item {
        margin-bottom: 24px;
        
        &.user-message {
          display: flex;
          justify-content: flex-end;
          
          .message-bubble {
            background: #165dff;
            color: #fff;
            border-radius: 12px 12px 0 12px;
            padding: 12px 16px;
            max-width: 60%;
            margin-right: 8px;
          }
        }
        
        &.assistant-message {
          display: flex;
          
          .message-bubble {
            background: #f7f8fa;
            border-radius: 12px 12px 12px 0;
            padding: 12px 16px;
            max-width: 70%;
            margin-left: 8px;
            
            &.loading {
              display: flex;
              align-items: center;
              gap: 8px;
            }
          }
          
          .sources {
            margin-top: 8px;
            font-size: 12px;
            color: #86909c;
          }
          
          .message-actions {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-top: 8px;
          }
        }
      }
    }
    
    .input-area {
      padding: 16px;
      border-top: 1px solid var(--color-border);
      display: flex;
      gap: 12px;
      align-items: flex-end;
    }
  }
}
</style>
```

------

### 2.4.2 实验页面集成AI助手

在学生查看实验指导书或编辑报告时，提供AI助手入口：

```vue
<template>
  <div class="experiment-page">
    <!-- 页面内容... -->
    
    <!-- AI助手浮动按钮 -->
    <a-button 
      type="primary" 
      shape="circle" 
      size="large"
      class="ai-assistant-fab"
      @click="openAIAssistant"
    >
      <icon-robot />
    </a-button>
    
    <!-- AI助手抽屉 -->
    <a-drawer
      v-model:visible="aiDrawerVisible"
      title="AI助手"
      :width="600"
      placement="right"
    >
      <ai-chat-panel 
        :context-type="'experiment'"
        :context-id="experimentId"
        :context-data="contextData"
      />
    </a-drawer>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import AIChatPanel from '@/components/AIChatPanel.vue'

const aiDrawerVisible = ref(false)
const experimentId = ref(1)

const contextData = computed(() => ({
  experiment_id: experimentId.value,
  experiment_title: '当前实验标题',
  guidebook_id: 1,
  current_step: 3
}))

const openAIAssistant = () => {
  aiDrawerVisible.value = true
}
</script>

<style scoped>
.ai-assistant-fab {
  position: fixed;
  right: 32px;
  bottom: 32px;
  width: 56px;
  height: 56px;
  font-size: 24px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 1000;
}
</style>
```

### 2.5.4 会话属性与配额悬浮卡片

**配额卡片（挂载在展开的助手抽屉侧边栏）**：

```vue
<template>
  <div class="quota-card">
    <h4>使用配额</h4>
    <a-progress 
      :percent="quotaPercent" 
      :status="quotaStatus"
    />
    <p>今日已用: {{ quota.daily.used }} / {{ quota.daily.limit }} tokens</p>
    <p>本月已用: {{ quota.monthly.used }} / {{ quota.monthly.limit }} tokens</p>
    <p>重置时间: {{ formatTime(quota.daily.reset_at) }}</p>
  </div>
</template>
```

**创建会话-模型选择与参数配置弹窗**：

```vue
<template>
  <a-modal v-model:visible="visible" title="选择AI模型">
    <a-radio-group v-model="selectedModel">
      <a-space direction="vertical">
        <a-radio 
          v-for="model in availableModels" 
          :key="model.model_key"
          :value="model.model_key"
          :disabled="model.requires_permission && !hasPermission"
        >
          <div class="model-option">
            <strong>{{ model.model_name }}</strong>
            <p>{{ model.description }}</p>
            <a-tag v-if="model.is_default">默认</a-tag>
            <a-tag v-if="model.requires_permission" color="orange">需要权限</a-tag>
          </div>
        </a-radio>
      </a-space>
    </a-radio-group>
    
    <a-divider />
    
    <a-form-item label="温度参数">
      <a-slider 
        v-model="temperature" 
        :min="currentModel.temperature_min"
        :max="currentModel.temperature_max"
        :step="0.1"
      />
      <span>{{ temperature }}</span>
    </a-form-item>
  </a-modal>
</template>
```

------

## 2.6 核心业务与控制链路

### 2.6.1 访问频率限制 (Rate Limit) 防范

平台应对模型服务层的安全瓶颈问题进行防护，引入基于 Redis 的“令牌桶”(Token Bucket)算法拦截层，与模型库里的 `rate_limit_rpm` 对应：

1. HTTP网关到达前：判定当前 User 对模型的 `/get_response/` 单位时间内并发数。
2. 满载打回：直接抛出类似 429 协议码被前端捕捉提示“并发超出”。
3. 突发容错：API Key 调度管理采用队列形式对溢出的非实时长队列使用时间交换安全。

### 2.6.2 学生提问流程全景

```
1. 学生点击全局工具栏"AI伪娘"按钮
   ↓
2. 系统唤起全局共享侧边栏
   ├─ 有待响应进程 → 加载中回放
   └─ 无 → 从缓存映射最新的当前历史
   ↓
3. 前端读取并附加本地模型偏好，发送请求
   ↓
4. AI 网关基于 Token 拦截与 权限鉴别
   ↓
5. 后端组装并调用 OpenAI 通信链
   ↓
6. 返回AI回复并结算配额消耗
```

### 2.6.3 异步死信兜底及队列解耦

此模块保障实验子系统（教学文档侧）与AI数据知识侧互相透明及不被宕机阻塞。消息队列若崩溃：
- **解耦模式**：异步发送 MQ，若发送丢失提供手动重放API工具。
- **协议框架**：
```python
message = {
    'event': 'guidebook_uploaded',
    'guidebook_id': guidebook.id,
    'file_path': guidebook.file_path,
    'retry_counts': 0, # 重试标签位
    'timestamp': datetime.now().isoformat()
}
producer.send('ai_index_pipeline', json.dumps(message))
```

------

## 2.7 计费控制技术实现要点

### 2.7.1 成本调度与API代理

```python
# chat/api_key_manager.py
from django.db.models import F
import random

class APIKeyManager:
    @staticmethod
    def get_available_key(provider='openai'):
        """获取可用的API Key（带负载均衡）"""
        # 1. 筛选可用未超额且错误数少于5次的Key
        keys = AIApiKey.objects.filter(
            provider=provider,
            is_active=True,
            error_count__lt=5
        ).exclude(
            daily_tokens_used__gte=F('daily_token_limit')
        ).exclude(
            monthly_tokens_used__gte=F('monthly_token_limit')
        ).order_by('-priority', 'daily_tokens_used')
        
        if not keys.exists():
            raise Exception("没有可用的API Key，请联系管理员")
        
        selected = random.choice(keys[:3])
        
        # 2. 解密Key
        from cryptography.fernet import Fernet
        f = Fernet(settings.ENCRYPTION_KEY)
        api_key = f.decrypt(selected.api_key_encrypted.encode()).decode()
        
        return selected.id, api_key
    
    @staticmethod
    def record_usage(key_id, tokens, cost):
        """记录API Key使用"""
        AIApiKey.objects.filter(id=key_id).update(
            daily_tokens_used=F('daily_tokens_used') + tokens,
            monthly_tokens_used=F('monthly_tokens_used') + tokens,
            total_tokens_used=F('total_tokens_used') + tokens,
            total_cost=F('total_cost') + cost,
            last_used_at=timezone.now(),
            error_count=0
        )
    
    @staticmethod
    def record_error(key_id, error_message):
        """记录外部请求响应异常和计数器叠加"""
        key = AIApiKey.objects.get(id=key_id)
        key.error_count = F('error_count') + 1
        key.last_error = error_message
        key.save()
        key.refresh_from_db()
        if key.error_count >= 5:
            key.is_active = False
            key.save()
            # send_alert(f"API Key {key.key_name} 已自动禁用")
```

**超限防护与用户配额系统**：

```python
# chat/quota_manager.py
class QuotaManager:
    @staticmethod
    def check_quota(user_id, estimated_tokens=1000):
        """检查用户配额，防超限"""
        daily_quota = AIUserQuota.objects.get(user_id=user_id, quota_type='daily')
        if daily_quota.tokens_used + estimated_tokens > daily_quota.token_limit:
            raise Exception(f"每日配额已用完，将于 {daily_quota.reset_at} 重置")
        
        monthly_quota = AIUserQuota.objects.get(user_id=user_id, quota_type='monthly')
        if monthly_quota.tokens_used + estimated_tokens > monthly_quota.token_limit:
            raise Exception("您本月已使用超限定Token额度，请联系管理员增加配额或下月1日重置后重试。")
        return True
    
    @staticmethod
    def deduct_quota(user_id, tokens_used):
        """原子扣除配额"""
        AIUserQuota.objects.filter(
            user_id=user_id,
            quota_type__in=['daily', 'monthly']
        ).update(tokens_used=F('tokens_used') + tokens_used)
```

**自动摘要**：

```python
from django.db.models import Max

def summarize_messages(conversation_id, start_seq, end_seq):
    # 此处为具体的摘要执行和入库逻辑
    pass

def auto_summarize_conversation(conversation_id):
    """长对话异步自动总结"""
    messages_count = ChatMessage.objects.filter(
        conversation_id=conversation_id
    ).count()
    
    # 每当消息数达到20的倍数时触发
    if messages_count % 20 == 0 and messages_count > 20:
        already_summarized = ChatConversationSummary.objects.filter(
            conversation_id=conversation_id
        ).aggregate(Max('message_range_end'))['message_range_end__max'] or 0
        
        # 总结从上次摘要结束到当前的前N条，保留最近的5条用于作为紧密上下文
        summarize_messages(conversation_id, already_summarized + 1, messages_count - 5)
```

**日志离线聚合规制**：每天固定时段执行异步聚合数据流水，生成多维度图表依赖的总账目快照至单独的大宽表层内，支撑 `admin/ai/stats/*` 查询。

### 2.7.2 超限防护与用户配额系统

```python
def get_ai_response_with_retry(conversation_id, question, max_retries=3):
    """带重试的AI响应"""
    for attempt in range(max_retries):
        try:
            return ai_service.get_response(conversation_id, question)
        except openai.error.RateLimitError:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # 指数退避
                continue
            else:
                return {
                    'answer': '抱歉，当前请求过多，请稍后再试。',
                    'error': True
                }
        except Exception as e:
            logger.error(f"AI响应失败: {e}")
            return {
                'answer': '抱歉，AI助手暂时无法回答，请稍后再试。',
                'error': True
            }
```

------

## 2.8 数据库表设计 (SQL底座)

以下是模块核心实体的 SQL 建表语句：

```sql
CREATE TABLE `chat_conversation` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '主键',
  `session_id` varchar(64) NOT NULL COMMENT '会话唯一标识（UUID）',
  `title` varchar(255) NOT NULL COMMENT '会话标题',
  `user_id` int(11) NOT NULL COMMENT '用户ID',
  `context_type` varchar(50) DEFAULT NULL COMMENT '上下文类型',
  `context_id` varchar(100) DEFAULT NULL COMMENT '上下文对象ID',
  `context_data` json DEFAULT NULL COMMENT '上下文数据快照',
  `message_count` int(11) DEFAULT 0 COMMENT '消息数量',
  `last_message_at` datetime DEFAULT NULL COMMENT '最后消息时间',
  `is_archived` tinyint(1) DEFAULT 0 COMMENT '是否归档',
  `model_name` varchar(50) DEFAULT NULL COMMENT 'AI模型名称',
  `temperature` decimal(3,2) DEFAULT NULL COMMENT '模型温度参数',
  `max_tokens` int(11) DEFAULT NULL COMMENT '最大token数',
  `created_by_id` int(11) DEFAULT NULL COMMENT '创建人ID',
  `updated_by_id` int(11) DEFAULT NULL COMMENT '更新人ID',
  `owner_organization_id` int(11) DEFAULT NULL COMMENT '所属组织ID',
  `is_deleted` tinyint(1) DEFAULT 0 COMMENT '软删除标志',
  `remark` varchar(255) DEFAULT NULL COMMENT '备注',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_session_id` (`session_id`),
  KEY `idx_user_updated` (`user_id`,`updated_at`),
  KEY `idx_context` (`context_type`,`context_id`),
  CONSTRAINT `fk_conversation_user` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='对话会话表';

CREATE TABLE `chat_message` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '主键',
  `conversation_id` bigint(20) NOT NULL COMMENT '所属会话ID',
  `role` varchar(20) NOT NULL COMMENT 'LangChain角色',
  `content` text NOT NULL COMMENT '消息内容',
  `content_type` varchar(20) DEFAULT NULL COMMENT '内容类型',
  `sequence` int(11) NOT NULL COMMENT '消息序号',
  `parent_message_id` bigint(20) DEFAULT NULL COMMENT '父消息ID',
  `prompt_tokens` int(11) DEFAULT 0 COMMENT '提示词token数',
  `completion_tokens` int(11) DEFAULT 0 COMMENT '回复token数',
  `total_tokens` int(11) DEFAULT 0 COMMENT '总token数',
  `model_name` varchar(50) DEFAULT NULL COMMENT '使用的模型',
  `finish_reason` varchar(50) DEFAULT NULL COMMENT '完成原因',
  `function_call` json DEFAULT NULL COMMENT '函数调用信息',
  `tool_calls` json DEFAULT NULL COMMENT '工具调用列表',
  `additional_kwargs` json DEFAULT NULL COMMENT '额外参数',
  `error_message` text DEFAULT NULL COMMENT '错误信息',
  `retry_count` int(11) DEFAULT 0 COMMENT '重试次数',
  `feedback` varchar(20) DEFAULT NULL COMMENT '用户反馈',
  `feedback_detail` text DEFAULT NULL COMMENT '反馈详情',
  `created_by_id` int(11) DEFAULT NULL COMMENT '创建人ID',
  `updated_by_id` int(11) DEFAULT NULL COMMENT '更新人ID',
  `owner_organization_id` int(11) DEFAULT NULL COMMENT '所属组织ID',
  `is_deleted` tinyint(1) DEFAULT 0 COMMENT '软删除标志',
  `remark` varchar(255) DEFAULT NULL COMMENT '备注',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  KEY `idx_conversation_sequence` (`conversation_id`,`sequence`),
  KEY `idx_conversation_created` (`conversation_id`,`created_at`),
  KEY `idx_role_created` (`role`,`created_at`),
  CONSTRAINT `fk_message_conversation` FOREIGN KEY (`conversation_id`) REFERENCES `chat_conversation` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='对话消息表';

CREATE TABLE `chat_experiment_context` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '主键',
  `conversation_id` bigint(20) NOT NULL COMMENT '会话ID',
  `experiment_id` bigint(20) DEFAULT NULL COMMENT '正在进行的实验ID',
  `submission_id` bigint(20) DEFAULT NULL COMMENT '正在编写的提交ID',
  `guidebook_id` bigint(20) DEFAULT NULL COMMENT '正在查看的指导书ID',
  `indexed_content_ids` json DEFAULT NULL COMMENT '已索引的文档ID列表',
  `created_by_id` int(11) DEFAULT NULL COMMENT '创建人ID',
  `updated_by_id` int(11) DEFAULT NULL COMMENT '更新人ID',
  `owner_organization_id` int(11) DEFAULT NULL COMMENT '所属组织ID',
  `is_deleted` tinyint(1) DEFAULT 0 COMMENT '软删除标志',
  `remark` varchar(255) DEFAULT NULL COMMENT '备注',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_conversation_id` (`conversation_id`),
  KEY `idx_experiment` (`experiment_id`),
  CONSTRAINT `fk_context_conversation` FOREIGN KEY (`conversation_id`) REFERENCES `chat_conversation` (`id`),
  CONSTRAINT `fk_context_experiment` FOREIGN KEY (`experiment_id`) REFERENCES `course_experiment` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='实验上下文关联表';

CREATE TABLE `chat_conversation_summary` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '主键',
  `conversation_id` bigint(20) NOT NULL COMMENT '会话ID',
  `summary_type` varchar(20) NOT NULL COMMENT '摘要类型',
  `summary_content` text NOT NULL COMMENT '摘要内容',
  `message_range_start` int(11) NOT NULL COMMENT '起始消息序号',
  `message_range_end` int(11) NOT NULL COMMENT '结束消息序号',
  `tokens_saved` int(11) DEFAULT 0 COMMENT '节省的token数',
  `created_by_id` int(11) DEFAULT NULL COMMENT '创建人ID',
  `updated_by_id` int(11) DEFAULT NULL COMMENT '更新人ID',
  `owner_organization_id` int(11) DEFAULT NULL COMMENT '所属组织ID',
  `is_deleted` tinyint(1) DEFAULT 0 COMMENT '软删除标志',
  `remark` varchar(255) DEFAULT NULL COMMENT '备注',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  KEY `idx_conversation` (`conversation_id`),
  CONSTRAINT `fk_summary_conversation` FOREIGN KEY (`conversation_id`) REFERENCES `chat_conversation` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='会话摘要表';

CREATE TABLE `ai_model_config` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `model_key` varchar(50) NOT NULL COMMENT '模型标识',
  `model_name` varchar(100) NOT NULL COMMENT '模型名称',
  `provider` varchar(50) NOT NULL COMMENT '提供商: openai/anthropic/azure',
  `model_type` varchar(50) NOT NULL COMMENT '模型类型: gpt-3.5-turbo/gpt-4/claude-3',
  `is_enabled` boolean DEFAULT true COMMENT '是否启用',
  `is_default` boolean DEFAULT false COMMENT '是否默认',
  `max_tokens` int DEFAULT 4000 COMMENT '最大token数',
  `temperature_default` decimal(3,2) DEFAULT 0.7 COMMENT '默认温度',
  `temperature_min` decimal(3,2) DEFAULT 0.0 COMMENT '温度最小值',
  `temperature_max` decimal(3,2) DEFAULT 2.0 COMMENT '温度最大值',
  `cost_per_1k_input` decimal(6,4) COMMENT '输入token成本($/1K)',
  `cost_per_1k_output` decimal(6,4) COMMENT '输出token成本($/1K)',
  `rate_limit_rpm` int COMMENT '每分钟请求限制',
  `rate_limit_tpm` int COMMENT '每分钟token限制',
  `allowed_roles` json COMMENT '允许使用的角色: ["student", "teacher"]',
  `created_by_id` int(11) DEFAULT NULL COMMENT '创建人ID',
  `updated_by_id` int(11) DEFAULT NULL COMMENT '更新人ID',
  `owner_organization_id` int(11) DEFAULT NULL COMMENT '所属组织ID',
  `is_deleted` tinyint(1) DEFAULT 0 COMMENT '软删除标志',
  `remark` varchar(255) DEFAULT NULL COMMENT '备注',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_model_key` (`model_key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='AI模型配置表';

CREATE TABLE `ai_api_key` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `provider` varchar(50) NOT NULL COMMENT '提供商: openai/anthropic',
  `key_name` varchar(100) NOT NULL COMMENT 'Key名称(用于识别)',
  `api_key_encrypted` text NOT NULL COMMENT '使用全体系统一AES256加密后的API Key',
  `is_active` boolean DEFAULT true COMMENT '是否启用',
  `priority` int DEFAULT 0 COMMENT '优先级(数字越大越优先)',
  `daily_token_limit` bigint COMMENT '每日token限制',
  `monthly_token_limit` bigint COMMENT '每月token限制',
  `daily_tokens_used` bigint DEFAULT 0 COMMENT '今日已用token',
  `monthly_tokens_used` bigint DEFAULT 0 COMMENT '本月已用token',
  `total_tokens_used` bigint DEFAULT 0 COMMENT '总计已用token',
  `total_cost` decimal(10,2) DEFAULT 0.00 COMMENT '总花费($)',
  `last_used_at` datetime COMMENT '最后使用时间',
  `last_error` text COMMENT '最后错误信息',
  `error_count` int DEFAULT 0 COMMENT '连续错误次数',
  `created_by_id` int(11) DEFAULT NULL COMMENT '创建人ID',
  `updated_by_id` int(11) DEFAULT NULL COMMENT '更新人ID',
  `owner_organization_id` int(11) DEFAULT NULL COMMENT '所属组织ID',
  `is_deleted` tinyint(1) DEFAULT 0 COMMENT '软删除标志',
  `remark` varchar(255) DEFAULT NULL COMMENT '备注',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_provider_active` (`provider`, `is_active`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='API Key管理表';

CREATE TABLE `ai_user_quota` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL COMMENT '用户ID',
  `quota_type` varchar(20) NOT NULL COMMENT '配额类型: daily/monthly/total',
  `token_limit` bigint NOT NULL COMMENT 'Token限制',
  `tokens_used` bigint DEFAULT 0 COMMENT '已使用token',
  `reset_at` datetime COMMENT '重置时间',
  `is_active` boolean DEFAULT true COMMENT '是否启用',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_user_quota_type` (`user_id`, `quota_type`),
  KEY `idx_reset_at` (`reset_at`),
  CONSTRAINT `fk_quota_user` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户AI配额表';

CREATE TABLE `ai_agent_config` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `agent_key` varchar(50) NOT NULL COMMENT 'Agent标识',
  `agent_name` varchar(100) NOT NULL COMMENT 'Agent名称',
  `description` text COMMENT '描述',
  `system_prompt` text NOT NULL COMMENT '系统提示词',
  `context_type` varchar(50) COMMENT '适用上下文: experiment/vm/general',
  `model_config_id` bigint COMMENT '默认模型ID',
  `temperature` decimal(3,2) DEFAULT 0.7,
  `max_tokens` int DEFAULT 2000,
  `enable_rag` boolean DEFAULT true COMMENT '是否启用RAG检索',
  `rag_top_k` int DEFAULT 3 COMMENT 'RAG检索数量',
  `enable_memory` boolean DEFAULT true COMMENT '是否启用对话记忆',
  `memory_window` int DEFAULT 20 COMMENT '记忆窗口大小',
  `language` varchar(10) DEFAULT 'zh-CN' COMMENT '语言',
  `is_active` boolean DEFAULT true,
  `created_by_id` int(11) DEFAULT NULL COMMENT '创建人ID',
  `updated_by_id` int(11) DEFAULT NULL COMMENT '更新人ID',
  `owner_organization_id` int(11) DEFAULT NULL COMMENT '所属组织ID',
  `is_deleted` tinyint(1) DEFAULT 0 COMMENT '软删除标志',
  `remark` varchar(255) DEFAULT NULL COMMENT '备注',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_agent_key` (`agent_key`),
  CONSTRAINT `fk_agent_model` FOREIGN KEY (`model_config_id`) REFERENCES `ai_model_config` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='智能体配置表';

CREATE TABLE `ai_knowledge_index_status` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '主键',
  `guidebook_id` bigint(20) NOT NULL COMMENT '被索引文档ID',
  `experiment_id` bigint(20) DEFAULT NULL COMMENT '归属实验ID',
  `status` varchar(20) NOT NULL COMMENT '状态: pending/processing/completed/failed',
  `chunk_num` int(11) DEFAULT 0 COMMENT '文档分出总片数',
  `remark` text COMMENT '故障或者执行备注',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_knowledge_guidebook` (`guidebook_id`),
  KEY `idx_knowledge_sts` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='知识库构建流水作业状态表';

CREATE TABLE `ai_usage_log` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `conversation_id` bigint COMMENT '会话ID',
  `message_id` bigint COMMENT '消息ID',
  `model_key` varchar(50) NOT NULL,
  `api_key_id` bigint COMMENT '使用的API Key ID',
  `prompt_tokens` int DEFAULT 0,
  `completion_tokens` int DEFAULT 0,
  `total_tokens` int DEFAULT 0,
  `cost` decimal(8,4) DEFAULT 0.0000 COMMENT '费用($)',
  `latency_ms` int COMMENT '响应延迟(毫秒)',
  `status` varchar(20) DEFAULT 'success' COMMENT 'success/error',
  `error_message` text COMMENT '错误信息',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_user_created` (`user_id`, `created_at`),
  KEY `idx_conversation` (`conversation_id`),
  KEY `idx_status` (`status`, `created_at`),
  CONSTRAINT `fk_usage_user` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `fk_usage_conversation` FOREIGN KEY (`conversation_id`) REFERENCES `chat_conversation` (`id`),
  CONSTRAINT `fk_usage_message` FOREIGN KEY (`message_id`) REFERENCES `chat_message` (`id`),
  CONSTRAINT `fk_usage_key` FOREIGN KEY (`api_key_id`) REFERENCES `ai_api_key` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='AI使用记录表';

## 2.9 权限控制设计与管理端审计

AI助手模块的数据权限遵循以下设计：

- **学生端权限**：
  - 会话查询：只能查询和查看本人创建的会话。
  - 会话管理：只能软删除、归档本人的会话，无权操作他人数据。
- **教师端权限**：
  - 教学追踪：教师可以通过“教学中心面板”或“实验详情”接口查询自己负责的班级内所有学生的历史提问对话。
  - **隔离性**：教师不能以学生的身份进行自动追问或修改消息，只能提供旁路查看权限：
    ```http
    GET /api/v1/chat/teacher/students/{student_id}/conversations/
    GET /api/v1/chat/teacher/experiments/{experiment_id}/conversations/
    ```
- **管理员权限**：
  - 拥有对全量会话记录、消耗统计等元数据的汇总管理权限。
