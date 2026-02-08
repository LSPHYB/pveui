import type { LxcContainerModel } from './types';

import { requestClient } from '#/api/request';

enum Api {
  GetLxcs = '/pve/lxc-containers/',
}

/**
 * 获取所有容器列表 (DB)
 */
export async function getLxcListApi() {
  return requestClient.get<LxcContainerModel[]>(Api.GetLxcs);
}

/**
 * 获取单个容器详情 (DB)
 */
export async function getLxcByIdApi(id: number | string) {
  return requestClient.get<LxcContainerModel>(`${Api.GetLxcs}${id}/`);
}

/**
 * 容器操作
 * @param id Database ID of the Container
 * @param action start, stop, shutdown, reboot
 */
export async function operateLxcApi(id: number | string, action: string) {
  return requestClient.post(`/pve/lxc-containers/${id}/container_action/`, {
    action,
  });
}

/**
 * 获取容器详情
 */
export async function getLxcDetailApi(node: string, vmid: number) {
  return requestClient.get<any>(
    `/pve/nodes/${node}/lxc/${vmid}/status/current`,
  );
}

/**
 * 同步所有容器列表
 */
export async function syncLxcListApi(serverId?: number) {
  return requestClient.post(`${Api.GetLxcs}sync_all/`, { server_id: serverId });
}
/**
 * 获取容器实时状态 (From PVE)
 */
export async function getLxcStatusByIdApi(id: number | string) {
  return requestClient.get(`${Api.GetLxcs}${id}/status/`);
}

/**
 * 获取容器RRD监控数据
 */
export async function getLxcRrdByIdApi(
  id: number | string,
  timeframe: string = 'hour',
  cf: string = 'AVERAGE',
) {
  return requestClient.get<any[]>(`${Api.GetLxcs}${id}/rrd/`, {
    params: { timeframe, cf },
  });
}

/**
 * 获取容器配置
 */
export async function getLxcConfigApi(id: number | string) {
  return requestClient.get<{ config: any }>(`${Api.GetLxcs}${id}/config/`);
}

/**
 * 更新容器配置
 */
export async function updateLxcConfigApi(id: number | string, params: any) {
  return requestClient.put(`${Api.GetLxcs}${id}/config/`, { params });
}

/**
 * 获取容器控制台会话
 */
export async function getLxcConsoleApi(id: number | string) {
  return requestClient.post(`${Api.GetLxcs}${id}/console-session/`);
}

/**
 * 获取容器备份列表
 */
export async function getLxcBackupsApi(id: number | string) {
  return requestClient.get<any>(`${Api.GetLxcs}${id}/backups/`);
}

/**
 * 创建容器备份
 */
export async function createLxcBackupApi(id: number | string, data: any) {
  return requestClient.post<any>(`${Api.GetLxcs}${id}/create_backup/`, data);
}

/**
 * 还原容器备份
 */
export async function restoreLxcBackupApi(id: number | string, data: any) {
  return requestClient.post<any>(`${Api.GetLxcs}${id}/restore_backup/`, data);
}

/**
 * 删除容器备份
 */
export async function deleteLxcBackupApi(id: number | string, data: any) {
  return requestClient.post<any>(`${Api.GetLxcs}${id}/delete_backup/`, data);
}

/**
 * 更新容器备份备注
 */
export async function updateLxcBackupNotesApi(id: number | string, data: any) {
  return requestClient.post<any>(
    `${Api.GetLxcs}${id}/update_backup_notes/`,
    data,
  );
}

/**
 * 更新容器备份保护状态
 */
export async function updateLxcBackupProtectionApi(
  id: number | string,
  data: any,
) {
  return requestClient.post<any>(
    `${Api.GetLxcs}${id}/update_backup_protection/`,
    data,
  );
}

/**
 * 获取容器快照列表
 */
export async function getLxcSnapshotsApi(id: number | string) {
  return requestClient.get<any>(`${Api.GetLxcs}${id}/snapshots/`);
}

/**
 * 创建容器快照
 */
export async function createLxcSnapshotApi(id: number | string, data: any) {
  return requestClient.post<any>(`${Api.GetLxcs}${id}/create_snapshot/`, data);
}

/**
 * 回滚容器快照
 */
export async function rollbackLxcSnapshotApi(id: number | string, data: any) {
  return requestClient.post<any>(
    `${Api.GetLxcs}${id}/rollback_snapshot/`,
    data,
  );
}

/**
 * 更新容器快照描述
 */
export async function updateLxcSnapshotApi(id: number | string, data: any) {
  return requestClient.post<any>(`${Api.GetLxcs}${id}/update_snapshot/`, data);
}

/**
 * 删除容器快照
 */
export async function deleteLxcSnapshotApi(id: number | string, data: any) {
  return requestClient.post<any>(`${Api.GetLxcs}${id}/delete_snapshot/`, data);
}

/**
 * 创建容器
 */
export async function createLxcApi(data: any) {
  return requestClient.post(Api.GetLxcs, data);
}

/**
 * 删除容器
 */
export async function deleteLxcApi(id: number | string, params?: any) {
  return requestClient.delete(`${Api.GetLxcs}${id}/`, { params });
}

export async function getPveListApi() {
  return requestClient.get<any[]>('/pve/servers/');
}

export async function getPveNodesApi(serverId: number) {
  return requestClient.get<any[]>(`/pve/servers/${serverId}/nodes/`);
}

export async function getPveStorageApi(serverId: number, node: string) {
  return requestClient.get<any[]>(`/pve/servers/${serverId}/nodes/${node}/storage/`);
}

export async function getPveStorageContentApi(
  serverId: number,
  node: string,
  storage: string,
  content?: string,
) {
  return requestClient.get<any[]>(
    `/pve/servers/${serverId}/nodes/${node}/storage/${storage}/content/`,
    { params: { content } },
  );
}

export async function getNextVmidApi(serverId: number) {
  return requestClient.get<any>(`/pve/servers/${serverId}/next-vmid/`);
}
