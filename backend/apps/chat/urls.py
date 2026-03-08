"""聊天模块及 AI 管理端路由。"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    AdminAIAgentConfigViewSet,
    AdminAIApiKeyViewSet,
    AdminAIKnowledgeIndexViewSet,
    AdminAIModelConfigViewSet,
    AdminAIUserQuotaViewSet,
    ChatConversationViewSet,
    AvailableModelsView,
    MyQuotaView,
    AdminAIStatsOverviewView,
    AdminAIUsageTrendView,
)

# 1. 基础对话路由 prefix: /api/v1/chat/
user_router = DefaultRouter()
user_router.register(r'conversations', ChatConversationViewSet, basename='chat-conversations')

# 2. 管理端路由 prefix: /api/v1/chat/admin/ai/
admin_router = DefaultRouter()
admin_router.register(r'models', AdminAIModelConfigViewSet, basename='admin-ai-models')
admin_router.register(r'api-keys', AdminAIApiKeyViewSet, basename='admin-ai-apikeys')
admin_router.register(r'quotas', AdminAIUserQuotaViewSet, basename='admin-ai-quotas')
admin_router.register(r'agents', AdminAIAgentConfigViewSet, basename='admin-ai-agents')
admin_router.register(r'knowledge/indexes', AdminAIKnowledgeIndexViewSet, basename='admin-ai-knowledge')


urlpatterns = [
    # 挂载用户端，形成: /api/v1/chat/conversations/
    path('', include(user_router.urls)),

    # 用户端独立视图
    # GET /api/v1/chat/models/available/
    path('models/available/', AvailableModelsView.as_view(), name='chat-available-models'),
    # GET /api/v1/chat/my-quota/
    path('my-quota/', MyQuotaView.as_view(), name='chat-my-quota'),

    # 管理端分析数据图表
    # GET /api/v1/chat/admin/ai/stats/overview/
    path('admin/ai/stats/overview/', AdminAIStatsOverviewView.as_view(), name='admin-ai-stats-overview'),
    # GET /api/v1/chat/admin/ai/stats/usage-trend/
    path('admin/ai/stats/usage-trend/', AdminAIUsageTrendView.as_view(), name='admin-ai-stats-usage-trend'),

    # 挂载管理端，形成: /api/v1/chat/admin/ai/models/
    path('admin/ai/', include(admin_router.urls)),
]
