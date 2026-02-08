import { requestClient } from '#/api/request';

export interface UserManagement {
  id: number;
  username: string;
  email: string;
  first_name?: string;
  last_name?: string;
  is_active: boolean;
  is_staff: boolean;
  is_superuser: boolean;
  date_joined: string;
  last_login?: string;
}

export interface UserListParams {
  page?: number;
  page_size?: number;
  search?: string;
}

export interface UserListResult {
  count: number;
  next?: null | string;
  previous?: null | string;
  results: UserManagement[];
}

export interface CreateUserData {
  username: string;
  email: string;
  password: string;
  first_name?: string;
  last_name?: string;
  is_active?: boolean;
  is_staff?: boolean;
  is_superuser?: boolean;
}

export interface UpdateUserData {
  username?: string;
  email?: string;
  password?: string;
  first_name?: string;
  last_name?: string;
  is_active?: boolean;
  is_staff?: boolean;
  is_superuser?: boolean;
}

/**
 * 获取用户列表
 */
export async function getUserList(params?: UserListParams) {
  return requestClient.get<UserListResult>('/rbac/users/', { params });
}

/**
 * 获取用户详情
 */
export async function getUserDetail(id: number) {
  return requestClient.get<UserManagement>(`/rbac/users/${id}/`);
}

/**
 * 创建用户
 */
export async function createUser(data: CreateUserData) {
  return requestClient.post<UserManagement>('/rbac/users/', data);
}

/**
 * 更新用户
 */
export async function updateUser(id: number, data: UpdateUserData) {
  return requestClient.put<UserManagement>(`/rbac/users/${id}/`, data);
}

/**
 * 删除用户
 */
export async function deleteUser(id: number) {
  return requestClient.delete(`/rbac/users/${id}/`);
}
