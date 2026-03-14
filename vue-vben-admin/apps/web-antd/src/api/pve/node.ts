import type { CreateNodeParams, PVEServerModel } from './types';

import { requestClient } from '#/api/request';

enum Api {
  GetServers = '/pve/servers/',
}

/**
 * 获取PVE服务器列表
 */
export async function getNodeListApi(params?: any) {
  return requestClient.get<PVEServerModel[]>(Api.GetServers, { params });
}

/**
 * 创建PVE服务器
 */
export async function createNodeApi(data: CreateNodeParams) {
  return requestClient.post<PVEServerModel>(Api.GetServers, data);
}

/**
 * 更新PVE服务器
 */
export async function updateNodeApi(
  id: number | string,
  data: Partial<CreateNodeParams>,
) {
  return requestClient.put<PVEServerModel>(`${Api.GetServers}${id}/`, data);
}

/**
 * 删除PVE服务器
 */
export async function deleteNodeApi(id: number | string) {
  return requestClient.delete(`${Api.GetServers}${id}/`);
}

/**
 * 测试PVE服务器连接
 */
export async function testNodeConnectionApi(id: number | string) {
  return requestClient.post(`${Api.GetServers}${id}/test_connection/`);
}

/**
 * 获取PVE服务器节点列表
 */
export async function getPveNodesApi(serverId: number) {
  return requestClient.get(`/pve/servers/${serverId}/nodes/`);
}

/**
 * 获取节点监控数据
 */
export async function getNodeMonitorApi(
  serverId: number,
  node: string,
  params: any,
) {
  return requestClient.get(`/pve/servers/${serverId}/nodes/${node}/monitor/`, {
    params,
  });
}

/**
 * 获取节点网络接口列表
 */
export async function getNodeNetworkApi(serverId: number, node: string) {
  return requestClient.get(`/pve/servers/${serverId}/nodes/${node}/network/`);
}

/**
 * 获取节点存储列表
 */
export async function getServerNodeStoragesApi(serverId: number, node: string) {
  return requestClient.get(`/pve/servers/${serverId}/nodes/${node}/storage/`);
}

/**
 * 获取存储内容列表 (ISO等)
 */
export async function getIsoListApi(
  serverId: number,
  node: string,
  storage: string,
  params?: any,
) {
  return requestClient.get(
    `/pve/servers/${serverId}/nodes/${node}/storage/${storage}/content/`,
    {
      params: { content: 'iso', ...params },
    },
  );
}

/**
 * 获取节点QEMU(VM)列表
 */
export async function getNodeQemuApi(serverId: number, node: string) {
  return requestClient.get(`/pve/servers/${serverId}/nodes/${node}/vms/`);
}

/**
 * 获取节点LXC列表
 */
export async function getNodeLxcApi(serverId: number, node: string) {
  return requestClient.get(`/pve/servers/${serverId}/nodes/${node}/lxc/`);
}

/**
 * 获取资源配置
 */
export async function getNodeResourceConfigApi(
  serverId: number,
  node: string,
  type: 'lxc' | 'qemu',
  vmid: number | string,
) {
  return requestClient.get(
    `/pve/servers/${serverId}/nodes/${node}/${type}/${vmid}/config/`,
  );
}

/**
 * 通过 QEMU Guest Agent 获取 VM 网络接口（含 IP）
 * 需要 VM 运行中且已安装 qemu-guest-agent
 */
export async function getVmAgentNetworkApi(
  serverId: number,
  node: string,
  vmid: number | string,
) {
  return requestClient.get(
    `/pve/servers/${serverId}/nodes/${node}/qemu/${vmid}/agent/network-get-interfaces/`,
  );
}

/**
 * 获取下一个可用的VMID
 */
export async function getNextVmidApi(serverId: number) {
  return requestClient.get<{ vmid: number }>(
    `/pve/servers/${serverId}/next-vmid/`,
  );
}
