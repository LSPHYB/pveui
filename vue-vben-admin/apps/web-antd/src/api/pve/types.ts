export interface PveStatus {
  id: string;
  node: string;
  type: string;
  status: 'offline' | 'online' | 'paused' | 'running' | 'stopped';
  uptime?: number;
}

export interface PveNode extends PveStatus {
  cpu: number;
  maxcpu: number;
  mem: number;
  maxmem: number;
  disk?: number;
  maxdisk?: number;
  level?: string;
  version?: string;
  ssl_fingerprint?: string;
}

export interface PveVm extends PveStatus {
  vmid: number;
  name: string;
  cpus?: number;
  maxcpu?: number;
  maxmem?: number;
  netin?: number;
  netout?: number;
  diskread?: number;
  diskwrite?: number;
  template?: number; // 0 or 1
  pid?: number;
  tags?: string;
  lock?: string;
}

export interface PveLxc extends PveVm {
  // LXC specific fields if any
}

export interface PveStorage extends PveStatus {
  storage: string;
  content: string;
  active: number;
  avail: number;
  total: number;
  used: number;
  shared: number;
  enabled: number;
}

export interface VmActionParams {
  node: string;
  vmid: number;
  param?: string; // Additional params
}

export interface VmConfig {
  [key: string]: any;
}

export interface PVEServerModel {
  id: number;
  name: string;
  host: string;
  port: number;
  token_id: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  remark?: string;
}

export interface VirtualMachineModel {
  id: number;
  server: number;
  server_name: string;
  vmid: number;
  name: string;
  node: string;
  status: string;
  cpu_cores: number;
  memory_mb: number;
  disk_gb: number;
  ip_address: string;
  created_at: string;
  updated_at: string;
  description?: string;
}

export interface CreateNodeParams {
  name: string;
  host: string;
  port: number;
  token_id: string;
  token_secret: string;
  verify_ssl?: boolean;
  remark?: string;
  is_active?: boolean;
}

export interface UpdateNodeParams extends Partial<CreateNodeParams> {
  id: number | string;
}



export interface LxcContainerModel extends VirtualMachineModel {
  // same fields for now
}

export interface NetworkTopologyModel {
  id: number;
  name: string;
  description: string;
  is_active: boolean;
  diagram_data: any;
  metadata: any;
  created_at: string;
  updated_at: string;
  remark?: string;
}

export interface NetworkTopologySaveParams {
  name: string;
  description?: string;
  is_active?: boolean;
  diagram_data?: any;
  metadata?: any;
  remark?: string;
}

export interface PveNetworkInterface {
  iface: string;
  type: string;
  active: number; // 1 or 0
  autostart: number; // 1 or 0
  bridge_ports?: string;
  address?: string;
  cidr?: string;
  gateway?: string;
  comments?: string;
  [key: string]: any;
}

/** 当前支持新增的网络设备类型 */
export type PveNetworkType = 'bond' | 'bridge' | 'vlan';

export type PveBondMode =
  | '802.3ad'
  | 'active-backup'
  | 'balance-alb'
  | 'balance-rr'
  | 'balance-tlb'
  | 'balance-xor'
  | 'broadcast';

export type PveBondHashPolicy = 'layer2' | 'layer2+3' | 'layer3+4';

/**
 * 创建网络设备的参数，字段名与 PVE API 保持一致
 * （POST /nodes/{node}/network）
 */
export interface CreateNetworkParams {
  iface: string;
  type: PveNetworkType;

  // 通用
  autostart?: boolean;
  cidr?: string;
  cidr6?: string;
  comments?: string;
  gateway?: string;
  gateway6?: string;
  mtu?: number | undefined;

  // bridge
  bridge_ports?: string;
  bridge_vids?: string;
  bridge_vlan_aware?: boolean;

  // bond
  'bond-primary'?: string;
  bond_mode?: PveBondMode;
  bond_xmit_hash_policy?: PveBondHashPolicy;
  slaves?: string;

  // vlan
  'vlan-id'?: number | undefined;
  'vlan-raw-device'?: string;
}

/**
 * 修改网络设备的参数（PUT /nodes/{node}/network/{iface}）
 *
 * iface 由 URL 决定、不可改名；type 不可变更，但 PVE 要求必传。
 * `delete` 是待清除的字段名列表 —— PVE 不会因为字段缺省就清空原值，
 * 必须显式声明要删哪些设置。
 */
export interface UpdateNetworkParams extends Omit<CreateNetworkParams, 'iface'> {
  delete?: string[];
}
