import { requestClient } from '#/api/request';

export interface SystemSetting {
  id: number;
  key: string;
  value: string;
  description: string;
  category: string;
  is_encrypted: boolean;
  is_public: boolean;
  remark?: string;
  [key: string]: any;
}

export function getSystemSettingsApi(params?: any) {
  return requestClient.get('/system/settings/', { params });
}

export function getSystemSettingApi(id: number) {
  return requestClient.get(`/system/settings/${id}/`);
}

export function createSystemSettingApi(data: any) {
  return requestClient.post('/system/settings/', data);
}

export function updateSystemSettingApi(id: number, data: any) {
  return requestClient.patch(`/system/settings/${id}/`, data);
}

export function deleteSystemSettingApi(id: number) {
  return requestClient.delete(`/system/settings/${id}/`);
}

export function bulkUpdateSystemSettingsApi(data: any) {
  return requestClient.post('/system/settings/bulk_update/', data);
}
