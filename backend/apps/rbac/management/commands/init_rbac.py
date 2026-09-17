"""初始化 RBAC 基础数据。

用法：
    python manage.py init_rbac
    python manage.py init_rbac --reset  # 删除现有数据后重新创建
    python manage.py init_rbac --create-superuser  # 如果不存在超级用户则创建（用户名：admin，密码：admin123）
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.rbac.models import Menu, Permission, Role, Organization, UserRole, UserOrganization

User = get_user_model()


class Command(BaseCommand):
    help = '初始化 RBAC 基础数据（菜单、权限、角色、组织）'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='删除现有数据后重新创建（危险操作）',
        )
        parser.add_argument(
            '--create-superuser',
            action='store_true',
            help='如果不存在超级用户则自动创建（默认用户名：admin，密码：admin123）',
        )
        parser.add_argument(
            '--superuser-username',
            type=str,
            default='admin',
            help='超级用户用户名（默认：admin）',
        )
        parser.add_argument(
            '--superuser-password',
            type=str,
            default='admin123',
            help='超级用户密码（默认：admin123）',
        )

    def handle(self, *args, **options):
        if options['reset']:
            self.stdout.write(self.style.WARNING('正在删除现有 RBAC 数据...'))
            UserRole.objects.all().delete()
            UserOrganization.objects.all().delete()
            Role.objects.all().delete()
            Permission.objects.all().delete()
            Menu.objects.all().delete()
            Organization.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('已删除现有数据'))

        # 1. 创建组织
        self.stdout.write('创建组织...')
        org_root = self._get_or_create_org('ROOT', '根组织', None, 0)
        org_admin = self._get_or_create_org('ADMIN', '系统管理部', org_root, 1)
        self.stdout.write(self.style.SUCCESS(f'  ✓ 创建组织: {org_root.name}, {org_admin.name}'))

        # 2. 创建菜单
        self.stdout.write('创建菜单...')
        # 顶级菜单
        menu_dashboard = self._get_or_create_menu('仪表盘', 'dashboard', 'dashboard/index', 'icon-dashboard', None, 0)
        menu_system = self._get_or_create_menu('系统管理', 'system', '', 'icon-settings', None, 1)
        menu_pve = self._get_or_create_menu('PVE管理', 'pve', '', 'icon-apps', None, 3)

        # 系统管理
        menu_user = self._get_or_create_menu('用户管理', 'user', 'system/user/index', 'icon-user', menu_system, 1)
        menu_role = self._get_or_create_menu('角色管理', 'role', 'system/role/index', 'icon-idcard', menu_system, 2)
        menu_menu = self._get_or_create_menu('菜单管理', 'menu', 'system/menu/index', 'icon-menu', menu_system, 3)
        menu_permission = self._get_or_create_menu('权限管理', 'permission', 'system/permission/index', 'icon-safe', menu_system, 4)
        menu_org = self._get_or_create_menu('组织管理', 'organization', 'system/organization/index', 'icon-apps', menu_system, 5)
        # 系统设置
        menu_system_setting = self._get_or_create_menu('系统设置', 'system-setting', 'system/setting/index', 'icon-settings', menu_system, 6)

        # 监控与日志（归入系统管理，不单独占一个顶级模块）
        menu_monitor = self._get_or_create_menu('监控概览', 'monitor-dashboard', 'system/monitor/index', 'icon-dashboard', menu_system, 7)
        menu_operation_log = self._get_or_create_menu('操作日志', 'operation-log', 'system/operation-log/index', 'icon-file', menu_system, 8)
        menu_login_log = self._get_or_create_menu('登录日志', 'login-log', 'system/login-log/index', 'icon-user', menu_system, 9)
        menu_tasks = self._get_or_create_menu('任务管理', 'task', 'system/task/index', 'icon-schedule', menu_system, 10)
        
        # PVE管理
        menu_pve_server = self._get_or_create_menu('PVE服务器管理', 'pve-server', 'pve/server/index', 'icon-computer', menu_pve, 1)
        menu_pve_vm = self._get_or_create_menu('虚拟机管理', 'pve-vm', 'pve/vm/index', 'icon-desktop', menu_pve, 2)
        menu_pve_storage = self._get_or_create_menu('存储管理', 'pve-storage', 'pve/storage/index', 'icon-storage', menu_pve, 3)
        menu_pve_node_monitor = self._get_or_create_menu('PVE节点监控', 'pve-node-monitor', 'pve/node-monitor/index', 'icon-bar-chart', menu_pve, 4)
        menu_pve_templates = self._get_or_create_menu('模板管理', 'pve-templates', 'pve/templates/index', 'icon-file', menu_pve, 6)
        menu_pve_network = self._get_or_create_menu('网络管理', 'pve-network', 'pve/network/index', 'icon-link', menu_pve, 7)
        menu_pve_topology = self._get_or_create_menu('网络拓扑', 'pve-topology', 'pve/topology/index', 'icon-share-alt', menu_pve, 8)
        menu_pve_lxc = self._get_or_create_menu('LXC容器管理', 'pve-lxc', 'pve/lxc/index', 'icon-apps', menu_pve, 9)

        # 清理遗留菜单：早期版本创建过「全局任务中心」(pve/tasks/index)，
        # 该页面只存在于已废弃的 Arco 版前端，web-antd 中没有对应组件。
        # 菜单留在库里会让前端注册出无效路由（route component is invalid）。
        legacy_menu = Menu.objects.filter(path='pve-tasks').first()
        if legacy_menu:
            # 对应接口仍然存在，权限改挂到 PVE 管理下而不是一并删除
            Permission.objects.filter(menu=legacy_menu).update(menu=menu_pve)
            legacy_menu.delete()
            self.stdout.write(self.style.WARNING(
                '  ✓ 移除遗留菜单「全局任务中心」（web-antd 无对应页面）'))

        self.stdout.write(self.style.SUCCESS('  ✓ 创建菜单: 系统管理 / 系统监控 / PVE管理 分组完成'))

        # 3. 创建权限
        self.stdout.write('创建权限...')
        perms = []
        
        # 仪表盘权限
        perms.append(self._get_or_create_permission('仪表盘查看', 'dashboard:view', 'GET', '/api/rbac/dashboard/', menu_dashboard))
        
        # 用户管理权限
        perms.append(self._get_or_create_permission('用户列表', 'user:list', 'GET', '/api/rbac/users/', menu_user))
        perms.append(self._get_or_create_permission('用户创建', 'user:create', 'POST', '/api/rbac/users/', menu_user))
        perms.append(self._get_or_create_permission('用户更新', 'user:update', 'PUT', '/api/rbac/users/', menu_user))
        perms.append(self._get_or_create_permission('用户删除', 'user:delete', 'DELETE', '/api/rbac/users/', menu_user))
        
        # 角色管理权限
        perms.append(self._get_or_create_permission('角色列表', 'role:list', 'GET', '/api/rbac/roles/', menu_role))
        perms.append(self._get_or_create_permission('角色创建', 'role:create', 'POST', '/api/rbac/roles/', menu_role))
        perms.append(self._get_or_create_permission('角色更新', 'role:update', 'PUT', '/api/rbac/roles/', menu_role))
        perms.append(self._get_or_create_permission('角色删除', 'role:delete', 'DELETE', '/api/rbac/roles/', menu_role))
        
        # 菜单管理权限
        perms.append(self._get_or_create_permission('菜单列表', 'menu:list', 'GET', '/api/rbac/menus/', menu_menu))
        perms.append(self._get_or_create_permission('菜单创建', 'menu:create', 'POST', '/api/rbac/menus/', menu_menu))
        perms.append(self._get_or_create_permission('菜单更新', 'menu:update', 'PUT', '/api/rbac/menus/', menu_menu))
        perms.append(self._get_or_create_permission('菜单删除', 'menu:delete', 'DELETE', '/api/rbac/menus/', menu_menu))
        
        # 权限管理权限
        perms.append(self._get_or_create_permission('权限列表', 'permission:list', 'GET', '/api/rbac/permissions/', menu_permission))
        perms.append(self._get_or_create_permission('权限创建', 'permission:create', 'POST', '/api/rbac/permissions/', menu_permission))
        perms.append(self._get_or_create_permission('权限更新', 'permission:update', 'PUT', '/api/rbac/permissions/', menu_permission))
        perms.append(self._get_or_create_permission('权限删除', 'permission:delete', 'DELETE', '/api/rbac/permissions/', menu_permission))
        
        # 组织管理权限
        perms.append(self._get_or_create_permission('组织列表', 'organization:list', 'GET', '/api/rbac/organizations/', menu_org))
        perms.append(self._get_or_create_permission('组织创建', 'organization:create', 'POST', '/api/rbac/organizations/', menu_org))
        perms.append(self._get_or_create_permission('组织更新', 'organization:update', 'PUT', '/api/rbac/organizations/', menu_org))
        perms.append(self._get_or_create_permission('组织删除', 'organization:delete', 'DELETE', '/api/rbac/organizations/', menu_org))
        
        # 系统监控权限
        perms.append(self._get_or_create_permission('系统监控查看', 'system:metrics', 'GET', '/api/rbac/system/metrics/', menu_monitor))
        # 任务管理权限（归属监控）
        perms.append(self._get_or_create_permission('任务列表', 'tasks:list', 'GET', '/api/tasks/tasks/', menu_tasks))
        perms.append(self._get_or_create_permission('任务创建', 'tasks:create', 'POST', '/api/tasks/tasks/', menu_tasks))
        perms.append(self._get_or_create_permission('任务更新', 'tasks:update', 'PUT', r'/api/tasks/tasks/\\d+/', menu_tasks))
        perms.append(self._get_or_create_permission('任务删除', 'tasks:delete', 'DELETE', r'/api/tasks/tasks/\\d+/', menu_tasks))
        perms.append(self._get_or_create_permission('任务立即执行', 'tasks:run_now', 'POST', r'/api/tasks/tasks/\\d+/run_now/', menu_tasks))
        # 操作日志权限
        perms.append(self._get_or_create_permission('操作日志列表', 'operation_log:list', 'GET', '/api/audit/logs/', menu_operation_log))
        perms.append(self._get_or_create_permission('操作日志查看', 'operation_log:view', 'GET', r'/api/audit/logs/\d+/', menu_operation_log))
        # 登录日志权限（归属监控）
        perms.append(self._get_or_create_permission('登录日志列表', 'login_log:list', 'GET', '/api/audit/login-logs/', menu_login_log))
        perms.append(self._get_or_create_permission('登录日志查看', 'login_log:view', 'GET', r'/api/audit/login-logs/\\d+/', menu_login_log))
        # 系统设置权限（归属系统管理）
        perms.append(self._get_or_create_permission('系统设置列表', 'system_setting:list', 'GET', '/api/system/settings/', menu_system_setting))
        perms.append(self._get_or_create_permission('系统设置创建', 'system_setting:create', 'POST', '/api/system/settings/', menu_system_setting))
        perms.append(self._get_or_create_permission('系统设置更新', 'system_setting:update', 'PUT', r'/api/system/settings/\\d+/', menu_system_setting))
        perms.append(self._get_or_create_permission('系统设置部分更新', 'system_setting:partial_update', 'PATCH', r'/api/system/settings/\\d+/', menu_system_setting))
        perms.append(self._get_or_create_permission('系统设置删除', 'system_setting:delete', 'DELETE', r'/api/system/settings/\\d+/', menu_system_setting))
        perms.append(self._get_or_create_permission('系统设置批量更新', 'system_setting:bulk_update', 'POST', '/api/system/settings/bulk_update/', menu_system_setting))
        perms.append(self._get_or_create_permission('系统设置按键获取', 'system_setting:get_by_key', 'GET', '/api/system/settings/get_by_key/', menu_system_setting))


        # PVE服务器管理权限
        perms.append(self._get_or_create_permission('PVE服务器列表', 'pve_server:list', 'GET', '/api/pve/servers/', menu_pve_server))
        perms.append(self._get_or_create_permission('PVE服务器创建', 'pve_server:create', 'POST', '/api/pve/servers/', menu_pve_server))
        perms.append(self._get_or_create_permission('PVE服务器更新', 'pve_server:update', 'PUT', r'/api/pve/servers/\\d+/', menu_pve_server))
        perms.append(self._get_or_create_permission('PVE服务器部分更新', 'pve_server:partial_update', 'PATCH', r'/api/pve/servers/\\d+/', menu_pve_server))
        perms.append(self._get_or_create_permission('PVE服务器删除', 'pve_server:delete', 'DELETE', r'/api/pve/servers/\\d+/', menu_pve_server))
        perms.append(self._get_or_create_permission('PVE服务器查看', 'pve_server:retrieve', 'GET', r'/api/pve/servers/\\d+/', menu_pve_server))
        perms.append(self._get_or_create_permission('PVE服务器测试连接', 'pve_server:test_connection', 'POST', r'/api/pve/servers/\\d+/test_connection/', menu_pve_server))
        perms.append(self._get_or_create_permission('PVE服务器获取节点', 'pve_server:nodes', 'GET', r'/api/pve/servers/\\d+/nodes/', menu_pve_server))
        perms.append(self._get_or_create_permission('PVE服务器获取节点虚拟机', 'pve_server:node_vms', 'GET', r'/api/pve/servers/\\d+/nodes/[^/]+/vms/', menu_pve_server))
        perms.append(self._get_or_create_permission('PVE服务器获取节点存储', 'pve_server:node_storage', 'GET', r'/api/pve/servers/\\d+/nodes/[^/]+/storage/', menu_pve_server))
        perms.append(self._get_or_create_permission('PVE服务器存储内容', 'pve_server:storage_content', 'GET', r'/api/pve/servers/\\d+/nodes/[^/]+/storage/[^/]+/content/', menu_pve_server))
        perms.append(self._get_or_create_permission('PVE服务器存储上传', 'pve_server:storage_upload', 'POST', r'/api/pve/servers/\\d+/nodes/[^/]+/storage/[^/]+/upload/', menu_pve_server))
        perms.append(self._get_or_create_permission('PVE服务器存储ISO列表', 'pve_server:storage_iso', 'GET', r'/api/pve/servers/\\d+/nodes/[^/]+/storage/[^/]+/iso/', menu_pve_server))
        perms.append(self._get_or_create_permission('PVE节点监控查看', 'pve_node:monitor', 'GET', r'/api/pve/servers/\\d+/nodes/[^/]+/monitor/', menu_pve_node_monitor))
        # 全局任务中心权限
        perms.append(self._get_or_create_permission('全局任务列表', 'pve_tasks:global_tasks', 'GET', '/api/pve/servers/global-tasks/', menu_pve))
        perms.append(self._get_or_create_permission('全局任务日志', 'pve_tasks:global_task_log', 'POST', '/api/pve/servers/task-log/', menu_pve))
        # 模板管理权限
        perms.append(self._get_or_create_permission('模板列表', 'pve_templates:list', 'GET', r'/api/pve/servers/\\d+/nodes/[^/]+/storage/[^/]+/content/', menu_pve_templates))
        perms.append(self._get_or_create_permission('模板上传', 'pve_templates:upload', 'POST', r'/api/pve/servers/\\d+/nodes/[^/]+/storage/[^/]+/upload/', menu_pve_templates))
        # 网络管理权限
        perms.append(self._get_or_create_permission('网络接口列表', 'pve_network:list', 'GET', r'/api/pve/servers/\\d+/nodes/[^/]+/network/', menu_pve_network))
        
        # PVE 存储管理权限
        perms.append(self._get_or_create_permission('PVE存储服务器列表', 'pve_storage:servers', 'GET', '/api/pve/servers/', menu_pve_storage))
        perms.append(self._get_or_create_permission('PVE存储节点列表', 'pve_storage:nodes', 'GET', r'/api/pve/servers/\\d+/nodes/', menu_pve_storage))
        perms.append(self._get_or_create_permission('PVE存储节点存储列表', 'pve_storage:node_storage', 'GET', r'/api/pve/servers/\\d+/nodes/[^/]+/storage/', menu_pve_storage))
        perms.append(self._get_or_create_permission('PVE存储内容列表', 'pve_storage:storage_content', 'GET', r'/api/pve/servers/\\d+/nodes/[^/]+/storage/[^/]+/content/', menu_pve_storage))
        perms.append(self._get_or_create_permission('PVE存储上传', 'pve_storage:storage_upload', 'POST', r'/api/pve/servers/\\d+/nodes/[^/]+/storage/[^/]+/upload/', menu_pve_storage))
        perms.append(self._get_or_create_permission('PVE存储ISO列表', 'pve_storage:storage_iso', 'GET', r'/api/pve/servers/\\d+/nodes/[^/]+/storage/[^/]+/iso/', menu_pve_storage))
        perms.append(self._get_or_create_permission('网络拓扑列表', 'pve_topology:list', 'GET', '/api/pve/network-topologies/', menu_pve_topology))
        perms.append(self._get_or_create_permission('网络拓扑创建', 'pve_topology:create', 'POST', '/api/pve/network-topologies/', menu_pve_topology))
        perms.append(self._get_or_create_permission('网络拓扑查看', 'pve_topology:retrieve', 'GET', r'/api/pve/network-topologies/\\d+/', menu_pve_topology))
        perms.append(self._get_or_create_permission('网络拓扑更新', 'pve_topology:update', 'PUT', r'/api/pve/network-topologies/\\d+/', menu_pve_topology))
        perms.append(self._get_or_create_permission('网络拓扑部分更新', 'pve_topology:partial_update', 'PATCH', r'/api/pve/network-topologies/\\d+/', menu_pve_topology))
        perms.append(self._get_or_create_permission('网络拓扑删除', 'pve_topology:delete', 'DELETE', r'/api/pve/network-topologies/\\d+/', menu_pve_topology))
        
        # LXC 容器管理权限
        perms.append(self._get_or_create_permission('LXC容器列表', 'pve_lxc:list', 'GET', '/api/pve/lxc-containers/', menu_pve_lxc))
        perms.append(self._get_or_create_permission('LXC容器创建', 'pve_lxc:create', 'POST', '/api/pve/lxc-containers/', menu_pve_lxc))
        perms.append(self._get_or_create_permission('LXC容器查看', 'pve_lxc:retrieve', 'GET', r'/api/pve/lxc-containers/\\d+/', menu_pve_lxc))
        perms.append(self._get_or_create_permission('LXC容器更新', 'pve_lxc:update', 'PUT', r'/api/pve/lxc-containers/\\d+/', menu_pve_lxc))
        perms.append(self._get_or_create_permission('LXC容器部分更新', 'pve_lxc:partial_update', 'PATCH', r'/api/pve/lxc-containers/\\d+/', menu_pve_lxc))
        perms.append(self._get_or_create_permission('LXC容器删除', 'pve_lxc:delete', 'DELETE', r'/api/pve/lxc-containers/\\d+/', menu_pve_lxc))
        perms.append(self._get_or_create_permission('LXC容器操作', 'pve_lxc:action', 'POST', r'/api/pve/lxc-containers/\\d+/container_action/', menu_pve_lxc))
        perms.append(self._get_or_create_permission('LXC容器同步状态', 'pve_lxc:sync_status', 'GET', r'/api/pve/lxc-containers/\\d+/sync_status/', menu_pve_lxc))
        perms.append(self._get_or_create_permission('LXC容器全量同步', 'pve_lxc:sync_all', 'POST', '/api/pve/lxc-containers/sync_all/', menu_pve_lxc))
        
        # 虚拟机管理权限
        perms.append(self._get_or_create_permission('虚拟机列表', 'pve_vm:list', 'GET', '/api/pve/virtual-machines/', menu_pve_vm))
        perms.append(self._get_or_create_permission('虚拟机创建', 'pve_vm:create_vm', 'POST', '/api/pve/virtual-machines/create_vm/', menu_pve_vm))
        perms.append(self._get_or_create_permission('虚拟机查看', 'pve_vm:retrieve', 'GET', r'/api/pve/virtual-machines/\\d+/', menu_pve_vm))
        perms.append(self._get_or_create_permission('虚拟机更新', 'pve_vm:update', 'PUT', r'/api/pve/virtual-machines/\\d+/', menu_pve_vm))
        perms.append(self._get_or_create_permission('虚拟机部分更新', 'pve_vm:partial_update', 'PATCH', r'/api/pve/virtual-machines/\\d+/', menu_pve_vm))
        perms.append(self._get_or_create_permission('虚拟机删除', 'pve_vm:delete', 'DELETE', r'/api/pve/virtual-machines/\\d+/', menu_pve_vm))
        perms.append(self._get_or_create_permission('虚拟机操作', 'pve_vm:vm_action', 'POST', r'/api/pve/virtual-machines/\\d+/vm_action/', menu_pve_vm))
        perms.append(self._get_or_create_permission('虚拟机同步状态', 'pve_vm:sync_status', 'GET', r'/api/pve/virtual-machines/\\d+/sync_status/', menu_pve_vm))
        perms.append(self._get_or_create_permission('虚拟机全量同步', 'pve_vm:sync_all', 'POST', '/api/pve/virtual-machines/sync_all/', menu_pve_vm))

        self.stdout.write(self.style.SUCCESS(f'  ✓ 创建权限: {len(perms)} 个'))

        # 4. 创建角色
        self.stdout.write('创建角色...')
        role_admin = self._get_or_create_role('超级管理员', 'ADMIN', '拥有所有权限', 'ALL')
        role_admin.permissions.set(perms)
        role_admin.menus.set([
            # 顶级
            menu_dashboard, menu_system, menu_pve,
            # 系统管理
            menu_user, menu_role, menu_menu, menu_permission, menu_org, menu_system_setting,
            # 系统监控
            menu_monitor, menu_operation_log, menu_login_log, menu_tasks,
            # PVE管理
            menu_pve_server, menu_pve_vm, menu_pve_storage, menu_pve_node_monitor, menu_pve_templates, menu_pve_network, menu_pve_topology, menu_pve_lxc,
        ])
        role_admin.custom_data_organizations.set([org_root, org_admin])
        
        role_user = self._get_or_create_role('普通用户', 'USER', '普通用户角色', 'SELF')
        role_user.menus.set([menu_user])
        
        self.stdout.write(self.style.SUCCESS(f'  ✓ 创建角色: {role_admin.name}, {role_user.name}'))

        # 5. 处理超级用户
        self.stdout.write('处理超级用户...')
        superusers = User.objects.filter(is_superuser=True)
        
        if options['create_superuser'] and not superusers.exists():
            # 自动创建超级用户
            username = options['superuser_username']
            password = options['superuser_password']
            
            if User.objects.filter(username=username).exists():
                self.stdout.write(self.style.WARNING(f'  ⚠ 用户名 {username} 已存在，跳过创建'))
            else:
                user = User.objects.create_superuser(
                    username=username,
                    email=f'{username}@example.com',
                    password=password,
                )
                self.stdout.write(self.style.SUCCESS(f'  ✓ 创建超级用户: {username} (密码: {password})'))
                superusers = User.objects.filter(is_superuser=True)  # 重新获取
        
        if superusers.exists():
            for user in superusers:
                UserRole.objects.get_or_create(user=user, role=role_admin)
                # 如果没有主组织，分配根组织
                if not UserOrganization.objects.filter(user=user, is_primary=True).exists():
                    UserOrganization.objects.get_or_create(
                        user=user,
                        organization=org_root,
                        defaults={'is_primary': True}
                    )
            self.stdout.write(self.style.SUCCESS(f'  ✓ 为 {superusers.count()} 个超级用户分配了管理员角色'))
        else:
            self.stdout.write(self.style.WARNING('  ⚠ 未找到超级用户'))
            self.stdout.write(self.style.WARNING('  💡 提示：运行 "python manage.py createsuperuser" 创建超级用户'))
            self.stdout.write(self.style.WARNING('  💡 或运行 "python manage.py init_rbac --create-superuser" 自动创建'))

        self.stdout.write(self.style.SUCCESS('\n✅ RBAC 初始化完成！'))

    def _get_or_create_org(self, code, name, parent, order):
        org, created = Organization.objects.get_or_create(
            code=code,
            defaults={
                'name': name,
                'parent': parent,
                'order': order,
                'is_active': True,
            }
        )
        if not created:
            org.name = name
            org.parent = parent
            org.order = order
            org.save()
        return org

    def _get_or_create_menu(self, title, path, component, icon, parent, order):
        menu, created = Menu.objects.get_or_create(
            path=path,
            defaults={
                'title': title,
                'component': component,
                'icon': icon,
                'parent': parent,
                'order': order,
                'is_hidden': False,
            }
        )
        if not created and menu.component != component:
            # 仅同步组件路径（前端路由变更需要跟进）；
            # title / icon / parent / order 可能已被用户在界面上调整过，
            # 初始化命令每次容器启动都会执行，覆盖会丢失这些定制。
            menu.component = component
            menu.save(update_fields=['component'])
        return menu

    def _get_or_create_permission(self, name, code, http_method, url_pattern, menu):
        perm, created = Permission.objects.get_or_create(
            code=code,
            defaults={
                'name': name,
                'http_method': http_method,
                'url_pattern': url_pattern,
                'menu': menu,
                'is_active': True,
            }
        )
        if not created:
            perm.name = name
            perm.http_method = http_method
            perm.url_pattern = url_pattern
            perm.menu = menu
            perm.save()
        return perm

    def _get_or_create_role(self, name, code, description, data_scope):
        role, created = Role.objects.get_or_create(
            code=code,
            defaults={
                'name': name,
                'description': description,
                'data_scope': data_scope,
            }
        )
        if not created:
            role.name = name
            role.description = description
            role.data_scope = data_scope
            role.save()
        return role

