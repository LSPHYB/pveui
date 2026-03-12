"""RBAC 视图集。

提供各模型的标准 CRUD；支持过滤、搜索与排序。
默认权限使用 IsAuthenticated，如需匿名访问可在 settings 中调整 DRF 默认权限。
"""

from typing import Dict, List

from django.contrib.auth import authenticate, login, logout, get_user_model
from rest_framework import viewsets, permissions, filters, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django_filters.rest_framework import DjangoFilterBackend
from apps.common.pagination import LargePageSizePagination
from .models import Menu, Permission, Role, UserRole, Organization, UserOrganization, UserProfile

# ... (omitted imports)

class UserInfoView(APIView):
    """获取当前用户信息：基本信息、角色、权限、主组织、扩展信息。"""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):  # noqa: D401
        user = request.user
        role_qs = Role.objects.filter(user_roles__user=user).distinct()
        perm_qs = Permission.objects.filter(roles__in=role_qs, is_active=True).distinct()

        # 获取主组织
        primary_org = None
        try:
            uo = UserOrganization.objects.filter(user=user, is_primary=True).select_related('organization').first()
            if uo:
                primary_org = {
                    "id": uo.organization.id,
                    "name": uo.organization.name,
                    "code": uo.organization.code,
                }
        except Exception:
            pass

        # 获取扩展信息 (UserProfile)
        # 注意: signals保证了profile存在，但旧数据可能没有，这里做个防护
        profile = getattr(user, 'profile', None)
        avatar = None
        biography = ''
        if profile:
            if profile.avatar:
                try:
                    avatar = request.build_absolute_uri(profile.avatar.url)
                except Exception:
                    pass
            biography = profile.biography

        data = {
            "id": user.id,
            "username": getattr(user, 'username', ''),
            "email": getattr(user, 'email', ''),
            "first_name": getattr(user, 'first_name', ''),
            "last_name": getattr(user, 'last_name', ''),
            "is_superuser": user.is_superuser,
            "roles": list(role_qs.values('id', 'name', 'code')),
            "permissions": list(perm_qs.values_list('code', flat=True)),
            "primary_organization": primary_org,
            "avatar": avatar,
            "biography": biography,
        }
        return Response(data)

    def patch(self, request):
        """更新当前用户信息（支持基本资料、头像、简介）。"""
        user = request.user
        data = request.data
        
        # 1. 更新基本字段
        allowed_fields = ['first_name', 'last_name', 'email']
        has_user_change = False
        
        for field in allowed_fields:
            if field in data:
                setattr(user, field, data.get(field))
                has_user_change = True
                
        if has_user_change:
            user.save()

        # 2. 更新 UserProfile (biography)
        # 确保 profile 存在
        if not hasattr(user, 'profile'):
            UserProfile.objects.create(user=user)
            user.refresh_from_db()

        profile = user.profile
        has_profile_change = False

        if 'biography' in data:
            profile.biography = data.get('biography')
            has_profile_change = True
        
        # 3. 更新头像 (request.FILES)
        avatar_file = request.FILES.get('avatar')
        if avatar_file:
            profile.avatar = avatar_file
            has_profile_change = True
        
        if has_profile_change:
            profile.save()

        # 重新构建返回数据
        avatar_url = None
        if profile.avatar:
            try:
                avatar_url = request.build_absolute_uri(profile.avatar.url)
            except Exception:
                pass

        return Response({"detail": "更新成功", "user": {
            "id": user.id,
            "username": getattr(user, 'username', ''),
            "email": getattr(user, 'email', ''),
            "first_name": getattr(user, 'first_name', ''),
            "last_name": getattr(user, 'last_name', ''),
            "biography": profile.biography,
            "avatar": avatar_url,
        }})
import platform
import os
import time
try:
    import psutil  # type: ignore
except Exception:  # pragma: no cover
    psutil = None  # type: ignore

