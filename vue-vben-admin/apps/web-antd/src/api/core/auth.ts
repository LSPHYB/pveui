import { baseRequestClient, requestClient } from '#/api/request';

export namespace AuthApi {
  /** 登录接口参数 */
  export interface LoginParams {
    password?: string;
    username?: string;
  }

  /** 登录接口返回值 - 适配Django */
  export interface LoginResult {
    accessToken: string; // 从Django的access字段映射
    refreshToken?: string; // 从Django的refresh字段映射
  }

  export interface RefreshTokenResult {
    data: string;
    status: number;
  }
}

/**
 * 登录 - 适配Django后端
 */
export async function loginApi(data: AuthApi.LoginParams) {
  console.log('[Login API] 📤 发送登录请求:', { username: data.username });

  // Django返回: {id, username, roles, permissions, access, refresh}
  // 使用any以免TS报错，我们需要手动检查结构
  const response = await requestClient.post<any>('/rbac/auth/login/', data);

  console.log('[Login API] 📥 后端原始响应:', response);

  // 核心修复：自动检测Token位置
  let accessToken = '';
  let refreshToken = '';

  // 情况1：直接在response中 (Django REST Framework 默认行为)
  if (response?.access) {
    accessToken = response.access;
    refreshToken = response.refresh;
    console.log('[Login API] ✅ 在响应根对象找到Token');
  }
  // 情况2：在response.data中 (通用API包装格式)
  else if (response?.data?.access) {
    accessToken = response.data.access;
    refreshToken = response.data.refresh;
    console.log('[Login API] ✅ 在responses.data中找到Token');
  }
  // 情况3：在response.token中 (另一种常见格式)
  else if (response?.token) {
    accessToken = response.token;
    console.log('[Login API] ✅ 在响应中找到Token字段');
  }

  // 详细的调试输出
  console.log(
    `[Login API] 🔑 提取结果: AccessToken=${accessToken ? '存在' : '空'}, RefreshToken=${refreshToken ? '存在' : '空'}`,
  );

  // 保存refresh token到localStorage (如果有)
  if (refreshToken) {
    localStorage.setItem('refresh_token', refreshToken);
    console.log('[Login API] 💾 已保存 refresh_token 到 localStorage');
  }

  if (!accessToken) {
    console.error(
      '[Login API] ❌ 警告: 未能从响应中提取到 accessToken！请检查上方输出的"后端原始响应"结构。',
    );
    // 尝试打印所有key帮助调试
    try {
      console.log('[Login API] 响应Keys:', Object.keys(response));
    } catch {}
  }

  // 将Django的响应格式转换为Vben期望的格式
  const result = {
    accessToken,
    refreshToken,
  } as AuthApi.LoginResult;

  return result;
}

/**
 * 刷新accessToken - Django使用JWT refresh token
 */
/**
 * 刷新accessToken - Django使用JWT refresh token
 */
export async function refreshTokenApi() {
  const refreshToken = localStorage.getItem('refresh_token');
  console.log(
    '[RefreshToken API] 🔄 尝试刷新Token, refresh_token:',
    refreshToken ? '存在' : '缺失',
  );

  if (!refreshToken) {
    console.warn('[RefreshToken API] ❌ 没有refresh_token，无法刷新');
    throw new Error('No refresh token available');
  }

  // 使用 baseRequestClient 发送请求，避免拦截器死循环
  // 注意：Django SimpleJWT 的 refresh 接口通常不需要 Authorization header，只需要 body 里的 refresh token
  const response = await baseRequestClient.post<any>('/rbac/auth/refresh/', {
    refresh: refreshToken,
  });

  console.log('[RefreshToken API] 📥 刷新响应:', response);

  // 兼容不同的响应结构
  const newAccessToken =
    response?.access ||
    response?.data?.access ||
    response?.token ||
    response?.data?.token;

  if (newAccessToken) {
    console.log('[RefreshToken API] ✅ 刷新成功, 获取到新的 AccessToken');
  } else {
    console.error('[RefreshToken API] ❌ 刷新失败: 响应中未找到 access token');
  }

  return {
    data: newAccessToken,
    status: 200,
  } as AuthApi.RefreshTokenResult;
}

/**
 * 退出登录 - 适配Django
 */
/**
 * 退出登录 - 适配Django
 */
export async function logoutApi() {
  const refreshToken = localStorage.getItem('refresh_token');
  console.log('[Logout API] 🚪 正在退出登录...');

  // 使用 requestClient 发送请求，因为它会自动附加当前 AccessToken 到 Header
  // 大多数后端 Logout 接口需要验证身份
  try {
    await requestClient.post('/rbac/auth/logout/', {
      refresh: refreshToken,
    });
    console.log('[Logout API] ✅ 服务端退出成功');
  } catch (error) {
    console.warn(
      '[Logout API] ⚠️ 服务端退出请求失败(可能是Token已失效), 继续执行本地清除:',
      error,
    );
  }

  // 清除本地存储的refresh token
  localStorage.removeItem('refresh_token');
}

/**
 * 获取用户权限码 - 从用户信息中获取
 */
export async function getAccessCodesApi() {
  const userInfo = await requestClient.get<any>('/rbac/auth/user-info/');
  // Django返回的permissions数组就是权限码
  return userInfo.permissions || [];
}
