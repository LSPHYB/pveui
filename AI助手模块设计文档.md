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
| conversation_type | varchar(20)  | 是   | 会话类型                         | ai_assistant / user_chat              |
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
| created_at        | datetime     | 是   | 创建时间                         | 自动生成                              |
| updated_at        | datetime     | 是   | 更新时间                         | 自动更新                              |

**业务规则**：

- 每次打开AI助手创建新会话，或继续旧会话
- `session_id` 用于前端识别会话
- `context_type` 和 `context_id` 关联业务对象（实验、虚拟机等）
- 自动根据首条消息生成会话标题

**会话类型说明**：

- `ai_assistant`：与AI助手对话
- `user_chat`：用户之间聊天（预留）

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
| message_type      | varchar(20) | 是   | 消息类型               | user / assistant / system / function  |
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
| created_at        | datetime    | 是   | 创建时间               | 自动生成                              |

**业务规则**：

- 用户提问和AI回答交替出现
- `sequence` 确保消息顺序
- 记录token使用情况，用于成本控制
- 用户可对AI回答点赞/点踩

**消息类型说明**：

- `user`：用户消息
- `assistant`：AI助手回复
- `system`：系统消息（如欢迎语）
- `function`：函数调用结果

**索引设计**：

```sql
INDEX idx_conversation_sequence (conversation_id, sequence)
INDEX idx_conversation_created (conversation_id, created_at)
INDEX idx_message_type (message_type, created_at)
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
| created_at          | datetime | 是   | 创建时间           | 自动生成 |

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
    "conversation_type": "ai_assistant",
    "message_count": 0,
    "created_at": "2024-03-10T15:00:00Z"
  }
}
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
    "conversation_type": "ai_assistant",
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
        "message_type": "user",
        "content": "请问如何创建一个新用户？",
        "sequence": 1,
        "created_at": "2024-03-10T14:05:00Z"
      },
      {
        "id": 2,
        "message_type": "assistant",
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

#### 5) 归档会话

```http
POST /api/v1/chat/conversations/{id}/archive/
```

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

**响应示例**（流式响应）：

```json
{
  "code": 200,
  "data": {
    "user_message": {
      "id": 10,
      "content": "请问chmod 755是什么意思？",
      "sequence": 19,
      "created_at": "2024-03-10T15:30:00Z"
    },
    "assistant_message": {
      "id": 11,
      "content": "chmod 755 是Linux文件权限设置命令...",
      "sequence": 20,
      "prompt_tokens": 520,
      "completion_tokens": 150,
      "total_tokens": 670,
      "sources": [
        {
          "guidebook_id": 1,
          "page": 3,
          "content_snippet": "chmod命令用于修改文件权限..."
        }
      ],
      "created_at": "2024-03-10T15:30:05Z"
    }
  }
}
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

------

### 2.3.3 LangChain核心实现

#### 1) RAG检索链

```python
# chat/langchain_service.py
from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings
from langchain.chat_models import ChatOpenAI
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory

class AIAssistantService:
    
    def __init__(self):
        self.embeddings = OpenAIEmbeddings()
        self.llm = ChatOpenAI(
            model_name="gpt-3.5-turbo",
            temperature=0.7
        )
    
    def get_response(self, conversation_id, user_question):
        """获取AI回复"""
        # 1. 获取会话上下文
        conversation = ChatConversation.objects.get(id=conversation_id)
        context = ChatExperimentContext.objects.get(conversation_id=conversation_id)
        
        # 2. 加载向量数据库
        vectorstore = Chroma(
            persist_directory=f"./chroma_db/guidebook_{context.guidebook_id}",
            embedding_function=self.embeddings
        )
        
        # 3. 检索相关文档
        docs = vectorstore.similarity_search(user_question, k=3)
        
        # 4. 获取对话历史
        messages = ChatMessage.objects.filter(
            conversation_id=conversation_id
        ).order_by('sequence')[:20]  # 最近20条
        
        chat_history = []
        for msg in messages:
            if msg.message_type == 'user':
                chat_history.append(("human", msg.content))
            elif msg.message_type == 'assistant':
                chat_history.append(("ai", msg.content))
        
        # 5. 构建检索链
        memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        
        # 填充历史记录
        for human_msg, ai_msg in chat_history:
            memory.chat_memory.add_user_message(human_msg)
            memory.chat_memory.add_ai_message(ai_msg)
        
        qa_chain = ConversationalRetrievalChain.from_llm(
            llm=self.llm,
            retriever=vectorstore.as_retriever(search_kwargs={"k": 3}),
            memory=memory,
            return_source_documents=True
        )
        
        # 6. 构建提示词
        system_prompt = f"""你是一个实验教学助手，正在帮助学生完成《{context.experiment.title}》实验。

请根据实验指导书的内容回答学生的问题。如果问题超出实验范围，请礼貌地提示学生。

回答要求：
1. 清晰、准确、简洁
2. 如果涉及命令，给出具体示例
3. 可以适当引用指导书原文
4. 鼓励学生独立思考

当前实验步骤：{context.submission.current_step if context.submission else '未知'}
"""
        
        # 7. 获取回复
        result = qa_chain({
            "question": user_question,
            "chat_history": chat_history
        })
        
        answer = result['answer']
        sources = result['source_documents']
        
        return {
            'answer': answer,
            'sources': sources,
            'tokens': {
                'prompt': result.get('prompt_tokens', 0),
                'completion': result.get('completion_tokens', 0),
                'total': result.get('total_tokens', 0)
            }
        }
```

