import type { LxcContainerModel, VirtualMachineModel } from './types';

import { requestClient } from '#/api/request';

enum Api {
  GetLxcs = '/pve/lxc-containers/',
  GetVms = '/pve/virtual-machines/',
}

/**
 * 获取所有虚拟机列表 (DB)
 */
export async function getVmListApi() {
  return requestClient.get<VirtualMachineModel[]>(Api.GetVms);
}

/**
 * 获取单个虚拟机详情 (DB)
 */
export async function getVmByIdApi(id: number | string) {
  return requestClient.get<VirtualMachineModel>(`/pve/virtual-machines/${id}/`);
}

/**
 * 获取所有容器列表 (DB)
 */
export async function getLxcListApi() {
  return requestClient.get<LxcContainerModel[]>(Api.GetLxcs);
}

/**
 * 获取虚拟机详情 (PVE direct)
 */
export async function getVmDetailApi(
  node: string,
  vmid: number,
  type: 'lxc' | 'qemu' = 'qemu',
) {
  // This might need valid server context, usually fetched via backend proxy
  // Currently assuming direct node access is not main path, but if needed:
  // We need to know which server it is on.
  // For now, let's leave it as is if it relies on a different proxy path,
  // OR if we should use the DB detail:
  // return requestClient.get<VirtualMachineModel>(`/pve/virtual-machines/${id}/`);
  return requestClient.get<any>(
    `/pve/nodes/${node}/${type}/${vmid}/status/current`,
  );
}

/**
 * 虚拟机电源操作
 * @param id Database ID of the VM
 * @param action start, stop, shutdown, reboot, suspend, resume, reset, hibernate
 */
export async function operateVmApi(id: number | string, action: string) {
  return requestClient.post(`/pve/virtual-machines/${id}/vm_action/`, {
    action,
  });
}

/**
 * 创建/克隆虚拟机
 */
export async function createVmApi(data: any) {
  return requestClient.post(`${Api.GetVms}create_vm/`, data);
}

/**
 * 获取虚拟机配置
 */
export async function getVmConfigApi(
  node: string,
  vmid: number,
  type: 'lxc' | 'qemu' = 'qemu',
) {
  return requestClient.get(`/pve/nodes/${node}/${type}/${vmid}/config/`);
}

/**
 * 获取虚拟机配置 (DB ID)
 */
export async function getVmConfigByIdApi(id: number | string) {
  return requestClient.get<any>(`/pve/virtual-machines/${id}/options/`);
}

/**
 * 更新虚拟机配置 (DB ID)
 */
export async function updateVmConfigApi(id: number | string, params: any) {
  return requestClient.post(`/pve/virtual-machines/${id}/options/`, params);
}

/**
 * 获取VNC连接信息
 */
export async function getVncProxyApi(
  node: string,
  vmid: number,
  type: 'lxc' | 'qemu' = 'qemu',
) {
  return requestClient.post(`/pve/nodes/${node}/${type}/${vmid}/vncproxy/`);
}

/**
 * 创建Console会话
 */
export async function createConsoleSessionApi(
  id: number | string,
  type: 'novnc' | 'spice' | 'xterm' = 'novnc',
) {
  return requestClient.post(`/pve/virtual-machines/${id}/console-session/`, {
    type,
  });
}

export async function deleteVmApi(
  id: number | string,
  params?: { purge?: boolean },
) {
  return requestClient.delete(`/pve/virtual-machines/${id}/`, { params });
}

/**
 * 同步所有虚拟机
 */
export async function syncAllVmsApi(serverId?: number) {
  return requestClient.post(`${Api.GetVms}sync_all/`, { server_id: serverId });
}

/**
 * 获取虚拟机实时状态 (DB ID -> Proxy)
 */
export async function getVmStatusByIdApi(id: number | string) {
  return requestClient.get<any>(`/pve/virtual-machines/${id}/status/current/`);
}

/**
 * 获取虚拟机RRD数据 (DB ID -> Proxy)
 * timeframe: hour, day, week, month, year
 */
export async function getVmRrdByIdApi(id: number | string, timeframe = 'hour') {
  return requestClient.get<any>(`/pve/virtual-machines/${id}/rrddata/`, {
    params: { timeframe },
  });
}

/**
 * 获取虚拟机备份列表
 */
export async function getVmBackupsApi(id: number | string) {
  return requestClient.get<any>(`/pve/virtual-machines/${id}/backups/`);
}

/**
 * 创建虚拟机备份
 */
export async function createVmBackupApi(id: number | string, data: any) {
  return requestClient.post<any>(
    `/pve/virtual-machines/${id}/create_backup/`,
    data,
  );
}

/**
 * 还原虚拟机备份
 */
export async function restoreVmBackupApi(id: number | string, data: any) {
  return requestClient.post<any>(
    `/pve/virtual-machines/${id}/restore_backup/`,
    data,
  );
}

/**
 * 删除备份
 */
export async function deleteVmBackupApi(id: number | string, data: any) {
  return requestClient.post<any>(
    `/pve/virtual-machines/${id}/delete_backup/`,
    data,
  );
}

/**
 * 更新备份备注
 */
export async function updateBackupNotesApi(id: number | string, data: any) {
  return requestClient.post<any>(
    `/pve/virtual-machines/${id}/update_backup_notes/`,
    data,
  );
}

/**
 * 更新备份保护状态
 */
export async function updateBackupProtectionApi(
  id: number | string,
  data: any,
) {
  return requestClient.post<any>(
    `/pve/virtual-machines/${id}/update_backup_protection/`,
    data,
  );
}

/**
 * 获取虚拟机快照列表
 */
export async function getVmSnapshotsApi(id: number | string) {
  return requestClient.get<any>(`/pve/virtual-machines/${id}/snapshots/`);
}

/**
 * 创建虚拟机快照
 */
export async function createVmSnapshotApi(id: number | string, data: any) {
  return requestClient.post<any>(
    `/pve/virtual-machines/${id}/create_snapshot/`,
    data,
  );
}

/**
 * 回滚到快照
 */
export async function rollbackSnapshotApi(id: number | string, data: any) {
  return requestClient.post<any>(
    `/pve/virtual-machines/${id}/rollback_snapshot/`,
    data,
  );
}

/**
 * 更新快照描述
 */
export async function updateSnapshotApi(id: number | string, data: any) {
  return requestClient.post<any>(
    `/pve/virtual-machines/${id}/update_snapshot/`,
    data,
  );
}

/**
 * 删除快照
 */
export async function deleteSnapshotApi(id: number | string, data: any) {
  return requestClient.post<any>(
    `/pve/virtual-machines/${id}/delete_snapshot/`,
    data,
  );
}
