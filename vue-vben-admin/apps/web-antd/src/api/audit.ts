import { requestClient } from '#/api/request';

/**
 * 审计日志 API
 */

// Operation Log Types
export interface OperationLog {
  id: number;
  user_display: string;
  username: string;
  action_type: string;
  action_type_display: string;
  request_method: string;
  request_path: string;
  request_params?: any;
  ip_address: string;
  user_agent: string;
  status_code: number;
  error_message?: string;
  object_repr?: string;
  content_type_display?: string;
  remark?: string;
  created_at: string;
}

export interface LoginLog {
  id: number;
  user_display: string;
  username: string;
  action_type: string; // 'login' | 'logout' | 'failed'
  action_type_display: string;
  ip_address: string;
  user_agent: string;
  status_code: number;
  created_at: string;
}

/**
 * 获取操作日志列表
 */
export async function getOperationLogList(params?: any) {
  return requestClient.get<{ count: number; results: OperationLog[] }>(
    '/audit/logs/',
    { params },
  );
}

/**
 * 获取操作日志详情
 */
export async function getOperationLogDetail(id: number) {
  return requestClient.get<OperationLog>(`/audit/logs/${id}/`);
}

/**
 * 获取登录日志列表
 */
export async function getLoginLogList(params?: any) {
  return requestClient.get<{ count: number; results: LoginLog[] }>(
    '/audit/login-logs/',
    { params },
  );
}