#### 2) 文档索引构建

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
    
    # 5. 更新索引状态
    guidebook.is_indexed = True
    guidebook.index_status = 'completed'
    guidebook.save()
    
    return len(chunks)
```

#### 3) Celery异步任务

```python
# chat/tasks.py
from celery import shared_task

@shared_task
def index_guidebook_async(guidebook_id):
    """异步建立文档索引"""
    try:
        chunk_count = index_guidebook(guidebook_id)
        return f"索引完成，共{chunk_count}个分块"
    except Exception as e:
        guidebook = CourseGuidebook.objects.get(id=guidebook_id)
        guidebook.index_status = 'failed'
        guidebook.save()
        raise e
```

------

## 2.4 前端设计

### 2.4.1 AI助手对话界面

**路由**：`/chat` 或作为浮动窗口

**组件设计**：

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
          :class="['message-item', message.message_type]"
        >
          <!-- 用户消息 -->
          <div v-if="message.message_type === 'user'" class="user-message">
            <a-avatar :size="32">{{ username[0] }}</a-avatar>
            <div class="message-bubble">
              <div class="message-content">{{ message.content }}</div>
              <div class="message-time">{{ formatTime(message.created_at) }}</div>
            </div>
          </div>
          
          <!-- AI回复 -->
          <div v-else-if="message.message_type === 'assistant'" class="assistant-message">
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
  
  // 立即显示用户消息
  messages.value.push({
    id: Date.now(),
    message_type: 'user',
    content: userMessage,
    created_at: new Date()
  })
  
  scrollToBottom()
  
  try {
    isLoading.value = true
    
    const response = await sendMessageAPI(currentConversationId.value, {
      content: userMessage
    })
    
    // 添加AI回复
    messages.value.push(response.data.assistant_message)
    scrollToBottom()
  } catch (error) {
    Message.error('发送失败')
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

------

## 2.5 核心业务流程

### 2.5.1 学生提问流程

```
1. 学生点击"AI助手"按钮
   ↓
2. 系统检查是否有活跃会话
   ├─ 有 → 加载历史对话
   └─ 无 → 创建新会话
   ↓
3. 系统识别上下文（当前实验、指导书）
   ↓
4. 学生输入问题
   ↓
5. 前端发送消息到后端
   ↓
6. 后端RAG检索相关文档
   ↓
7. LangChain构建提示词
   ↓
8. 调用OpenAI API
   ↓
9. 保存对话记录
   ↓
10. 返回AI回复（附引用来源）
   ↓
11. 前端展示回答
```

### 2.5.2 文档索引流程

```
1. 教师上传指导书
   ↓
2. 保存文件到存储
   ↓
3. 触发Celery异步任务
   ↓
4. 提取PDF/Word文本内容
   ↓
5. 文本分块（500字符/块）
   ↓
6. 调用OpenAI Embedding API
   ↓
7. 存储向量到ChromaDB
   ↓
8. 更新索引状态：completed
   ↓
9. AI助手可检索该文档
```

------

## 2.6 技术实现要点

### 2.6.1 成本控制

**Token统计**：

```python
def save_message_with_tokens(conversation_id, role, content, usage):
    """保存消息并记录token使用"""
    message = ChatMessage.objects.create(
        conversation_id=conversation_id,
        message_type=role,
        content=content,
        prompt_tokens=usage.get('prompt_tokens', 0),
        completion_tokens=usage.get('completion_tokens', 0),
        total_tokens=usage.get('total_tokens', 0)
    )
    
    # 统计用户总消耗
    user_total_tokens = ChatMessage.objects.filter(
        conversation__user_id=message.conversation.user_id
    ).aggregate(Sum('total_tokens'))['total_tokens__sum']
    
    # 检查是否超限
    if user_total_tokens > 100000:  # 10万token限制
        raise Exception("Token使用超限，请联系管理员")
    
    return message
```

**自动摘要**：

```python
def auto_summarize_conversation(conversation_id):
    """长对话自动总结"""
    messages = ChatMessage.objects.filter(
        conversation_id=conversation_id
    ).order_by('sequence')
    
    if messages.count() > 20:
        # 总结前15条消息
        old_messages = messages[:15]
        
        summary_prompt = f"""请总结以下对话的关键信息：

{format_messages_for_summary(old_messages)}

要求：用2-3句话概括对话要点。
"""
        
        summary = llm.invoke(summary_prompt)
        
        # 保存摘要
        ChatConversationSummary.objects.create(
            conversation_id=conversation_id,
            summary_content=summary,
            message_range_start=1,
            message_range_end=15,
            tokens_saved=calculate_tokens_saved(old_messages)
        )
        
        return summary
```

### 2.6.2 错误处理

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