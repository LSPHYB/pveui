import type { RouteRecordRaw } from 'vue-router';

const routes: RouteRecordRaw[] = [
  {
    path: '/system',
    name: 'System',
    component: () => import('#/layouts/basic.vue'),
    meta: {
      title: '系统管理',
      icon: 'lucide:settings',
      order: 20,
    },
    children: [
      {
        path: 'user',
        name: 'System_User',
        component: () => import('#/views/system/user/index.vue'),
        meta: {
          title: '用户管理',
          icon: 'lucide:users',
        },
      },
      {
        path: 'role',
        name: 'System_Role',
        component: () => import('#/views/system/role/index.vue'),
        meta: {
          title: '角色管理',
          icon: 'lucide:shield',
        },
      },
      {
        path: 'menu',
        name: 'System_Menu',
        component: () => import('#/views/system/menu/index.vue'),
        meta: {
          title: '菜单管理',
          icon: 'lucide:menu',
        },
      },
    ],
  },
];

export default routes;
