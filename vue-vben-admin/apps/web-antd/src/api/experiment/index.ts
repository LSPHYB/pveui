import type {
  ApiResponse,
  CreateExperimentPayload,
  ExperimentDetail,
  ExperimentListItem,
  GuidebookListItem,
  GuidebookPreviewResult,
  PaginatedData,
  SubmissionDetail,
  SubmissionListItem,
} from './types';

import { requestClient } from '#/api/request';

/** 
 * 从响应中提取业务数据，兼容两层包装：
 *  1. Axios 响应对象  → response.data  （HTTP 响应体）
 *  2. 后端统一格式     → body.data      （{ code, message, data } 中的 data 字段）
 *
 * 注意：当前项目的 requestClient 未通过 defaultResponseInterceptor 实现
 * responseReturn:'data'，所以 requestClient.get/post 等方法始终返回完整
 * AxiosResponse 对象，需在此处手动剥离。
 */
function extractData<T>(res: any): T {
  // Step 1: 若是完整 Axios 响应（有 headers），取 response.data（HTTP 响应体）
  let body: any = res;
  if (res && typeof res === 'object' && 'headers' in res && 'data' in res) {
    body = res.data;
  }
  // Step 2: 若是后端包装格式 { code, data }，取内层 data
  if (body && typeof body === 'object' && 'code' in body && 'data' in body) {
    return body.data as T;
  }
  return body as T;
}


// ─────────────────────── Experiment ───────────────────────

/** 获取实验列表 */
export async function getExperimentListApi(params?: Record<string, any>) {
  const res = await requestClient.get<ApiResponse<PaginatedData<ExperimentListItem>>>(
    '/v1/experiments/',
    { params },
  );
  return extractData<PaginatedData<ExperimentListItem>>(res);
}

/** 获取实验详情 */
export async function getExperimentDetailApi(id: number | string) {
  const res = await requestClient.get<ApiResponse<ExperimentDetail>>(
    `/v1/experiments/${id}/`,
  );
  return extractData<ExperimentDetail>(res);
}

/** 创建实验 */
export async function createExperimentApi(data: CreateExperimentPayload) {
  const res = await requestClient.post<ApiResponse<ExperimentDetail>>(
    '/v1/experiments/',
    data,
  );
  return extractData<ExperimentDetail>(res);
}

/** 更新实验（PATCH） */
export async function updateExperimentApi(
  id: number | string,
  data: Partial<CreateExperimentPayload>,
) {
  const res = await requestClient.request<ApiResponse<ExperimentDetail>>(
    `/v1/experiments/${id}/`,
    { data, method: 'PATCH' },
  );
  return extractData<ExperimentDetail>(res);
}

/** 删除实验（软删除） */
export async function deleteExperimentApi(id: number | string) {
  const res = await requestClient.delete<ApiResponse<null>>(
    `/v1/experiments/${id}/`,
  );
  return extractData<null>(res);
}

/** 发布实验 */
export async function publishExperimentApi(id: number | string) {
  const res = await requestClient.post<ApiResponse<{ id: number; status: string }>>(
    `/v1/experiments/${id}/publish/`,
  );
  return extractData<{ id: number; status: string }>(res);
}

/** 归档实验 */
export async function archiveExperimentApi(id: number | string) {
  const res = await requestClient.post<ApiResponse<{ id: number; status: string }>>(
    `/v1/experiments/${id}/archive/`,
  );
  return extractData<{ id: number; status: string }>(res);
}

/** 导出成绩（返回 Blob 用于下载） */
export function getExportGradesUrl(id: number | string) {
  return `/api/v1/experiments/${id}/export_grades/`;
}

// ─────────────────────── Guidebook ───────────────────────

/** 获取实验指导书列表 */
export async function getGuidebookListApi(experimentId: number | string) {
  const res = await requestClient.get<ApiResponse<GuidebookListItem[]>>(
    `/v1/experiments/${experimentId}/guidebooks/`,
  );
  return extractData<GuidebookListItem[]>(res);
}

