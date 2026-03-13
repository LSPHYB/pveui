import type { MenuTreeResult } from './types';

import { requestClient } from '#/api/request';

export * from './types';

/**
 * 获取菜单树
 * @param params - 可选参数，例如 { include_hidden: true } 以包含隐藏菜单
 */
export async function getMenuTreeApi(params?: { include_hidden?: boolean }) {
  return requestClient.get<MenuTreeResult>('/rbac/menu-tree/', { params });
}

/**
 * 获取菜单列表
 */
export async function getMenuList(params?: any) {
  return requestClient.get('/rbac/menus/', { params });
}

/**
 * 创建菜单
 */
export async function createMenu(data: any) {
  return requestClient.post('/rbac/menus/', data);
}

/**
 * 更新菜单
 */
export async function updateMenu(id: number, data: any) {
  return requestClient.put(`/rbac/menus/${id}/`, data);
}

/**
 * 删除菜单
 */
export async function deleteMenu(id: number) {
  return requestClient.delete(`/rbac/menus/${id}/`);
}

/**
 * 获取菜单详情
 */
export async function getMenuDetail(id: number) {
  return requestClient.get(`/rbac/menus/${id}/`);
}
