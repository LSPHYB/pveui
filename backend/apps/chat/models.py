"""AI 助手模块模型：对话会话、消息、上下文、摘要、AI模型配置、API Key、配额、智能体配置、知识库状态、使用记录。"""

from django.conf import settings
from django.db import models

from apps.common.models import BaseAuditModel


# ---------------------------------------------------------------------------
# 2.2.1 对话会话实体
# ---------------------------------------------------------------------------

class ChatConversation(BaseAuditModel):
    """对话会话：代表一次完整的 AI 对话会话，包含多条消息。"""

    session_id = models.CharField(
        max_length=64, unique=True, verbose_name='会话唯一标识（UUID）'
    )
    title = models.CharField(max_length=255, verbose_name='会话标题')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='ai_conversations',
        verbose_name='用户',
    )
    context_type = models.CharField(
        max_length=50, blank=True, default='',
        verbose_name='上下文类型', help_text='experiment / vm / general'
    )
    context_id = models.CharField(
        max_length=100, blank=True, default='',
        verbose_name='上下文对象ID', help_text='如实验ID'
    )
    context_data = models.JSONField(
        null=True, blank=True,
        verbose_name='上下文数据快照',
        help_text='如 {"experiment_title": "Linux用户管理"}'
    )
    message_count = models.IntegerField(default=0, verbose_name='消息数量')
    last_message_at = models.DateTimeField(
        null=True, blank=True, verbose_name='最后消息时间'
    )
    is_archived = models.BooleanField(default=False, verbose_name='是否归档')
    model_name = models.CharField(
        max_length=50, blank=True, default='',
        verbose_name='AI模型名称', help_text='gpt-3.5-turbo / gpt-4'
    )
    temperature = models.DecimalField(
        max_digits=3, decimal_places=2, null=True, blank=True,
        verbose_name='模型温度参数'
    )
    max_tokens = models.IntegerField(
        null=True, blank=True, verbose_name='最大token数'
    )

    class Meta:
        verbose_name = '对话会话'
        verbose_name_plural = '对话会话'
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['user', 'updated_at'], name='idx_conv_user_updated'),
            models.Index(fields=['context_type', 'context_id'], name='idx_conv_context'),
        ]

    def __str__(self) -> str:
        return f"[{self.session_id}] {self.title}"


# ---------------------------------------------------------------------------
# 2.2.2 对话消息实体
# ---------------------------------------------------------------------------