User = get_user_model()
from .serializers import (
    MenuSerializer,
    PermissionSerializer,
    RoleSerializer,
    UserRoleSerializer,
    OrganizationSerializer,
    UserOrganizationSerializer,
    UserSerializer,
    UserCreateSerializer,
    UserUpdateSerializer,
)
from apps.audit.models import OperationLog


class DefaultPermission(permissions.IsAuthenticated):
    """默认认证权限：要求登录（已弃用，现在使用全局 RBACPermission）。"""
    pass


class MenuViewSet(viewsets.ModelViewSet):
    """菜单 CRUD 与列表检索。列表接口返回树形结构。"""
    queryset = Menu.objects.all().order_by('order', 'id')
    serializer_class = MenuSerializer
    # 使用全局 RBACPermission（在 settings 中配置）
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['parent', 'is_hidden']
    search_fields = ['title', 'path', 'component']
    ordering_fields = ['order', 'id', 'title']

    def list(self, request, *args, **kwargs):
        """返回树形结构的菜单列表。"""
        # 获取所有菜单（应用过滤、搜索等）
        queryset = self.filter_queryset(self.get_queryset())
        menus = list(queryset.prefetch_related('children'))

        def to_node(m: Menu) -> Dict:
            """将菜单模型转换为树节点。"""
            return {
                "id": m.id,
                "title": m.title,
                "path": m.path,
                "component": m.component,
                "icon": m.icon,
                "order": m.order,
                "parent": m.parent_id,
                "is_hidden": m.is_hidden,
                "children": [],
            }

        # 构建节点映射
        node_map: Dict[int, Dict] = {m.id: to_node(m) for m in menus}
        roots: List[Dict] = []

        # 构建树形结构
        for m in menus:
            node = node_map[m.id]
            if m.parent_id and m.parent_id in node_map:
                node_map[m.parent_id]["children"].append(node)
            else:
                roots.append(node)

        def sort_tree(nodes: List[Dict]):
            """递归排序树节点。"""
            nodes.sort(key=lambda n: (n.get('order', 0), n.get('id', 0)))
            for n in nodes:
                sort_tree(n.get('children', []))

        sort_tree(roots)

        # 返回树形结构（不使用分页）
        return Response(roots)


class PermissionViewSet(viewsets.ModelViewSet):
    """权限 CRUD 与列表检索。"""
    queryset = Permission.objects.all().order_by('id')
    serializer_class = PermissionSerializer
    # 使用全局 RBACPermission（在 settings 中配置）
    pagination_class = LargePageSizePagination  # 使用支持大页面大小的分页器
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['http_method', 'menu', 'is_active']
    search_fields = ['name', 'code', 'url_pattern']
    ordering_fields = ['id', 'code', 'name']


class RoleViewSet(viewsets.ModelViewSet):
    """角色 CRUD 与列表检索，支持 data_scope 与自定义组织集合。"""
    queryset = Role.objects.all().order_by('id')
    serializer_class = RoleSerializer
    # 使用全局 RBACPermission（在 settings 中配置）
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['data_scope']
    search_fields = ['name', 'code']
    ordering_fields = ['id', 'name', 'code']


