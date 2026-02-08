import { useUserStore } from '@vben/stores';

/**
 * Permission hook for checking user permissions
 */
export function usePermission() {
  const userStore = useUserStore();

  /**
   * Check if user has specific permission code
   * @param permissionCode - Permission code to check (e.g., 'pve_server:create')
   * @returns true if user has the permission
   */
  const hasPermission = (permissionCode: string): boolean => {
    if (!permissionCode) return true;

    let userInfo = userStore.userInfo;
    console.log('[Permission] Checking permission:', permissionCode);
    console.log('[Permission] Raw UserInfo:', userInfo);

    if (!userInfo) {
      console.log('[Permission] No userInfo, returning false');
      return false;
    }

    // Handle case where userInfo might be wrapped in Axios response
    // If userInfo has 'data' property, extract the actual user data
    if (userInfo && typeof userInfo === 'object' && 'data' in userInfo) {
      console.log('[Permission] UserInfo is Axios response, extracting data');
      userInfo = (userInfo as any).data;
    }

    console.log('[Permission] Actual user data:', userInfo);

    // Admin or superuser has all permissions
    if (userInfo.is_superuser) {
      console.log('[Permission] User is superuser, returning true');
      return true;
    }

    if (userInfo.username === 'admin') {
      console.log('[Permission] User is admin, returning true');
      return true;
    }

    // Check if user's permissions include the requested permission code
    const permissions = userInfo.permissions || [];
    const permissionResult = permissions.includes(permissionCode);
    console.log('[Permission] User permissions:', permissions);
    console.log('[Permission] Has permission?', permissionResult);
    return permissionResult;
  };

  /**
   * Check if user has any of the specified permissions
   * @param permissionCodes - Array of permission codes
   * @returns true if user has at least one permission
   */
  const hasAnyPermission = (permissionCodes: string[]): boolean => {
    return permissionCodes.some((code) => hasPermission(code));
  };

  /**
   * Check if user has all of the specified permissions
   * @param permissionCodes - Array of permission codes
   * @returns true if user has all permissions
   */
  const hasAllPermissions = (permissionCodes: string[]): boolean => {
    return permissionCodes.every((code) => hasPermission(code));
  };

  return {
    hasPermission,
    hasAnyPermission,
    hasAllPermissions,
  };
}
