import type { RouteRecordRaw } from 'vue-router';

// 注意：含动态参数 :id 的隐藏页已迁移至 core.ts 的根路由子节点
// 此文件只保留需要 generateAccessible 处理（即后端菜单控制）的可见路由骨架
const routes: RouteRecordRaw[] = [
  {
    path: '/experiments',
    name: 'Experiments',
    component: () => import('#/layouts/basic.vue'),
    meta: {
      title: '实验课程',
      icon: 'lucide:flask-conical',
      order: 20,
    },
    children: [
      // ─── 教师端（显示在菜单中，由后端菜单控制） ───
      {
        path: 'teacher',
        name: 'TeacherExperiments',
        component: () => import('#/views/experiments/teacher/index.vue'),
        meta: {
          title: '实验管理',
          icon: 'lucide:clipboard-list',
        },
      },
      {
        path: 'teacher/submissions',
        name: 'TeacherSubmissions',
        component: () => import('#/views/experiments/teacher/SubmissionList.vue'),
        meta: {
          title: '提交管理',
          icon: 'lucide:file-check-2',
        },
      },
      // ─── 学生端（显示在菜单中，由后端菜单控制） ───
      {
        path: 'student',
        name: 'StudentExperiments',
        component: () => import('#/views/experiments/student/index.vue'),
        meta: {
          title: '我的实验',
          icon: 'lucide:book-open',
        },
      },
    ],
  },
];

export default routes;
