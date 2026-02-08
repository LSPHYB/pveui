import { requestClient } from '#/api/request';

export interface Role {
  id: number;
  name: string;
  code: string;
  description?: string;
  menus?: number[];
  permissions?: number[];
  data_scope?: 'ALL' | 'CUSTOM' | 'DEPT' | 'DEPT_AND_SUB' | 'SELF';
  custom_data_organizations?: number[];
  is_active?: boolean; // Note: Model doesn't have is_active on Role, but maybe serialization adds it or I confused it with Permission. Model has NO is_active on Role.
}

export interface RoleListParams {
  page?: number;
  page_size?: number;
  search?: string;
}

export interface RoleListResult {
  count: number;
  next?: null | string;
  previous?: null | string;
  results: Role[];
}

export interface CreateRoleData {
  name: string;
  code: string;
  description?: string;
  menus?: number[];
  permissions?: number[];
  data_scope?: string;
  custom_data_organizations?: number[];
}

export interface UpdateRoleData {
  name?: string;
  code?: string;
  description?: string;
  menus?: number[];
  permissions?: number[];
  data_scope?: string;
  custom_data_organizations?: number[];
}

/**
 * 获取角色列表
 */
export async function getRoleList(params?: RoleListParams) {
  return requestClient.get<RoleListResult>('/rbac/roles/', { params });
}

/**
 * 获取角色详情
 */
export async function getRoleDetail(id: number) {
  return requestClient.get<Role>(`/rbac/roles/${id}/`);
}

/**
 * 创建角色
 */
export async function createRole(data: CreateRoleData) {
  return requestClient.post<Role>('/rbac/roles/', data);
}

/**
 * 更新角色
 */
export async function updateRole(id: number, data: UpdateRoleData) {
  return requestClient.put<Role>(`/rbac/roles/${id}/`, data);
}

/**
 * 删除角色
 */
export async function deleteRole(id: number) {
  return requestClient.delete(`/rbac/roles/${id}/`);
}