class UserRoleViewSet(viewsets.ModelViewSet):
    """用户-角色绑定 CRUD 与列表检索。"""
    queryset = UserRole.objects.all().order_by('-created_at')
    serializer_class = UserRoleSerializer
    permission_classes = [DefaultPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['user', 'role']
    search_fields = ['user__username', 'role__name']
    ordering_fields = ['created_at', 'id']


class OrganizationViewSet(viewsets.ModelViewSet):
    """组织 CRUD 与列表检索。"""
    queryset = Organization.objects.all().order_by('order', 'id')
    serializer_class = OrganizationSerializer
    # 使用全局 RBACPermission（在 settings 中配置）
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['parent', 'is_active']
    search_fields = ['name', 'code']
    ordering_fields = ['order', 'id', 'name']

    def list(self, request, *args, **kwargs):
        """返回树形结构的组织列表（与菜单一致，不分页）。"""
        queryset = self.filter_queryset(self.get_queryset())
        orgs = list(queryset)

        def to_node(o: Organization) -> Dict:
            return {
                "id": o.id,
                "name": o.name,
                "code": o.code,
                "order": o.order,
                "is_active": o.is_active,
                "parent": o.parent_id,
                "leader": o.leader_id if getattr(o, 'leader_id', None) else None,
                "children": [],
            }

        node_map: Dict[int, Dict] = {o.id: to_node(o) for o in orgs}
        roots: List[Dict] = []

        for o in orgs:
            node = node_map[o.id]
            if o.parent_id and o.parent_id in node_map:
                node_map[o.parent_id]["children"].append(node)
            else:
                roots.append(node)

        def sort_tree(nodes: List[Dict]):
            nodes.sort(key=lambda n: (n.get('order', 0), n.get('id', 0)))
            for n in nodes:
                sort_tree(n.get('children', []))

        sort_tree(roots)

        return Response(roots)


class UserOrganizationViewSet(viewsets.ModelViewSet):
    """用户-组织绑定 CRUD 与列表检索。"""
    queryset = UserOrganization.objects.all().order_by('-created_at')
    serializer_class = UserOrganizationSerializer
    permission_classes = [DefaultPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['user', 'organization', 'is_primary']
    search_fields = ['user__username', 'organization__name']
    ordering_fields = ['created_at', 'id']


class UserViewSet(viewsets.ModelViewSet):
    """用户 CRUD 与列表检索。支持数据权限过滤。"""
    queryset = User.objects.all().order_by('-id')
    # 使用全局 RBACPermission（在 settings 中配置）
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active', 'is_staff', 'is_superuser']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering_fields = ['id', 'username', 'date_joined']

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        return UserSerializer

    def get_queryset(self):
        """用户视图的数据权限过滤：基于用户所属的组织。"""
        queryset = super(viewsets.ModelViewSet, self).get_queryset()
        user = self.request.user

        # 超级用户拥有所有数据权限
        if user.is_superuser:
            return queryset

        # 获取用户的所有角色及其数据权限
        from .models import Role
        user_roles = Role.objects.filter(user_roles__user=user).select_related().prefetch_related('custom_data_organizations')
        
        if not user_roles.exists():
            # 没有角色，只返回自己
            return queryset.filter(id=user.id)

        # 获取最宽泛的数据权限
        data_scope, custom_orgs = self._get_broadest_data_scope(user_roles)
        
        # 根据数据权限范围过滤（用户视图基于用户所属组织）
        if data_scope == 'ALL':
            return queryset
        elif data_scope == 'SELF':
            return queryset.filter(id=user.id)
        elif data_scope == 'DEPT':
            return self._filter_users_by_dept(queryset, user)
        elif data_scope == 'DEPT_AND_SUB':
            return self._filter_users_by_dept_and_sub(queryset, user)
        elif data_scope == 'CUSTOM':
            return self._filter_users_by_custom(queryset, custom_orgs)
        else:
            # 默认只返回自己
            return queryset.filter(id=user.id)

    def _filter_users_by_dept(self, queryset, user):
        """过滤：本部门的用户。"""
        primary_org = self._get_user_primary_org(user)
        if not primary_org:
            return queryset.filter(id=user.id)
        
        # 获取属于该组织的所有用户
        from .models import UserOrganization
        user_ids = UserOrganization.objects.filter(organization=primary_org).values_list('user_id', flat=True)
        return queryset.filter(id__in=user_ids)

    def _filter_users_by_dept_and_sub(self, queryset, user):
        """过滤：本部门及其子部门的用户。"""
        primary_org = self._get_user_primary_org(user)
        if not primary_org:
            return queryset.filter(id=user.id)
        
        # 获取主组织及其所有子组织的ID
        org_ids = self._get_org_and_children_ids(primary_org)
        
        # 获取属于这些组织的所有用户
        from .models import UserOrganization
        user_ids = UserOrganization.objects.filter(organization_id__in=org_ids).values_list('user_id', flat=True)
        return queryset.filter(id__in=user_ids)

    def _filter_users_by_custom(self, queryset, custom_orgs):
        """过滤：自定义组织的用户。"""
        if not custom_orgs:
            return queryset.none()
        
        org_ids = [org.id for org in custom_orgs]
        from .models import UserOrganization
        user_ids = UserOrganization.objects.filter(organization_id__in=org_ids).values_list('user_id', flat=True)
        return queryset.filter(id__in=user_ids)

    def _get_user_primary_org(self, user):
        """获取用户的主组织。"""
        from .models import UserOrganization
        try:
            uo = UserOrganization.objects.filter(user=user, is_primary=True).select_related('organization').first()
            if uo:
                return uo.organization
        except Exception:
            pass
        return None

    def _get_org_and_children_ids(self, org):
        """获取组织及其所有子组织的ID列表（递归）。"""
        from .models import Organization
        org_ids = [org.id]
        
        def get_children(organization):
            """递归获取子组织。"""
            children = Organization.objects.filter(parent=organization)
            for child in children:
                org_ids.append(child.id)
                get_children(child)
        
        get_children(org)
        return org_ids

    def _get_broadest_data_scope(self, roles):
        """获取最宽泛的数据权限范围。"""
        from .models import Organization
        priority_map = {
            'ALL': 5,
            'DEPT_AND_SUB': 4,
            'DEPT': 3,
            'CUSTOM': 2,
            'SELF': 1,
        }
        
        max_priority = 0
        broadest_scope = 'SELF'
        custom_orgs = []
        
        for role in roles:
            priority = priority_map.get(role.data_scope, 0)
            if priority > max_priority:
                max_priority = priority
                broadest_scope = role.data_scope
        
        if broadest_scope == 'CUSTOM':
            custom_org_ids = set()
            for role in roles:
                if role.data_scope == 'CUSTOM':
                    custom_org_ids.update(role.custom_data_organizations.values_list('id', flat=True))
            custom_orgs = list(Organization.objects.filter(id__in=custom_org_ids))
        
        return broadest_scope, custom_orgs


class LoginView(APIView):
    """登录接口：JWT 认证。"""

    permission_classes = [permissions.AllowAny]

    def post(self, request):  # noqa: D401
        username = request.data.get('username')
        password = request.data.get('password')
        if not username or not password:
            # 记录登录失败日志（参数缺失）
            try:
                OperationLog.objects.create(
                    user=None,
                    username=username or '',
                    action_type=OperationLog.ACTION_LOGIN,
                    request_path=request.path,
                    request_method='POST',
                    request_params={'body': {'username': username or '', 'password': '***'}},
                    ip_address=request.META.get('REMOTE_ADDR', ''),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
                    status_code=status.HTTP_400_BAD_REQUEST,
                    error_message='用户名或密码不能为空',
                )
            except Exception:
                pass
            return Response({"detail": "用户名或密码不能为空"}, status=status.HTTP_400_BAD_REQUEST)
        user = authenticate(request, username=username, password=password)
        if user is None:
            # 记录登录失败日志（认证失败）
            try:
                OperationLog.objects.create(
                    user=None,
                    username=username or '',
                    action_type=OperationLog.ACTION_LOGIN,
                    request_path=request.path,
                    request_method='POST',
                    request_params={'body': {'username': username or '', 'password': '***'}},
                    ip_address=request.META.get('REMOTE_ADDR', ''),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
                    status_code=status.HTTP_400_BAD_REQUEST,
                    error_message='用户名或密码错误',
                )
            except Exception:
                pass
            return Response({"detail": "用户名或密码错误"}, status=status.HTTP_400_BAD_REQUEST)
        if not user.is_active:
            # 记录登录失败日志（未启用）
            try:
                OperationLog.objects.create(
                    user=user,
                    username=getattr(user, 'username', '') or username or '',
                    action_type=OperationLog.ACTION_LOGIN,
                    request_path=request.path,
                    request_method='POST',
                    request_params={'body': {'username': username or '', 'password': '***'}},
                    ip_address=request.META.get('REMOTE_ADDR', ''),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
                    status_code=status.HTTP_403_FORBIDDEN,
                    error_message='用户未启用',
                )
            except Exception:
                pass
            return Response({"detail": "用户未启用"}, status=status.HTTP_403_FORBIDDEN)

        # 生成JWT token
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        # 记录登录成功日志
        try:
            OperationLog.objects.create(
                user=user,
                username=getattr(user, 'username', '') or username or '',
                action_type=OperationLog.ACTION_LOGIN,
                request_path=request.path,
                request_method='POST',
                request_params={'body': {'username': username or '', 'password': '***'}},
                ip_address=request.META.get('REMOTE_ADDR', ''),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
                status_code=status.HTTP_200_OK,
                error_message='',
            )
        except Exception:
            pass

        role_qs = Role.objects.filter(user_roles__user=user).distinct()
        perm_qs = Permission.objects.filter(roles__in=role_qs, is_active=True).distinct()
        data = {
            "id": user.id,
            "username": getattr(user, 'username', ''),
            "roles": list(role_qs.values_list('code', flat=True)),
            "permissions": list(perm_qs.values_list('code', flat=True)),
            "access": access_token,
            "refresh": refresh_token,
        }
        return Response(data)


class LogoutView(APIView):
    """退出登录接口：JWT 认证（将 refresh token 加入黑名单）。"""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):  # noqa: D401
        user = request.user if (hasattr(request, 'user') and request.user.is_authenticated) else None
        username = getattr(user, 'username', '') if user else ''
        
        # JWT 认证：将 refresh token 加入黑名单
        try:
            refresh_token = request.data.get('refresh')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
        except Exception:
            # 如果黑名单功能未启用或token无效，忽略错误
            pass
        
        # 记录登出日志
        try:
            OperationLog.objects.create(
                user=user,
                username=username,
                action_type=OperationLog.ACTION_LOGOUT,
                request_path=request.path,
                request_method='POST',
                request_params={},
                ip_address=request.META.get('REMOTE_ADDR', ''),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
                status_code=status.HTTP_200_OK,
                error_message='',
            )
        except Exception:
            pass
        return Response({"detail": "退出成功"})





class CheckPermissionView(APIView):
    """权限检查接口：用于前端按钮级权限控制。

    Request JSON: { "code": "permission_code" }
    Response JSON: { "has_permission": true/false }
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):  # noqa: D401
        code = request.data.get('code')
        if not code:
            return Response({"detail": "权限编码不能为空"}, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        if user.is_superuser:
            return Response({"has_permission": True})

        role_qs = Role.objects.filter(user_roles__user=user).distinct()
        has_perm = Permission.objects.filter(
            code=code,
            roles__in=role_qs,
            is_active=True
        ).exists()

        return Response({"has_permission": has_perm})


class ChangePasswordView(APIView):
    """修改密码接口。

    Request JSON: { "old_password": "...", "new_password": "..." }
    Response JSON: { "detail": "修改成功" }
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):  # noqa: D401
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')

        if not old_password or not new_password:
            return Response({"detail": "旧密码和新密码不能为空"}, status=status.HTTP_400_BAD_REQUEST)

        if len(new_password) < 6:
            return Response({"detail": "新密码长度至少6位"}, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        if not user.check_password(old_password):
            return Response({"detail": "旧密码错误"}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()

        return Response({"detail": "密码修改成功"})


class UserPermissionsView(APIView):
    """获取当前用户所有权限列表（包含权限详情）。"""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):  # noqa: D401
        user = request.user
        if user.is_superuser:
            permissions_list = list(
                Permission.objects.filter(is_active=True).values('id', 'name', 'code', 'http_method', 'url_pattern')
            )
        else:
            role_qs = Role.objects.filter(user_roles__user=user).distinct()
            permissions_list = list(
                Permission.objects.filter(roles__in=role_qs, is_active=True).distinct()
                .values('id', 'name', 'code', 'http_method', 'url_pattern')
            )

        return Response({"permissions": permissions_list})


class UserOrganizationsView(APIView):
    """获取当前用户所属组织信息（包含主组织标记）。"""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):  # noqa: D401
        user = request.user
        uo_list = UserOrganization.objects.filter(user=user).select_related('organization').order_by('-is_primary', 'created_at')

        organizations = []
        primary_org = None
        for uo in uo_list:
            org_data = {
                "id": uo.organization.id,
                "name": uo.organization.name,
                "code": uo.organization.code,
                "is_primary": uo.is_primary,
                "created_at": uo.created_at.isoformat() if uo.created_at else None,
            }
            organizations.append(org_data)
            if uo.is_primary:
                primary_org = org_data

        return Response({
            "organizations": organizations,
            "primary_organization": primary_org,
        })


