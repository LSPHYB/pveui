"""AI 助手模块序列化器。"""

from rest_framework import serializers
from .models import (
    AIAgentConfig,
    AIApiKey,
    AIKnowledgeIndexStatus,
    AIModelConfig,
    AIUsageLog,
    AIUserQuota,
    ChatConversation,
    ChatConversationSummary,
    ChatExperimentContext,
    ChatMessage,
)


# ---------------------------------------------------------------------------
# 1. 消息序列化器
# ---------------------------------------------------------------------------

class ChatMessageSerializer(serializers.ModelSerializer):
    """对话消息序列化器（读取）。"""
    
    class Meta:
        model = ChatMessage
        fields = [
            'id', 'role', 'content', 'content_type', 'sequence',
            'parent_message', 'prompt_tokens', 'completion_tokens', 'total_tokens',
            'model_name', 'finish_reason', 'function_call', 'tool_calls',
            'additional_kwargs', 'error_message', 'retry_count',
            'feedback', 'feedback_detail', 'created_at',
        ]
        read_only_fields = fields


class ChatMessageCreateSerializer(serializers.Serializer):
    """发送消息请求（写入）。"""
    content = serializers.CharField(max_length=8000)


class ChatMessageFeedbackSerializer(serializers.Serializer):
    """消息反馈请求（点赞/点踩）。"""
    feedback = serializers.ChoiceField(choices=ChatMessage.FEEDBACK_CHOICES)
    feedback_detail = serializers.CharField(max_length=500, required=False, allow_blank=True)


# ---------------------------------------------------------------------------
# 2. 会话序列化器
# ---------------------------------------------------------------------------

class ChatConversationListSerializer(serializers.ModelSerializer):
    """我的会话列表序列化器。"""
    last_message_preview = serializers.SerializerMethodField()

    class Meta:
        model = ChatConversation
        fields = [
            'id', 'session_id', 'title', 'context_type', 'context_id',
            'context_data', 'message_count', 'last_message_at',
            'is_archived', 'model_name', 'created_at', 'updated_at',
            'last_message_preview',
        ]

    def get_last_message_preview(self, obj):
        last_msg = obj.messages.filter(role='ai').order_by('-sequence').first()
        if last_msg:
            return last_msg.content[:100]
        return ''


class ChatConversationDetailSerializer(serializers.ModelSerializer):
    """会话详情序列化器（包含消息列表）。"""
    messages = ChatMessageSerializer(many=True, read_only=True)

    class Meta:
        model = ChatConversation
        fields = [
            'id', 'session_id', 'title', 'context_type', 'context_id',
            'context_data', 'message_count', 'last_message_at',
            'is_archived', 'model_name', 'temperature', 'max_tokens',
            'created_at', 'updated_at', 'messages',
        ]


class ChatConversationCreateSerializer(serializers.Serializer):
    """创建会话请求。"""
    context_type = serializers.CharField(max_length=50, required=False, default='general')
    context_id = serializers.CharField(max_length=100, required=False, default='')
    model_key = serializers.CharField(max_length=50, required=False, default='')
    temperature = serializers.DecimalField(
        max_digits=3, decimal_places=2, required=False, default=None
    )
    context_data = serializers.JSONField(required=False, default=dict)


# ---------------------------------------------------------------------------
# 3. 实验上下文关联
# ---------------------------------------------------------------------------

class ChatExperimentContextSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatExperimentContext
        fields = [
            'id', 'conversation', 'experiment', 'submission',
            'guidebook', 'indexed_content_ids', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


# ---------------------------------------------------------------------------
# 4. 管理端：AI 模型配置
# ---------------------------------------------------------------------------

class AIModelConfigSerializer(serializers.ModelSerializer):
    """AI模型配置管理序列化器。"""
    
    class Meta:
        model = AIModelConfig
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by', 'updated_by', 'owner_organization']


class AIModelConfigToggleSerializer(serializers.Serializer):
    """快捷切换启用状态请求。"""
    is_enabled = serializers.BooleanField()


# ---------------------------------------------------------------------------
# 5. 管理端：API Key 管理
# ---------------------------------------------------------------------------

class AIApiKeyListSerializer(serializers.ModelSerializer):
    """API Key 列表序列化器（隐藏完整明文，仅展示脱敏后的信息）。"""
    api_key_masked = serializers.SerializerMethodField()

    class Meta:
        model = AIApiKey
        fields = [
            'id', 'provider', 'key_name', 'base_url', 'api_key_masked', 'is_active', 'priority',
            'daily_token_limit', 'monthly_token_limit', 'daily_tokens_used',
            'monthly_tokens_used', 'total_tokens_used', 'total_cost',
            'last_used_at', 'last_error', 'error_count', 'created_at', 'updated_at'
        ]

    def get_api_key_masked(self, obj):
        # 取加密后字符串的简单掩码（实际可能是密文，仅展示后8位，或统一返回****）
        raw = obj.api_key_encrypted
        if raw and len(raw) > 8:
            return f"****{raw[-8:]}"
        return "****"


class AIApiKeyCreateSerializer(serializers.Serializer):
    """创建 API Key 序列化器（接收明文 api_key）。"""
    provider = serializers.CharField(max_length=50)
    key_name = serializers.CharField(max_length=100)
    base_url = serializers.CharField(max_length=255, required=False, allow_blank=True)
    api_key = serializers.CharField(max_length=1000, write_only=True)
    priority = serializers.IntegerField(default=0)
    daily_token_limit = serializers.IntegerField(required=False, allow_null=True)
    monthly_token_limit = serializers.IntegerField(required=False, allow_null=True)
    remark = serializers.CharField(max_length=255, required=False, allow_blank=True)


class AIApiKeyRotateSerializer(serializers.Serializer):
    """轮换 API Key 请求。"""
    new_api_key = serializers.CharField(max_length=1000)


# ---------------------------------------------------------------------------
# 6. 管理端：用户配额管理
# ---------------------------------------------------------------------------

class AIUserQuotaSerializer(serializers.ModelSerializer):
    """用户配额序列化器。"""
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = AIUserQuota
        fields = '__all__'
        read_only_fields = ['user', 'created_at', 'updated_at']


class AIUserQuotaBatchSerializer(serializers.Serializer):
    """批量设置配额请求。"""
    user_ids = serializers.ListField(child=serializers.IntegerField(), min_length=1)
    quota_type = serializers.ChoiceField(choices=AIUserQuota.QUOTA_TYPE_CHOICES)
    token_limit = serializers.IntegerField(min_value=0)
    reset_at = serializers.DateTimeField(required=False, allow_null=True)


# ---------------------------------------------------------------------------
# 7. 管理端：智能体配置
# ---------------------------------------------------------------------------

class AIAgentConfigSerializer(serializers.ModelSerializer):
    """智能体配置序列化器。"""
    owner_organization_id = serializers.IntegerField(source='owner_organization.id', required=False, allow_null=True)
    bounded_experiment_id = serializers.IntegerField(source='bounded_experiment.id', required=False, allow_null=True)

    class Meta:
        model = AIAgentConfig
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']

    def update(self, instance, validated_data):
        # Allow clearing organization / experiment by setting to null
        owner_organization = validated_data.pop('owner_organization', None)
        if owner_organization is not None:
             if isinstance(owner_organization, dict):
                  instance.owner_organization_id = owner_organization.get('id')
             else:
                  instance.owner_organization = owner_organization
        elif 'owner_organization' in self.initial_data and self.initial_data.get('owner_organization_id') is None:
             instance.owner_organization = None

        bounded_experiment = validated_data.pop('bounded_experiment', None)
        if bounded_experiment is not None:
             if isinstance(bounded_experiment, dict):
                  instance.bounded_experiment_id = bounded_experiment.get('id')
             else:
                  instance.bounded_experiment = bounded_experiment
        elif 'bounded_experiment' in self.initial_data and self.initial_data.get('bounded_experiment_id') is None:
             instance.bounded_experiment = None

        return super().update(instance, validated_data)

    def create(self, validated_data):
        owner_organization = validated_data.pop('owner_organization', None)
        bounded_experiment = validated_data.pop('bounded_experiment', None)

        instance = super().create(validated_data)

        if owner_organization is not None:
             if isinstance(owner_organization, dict):
                  instance.owner_organization_id = owner_organization.get('id')
             else:
                  instance.owner_organization = owner_organization
                  
        if bounded_experiment is not None:
             if isinstance(bounded_experiment, dict):
                  instance.bounded_experiment_id = bounded_experiment.get('id')
             else:
                  instance.bounded_experiment = bounded_experiment

        if owner_organization or bounded_experiment:
            instance.save()
            
        return instance


class AIAgentTestSerializer(serializers.Serializer):
    """智能体连通性测试请求。"""
    question = serializers.CharField(max_length=2000)
    agent_key = serializers.CharField(max_length=50)


# ---------------------------------------------------------------------------
# 8. 知识库与使用记录
# ---------------------------------------------------------------------------

class AIKnowledgeIndexStatusSerializer(serializers.ModelSerializer):
    """知识库构建状态序列化器。"""
    guidebook_title = serializers.CharField(source='guidebook.title', read_only=True)
    experiment_title = serializers.CharField(source='experiment.title', read_only=True, default='')

    class Meta:
        model = AIKnowledgeIndexStatus
        fields = '__all__'


class AIKnowledgeRebuildSerializer(serializers.Serializer):
    """触发重建请求。"""
    guidebook_ids = serializers.ListField(child=serializers.IntegerField(), min_length=1)
    force = serializers.BooleanField(default=False)
    clear_existing = serializers.BooleanField(default=False)


class AIUsageLogSerializer(serializers.ModelSerializer):
    """使用记录日志序列化器。"""
    class Meta:
        model = AIUsageLog
        fields = '__all__'
