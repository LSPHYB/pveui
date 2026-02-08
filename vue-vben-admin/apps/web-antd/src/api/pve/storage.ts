import type { PveStorage } from './types';

import { requestClient } from '#/api/request';

/**
 * 获取指定节点的存储列表
 */
/**
 * 获取指定节点的存储列表
 */
export async function getStorageListApi(serverId: number, node: string) {
  return requestClient.get<PveStorage[]>(
    `/pve/servers/${serverId}/nodes/${node}/storage/`,
  );
}

/**
 * 获取存储内容
 */
export async function getStorageContentApi(
  serverId: number | string,
  node: string,
  storage: string,
  content?: string,
) {
  return requestClient.get<any[]>(
    `/pve/servers/${serverId}/nodes/${node}/storage/${storage}/content/`,
    {
      params: { content },
    },
  );
}

/**
 * 上传文件到存储
 */
export async function uploadToStorageApi(
  serverId: number | string,
  node: string,
  storage: string,
  params: any,
) {
  return requestClient.post(
    `/pve/servers/${serverId}/nodes/${node}/storage/${storage}/upload/`,
    params,
    {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    },
  );
}

/**
 * 删除存储内容
 */
export async function deleteStorageContentApi(
  serverId: number | string,
  node: string,
  storage: string,
  volume: string,
) {
  return requestClient.delete(
    `/pve/servers/${serverId}/nodes/${node}/storage/${storage}/content/`,
    {
      params: { volume },
    },
  );
}
