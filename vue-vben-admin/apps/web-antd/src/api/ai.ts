import { requestClient } from '#/api/request';

// ───────────────────────────────────────────────────────
// 管理端 API (Admin)
// 基础路径: /api/v1/chat/admin/ai/
// ───────────────────────────────────────────────────────

/** 获取AI模型配置列表 */
export async function getAiModelsApi(params?: any) {
  return requestClient.get('/chat/admin/ai/models/', { params });
}

/** 新建AI模型配置 */
export async function createAiModelApi(data: any) {
  return requestClient.post('/chat/admin/ai/models/', data);
}

/** 更新AI模型配置 */
export async function updateAiModelApi(id: number, data: any) {
  return requestClient.put(`/chat/admin/ai/models/${id}/`, data);
}

export async function testAiModelConnectionApi(id: number | string) {
  return requestClient.post(
    `/chat/admin/ai/models/${id}/test-connection/`,
  );
}

/** 删除AI模型配置 */
export async function deleteAiModelApi(id: number) {
  return requestClient.delete(`/chat/admin/ai/models/${id}/`);
}

/** 切换模型启用状态 */
export async function toggleAiModelApi(id: number, is_enabled: boolean) {
  return requestClient.post(`/chat/admin/ai/models/${id}/toggle/`, {
    is_enabled,
  });
}

/** 获取API Key列表 */
export async function getAiApiKeysApi(params?: any) {
  return requestClient.get('/chat/admin/ai/api-keys/', { params });
}

/** 新建API Key */
export async function createAiApiKeyApi(data: any) {
  return requestClient.post('/chat/admin/ai/api-keys/', data);
}

/** 轮换API Key */
export async function rotateAiApiKeyApi(id: number, data: any) {
  return requestClient.post(`/chat/admin/ai/api-keys/${id}/rotate/`, data);
}

/** 禁用API Key */
export async function disableAiApiKeyApi(id: number) {
  return requestClient.post(`/chat/admin/ai/api-keys/${id}/disable/`);
}

/** 删除API Key */
export async function deleteAiApiKeyApi(id: number) {
  return requestClient.delete(`/chat/admin/ai/api-keys/${id}/`);
}

/** 获取用户配额列表 */
export async function getAiQuotasApi(params?: any) {
  return requestClient.get('/chat/admin/ai/quotas/', { params });
}

/** 批量设置用户配额 */
export async function batchSetAiQuotasApi(data: any) {
  return requestClient.post('/chat/admin/ai/quotas/batch-set/', data);
}

/** 修改单个用户配额 */
export async function updateAiQuotaApi(id: number, data: any) {
  return requestClient.put(`/chat/admin/ai/quotas/${id}/`, data);
}

/** 删除某个用户配额 */
export async function deleteAiQuotaApi(id: number) {
  return requestClient.delete(`/chat/admin/ai/quotas/${id}/`);
}

/** 重置单个用户配额 */
export async function resetAiQuotaApi(id: number) {
  return requestClient.post(`/chat/admin/ai/quotas/${id}/reset/`);
}

/** 获取智能体配置列表 */
export async function getAiAgentsApi(params?: any) {
  return requestClient.get('/chat/admin/ai/agents/', { params });
}

/** 新建智能体配置 */
export async function createAiAgentApi(data: any) {
  return requestClient.post('/chat/admin/ai/agents/', data);
}

/** 更新智能体配置 */
export async function updateAiAgentApi(id: number, data: any) {
  return requestClient.put(`/chat/admin/ai/agents/${id}/`, data);
}

/** 删除智能体配置 */
export async function deleteAiAgentApi(id: number) {
  return requestClient.delete(`/chat/admin/ai/agents/${id}/`);
}

/** 测试智能体 */
export async function testAiAgentApi(id: number, data: any) {
  return requestClient.post(`/chat/admin/ai/agents/${id}/test/`, data);
}

/** 获取知识库索引状态列表 */
export async function getAiKnowledgeIndexesApi(params?: any) {
  return requestClient.get('/chat/admin/ai/knowledge/indexes/', { params });
}

/** 触发知识库重建 */
export async function rebuildAiKnowledgeIndexApi(data: any) {
  return requestClient.post(
    '/chat/admin/ai/knowledge/indexes/rebuild/',
    data,
  );
}

/** 统计总览 */
export async function getAiStatsOverviewApi() {
  return requestClient.get('/chat/admin/ai/stats/overview/');
}

/** 近30天使用趋势 */
export async function getAiUsageTrendApi() {
  return requestClient.get('/chat/admin/ai/stats/usage-trend/');
}

// ───────────────────────────────────────────────────────
// 用户端 API (User-side, 供 AiChatDrawer 使用)
// 基础路径: /api/v1/chat/
// ───────────────────────────────────────────────────────

/**
 * 获取当前用户可用的 AI 模型列表
 * GET /api/v1/chat/models/available/
 */
export async function getAvailableModelsApi() {
  return requestClient.get('/chat/models/available/');
}

/**
 * 查看我的配额使用情况
 * GET /api/v1/chat/my-quota/
 */
export async function getMyQuotaApi() {
  return requestClient.get('/chat/my-quota/');
}

/**
 * 获取我的会话列表
 * GET /api/v1/chat/conversations/my/
 */
export async function getMyConversationsApi(params?: {
  page?: number;
  page_size?: number;
  is_archived?: boolean;
  context_type?: string;
}) {
  return requestClient.get('/chat/conversations/my/', { params });
}

/**
 * 创建新会话
 * POST /api/v1/chat/conversations/
 */
export async function createConversationApi(data: {
  context_type?: string;
  context_id?: string;
  model_key?: string;
  temperature?: number;
  context_data?: Record<string, any>;
}) {
  return requestClient.post('/chat/conversations/', data);
}

/**
 * 获取会话详情（含消息列表）
 * GET /api/v1/chat/conversations/{id}/
 */
export async function getConversationDetailApi(id: number) {
  return requestClient.get(`/chat/conversations/${id}/`);
}

/**
 * 软删除会话
 * DELETE /api/v1/chat/conversations/{id}/
 */
export async function deleteConversationApi(id: number) {
  return requestClient.delete(`/chat/conversations/${id}/`);
}

/**
 * 归档会话
 * POST /api/v1/chat/conversations/{id}/archive/
 */
export async function archiveConversationApi(id: number) {
  return requestClient.post(`/chat/conversations/${id}/archive/`);
}
