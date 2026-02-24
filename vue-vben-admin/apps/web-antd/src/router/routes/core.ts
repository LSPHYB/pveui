import type { RouteRecordRaw } from 'vue-router';

import { LOGIN_PATH } from '@vben/constants';
import { preferences } from '@vben/preferences';

import { $t } from '#/locales';

const BasicLayout = () => import('#/layouts/basic.vue');
const AuthPageLayout = () => import('#/layouts/auth.vue');
/** 全局404页面 */
const fallbackNotFoundRoute: RouteRecordRaw = {
  component: () => import('#/views/_core/fallback/not-found.vue'),
  meta: {
    hideInBreadcrumb: true,
    hideInMenu: true,
    hideInTab: true,
    title: '404',
  },
  name: 'FallbackNotFound',
  path: '/:path(.*)*',
};

/** 基本路由，这些路由是必须存在的 */
const coreRoutes: RouteRecordRaw[] = [
  /**
   * 根路由
   * 使用基础布局，作为所有页面的父级容器，子级就不必配置BasicLayout。
   * 此路由必须存在，且不应修改
   */
  {
    component: BasicLayout,
    meta: {
      hideInBreadcrumb: true,
      title: 'Root',
    },
    name: 'Root',
    path: '/',
    redirect: preferences.app.defaultHomePath,
    children: [
      {
        path: 'pve/vm/detail/:id',
        name: 'PVE_VM_Detail',
        component: () => import('#/views/pve/vm/detail/index.vue'),
        meta: {
          hideInMenu: true,
          hideInTab: false,
          title: '虚拟机详情',
          currentActiveMenu: '/pve/vm',
        },
      },
      {
        path: 'pve/lxc/detail/:id',
        name: 'PVE_LXC_Detail',
        component: () => import('#/views/pve/lxc/detail/index.vue'),
        meta: {
          hideInMenu: true,
          hideInTab: false,
          title: '容器详情',
          currentActiveMenu: '/pve/lxc',
        },
      },
      {
        path: 'profile/index',
        name: 'Profile',
        component: () => import('#/views/system/profile/index.vue'),
        meta: {
          title: '个人中心',
        },
      },
      // ─── 实验课程：含动态参数的隐藏页（与 PVE 详情页模式一致，直接注册到根路由） ───
      {
        path: 'experiments/teacher/create',
        name: 'TeacherExperimentCreate',
        component: () => import('#/views/experiments/teacher/ExperimentForm.vue'),
        meta: { hideInMenu: true, title: '创建实验', activePath: '/experiments/teacher' },
      },
      {
        path: 'experiments/teacher/edit/:id',
        name: 'TeacherExperimentEdit',
        component: () => import('#/views/experiments/teacher/ExperimentForm.vue'),
        meta: { hideInMenu: true, title: '编辑实验', activePath: '/experiments/teacher' },
      },
      {
        path: 'experiments/teacher/grade/:id',
        name: 'TeacherGradeSubmission',
        component: () => import('#/views/experiments/teacher/GradeSubmission.vue'),
        meta: { hideInMenu: true, title: '批改作业', activePath: '/experiments/teacher/submissions' },
      },
      {
        path: 'experiments/student/:id',
        name: 'StudentExperimentDetail',
        component: () => import('#/views/experiments/student/ExperimentDetail.vue'),
        meta: { hideInMenu: true, title: '实验详情', activePath: '/experiments/student' },
      },
      {
        path: 'experiments/student/:id/grade',
        name: 'StudentGradeView',
        component: () => import('#/views/experiments/student/GradeView.vue'),
        meta: { hideInMenu: true, title: '查看成绩', activePath: '/experiments/student' },
      },
      {
        path: 'experiments/student/submissions/:id/edit',
        name: 'StudentSubmissionEditor',
        component: () => import('#/views/experiments/student/SubmissionEditor.vue'),
        meta: { hideInMenu: true, title: '编辑报告', activePath: '/experiments/student' },
      },

    ],
  },
  {
    component: AuthPageLayout,
    meta: {
      hideInTab: true,
      title: 'Authentication',
    },
    name: 'Authentication',
    path: '/auth',
    redirect: LOGIN_PATH,
    children: [
      {
        name: 'Login',
        path: 'login',
        component: () => import('#/views/_core/authentication/login.vue'),
        meta: {
          title: $t('page.auth.login'),
        },
      },
      {
        name: 'CodeLogin',
        path: 'code-login',
        component: () => import('#/views/_core/authentication/code-login.vue'),
        meta: {
          title: $t('page.auth.codeLogin'),
        },
      },
      {
        name: 'QrCodeLogin',
        path: 'qrcode-login',
        component: () =>
          import('#/views/_core/authentication/qrcode-login.vue'),
        meta: {
          title: $t('page.auth.qrcodeLogin'),
        },
      },
      {
        name: 'ForgetPassword',
        path: 'forget-password',
        component: () =>
          import('#/views/_core/authentication/forget-password.vue'),
        meta: {
          title: $t('page.auth.forgetPassword'),
        },
      },
      {
        name: 'Register',
        path: 'register',
        component: () => import('#/views/_core/authentication/register.vue'),
        meta: {
          title: $t('page.auth.register'),
        },
      },
    ],
  },
];

export { coreRoutes, fallbackNotFoundRoute };
