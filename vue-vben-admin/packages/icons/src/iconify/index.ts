import { createIconifyIcon } from '@vben-core/icons';

export * from '@vben-core/icons';

export const MdiKeyboardEsc = createIconifyIcon('mdi:keyboard-esc');

// Dashboard & General
export const IconDashboard = createIconifyIcon('lucide:layout-dashboard');
export const IconApps = createIconifyIcon('lucide:layout-grid');
export const IconSettings = createIconifyIcon('lucide:settings');
export const IconMonitor = createIconifyIcon('lucide:activity'); // or monitor

// System Management
export const IconUser = createIconifyIcon('lucide:user');
export const IconUsers = createIconifyIcon('lucide:users'); // for roles/teams
export const IconMenu = createIconifyIcon('lucide:menu');
export const IconSafety = createIconifyIcon('lucide:shield'); // permissions
export const IconOrganization = createIconifyIcon('lucide:building');
export const IconLog = createIconifyIcon('lucide:file-text');

// PVE specific (generic replacements)
export const IconServer = createIconifyIcon('lucide:server');
export const IconStorage = createIconifyIcon('lucide:hard-drive');
export const IconNetwork = createIconifyIcon('lucide:network');
