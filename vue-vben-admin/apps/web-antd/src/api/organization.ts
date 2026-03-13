import { requestClient } from '#/api/request';

export interface Organization {
  id: number;
  name: string;
  code?: string;
  parent?: null | number;
  children?: Organization[];
  description?: string;
  is_active?: boolean;
}

export interface OrganizationListParams {
  page?: number;
  page_size?: number;
  search?: string;
}

export interface OrganizationListResult {
  count: number;
  next?: null | string;
  previous?: null | string;
  results: Organization[];
}

/**
 * 获取组织列表
 */
export async function getOrganizationList(params?: OrganizationListParams) {
  return requestClient.get<OrganizationListResult>('/rbac/organizations/', {
    params,
  });
}

/**
 * 获取组织详情
 */
export async function getOrganizationDetail(id: number) {
  return requestClient.get<Organization>(`/rbac/organizations/${id}/`);
}

/**
 * 获取组织树
 */
export async function getOrganizationTree(params?: { only_active?: boolean }) {
  return requestClient.get<Organization[]>('/rbac/organizations/tree/', {
    params,
  });
}

export async function createOrganization(data: any) {
  return requestClient.post('/rbac/organizations/', data);
}

export async function updateOrganization(id: number, data: any) {
  return requestClient.put(`/rbac/organizations/${id}/`, data);
}

export async function deleteOrganization(id: number) {
  return requestClient.delete(`/rbac/organizations/${id}/`);
}