class ChatMessage(BaseAuditModel):
    """对话消息：具体的对话消息记录，user_id / role / content 三要素。"""

    ROLE_CHOICES = [
        ('human', '用户'),
        ('ai', 'AI助手'),
        ('system', '系统'),
        ('function', '函数调用'),
    ]

    CONTENT_TYPE_CHOICES = [
        ('text', '纯文本'),
        ('markdown', 'Markdown'),
        ('code', '代码'),
    ]

    FINISH_REASON_CHOICES = [
        ('stop', '正常结束'),
        ('length', '长度截断'),
        ('function_call', '函数调用'),
    ]

    FEEDBACK_CHOICES = [
        ('helpful', '有帮助'),
        ('not_helpful', '没帮助'),
    ]

    conversation = models.ForeignKey(
        ChatConversation,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name='所属会话',
    )
    role = models.CharField(
        max_length=20, choices=ROLE_CHOICES, verbose_name='LangChain角色'
    )
    content = models.TextField(verbose_name='消息内容')
    content_type = models.CharField(
        max_length=20, choices=CONTENT_TYPE_CHOICES,
        blank=True, default='text', verbose_name='内容类型'
    )
    sequence = models.IntegerField(verbose_name='消息序号（会话内递增）')
    parent_message = models.ForeignKey(
        'self',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='children',
        verbose_name='父消息（支持消息树）',
    )
    prompt_tokens = models.IntegerField(default=0, verbose_name='提示词token数')
    completion_tokens = models.IntegerField(default=0, verbose_name='回复token数')
    total_tokens = models.IntegerField(default=0, verbose_name='总token数')
    model_name = models.CharField(
        max_length=50, blank=True, default='', verbose_name='使用的模型'
    )
    finish_reason = models.CharField(
        max_length=50, choices=FINISH_REASON_CHOICES,
        blank=True, default='', verbose_name='完成原因'
    )
    function_call = models.JSONField(
        null=True, blank=True,
        verbose_name='函数调用信息',
        help_text='{"name": "search_doc", "args": {...}}'
    )
    tool_calls = models.JSONField(
        null=True, blank=True, verbose_name='工具调用列表'
    )
    additional_kwargs = models.JSONField(
        null=True, blank=True, verbose_name='额外参数'
    )
    error_message = models.TextField(
        blank=True, default='', verbose_name='错误信息'
    )
    retry_count = models.IntegerField(default=0, verbose_name='重试次数')
    feedback = models.CharField(
        max_length=20, choices=FEEDBACK_CHOICES,
        blank=True, default='', verbose_name='用户反馈'
    )
    feedback_detail = models.TextField(
        blank=True, default='', verbose_name='反馈详情'
    )

    class Meta:
        verbose_name = '对话消息'
        verbose_name_plural = '对话消息'
        ordering = ['sequence']
        indexes = [
            models.Index(
                fields=['conversation', 'sequence'],
                name='idx_msg_conv_seq'
            ),
            models.Index(
                fields=['conversation', 'created_at'],
                name='idx_msg_conv_created'
            ),
            models.Index(
                fields=['role', 'created_at'],
                name='idx_msg_role_created'
            ),
        ]

    def __str__(self) -> str:
        return f"[{self.role}] #{self.sequence} in conversation {self.conversation_id}"


# ---------------------------------------------------------------------------
# 2.2.3 实验上下文关联实体
# ---------------------------------------------------------------------------

class ChatExperimentContext(BaseAuditModel):
    """实验上下文关联：将 AI 对话与实验业务对象绑定，增强 RAG 检索相关性。"""

    conversation = models.OneToOneField(
        ChatConversation,
        on_delete=models.CASCADE,
        related_name='experiment_context',
        verbose_name='所属会话',
    )
    experiment = models.ForeignKey(
        'experiments.CourseExperiment',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='ai_contexts',
        verbose_name='正在进行的实验',
    )
    submission = models.ForeignKey(
        'experiments.CourseSubmission',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='ai_contexts',
        verbose_name='正在编写的提交',
    )
    guidebook = models.ForeignKey(
        'experiments.CourseGuidebook',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='ai_contexts',
        verbose_name='正在查看的指导书',
    )
    indexed_content_ids = models.JSONField(
        null=True, blank=True,
        verbose_name='已索引的文档ID列表', help_text='[1, 2]'
    )

    class Meta:
        verbose_name = '实验上下文关联'
        verbose_name_plural = '实验上下文关联'
        indexes = [
            models.Index(fields=['experiment'], name='idx_exp_context_exp'),
        ]

    def __str__(self) -> str:
        return f"Context for conversation {self.conversation_id}"


# ---------------------------------------------------------------------------
# 2.2.4 会话摘要实体
# ---------------------------------------------------------------------------

class ChatConversationSummary(BaseAuditModel):
    """会话摘要：长对话自动总结，节省 Token 消耗。"""

    SUMMARY_TYPE_CHOICES = [
        ('auto', '自动生成'),
        ('manual', '手动生成'),
    ]

    conversation = models.ForeignKey(
        ChatConversation,
        on_delete=models.CASCADE,
        related_name='summaries',
        verbose_name='所属会话',
    )
    summary_type = models.CharField(
        max_length=20, choices=SUMMARY_TYPE_CHOICES, verbose_name='摘要类型'
    )
    summary_content = models.TextField(verbose_name='摘要内容')
    message_range_start = models.IntegerField(verbose_name='起始消息序号')
    message_range_end = models.IntegerField(verbose_name='结束消息序号')
    tokens_saved = models.IntegerField(default=0, verbose_name='节省的token数')

    class Meta:
        verbose_name = '会话摘要'
        verbose_name_plural = '会话摘要'
        ordering = ['message_range_start']
        indexes = [
            models.Index(fields=['conversation'], name='idx_summary_conv'),
        ]

    def __str__(self) -> str:
        return (
            f"Summary[{self.message_range_start}-{self.message_range_end}] "
            f"for conversation {self.conversation_id}"
        )


