import type { Recordable, UserInfo } from '@vben/types';

import { ref } from 'vue';
import { useRouter } from 'vue-router';

import { LOGIN_PATH } from '@vben/constants';
import { preferences } from '@vben/preferences';
import { resetAllStores, useAccessStore, useUserStore } from '@vben/stores';

import { notification } from 'ant-design-vue';
import { defineStore } from 'pinia';

import { getAccessCodesApi, getUserInfoApi, loginApi, logoutApi } from '#/api';
import { $t } from '#/locales';

export const useAuthStore = defineStore('auth', () => {
  const accessStore = useAccessStore();
  const userStore = useUserStore();
  const router = useRouter();

  const loginLoading = ref(false);

  /**
   * 异步处理登录操作
   * Asynchronously handle the login process
   * @param params 登录表单数据
   */
  async function authLogin(
    params: Recordable<any>,
    onSuccess?: () => Promise<void> | void,
  ) {
    // 异步处理用户登录操作并获取 accessToken
    let userInfo: null | UserInfo = null;
    try {
      loginLoading.value = true;
      console.log('[Auth] 🚀 开始登录流程...');
      const loginResult = await loginApi(params);
      console.log('[Auth] 📦 loginApi返回完整对象:', loginResult);
      const { accessToken } = loginResult;
      console.log(
        '[Auth] ✅ 登录API返回, accessToken:',
        accessToken ? '存在' : '不存在',
      );

      // 如果成功获取到 accessToken
      if (accessToken) {
        console.log('[Auth] 💾 保存 accessToken...');
        accessStore.setAccessToken(accessToken);
        console.log(
          '[Auth] ✅ accessToken 已保存, 当前token:',
          accessStore.accessToken ? '存在' : '不存在',
        );

        // 获取用户信息并存储到 accessStore 中
        console.log('[Auth] 🔄 并行获取用户信息和权限码...');
        const [fetchUserInfoResult, accessCodes] = await Promise.all([
          fetchUserInfo(),
          getAccessCodesApi(),
        ]);

        userInfo = fetchUserInfoResult;
        console.log('[Auth] ✅ 用户信息:', userInfo);
        console.log('[Auth] ✅ 权限码:', accessCodes);

        userStore.setUserInfo(userInfo);
        accessStore.setAccessCodes(accessCodes);
        console.log('[Auth] 💾 用户信息和权限码已保存');

        const targetPath = userInfo.homePath || preferences.app.defaultHomePath;
        console.log('[Auth] 🏠 homePath:', userInfo.homePath);
        console.log(
          '[Auth] 🏠 defaultHomePath:',
          preferences.app.defaultHomePath,
        );
        console.log('[Auth] 🎯 目标跳转路径:', targetPath);

        if (accessStore.loginExpired) {
          console.log('[Auth] ⚠️ 登录已过期，重置状态');
          accessStore.setLoginExpired(false);
        } else {
          console.log('[Auth] 🔀 准备跳转...');
          if (onSuccess) {
            console.log('[Auth] 🔀 执行 onSuccess 回调');
            await onSuccess?.();
          } else {
            console.log('[Auth] 🔀 执行 router.push 到:', targetPath);
            await router.push(targetPath);
            console.log('[Auth] ✅ router.push 完成');
          }
        }

        if (userInfo?.realName) {
          notification.success({
            description: `${$t('authentication.loginSuccessDesc')}:${userInfo?.realName}`,
            duration: 3,
            message: $t('authentication.loginSuccess'),
          });
        }
      } else {
        console.error('[Auth] ❌ 登录失败: accessToken 为空');
      }
    } catch (error) {
      console.error('[Auth] ❌ 登录出错:', error);
      throw error;
    } finally {
      loginLoading.value = false;
      console.log('[Auth] 🏁 登录流程结束');
    }

    return {
      userInfo,
    };
  }

  // 防止 token 过期时 logoutApi 401 → doReAuthenticate → logout 无限循环
  let isLoggingOut = false;

  async function logout(redirect: boolean = true) {
    // 如果已经正在登出，直接返回，避免无限循环
    if (isLoggingOut) {
      console.warn('[Logout] ⚠️ 已在登出流程中，跳过重复调用');
      return;
    }
    isLoggingOut = true;

    try {
      console.log('[Logout API] 🚪 正在退出登录...');
      // 只有 accessToken 存在时才调用后端登出接口
      // 若 token 已失效（由 doReAuthenticate 清空），跳过此调用以防无限循环
      if (accessStore.accessToken) {
        await logoutApi();
      } else {
        console.warn('[Logout API] ⚠️ accessToken 已失效，跳过后端登出请求');
      }
    } catch {
      // 接口失败不影响本地登出流程
    } finally {
      isLoggingOut = false;
    }

    resetAllStores();
    accessStore.setLoginExpired(false);

    // 回登录页带上当前路由地址
    await router.replace({
      path: LOGIN_PATH,
      query: redirect
        ? {
          redirect: encodeURIComponent(router.currentRoute.value.fullPath),
        }
        : {},
    });
  }

  async function fetchUserInfo() {
    let userInfo: null | UserInfo = null;
    userInfo = await getUserInfoApi();
    userStore.setUserInfo(userInfo);
    return userInfo;
  }

  function $reset() {
    loginLoading.value = false;
  }

  return {
    $reset,
    authLogin,
    fetchUserInfo,
    loginLoading,
    logout,
  };
});
