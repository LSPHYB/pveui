"""通用中间件，包括 WebSocket JWT 认证中间件。"""

from urllib.parse import parse_qs
from channels.middleware import BaseMiddleware
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


class JWTAuthMiddleware(BaseMiddleware):
    """WebSocket JWT 认证中间件。"""

    async def __call__(self, scope, receive, send):
        # 只处理 WebSocket 连接
        if scope["type"] != "websocket":
            return await super().__call__(scope, receive, send)

        # SSH Console 使用自己的 session token 验证机制，跳过 JWT 验证
        path = scope.get("path", "")
        if "/ws/ssh/" in path:
            # SSH Console 会在 connect() 方法中验证 session token
            scope["user"] = AnonymousUser()  # 设置为匿名用户，由 Consumer 自己验证
            return await super().__call__(scope, receive, send)

        # 从查询参数或请求头获取 token
        token = self._get_token_from_scope(scope)
        
        if token:
            try:
                # 验证并解析 JWT token
                access_token = AccessToken(token)
                user_id = access_token.get('user_id')
                
                if user_id:
                    # 异步获取用户
                    user = await self.get_user(user_id)
                    scope["user"] = user
                else:
                    scope["user"] = AnonymousUser()
            except (InvalidToken, TokenError) as e:
                logger.warning(f"WebSocket JWT token 验证失败: {e}")
                scope["user"] = AnonymousUser()
            except Exception as e:
                logger.error(f"WebSocket JWT 认证出错: {e}")
                scope["user"] = AnonymousUser()
        else:
            scope["user"] = AnonymousUser()

        return await super().__call__(scope, receive, send)

    def _get_token_from_scope(self, scope):
        """从 WebSocket scope 中获取 JWT token。"""
        # 1. 从查询参数获取（用于 PVE console 和 SSH console）
        query_string = scope.get("query_string", b"").decode()
        if query_string:
            query_params = parse_qs(query_string)
            # 检查是否有 jwt_token 或 token 参数（兼容两种命名）
            jwt_tokens = query_params.get("jwt_token", [])
            if jwt_tokens:
                return jwt_tokens[0]
            # 如果没有 jwt_token，尝试 token 参数
            tokens = query_params.get("token", [])
            if tokens:
                return tokens[0]
        
        # 2. 从请求头获取 Authorization
        headers = dict(scope.get("headers", []))
        auth_header = headers.get(b"authorization", b"").decode()
        if auth_header:
            # 格式: "Bearer <token>"
            parts = auth_header.split()
            if len(parts) == 2 and parts[0].lower() == "bearer":
                return parts[1]
        
        return None

    @database_sync_to_async
    def get_user(self, user_id):
        """异步获取用户对象。"""
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return AnonymousUser()