# ---------------------------------------------------------------------------
# 2.2.5 AI 模型配置实体
# ---------------------------------------------------------------------------

class AIModelConfig(BaseAuditModel):
    """AI 模型配置：记录可用的 AI 模型及其参数、成本、频率限制等。"""

    model_key = models.CharField(
        max_length=50, unique=True, verbose_name='模型标识',
        help_text='如 gpt-3.5-turbo'
    )
    model_name = models.CharField(max_length=100, verbose_name='模型名称')
    api_key = models.ForeignKey(
        'AIApiKey', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='models', verbose_name='绑定的 API Key / 通道'
    )
    model_type = models.CharField(
        max_length=50, verbose_name='模型类型',
        help_text='gpt-3.5-turbo / gpt-4 / claude-3'
    )
    is_enabled = models.BooleanField(default=True, verbose_name='是否启用')
    is_default = models.BooleanField(default=False, verbose_name='是否默认模型')
    max_tokens = models.IntegerField(default=4000, verbose_name='最大token数')
    temperature_default = models.DecimalField(
        max_digits=3, decimal_places=2, default='0.70', verbose_name='默认温度'
    )
    allowed_roles = models.JSONField(
        null=True, blank=True,
        verbose_name='允许使用的角色列表',
        help_text='["student", "teacher"]'
    )

    class Meta:
        verbose_name = 'AI模型配置'
        verbose_name_plural = 'AI模型配置'
        ordering = ['model_key']

    def __str__(self) -> str:
        provider = self.api_key.provider if self.api_key else 'Unassigned'
        return f"[{provider}] {self.model_name} ({self.model_key})"


# ---------------------------------------------------------------------------
# 2.2.6 API Key 管理实体
# ---------------------------------------------------------------------------

class AIApiKey(BaseAuditModel):
    """API Key 管理：各 AI 提供商的 API Key 及其用量统计。"""

    provider = models.CharField(
        max_length=50, verbose_name='提供商',
        help_text='openai / anthropic'
    )
    key_name = models.CharField(
        max_length=100, verbose_name='Key名称', help_text='用于人工识别，如 OpenAI-Default'
    )
    base_url = models.CharField(
        max_length=255, null=True, blank=True,
        verbose_name='代理/Base URL',
        help_text='默认 https://api.openai.com/v1 或兼容提供商的自建网关地址'
    )
    api_key_encrypted = models.TextField(
        verbose_name='API Key（AES256加密存储）'
    )
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    priority = models.IntegerField(
        default=0, verbose_name='优先级', help_text='数字越大越优先'
    )
    daily_token_limit = models.BigIntegerField(
        null=True, blank=True, verbose_name='每日token限制'
    )
    monthly_token_limit = models.BigIntegerField(
        null=True, blank=True, verbose_name='每月token限制'
    )
    daily_tokens_used = models.BigIntegerField(
        default=0, verbose_name='今日已用token'
    )
    monthly_tokens_used = models.BigIntegerField(
        default=0, verbose_name='本月已用token'
    )
    total_tokens_used = models.BigIntegerField(
        default=0, verbose_name='总计已用token'
    )
    total_cost = models.DecimalField(
        max_digits=10, decimal_places=2, default='0.00',
        verbose_name='总花费($)'
    )
    last_used_at = models.DateTimeField(
        null=True, blank=True, verbose_name='最后使用时间'
    )
    last_error = models.TextField(
        blank=True, default='', verbose_name='最后错误信息'
    )
    error_count = models.IntegerField(default=0, verbose_name='连续错误次数')

    class Meta:
        verbose_name = 'AI API Key'
        verbose_name_plural = 'AI API Key'
        ordering = ['-priority', 'provider']
        indexes = [
            models.Index(
                fields=['provider', 'is_active'],
                name='idx_apikey_provider_active'
            ),
        ]

    def __str__(self) -> str:
        return f"[{self.provider}] {self.key_name}"


