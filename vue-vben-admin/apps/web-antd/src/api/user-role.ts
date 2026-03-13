import { requestClient } from '#/api/request';

export interface UserRole {
  id: number;
  user: number;
  role: number;
  created_at?: string;
}

export interface UserRoleListParams {
  page?: number;
  page_size?: number;
  user?: number;
  role?: number;
}

export interface UserRoleListResult {
  count: number;
  next?: null | string;
  previous?: null | string;
  results: UserRole[];
}

export interface CreateUserRoleData {
  user: number;
  role: number;
}

/**
 * 获取用户角色列表
 */
export async function getUserRoleList(params?: UserRoleListParams) {
  return requestClient.get<UserRoleListResult>('/rbac/user-roles/', { params });
}

/**
 * 获取用户角色详情
 */
export async function getUserRoleDetail(id: number) {
  return requestClient.get<UserRole>(`/rbac/user-roles/${id}/`);
}

/**
 * 创建用户角色关联
 */
export async function createUserRole(data: CreateUserRoleData) {
  return requestClient.post<UserRole>('/rbac/user-roles/', data);
}

/**
 * 删除用户角色关联
 */
export async function deleteUserRole(id: number) {
  return requestClient.delete(`/rbac/user-roles/${id}/`);
}
