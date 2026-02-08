import { requestClient } from '#/api/request';

export interface Permission {
  id: number;
  name: string;
  code: string;
  http_method: string;
  url_pattern: string;
  menu: null | number | { title: string }; // Handle relation expansion
  menu_id?: null | number; // Backend might use menu_id instead of menu
  is_active: boolean;
}

export interface PermissionListParams {
  page?: number;
  page_size?: number;
  search?: string;
}

export interface PermissionListResult {
  count: number;
  next?: null | string;
  previous?: null | string;
  results: Permission[];
}

/**
 * 获取权限列表
 */
export async function getPermissionList(params?: PermissionListParams) {
  return requestClient.get<PermissionListResult>('/rbac/permissions/', {
    params,
  });
}

/**
 * 获取权限详情
 */
export async function getPermissionDetail(id: number) {
  return requestClient.get<Permission>(`/rbac/permissions/${id}/`);
}

export async function createPermission(data: any) {
  return requestClient.post('/rbac/permissions/', data);
}

export async function updatePermission(id: number, data: any) {
  return requestClient.put(`/rbac/permissions/${id}/`, data);
}

export async function deletePermission(id: number) {
  return requestClient.delete(`/rbac/permissions/${id}/`);
}