# ---------------------------------------------------------------------------
# 2.2.7 用户配额实体
# ---------------------------------------------------------------------------

class AIUserQuota(BaseAuditModel):
    """用户 AI 使用配额：管控用户每日/每月/累计的 API 调用限额。"""

    QUOTA_TYPE_CHOICES = [
        ('daily', '每日配额'),
        ('monthly', '每月配额'),
        ('total', '总量配额'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='ai_quotas',
        verbose_name='用户',
    )
    quota_type = models.CharField(
        max_length=20, choices=QUOTA_TYPE_CHOICES, verbose_name='配额类型'
    )
    token_limit = models.BigIntegerField(verbose_name='Token限制')
    tokens_used = models.BigIntegerField(default=0, verbose_name='已使用token')
    reset_at = models.DateTimeField(
        null=True, blank=True, verbose_name='下次重置时间'
    )
    is_active = models.BooleanField(default=True, verbose_name='是否启用')

    class Meta:
        verbose_name = '用户AI配额'
        verbose_name_plural = '用户AI配额'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'quota_type'],
                name='uk_user_quota_type'
            )
        ]
        indexes = [
            models.Index(fields=['reset_at'], name='idx_quota_reset_at'),
        ]

    def __str__(self) -> str:
        return f"[{self.get_quota_type_display()}] user={self.user_id} used={self.tokens_used}/{self.token_limit}"


# ---------------------------------------------------------------------------
# 2.2.8 智能体配置实体
# ---------------------------------------------------------------------------

class AIAgentConfig(BaseAuditModel):
    """智能体配置：管理不同上下文下的 AI 预设 Prompt 与行为参数。"""

    agent_key = models.CharField(
        max_length=50, unique=True,
        verbose_name='Agent标识', help_text='如 linux_assistant'
    )
    agent_name = models.CharField(max_length=100, verbose_name='Agent名称')
    description = models.TextField(blank=True, default='', verbose_name='描述')
    system_prompt = models.TextField(verbose_name='系统提示词（System Prompt）')
    context_type = models.CharField(
        max_length=50, blank=True, default='',
        verbose_name='适用上下文', help_text='experiment / vm / general'
    )
    bounded_experiment = models.ForeignKey(
        'experiments.CourseExperiment',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='dedicated_agents',
        verbose_name='绑定特定实验',
        help_text='留空则为该组织/全局通用的预设代理'
    )
    model_config = models.ForeignKey(
        AIModelConfig,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='agents',
        verbose_name='默认模型配置',
    )
    temperature = models.DecimalField(
        max_digits=3, decimal_places=2, default='0.70',
        verbose_name='温度参数'
    )
    max_tokens = models.IntegerField(default=2000, verbose_name='最大token数')
    enable_rag = models.BooleanField(default=True, verbose_name='是否启用RAG检索')
    rag_top_k = models.IntegerField(default=3, verbose_name='RAG检索文档数量')
    enable_memory = models.BooleanField(default=True, verbose_name='是否启用对话记忆')
    memory_window = models.IntegerField(default=20, verbose_name='记忆窗口大小（消息条数）')
    language = models.CharField(
        max_length=10, default='zh-CN', verbose_name='语言'
    )
    is_active = models.BooleanField(default=True, verbose_name='是否启用')

    class Meta:
        verbose_name = '智能体配置'
        verbose_name_plural = '智能体配置'
        ordering = ['agent_key']

    def __str__(self) -> str:
        return f"[{self.agent_key}] {self.agent_name}"