class OrganizationTreeView(APIView):
    """获取组织树（用于前端组织选择器）。

    可选参数：only_active (bool) - 仅返回启用组织
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):  # noqa: D401
        only_active = request.query_params.get('only_active', 'false').lower() == 'true'
        qs = Organization.objects.all()
        if only_active:
            qs = qs.filter(is_active=True)
        orgs = list(qs.order_by('order', 'id'))

        def to_node(o: Organization) -> Dict:
            return {
                "id": o.id,
                "name": o.name,
                "code": o.code,
                "order": o.order,
                "is_active": o.is_active,
                "parent": o.parent_id,
                "leader_id": o.leader_id if o.leader else None,
                "children": [],
            }

        node_map: Dict[int, Dict] = {o.id: to_node(o) for o in orgs}
        roots: List[Dict] = []
        for o in orgs:
            node = node_map[o.id]
            if o.parent_id and o.parent_id in node_map:
                node_map[o.parent_id]["children"].append(node)
            else:
                roots.append(node)

        def sort_tree(nodes: List[Dict]):
            nodes.sort(key=lambda n: (n.get('order', 0), n.get('id', 0)))
            for n in nodes:
                sort_tree(n.get('children', []))

        sort_tree(roots)
        return Response(roots)


class MenuTreeView(APIView):
    """返回当前用户可见的菜单树。"""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):  # noqa: D401
        user = request.user
        if user.is_superuser:
            menus = list(Menu.objects.filter(is_hidden=False).order_by('order', 'id'))
        else:
            role_qs = Role.objects.filter(user_roles__user=user).distinct()
            menus = list(
                Menu.objects.filter(roles__in=role_qs, is_hidden=False).distinct().order_by('order', 'id')
            )

        def to_node(m: Menu) -> Dict:
            return {
                "id": m.id,
                "title": m.title,
                "path": m.path,
                "component": m.component,
                "icon": m.icon,
                "order": m.order,
                "parent": m.parent_id,
                "children": [],
            }

        node_map: Dict[int, Dict] = {m.id: to_node(m) for m in menus}
        roots: List[Dict] = []
        for m in menus:
            node = node_map[m.id]
            if m.parent_id and m.parent_id in node_map:
                node_map[m.parent_id]["children"].append(node)
            else:
                roots.append(node)

        def sort_tree(nodes: List[Dict]):
            nodes.sort(key=lambda n: (n.get('order', 0), n.get('id', 0)))
            for n in nodes:
                sort_tree(n.get('children', []))

        sort_tree(roots)
        return Response(roots)


class SystemMetricsView(APIView):
    """系统监控指标：CPU、内存、磁盘、启动时间等。"""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):  # noqa: D401
        if psutil is None:
            return Response({
                "detail": "psutil 未安装，请先安装依赖：pip install psutil"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        try:
            boot_ts = psutil.boot_time()
            uptime = int(time.time() - boot_ts)

            cpu = {
                "count_logical": psutil.cpu_count(logical=True),
                "count_physical": psutil.cpu_count(logical=False),
                "percent": psutil.cpu_percent(interval=0.2),
                "load_avg": os.getloadavg() if hasattr(os, 'getloadavg') else None,
            }

            vm = psutil.virtual_memory()
            mem = {
                "total": vm.total,
                "available": vm.available,
                "used": vm.used,
                "free": vm.free,
                "percent": vm.percent,
            }

            sm = psutil.swap_memory()
            swap = {
                "total": sm.total,
                "used": sm.used,
                "free": sm.free,
                "percent": sm.percent,
            }

            disks = []
            for part in psutil.disk_partitions(all=False):
                try:
                    du = psutil.disk_usage(part.mountpoint)
                    disks.append({
                        "device": part.device,
                        "mountpoint": part.mountpoint,
                        "fstype": part.fstype,
                        "total": du.total,
                        "used": du.used,
                        "free": du.free,
                        "percent": du.percent,
                    })
                except Exception:
                    pass

            net = {}
            try:
                ni = psutil.net_io_counters()
                net = {
                    "bytes_sent": ni.bytes_sent,
                    "bytes_recv": ni.bytes_recv,
                    "packets_sent": ni.packets_sent,
                    "packets_recv": ni.packets_recv,
                }
            except Exception:
                net = {}

            data = {
                "platform": {
                    "system": platform.system(),
                    "release": platform.release(),
                    "version": platform.version(),
                    "python": platform.python_version(),
                    "machine": platform.machine(),
                    "processor": platform.processor(),
                },
                "uptime_seconds": uptime,
                "cpu": cpu,
                "memory": mem,
                "swap": swap,
                "disks": disks,
                "network": net,
            }

            return Response(data)
        except Exception as e:
            return Response({"detail": f"metrics 采集失败: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DashboardView(APIView):
    """仪表盘数据：统计概览、最近操作、系统状态等。"""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):  # noqa: D401
        """获取仪表盘数据。"""
        from django.utils import timezone
        from datetime import timedelta
        from django.db.models import Count, Q
        from apps.audit.models import OperationLog
        from apps.tasks.models import Job
        
        # 1. 统计概览
        stats = {
            'users': User.objects.filter(is_active=True).count(),
            'roles': Role.objects.count(),  # Role 模型没有 is_active 字段
            'menus': Menu.objects.filter(is_hidden=False).count(),
            'permissions': Permission.objects.filter(is_active=True).count(),
            'organizations': Organization.objects.filter(is_active=True).count(),
            'operation_logs': OperationLog.objects.count(),
            'tasks': Job.objects.count(),
            'active_tasks': Job.objects.filter(status=1).count(),
        }

        # 2. 最近操作日志（最近 10 条）
        recent_logs = OperationLog.objects.select_related('user', 'content_type').order_by('-created_at')[:10]
        recent_logs_data = []
        for log in recent_logs:
            recent_logs_data.append({
                'id': log.id,
                'username': log.username or log.user.username if log.user else '匿名',
                'action_type': log.action_type,
                'action_type_display': log.get_action_type_display(),
                'request_path': log.request_path,
                'request_method': log.request_method,
                'status_code': log.status_code,
                'created_at': log.created_at.isoformat() if log.created_at else None,
            })

        # 3. 操作类型统计（最近 7 天）
        seven_days_ago = timezone.now() - timedelta(days=7)
        action_stats = OperationLog.objects.filter(
            created_at__gte=seven_days_ago
        ).values('action_type').annotate(count=Count('id')).order_by('-count')
        action_stats_data = {
            item['action_type']: item['count'] for item in action_stats
        }

        # 4. 每日操作统计（最近 7 天，用于图表）
        daily_stats = []
        for i in range(6, -1, -1):  # 从 6 天前到今天
            day_start = (timezone.now() - timedelta(days=i)).replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(days=1)
            count = OperationLog.objects.filter(
                created_at__gte=day_start,
                created_at__lt=day_end
            ).count()
            daily_stats.append({
                'date': day_start.strftime('%Y-%m-%d'),
                'count': count,
            })

        # 5. 最近登录用户（最近 7 天有操作的用户）
        recent_users = User.objects.filter(
            operation_logs__created_at__gte=seven_days_ago
        ).distinct().annotate(
            log_count=Count('operation_logs', filter=Q(operation_logs__created_at__gte=seven_days_ago))
        ).order_by('-log_count')[:10]
        recent_users_data = []
        for user in recent_users:
            recent_users_data.append({
                'id': user.id,
                'username': user.username,
                'email': getattr(user, 'email', ''),
                'log_count': user.log_count,
            })

        # 6. 系统状态（简化版，避免重复调用 SystemMetricsView）
        system_status = {}
        try:
            if psutil:
                cpu_percent = psutil.cpu_percent(interval=0.1)
                mem = psutil.virtual_memory()
                system_status = {
                    'cpu_percent': round(cpu_percent, 1),
                    'memory_percent': round(mem.percent, 1),
                    'memory_used_gb': round(mem.used / (1024 ** 3), 2),
                    'memory_total_gb': round(mem.total / (1024 ** 3), 2),
                }
        except Exception:
            pass

        # 7. 错误操作统计（状态码 >= 400）
        error_count = OperationLog.objects.filter(
            created_at__gte=seven_days_ago,
            status_code__gte=400
        ).count()

        # 8. 最活跃的 API 路径（最近 7 天）
        top_paths = OperationLog.objects.filter(
            created_at__gte=seven_days_ago
        ).values('request_path').annotate(count=Count('id')).order_by('-count')[:10]
        top_paths_data = [
            {'path': item['request_path'], 'count': item['count']}
            for item in top_paths
        ]

        data = {
            'stats': stats,
            'recent_logs': recent_logs_data,
            'action_stats': action_stats_data,
            'daily_stats': daily_stats,
            'recent_users': recent_users_data,
            'system_status': system_status,
            'error_count': error_count,
            'top_paths': top_paths_data,
        }
        return Response(data)

class RegisterView(APIView):
    """用户自注册接口：无需登录，创建账号后自动赋予默认学生角色。

    Request JSON: { "username": "...", "password": "..." }
    Response JSON: { "detail": "注册成功，请登录" }
    """

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        username = request.data.get('username', '').strip()
        password = request.data.get('password', '')

        # 基础校验
        if not username or not password:
            return Response({'detail': '用户名和密码不能为空'}, status=status.HTTP_400_BAD_REQUEST)

        if len(username) < 3:
            return Response({'detail': '用户名至少3个字符'}, status=status.HTTP_400_BAD_REQUEST)

        if len(password) < 6:
            return Response({'detail': '密码长度至少6位'}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(username=username).exists():
            return Response({'detail': '用户名已被注册，请换一个'}, status=status.HTTP_400_BAD_REQUEST)

        # 创建用户
        user = User.objects.create_user(username=username, password=password)
        user.is_active = True
        user.save()

        # 自动赋予"学生"角色（code='student'，找不到则跳过）
        try:
            from .models import Role, UserRole
            student_role = Role.objects.filter(code='student').first()
            if student_role:
                UserRole.objects.get_or_create(user=user, role=student_role)
        except Exception:
            pass

        return Response({'detail': '注册成功，请登录'}, status=status.HTTP_201_CREATED)
