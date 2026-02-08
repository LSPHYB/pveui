import type { Router } from 'vue-router';

import { LOGIN_PATH } from '@vben/constants';
import { preferences } from '@vben/preferences';
import { useAccessStore, useUserStore } from '@vben/stores';
import { startProgress, stopProgress } from '@vben/utils';

import { accessRoutes, coreRouteNames } from '#/router/routes';
import { useAuthStore } from '#/store';

import { generateAccess } from './access';

/**
 * 通用守卫配置
 * @param router
 */
function setupCommonGuard(router: Router) {
  // 记录已经加载的页面
  const loadedPaths = new Set<string>();

  router.beforeEach((to) => {
    to.meta.loaded = loadedPaths.has(to.path);

    // 页面加载进度条
    if (!to.meta.loaded && preferences.transition.progress) {
      startProgress();
    }
    return true;
  });

  router.afterEach((to) => {
    // 记录页面是否加载,如果已经加载，后续的页面切换动画等效果不在重复执行

    loadedPaths.add(to.path);

    // 关闭页面加载进度条
    if (preferences.transition.progress) {
      stopProgress();
    }
  });
}

/**
 * 权限访问守卫配置
 * @param router
 */
function setupAccessGuard(router: Router) {
  router.beforeEach(async (to, from) => {
    console.log('[Guard] 🛡️ 路由守卫触发');
    console.log('[Guard] 📍 从:', from.path, '到:', to.path);

    const accessStore = useAccessStore();
    const userStore = useUserStore();
    const authStore = useAuthStore();

    console.log(
      '[Guard] 🔑 当前 accessToken:',
      accessStore.accessToken ? '存在' : '不存在',
    );
    console.log('[Guard] 🔐 是否已检查权限:', accessStore.isAccessChecked);

    // 基本路由，这些路由不需要进入权限拦截
    if (coreRouteNames.includes(to.name as string)) {
      console.log('[Guard] ✅ 核心路由，跳过权限检查:', to.name);
      if (to.path === LOGIN_PATH && accessStore.accessToken) {
        const redirectPath = decodeURIComponent(
          (to.query?.redirect as string) ||
            userStore.userInfo?.homePath ||
            preferences.app.defaultHomePath,
        );
        console.log('[Guard] 🔀 已登录访问登录页，重定向到:', redirectPath);
        return redirectPath;
      }
      return true;
    }

    // accessToken 检查
    if (!accessStore.accessToken) {
      console.log('[Guard] ❌ 无 accessToken');
      // 明确声明忽略权限访问权限，则可以访问
      if (to.meta.ignoreAccess) {
        console.log('[Guard] ⚠️ 路由忽略权限检查，允许访问');
        return true;
      }

      // 没有访问权限，跳转登录页面
      if (to.fullPath !== LOGIN_PATH) {
        console.log('[Guard] 🔀 未登录，重定向到登录页');
        return {
          path: LOGIN_PATH,
          // 如不需要，直接删除 query
          query:
            to.fullPath === preferences.app.defaultHomePath
              ? {}
              : { redirect: encodeURIComponent(to.fullPath) },
          // 携带当前跳转的页面，登录后重新跳转该页面
          replace: true,
        };
      }
      return to;
    }

    // 是否已经生成过动态路由
    if (accessStore.isAccessChecked) {
      console.log('[Guard] ✅ 已生成动态路由，直接放行');
      return true;
    }

    console.log('[Guard] 🔄 开始生成动态路由...');
    // 生成路由表
    // 当前登录用户拥有的角色标识列表
    const userInfo = userStore.userInfo || (await authStore.fetchUserInfo());
    console.log('[Guard] 👤 用户信息:', userInfo);
    const userRoles = userInfo.roles ?? [];
    console.log('[Guard] 👔 用户角色:', userRoles);

    // 生成菜单和路由
    console.log('[Guard] 🔄 调用 generateAccess...');
    const { accessibleMenus, accessibleRoutes } = await generateAccess({
      roles: userRoles,
      router,
      // 则会在菜单中显示，但是访问会被重定向到403
      routes: accessRoutes,
    });

    console.log('[Guard] 📋 生成的菜单数量:', accessibleMenus?.length || 0);
    console.log('[Guard] 📋 生成的菜单:', accessibleMenus);
    console.log('[Guard] 🛣️ 生成的路由数量:', accessibleRoutes?.length || 0);
    console.log('[Guard] 🛣️ 生成的路由:', accessibleRoutes);

    // 保存菜单信息和路由信息
    accessStore.setAccessMenus(accessibleMenus);
    accessStore.setAccessRoutes(accessibleRoutes);
    accessStore.setIsAccessChecked(true);
    console.log('[Guard] 💾 菜单和路由已保存，isAccessChecked 已设置为 true');

    const redirectPath = (from.query.redirect ??
      (to.path === preferences.app.defaultHomePath
        ? userInfo.homePath || preferences.app.defaultHomePath
        : to.fullPath)) as string;

    console.log('[Guard] 🎯 最终重定向路径:', redirectPath);
    console.log('[Guard] 🔀 执行重定向...');

    const resolved = router.resolve(decodeURIComponent(redirectPath));
    console.log('[Guard] 🔍 解析后的路由:', resolved);

    return {
      ...resolved,
      replace: true,
    };
  });
}

/**
 * 项目守卫配置
 * @param router
 */
function createRouterGuard(router: Router) {
  /** 通用 */
  setupCommonGuard(router);
  /** 权限访问 */
  setupAccessGuard(router);
}

export { createRouterGuard };
