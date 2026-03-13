import type { UserInfo } from '@vben/types';

import { requestClient } from '#/api/request';

/**
 * 获取用户信息 - 适配Django
 */
export async function getUserInfoApi() {
  const result: any = await requestClient.get<any>('/rbac/auth/user-info/');
  const userInfo = result.data || result;

  // Ensure realName is populated for Vben UI
  return {
    ...userInfo,
    realName: ([userInfo.first_name, userInfo.last_name].filter(Boolean).join(' ')) || userInfo.username,
  } as UserInfo;
}