/** 上传指导文档（multipart） */
export async function uploadGuidebookApi(
  experimentId: number | string,
  formData: FormData,
) {
  const res = await requestClient.post<ApiResponse<GuidebookListItem>>(
    `/v1/experiments/${experimentId}/guidebooks/`,
    formData,
    { headers: { 'Content-Type': 'multipart/form-data' } },
  );
  return extractData<GuidebookListItem>(res);
}

/** 删除指导文档 */
export async function deleteGuidebookApi(id: number | string) {
  const res = await requestClient.delete<ApiResponse<null>>(
    `/v1/guidebooks/${id}/`,
  );
  return extractData<null>(res);
}

/** 预览指导文档 */
export async function previewGuidebookApi(id: number | string) {
  const res = await requestClient.get<ApiResponse<GuidebookPreviewResult>>(
    `/v1/guidebooks/${id}/preview/`,
  );
  return extractData<GuidebookPreviewResult>(res);
}

/** 下载指导文档 URL */
export function getGuidebookDownloadUrl(id: number | string) {
  return `/api/v1/guidebooks/${id}/download/`;
}

// ─────────────────────── Submission ───────────────────────

/** 获取提交列表（教师/学生） */
export async function getSubmissionListApi(params?: Record<string, any>) {
  const res = await requestClient.get<ApiResponse<PaginatedData<SubmissionListItem>>>(
    '/v1/submissions/',
    { params },
  );
  return extractData<PaginatedData<SubmissionListItem>>(res);
}

/** 获取我的提交（学生），不存在自动创建草稿 */
export async function getMySubmissionApi(experimentId: number | string) {
  const res = await requestClient.get<ApiResponse<SubmissionDetail>>(
    '/v1/submissions/my/',
    { params: { experiment_id: experimentId } },
  );
  return extractData<SubmissionDetail>(res);
}

/** 获取提交详情 */
export async function getSubmissionDetailApi(id: number | string) {
  const res = await requestClient.get<ApiResponse<SubmissionDetail>>(
    `/v1/submissions/${id}/`,
  );
  return extractData<SubmissionDetail>(res);
}

/** 保存草稿（自动保存，PATCH） */
export async function saveDraftApi(
  id: number | string,
  data: { report_title?: string; report_content?: string; vm_info?: any; operation_logs?: any[] },
) {
  const res = await requestClient.request<ApiResponse<{ last_auto_save: string }>>(
    `/v1/submissions/${id}/`,
    { data, method: 'PATCH' },
  );
  return extractData<{ last_auto_save: string }>(res);
}

/** 提交报告 */
export async function submitReportApi(id: number | string) {
  const res = await requestClient.post<ApiResponse<any>>(
    `/v1/submissions/${id}/submit/`,
    { confirm_submission: true },
  );
  return extractData<any>(res);
}

/** 批改提交（教师） */
export async function gradeSubmissionApi(
  id: number | string,
  data: {
    score: number;
    feedback?: string;
    scoring_details?: Record<string, any>;
  },
) {
  const res = await requestClient.post<ApiResponse<any>>(
    `/v1/submissions/${id}/grade/`,
    data,
  );
  return extractData<any>(res);
}

/** 退回修改（教师） */
export async function returnSubmissionApi(id: number | string, reason: string) {
  const res = await requestClient.post<ApiResponse<any>>(
    `/v1/submissions/${id}/return/`,
    { reason },
  );
  return extractData<any>(res);
}

/** 上传附件（multipart） */
export async function uploadAttachmentApi(
  submissionId: number | string,
  formData: FormData,
) {
  const res = await requestClient.post<ApiResponse<any>>(
    `/v1/submissions/${submissionId}/attachments/`,
    formData,
    { headers: { 'Content-Type': 'multipart/form-data' } },
  );
  return extractData<any>(res);
}

/** 删除附件 */
export async function deleteAttachmentApi(id: number | string) {
  const res = await requestClient.delete<ApiResponse<null>>(
    `/v1/attachments/${id}/`,
  );
  return extractData<null>(res);
}

/** 下载附件 URL */
export function getAttachmentDownloadUrl(id: number | string) {
  return `/api/v1/attachments/${id}/download/`;
}
