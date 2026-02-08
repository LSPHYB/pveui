import type { RouteRecordStringComponent } from '@vben/types';

import { requestClient } from '#/api/request';

/**
 * Django菜单格式: {id, title, path, icon, component, parent, order, hidden, children}
 * Vben格式: {name, path, component, meta: {title, icon, order}, children}
 */
/**
 * Transform legacy icon names to Iconify format
 */
function getIcon(icon?: string) {
  if (!icon) return 'lucide:layout-dashboard';

  // If it's already in Iconify format (has colon)
  if (icon.includes(':')) return icon;

  // Handle legacy icon names
  const name = icon.replace(/^icon-/, '');

  // Specific mappings for common icons
  const mapping: Record<string, string> = {
    dashboard: 'lucide:layout-dashboard',
    apps: 'lucide:layout-grid',
    settings: 'lucide:settings',
    monitor: 'lucide:activity', // or lucide:monitor
    user: 'lucide:user',
    users: 'lucide:users',
    system: 'lucide:settings-2',
    menu: 'lucide:menu',
    role: 'lucide:shield',
    log: 'lucide:file-text',
    server: 'lucide:server',
    storage: 'lucide:hard-drive',
  };

  if (mapping[name]) {
    return mapping[name];
  }

  // Fallback for others: try ant-design as it matches the old naming often
  return `ant-design:${name}-outlined`;
}

