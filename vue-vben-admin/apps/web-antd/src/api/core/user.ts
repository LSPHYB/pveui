import type { UserInfo } from '@vben/types';

import { requestClient } from '#/api/request';

/**
 * 获取用户信息 - 适配Django
 */
export async function getUserInfoApi() {
  return requestClient.get<UserInfo>('/rbac/auth/user-info/');
}
