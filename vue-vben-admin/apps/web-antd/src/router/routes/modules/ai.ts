import type { RouteRecordRaw } from 'vue-router';

// 路由骨架：左侧菜单由后端数据库菜单树控制。
// 此文件只负责提供 path→component 的懒加载映射，
// 子路由 path 必须与数据库 rbac_menu 的 path 字段一一对应。
const routes: RouteRecordRaw[] = [
  {
    path: '/ai',
    name: 'AI',
    component: () => import('#/layouts/basic.vue'),
    meta: {
      title: 'AI管理中心',
      icon: 'lucide:bot',
      order: 30,
    },
    children: [
      {
        path: 'dashboard',
        name: 'AI_Dashboard',
        component: () => import('#/views/ai/dashboard/index.vue'),
        meta: {
          title: '数据大盘',
          icon: 'lucide:area-chart',
        },
      },
      {
        path: 'models',
        name: 'AI_Models',
        component: () => import('#/views/ai/models/index.vue'),
        meta: {
          title: '模型管理',
          icon: 'lucide:cpu',
        },
      },
      {
        path: 'api-keys',
        name: 'AI_ApiKeys',
        component: () => import('#/views/ai/api-keys/index.vue'),
        meta: {
          title: 'API密钥',
          icon: 'lucide:key',
        },
      },
      {
        path: 'quotas',
        name: 'AI_Quotas',
        component: () => import('#/views/ai/quotas/index.vue'),
        meta: {
          title: '额度分配',
          icon: 'lucide:gauge',
        },
      },
      {
        path: 'agents',
        name: 'AI_Agents',
        component: () => import('#/views/ai/agents/index.vue'),
        meta: {
          title: '智能体人设',
          icon: 'lucide:brain',
        },
      },
      {
        path: 'knowledge',
        name: 'AI_Knowledge',
        component: () => import('#/views/ai/knowledge/index.vue'),
        meta: {
          title: '知识库状态',
          icon: 'lucide:library',
        },
      },
    ],
  },
];

export default routes;
