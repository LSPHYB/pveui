import type { ChangePasswordParams, OrganizationInfo } from './types';

/**
 * 用户认证相关API - Django特有接口
 * 注意: loginApi, logoutApi, getUserInfoApi 已在 core/auth.ts 和 core/user.ts 中实现
 * 这里只保留Django特有的其他接口
 */
import { requestClient } from '#/api/request';

/**
 * 修改密码
 */
export async function changePasswordApi(data: ChangePasswordParams) {
  return requestClient.post<void>('/rbac/auth/change-password/', data);
}

/**
 * 获取当前用户权限列表
 */
export async function getUserPermissionsApi() {
  return requestClient.get<string[]>('/rbac/auth/permissions/');
}

/**
 * 获取当前用户组织信息
 */
export async function getUserOrganizationsApi() {
  return requestClient.get<OrganizationInfo[]>('/rbac/auth/organizations/');
}
