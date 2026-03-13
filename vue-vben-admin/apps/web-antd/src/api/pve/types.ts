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