function transformDjangoMenuToVben(
  djangoMenus: any[],
  parentHidden: boolean = false,
): RouteRecordStringComponent[] {
  console.log(
    '[Menu Transform] 🔄 开始转换菜单，数量:',
    djangoMenus?.length || 0,
    '| 父级隐藏:',
    parentHidden,
  );

  if (!djangoMenus || !Array.isArray(djangoMenus) || djangoMenus.length === 0) {
    console.warn('[Menu Transform] ⚠️ Django菜单为空或格式错误！');
    return [];
  }

  // 过滤掉无效的菜单项（缺少必要字段）
  const validMenus = djangoMenus.filter((menu) => {
    // ... filtering logic ...
    const hasTitle = menu && menu.title;
    const hasPath = menu && menu.path;

    if (!hasTitle || !hasPath) {
      // ... warning ...
      return false;
    }

    // 如果不是父级菜单（没有子菜单），必须有component
    const hasChildren =
      menu.children && Array.isArray(menu.children) && menu.children.length > 0;
    if (!hasChildren && !menu.component) {
      // ... warning ...
      return false;
    }
    return true;
  });

  console.log(
    `\n[Menu Transform] 📊 有效菜单数量: ${validMenus.length}/${djangoMenus.length}`,
  );

  return validMenus.map((menu, index) => {
    console.log(`\n[Menu Transform] 🔧 转换菜单 [${index}]: "${menu.title}"`);

    // 判断当前菜单是否应该被隐藏（自身隐藏 或 父级隐藏）
    const isHidden = parentHidden || menu.hidden || menu.is_hidden;

    console.log(`[Menu Transform]   原始数据:`, {
      path: menu.path,
      component: menu.component,
      parent: menu.parent,
      order: menu.order,
      icon: menu.icon,
      hidden: menu.hidden || menu.is_hidden,
      parentHidden,
      finalHidden: isHidden,
    });

    // 生成唯一的name，确保符合路由命名规范
    const routeName =
      menu.path?.replaceAll('/', '_').replace(/^_/, '').replaceAll('-', '_') || // 替换连字符为下划线
      `Menu_${menu.id}`;

    // 确定component值
    let componentValue = menu.component || 'BasicLayout';

    // 处理子菜单的情况
    const hasChildren =
      menu.children && Array.isArray(menu.children) && menu.children.length > 0;
    if (hasChildren && (!menu.component || menu.component === '')) {
      componentValue = 'BasicLayout';
    }

    const vbenMenu: RouteRecordStringComponent = {
      name: routeName,
      path: menu.path,
      component: componentValue,
      meta: {
        title: menu.title,
        icon: getIcon(menu.icon),
        order: Number(menu.order) || 0,
      },
    };

    // 处理隐藏菜单（包括继承父级的隐藏状态）
    if (isHidden) {
      if (vbenMenu.meta) {
        vbenMenu.meta.hideInMenu = true;
      }
      console.log(
        `[Menu Transform]   ⚠️ 菜单 "${menu.title}" 被隐藏 (自身: ${menu.hidden || menu.is_hidden}, 父级: ${parentHidden})`,
      );
    }

    // 处理子菜单 - 传递当前菜单的隐藏状态给子菜单
    if (hasChildren) {
      // 重点：如果当前菜单被隐藏，子菜单也应该被隐藏
      const transformedChildren = transformDjangoMenuToVben(
        menu.children,
        isHidden,
      );
      if (transformedChildren.length > 0) {
        vbenMenu.children = transformedChildren;

        // 如果有子菜单但没有component，设置为BasicLayout并重定向到第一个子菜单
        if (!menu.component || menu.component === 'BasicLayout') {
          vbenMenu.component = 'BasicLayout';
          if (vbenMenu.children[0]?.path) {
            vbenMenu.redirect = vbenMenu.children[0].path;
          }
        }
      }
    }

    // 处理component路径
    if (
      vbenMenu.component &&
      vbenMenu.component !== 'BasicLayout' &&
      vbenMenu.component !== 'IFrameView'
    ) {
      // 清理component路径
      vbenMenu.component = vbenMenu.component
        .replace(/^view\//, '')
        .replace(/^views\//, '')
        .trim();

      // 移除开头的斜杠（先清理可能的多余斜杠）
      vbenMenu.component = vbenMenu.component.replace(/^\/+/, '');

      // 确保以/开头 (Vben 静态菜单使用了 / 开头，说明这里需要绝对路径)
      vbenMenu.component = `/${vbenMenu.component}`;

      // 移除尾部的斜杠
      vbenMenu.component = vbenMenu.component.replace(/\/+$/, '');
    }

    return vbenMenu;
  });
}

/**
 * 获取用户所有菜单 - 适配Django
 */
export async function getAllMenusApi() {
  console.log('[Menu API] 🔄 开始获取Django菜单...');
  let djangoMenus: any[] = [];

  try {
    // Backend exposes /api/rbac/menu-tree/
    // 注意: requestClient 返回完整的 Axios 响应对象(因为默认拦截器被注释掉了)
    const response: any = await requestClient.get('/rbac/menu-tree/');

    console.log('[Menu API] 📦 原始响应:', response);
    console.log('[Menu API] 📦 响应类型:', typeof response);
    console.log('[Menu API] 📦 是否有data属性:', 'data' in response);

    // 提取实际的菜单数组
    if (Array.isArray(response)) {
      // 如果直接是数组（某些配置下可能）
      djangoMenus = response;
    } else if (response && Array.isArray(response.data)) {
      // Axios响应对象格式: { data: [...], status: 200, ... }
      djangoMenus = response.data;
    } else if (response && response.data) {
      // 可能是其他包装格式
      console.warn(
        '[Menu API] ⚠️ 意外的响应格式，尝试使用 response.data:',
        response.data,
      );
      djangoMenus = Array.isArray(response.data) ? response.data : [];
    } else {
      console.warn('[Menu API] ⚠️ 无法识别的响应格式:', response);
      djangoMenus = [];
    }

    console.log('[Menu API] ✅ 提取到的菜单数组:', djangoMenus);
    console.log('[Menu API] 📊 菜单数量:', djangoMenus.length);
  } catch (error) {
    console.error(
      '[Menu API] ❌ 获取Django菜单失败 (将使用静态兜底菜单):',
      error,
    );
    djangoMenus = [];
  }

  // 转换Django菜单格式为Vben格式
  console.log('[Menu API] 🔧 开始转换菜单格式...');
  const vbenMenus = transformDjangoMenuToVben(djangoMenus);
  console.log('[Menu API] ✅ 转换后的Vben菜单:', vbenMenus);
  console.log('[Menu API] 📊 转换后菜单数量:', vbenMenus.length);

  // ----------------------------------------------------------------
  // 静态菜单兜底：仅当后端菜单为空时才注入
  // ----------------------------------------------------------------
  if (vbenMenus.length === 0) {
    console.warn('[Menu API] ⚠️ 后端菜单为空，使用静态兜底菜单');

    const staticMenus: RouteRecordStringComponent[] = [
      {
        name: 'Dashboard',
        path: '/dashboard',
        component: 'BasicLayout',
        meta: {
          title: '仪表盘',
          icon: 'lucide:layout-dashboard',
          order: 0,
        },
        children: [
          {
            name: 'Analytics',
            path: '/analytics',
            component: 'dashboard/analytics/index',
            meta: {
              title: '分析页',
              icon: 'lucide:area-chart',
              affixTab: true,
            },
          },
        ],
      },
      {
        name: 'PVE',
        path: '/pve',
        component: 'BasicLayout',
        meta: {
          title: 'PVE资源',
          icon: 'lucide:server',
          order: 10,
        },
        children: [
          {
            name: 'PVE_VM',
            path: '/pve/vm',
            component: 'pve/vm/index',
            meta: {
              title: '虚拟机',
              icon: 'lucide:monitor',
            },
          },
          {
            name: 'PVE_LXC',
            path: '/pve/lxc',
            component: 'pve/lxc/index',
            meta: {
              title: '容器',
              icon: 'lucide:box',
            },
          },
        ],
      },
      {
        name: 'System',
        path: '/system',
        component: 'BasicLayout',
        meta: {
          title: '系统管理',
          icon: 'lucide:settings',
          order: 20,
        },
        children: [
          {
            name: 'System_User',
            path: '/system/user',
            component: 'system/user/index',
            meta: {
              title: '用户管理',
              icon: 'lucide:users',
            },
          },
          {
            name: 'System_Menu',
            path: '/system/menu',
            component: 'system/menu/index',
            meta: {
              title: '菜单管理',
              icon: 'lucide:menu',
            },
          },
        ],
      },
    ];

    console.log('[Menu API] 💉 使用静态菜单:', staticMenus.length, '个');
    return staticMenus;
  }

  console.log('[Menu API] ✅ 返回后端菜单:', vbenMenus.length, '个');
  return vbenMenus;
}
