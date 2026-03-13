import type { RouteRecordRaw } from 'vue-router';

const routes: RouteRecordRaw[] = [
  {
    path: '/pve',
    name: 'PVE',
    component: () => import('#/layouts/basic.vue'),
    meta: {
      title: 'PVE资源',
      icon: 'lucide:server',
      order: 10,
    },
    children: [
      {
        path: 'vm',
        name: 'PVE_VM',
        component: () => import('#/views/pve/vm/index.vue'),
        meta: {
          title: '虚拟机',
          icon: 'lucide:monitor',
        },
      },
      {
        path: 'lxc',
        name: 'PVE_LXC',
        component: () => import('#/views/pve/lxc/index.vue'),
        meta: {
          title: '容器',
          icon: 'lucide:box',
        },
      },
      {
        path: 'server',
        name: 'PVE_Server',
        component: () => import('#/views/pve/server/index.vue'),
        meta: {
          title: '节点',
          icon: 'lucide:hard-drive',
        },
      },
      {
        path: 'storage',
        name: 'PVE_Storage',
        component: () => import('#/views/pve/storage/index.vue'),
        meta: {
          title: '存储',
          icon: 'lucide:database',
        },
      },
      {
        path: 'network',
        name: 'PVE_Network',
        component: () => import('#/views/pve/network/index.vue'),
        meta: {
          title: '网络',
          icon: 'lucide:network',
        },
      },
      {
        path: 'tasks',
        name: 'PVE_Tasks',
        component: () => import('#/views/pve/tasks/index.vue'),
        meta: {
          title: '任务日志',
          icon: 'lucide:file-clock',
        },
      },
      {
        path: 'topology',
        name: 'PVE_Topology',
        component: () => import('#/views/pve/topology/index.vue'),
        meta: {
          title: '网络拓扑',
          icon: 'lucide:share-2',
        },
      },
      {
        path: 'templates',
        name: 'PVE_Templates',
        component: () => import('#/views/pve/templates/index.vue'),
        meta: {
          title: '模板管理',
          icon: 'lucide:file-box',
        },
      },
    ],
  },
];

export default routes;
