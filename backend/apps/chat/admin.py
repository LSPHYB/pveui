"""聊天模块及 AI 管理端的 Django Admin 注册配置。"""

from django.contrib import admin
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

@admin.register(ChatConversation)
class ChatConversationAdmin(admin.ModelAdmin):
    list_display = ('session_id', 'title', 'user', 'context_type', 'message_count', 'is_archived', 'created_at')
    list_filter = ('context_type', 'is_archived', 'model_name')
    search_fields = ('session_id', 'title', 'user__username')
    readonly_fields = ('session_id', 'message_count', 'last_message_at')

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('conversation', 'role', 'sequence', 'content_type', 'created_at')
    list_filter = ('role', 'content_type', 'finish_reason')
    search_fields = ('content', 'conversation__session_id')
    readonly_fields = ('prompt_tokens', 'completion_tokens', 'total_tokens')

@admin.register(AIModelConfig)
class AIModelConfigAdmin(admin.ModelAdmin):
    list_display = ('model_key', 'model_name', 'model_type', 'is_enabled', 'is_default')
    list_filter = ('model_type', 'is_enabled')
    search_fields = ('model_key', 'model_name')

@admin.register(AIApiKey)
class AIApiKeyAdmin(admin.ModelAdmin):
    list_display = ('provider', 'key_name', 'is_active', 'priority', 'total_cost', 'last_used_at')
    list_filter = ('provider', 'is_active')
    search_fields = ('key_name',)

@admin.register(AIUserQuota)
class AIUserQuotaAdmin(admin.ModelAdmin):
    list_display = ('user', 'quota_type', 'tokens_used', 'token_limit', 'reset_at', 'is_active')
    list_filter = ('quota_type', 'is_active')
    search_fields = ('user__username',)

@admin.register(AIAgentConfig)
class AIAgentConfigAdmin(admin.ModelAdmin):
    list_display = ('agent_key', 'agent_name', 'context_type', 'enable_rag', 'enable_memory', 'is_active')
    list_filter = ('context_type', 'is_active')
    search_fields = ('agent_key', 'agent_name')

admin.site.register(ChatExperimentContext)
admin.site.register(ChatConversationSummary)
admin.site.register(AIKnowledgeIndexStatus)
admin.site.register(AIUsageLog)
