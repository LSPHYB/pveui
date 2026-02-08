/**
 * Django菜单格式到Vben路由格式的转换工具
 */
import type { RouteRecordRaw } from 'vue-router';

import type { MenuItem } from '#/api/menu/types';

/**
 * 将Django菜单树转换为Vben路由配置
 * Django格式: {id, title, path, icon, component, parent, order, hidden, children}
 * Vben格式: RouteRecordRaw
 */
export function transformMenuToRoutes(menuTree: MenuItem[]): RouteRecordRaw[] {
  const routes: RouteRecordRaw[] = [];

  function processMenuItem(
    menu: MenuItem,
    parentPath = '',
  ): null | RouteRecordRaw {
    // 构建完整路径
    let fullPath = menu.path;
    if (!fullPath.startsWith('/')) {
      fullPath = parentPath ? `${parentPath}/${fullPath}` : `/${fullPath}`;
    }

    // 基础路由配置
    const route: RouteRecordRaw = {
      path: fullPath,
      name:
        menu.path.replaceAll('/', '_').replace(/^_/, '') || `menu_${menu.id}`,
      meta: {
        title: menu.title,
        icon: menu.icon || 'lucide:layout-dashboard',
        hideInMenu: menu.hidden || false,
        order: menu.order || 0,
      },
    };

    // 处理组件
    if (menu.component) {
      // Django返回的component格式: "view/pve/vm/index" 或 "pve/vm/index"
      const componentPath = menu.component
        .replace(/^view\//, '')
        .replace(/^views\//, '');

      route.component = () => import(`#/views/${componentPath}.vue`);
    }

    // 处理子菜单
    if (menu.children && menu.children.length > 0) {
      route.children = menu.children
        .map((child) => processMenuItem(child, fullPath))
        .filter((r): r is RouteRecordRaw => r !== null);

      // 如果有子菜单但没有component,重定向到第一个子菜单
      if (!menu.component && route.children.length > 0) {
        const firstChild = route.children[0];
        route.redirect = firstChild.path;
      }
    }

    return route;
  }

  menuTree.forEach((menu) => {
    const route = processMenuItem(menu);
    if (route) {
      routes.push(route);
    }
  });

  return routes;
}

/**
 * 为空白页面创建默认组件路径
 */
export function getPlaceholderComponent() {
  return () => import('#/views/_core/fallback/not-found.vue');
}
