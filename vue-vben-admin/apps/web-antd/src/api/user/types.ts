/**
 * 用户相关类型定义
 */

/** 登录请求参数 */
export interface LoginParams {
  username: string;
  password: string;
}

/** 登录响应数据 */
export interface LoginResult {
  id: number;
  username: string;
  email?: string;
  is_superuser?: boolean;
  roles: RoleInfo[] | string[];
  permissions: string[];
  access: string; // JWT access token
  refresh: string; // JWT refresh token
}

/** 角色信息 */
export interface RoleInfo {
  id: number;
  code: string;
  name: string;
}

/** 用户信息 */
export interface UserInfo {
  id: number;
  username: string;
  email?: string;
  realName?: string; // 真实姓名
  first_name?: string;
  last_name?: string;
  biography?: string;
  avatar?: string; // 头像URL
  is_superuser?: boolean;
  roles: RoleInfo[] | string[];
  permissions: string[];
  primary_organization?: null | OrganizationInfo;
}

/** 组织信息 */
export interface OrganizationInfo {
  id: number;
  name: string;
  code?: string;
  parent?: null | number;
}

/** 修改密码参数 */
export interface ChangePasswordParams {
  old_password: string;
  new_password: string;
}

/** 退出登录参数 */
export interface LogoutParams {
  refresh: string;
}
