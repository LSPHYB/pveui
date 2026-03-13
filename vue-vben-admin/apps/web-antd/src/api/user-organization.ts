import { requestClient } from '#/api/request';

export interface UserOrganization {
  id: number;
  user: number;
  organization: number;
  is_primary: boolean;
  created_at?: string;
}

export interface UserOrganizationListParams {
  page?: number;
  page_size?: number;
  user?: number;
  organization?: number;
}

export interface UserOrganizationListResult {
  count: number;
  next?: null | string;
  previous?: null | string;
  results: UserOrganization[];
}

export interface CreateUserOrganizationData {
  user: number;
  organization: number;
  is_primary?: boolean;
}

export interface UpdateUserOrganizationData {
  user?: number;
  organization?: number;
  is_primary?: boolean;
}

/**
 * 获取用户组织列表
 */
export async function getUserOrganizationList(
  params?: UserOrganizationListParams,
) {
  return requestClient.get<UserOrganizationListResult>(
    '/rbac/user-organizations/',
    { params },
  );
}

/**
 * 获取用户组织详情
 */
export async function getUserOrganizationDetail(id: number) {
  return requestClient.get<UserOrganization>(`/rbac/user-organizations/${id}/`);
}

/**
 * 创建用户组织关联
 */
export async function createUserOrganization(data: CreateUserOrganizationData) {
  return requestClient.post<UserOrganization>(
    '/rbac/user-organizations/',
    data,
  );
}

/**
 * 更新用户组织关联
 */
export async function updateUserOrganization(
  id: number,
  data: UpdateUserOrganizationData,
) {
  return requestClient.put<UserOrganization>(
    `/rbac/user-organizations/${id}/`,
    data,
  );
}

/**
 * 删除用户组织关联
 */
export async function deleteUserOrganization(id: number) {
  return requestClient.delete(`/rbac/user-organizations/${id}/`);
}
