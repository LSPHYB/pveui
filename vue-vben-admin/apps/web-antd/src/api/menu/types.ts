/**
 * 菜单相关类型定义
 */

/** 菜单项 */
export interface MenuItem {
  id: number;
  title: string;
  path: string;
  icon?: string;
  component?: string;
  parent?: null | number;
  order?: number;
  is_hidden?: boolean;
  children?: MenuItem[];
}

/** 菜单树响应 */
export type MenuTreeResult = MenuItem[];
