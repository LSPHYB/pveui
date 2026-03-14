import type {
  NetworkTopologyModel,
  NetworkTopologySaveParams,
} from './types';

import { requestClient } from '#/api/request';

const BASE = '/pve/network-topologies/';

export function getTopologyListApi(params?: {
  is_active?: boolean;
  search?: string;
  ordering?: string;
}) {
  return requestClient.get<NetworkTopologyModel[]>(BASE, { params });
}

export function getTopologyDetailApi(id: number | string) {
  return requestClient.get<NetworkTopologyModel>(`${BASE}${id}/`);
}

export function createTopologyApi(data: NetworkTopologySaveParams) {
  return requestClient.post<NetworkTopologyModel>(BASE, data);
}

export function updateTopologyApi(
  id: number | string,
  data: Partial<NetworkTopologySaveParams>,
) {
  return requestClient.put<NetworkTopologyModel>(`${BASE}${id}/`, data);
}

export function deleteTopologyApi(id: number | string) {
  return requestClient.delete(`${BASE}${id}/`);
}
