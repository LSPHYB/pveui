import type {
  CreateNetworkParams,
  CreateNodeParams,
  PVEServerModel,
  UpdateNetworkParams,
} from './types';

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
 * 创建网络设备（Linux Bridge / Bond / VLAN）
 *
 * 注意：PVE 只写入待应用配置，需要再调用 applyNodeNetworkApi 才会生效。
 */
export async function createNodeNetworkApi(
  serverId: number,
  node: string,
  data: CreateNetworkParams,
) {
  return requestClient.post(
    `/pve/servers/${serverId}/nodes/${node}/network/`,
    data,
  );
}

/**
 * 读取单个网络接口的配置
 */
export async function getNodeNetworkIfaceApi(
  serverId: number,
  node: string,
  iface: string,
) {
  return requestClient.get(
    `/pve/servers/${serverId}/nodes/${node}/network/${iface}/`,
  );
}

/**
 * 修改网络设备配置
 *
 * 注意：要清空某个已有设置，必须把字段名放进 data.delete，
 * 仅仅不传该字段 PVE 会保留原值。改动同样需要 applyNodeNetworkApi 才生效。
 */
export async function updateNodeNetworkApi(
  serverId: number,
  node: string,
  iface: string,
  data: UpdateNetworkParams,
) {
  return requestClient.put(
    `/pve/servers/${serverId}/nodes/${node}/network/${iface}/`,
    data,
  );
}

/**
 * 删除网络设备（需应用配置后生效）
 */
export async function deleteNodeNetworkApi(
  serverId: number,
  node: string,
  iface: string,
) {
  return requestClient.delete(
    `/pve/servers/${serverId}/nodes/${node}/network/${iface}/`,
  );
}

/**
 * 应用（重载）待生效的网络配置
 */
export async function applyNodeNetworkApi(serverId: number, node: string) {
  return requestClient.put(`/pve/servers/${serverId}/nodes/${node}/network/`);
}

/**
 * 回滚尚未应用的网络配置变更
 */
export async function revertNodeNetworkApi(serverId: number, node: string) {
  return requestClient.delete(`/pve/servers/${serverId}/nodes/${node}/network/`);
}

/**
 * 创建 PVE 节点 Shell 会话，返回一次性 WebSocket 代理地址
 *
 * 需要 PVE 用户名/密码：termproxy 不接受 API Token。凭据仅用于换取 ticket，
 * 后端不会存储，也不会回传给前端。
 */
export async function createNodeShellSessionApi(
  serverId: number,
  data: { node: string; password: string; username: string },
): Promise<{
  node: string;
  proxy_path: string;
  proxy_url: string;
  user: string;
}> {
  const res: any = await requestClient.post(
    `/pve/servers/${serverId}/shell-session/`,
    data,
  );
  // request.ts 注释掉了 defaultResponseInterceptor，RequestClient 会原样返回
  // 完整的 axios 响应，响应体在 .data 上。`?? res` 兼容将来重新启用解包拦截器。
  return res?.data ?? res;
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