# ---------------------------------------------------------------------------
# 2.2.9 知识库状态实体
# ---------------------------------------------------------------------------

class AIKnowledgeIndexStatus(models.Model):
    """知识库构建状态：记录各实验指导文档的 RAG 向量库构建流水状态。

    此模型不继承 BaseAuditModel，与设计文档 SQL 建表语句保持一致。
    """

    STATUS_CHOICES = [
        ('pending', '等待处理'),
        ('processing', '处理中'),
        ('completed', '已完成'),
        ('failed', '失败'),
    ]

    guidebook = models.OneToOneField(
        'experiments.CourseGuidebook',
        on_delete=models.CASCADE,
        related_name='knowledge_index_status',
        verbose_name='被索引文档',
    )
    experiment = models.ForeignKey(
        'experiments.CourseExperiment',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='knowledge_index_statuses',
        verbose_name='归属实验',
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='pending',
        verbose_name='索引状态'
    )
    chunk_num = models.IntegerField(
        default=0, verbose_name='文档分片总数'
    )
    remark = models.TextField(
        blank=True, default='', verbose_name='备注/错误原因'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '知识库构建状态'
        verbose_name_plural = '知识库构建状态'
        indexes = [
            models.Index(fields=['status'], name='idx_knowledge_sts'),
        ]

    def __str__(self) -> str:
        return f"[{self.get_status_display()}] guidebook={self.guidebook_id}"


# ---------------------------------------------------------------------------
# 2.2.10 AI 使用记录实体
# ---------------------------------------------------------------------------

class AIUsageLog(models.Model):
    """AI 使用记录：明细记录每次 API 调用的 Token 消耗与计费信息，用于报表和对账。

    此模型不继承 BaseAuditModel（无 updated_by / owner_organization 语义），
    仅保留 user 外键与 created_at，与设计文档 SQL 建表语句保持一致。
    """

    STATUS_CHOICES = [
        ('success', '成功'),
        ('error', '失败'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='ai_usage_logs',
        verbose_name='用户',
    )
    conversation = models.ForeignKey(
        ChatConversation,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='usage_logs',
        verbose_name='所属会话',
    )
    message = models.ForeignKey(
        ChatMessage,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='usage_logs',
        verbose_name='所属消息',
    )
    model_key = models.CharField(max_length=50, verbose_name='模型标识')
    api_key = models.ForeignKey(
        AIApiKey,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='usage_logs',
        verbose_name='使用的API Key',
    )
    prompt_tokens = models.IntegerField(default=0, verbose_name='提示词token数')
    completion_tokens = models.IntegerField(default=0, verbose_name='补全token数')
    total_tokens = models.IntegerField(default=0, verbose_name='总token数')
    cost = models.DecimalField(
        max_digits=8, decimal_places=4, default='0.0000',
        verbose_name='费用($)'
    )
    latency_ms = models.IntegerField(
        null=True, blank=True, verbose_name='响应延迟(毫秒)'
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='success',
        verbose_name='调用状态'
    )
    error_message = models.TextField(
        blank=True, default='', verbose_name='错误详情'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        verbose_name = 'AI使用记录'
        verbose_name_plural = 'AI使用记录'
        ordering = ['-created_at']
        indexes = [
            models.Index(
                fields=['user', 'created_at'],
                name='idx_usage_user_created'
            ),
            models.Index(
                fields=['conversation'],
                name='idx_usage_conversation'
            ),
            models.Index(
                fields=['status', 'created_at'],
                name='idx_usage_status'
            ),
        ]

    def __str__(self) -> str:
        return (
            f"[{self.status}] user={self.user_id} "
            f"model={self.model_key} tokens={self.total_tokens}"
        )
