import { requestClient } from '#/api/request';

export interface TaskItem {
  jobId: string;
  jobName: string;
  invokeTarget: string;
  cronExpression: string;
  jobParams: any[];
  status: number; // 1: enabled, 0: disabled
  nextValidTime?: string;
  [key: string]: any;
}

export function listTasksApi(params?: any) {
  return requestClient.get('/tasks/tasks/', { params });
}

export function createTaskApi(data: any) {
  return requestClient.post('/tasks/tasks/', data);
}

export function updateTaskApi(id: number | string, data: any) {
  return requestClient.put(`/tasks/tasks/${id}/`, data);
}

export function deleteTaskApi(id: number | string) {
  return requestClient.delete(`/tasks/tasks/${id}/`);
}

export function runTaskNowApi(id: number | string) {
  return requestClient.post(`/tasks/tasks/${id}/run_now/`);
}
