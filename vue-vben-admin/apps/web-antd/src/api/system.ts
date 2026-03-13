import { requestClient } from '#/api/request';

export interface DashboardData {
  stats: {
    menus: number;
    operation_logs: number;
    roles: number;
    users: number;
  };
  recent_logs: any[];
  daily_stats: { count: number; date: string }[];
  recent_users: any[];
  system_status: {
    cpu_percent: number;
    memory_percent: number;
    memory_total_gb: number;
    memory_used_gb: number;
  };
  error_count: number;
  top_paths: { count: number; path: string }[];
}

/**
 * 获取仪表盘数据
 */
export async function getDashboardDataApi() {
  return requestClient.get<DashboardData>('/rbac/dashboard/');
}

export async function getSystemMetricsApi() {
  return requestClient.get('/rbac/system/metrics/');
}
