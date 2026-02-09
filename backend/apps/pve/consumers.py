"""PVE控制台WebSocket代理：将浏览器的noVNC流量转发到PVE。"""

import asyncio
import json
import logging
import ssl
from urllib.parse import parse_qs

import websockets
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.core.cache import cache

from .models import VirtualMachine

logger = logging.getLogger(__name__)

SESSION_CACHE_PREFIX = "pve_console_session:"
SESSION_CACHE_TTL = 60  # 秒


class PVEConsoleConsumer(AsyncWebsocketConsumer):
    """代理浏览器与PVE之间的VNC WebSocket流量。"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.vm = None
        self.session_data = None
        self.pve_ws = None
        self.pve_to_client_task = None

    async def connect(self):
        self.user = self.scope.get("user")
        if not self.user or not self.user.is_authenticated:
            logger.warning("PVEConsoleConsumer: unauthenticated user, closing")
            await self.close()
            return

        self.vmid = self.scope["url_route"]["kwargs"].get("vm_id")
        token = self._get_query_token()
        if not token:
            logger.warning("PVEConsoleConsumer: missing token")
            await self.close()
            return

        cache_key = SESSION_CACHE_PREFIX + token
        session = cache.get(cache_key)
        cache.delete(cache_key)
        if not session:
            logger.warning("PVEConsoleConsumer: session not found or expired")
            await self.close()
            return

        websocket_url = session.get("websocket_url")
        if not websocket_url:
            logger.error("PVEConsoleConsumer: websocket_url missing in session data")
            await self.close()
            return

        vm = await self._get_vm()
        if not vm:
            logger.error("PVEConsoleConsumer: VM not found for id %s", self.vmid)
            await self.close()
            return

        tls_context = ssl.create_default_context()
        tls_context.check_hostname = False
        tls_context.verify_mode = ssl.CERT_NONE

        try:
            extra_headers = {}
            origin = session.get('origin')
            if origin:
                extra_headers['Origin'] = origin
            # 使用与REST相同的Token认证头，避免需要PVEAuthCookie
            if vm.server and vm.server.token_id and vm.server.token_secret:
                extra_headers['Authorization'] = f'PVEAPIToken={vm.server.token_id}={vm.server.token_secret}'

            self.pve_ws = await websockets.connect(
                websocket_url,
                ssl=tls_context,
                max_size=None,
                ping_interval=None,
                extra_headers=extra_headers or None,
                subprotocols=['binary'],
            )
        except Exception as e:
            logger.exception("PVEConsoleConsumer: failed to connect to PVE VNC websocket: %s", e)
            await self.close()
            return

        await self.accept()
        self.pve_to_client_task = asyncio.create_task(self._relay_from_pve())

    async def disconnect(self, close_code):
        if self.pve_to_client_task:
            self.pve_to_client_task.cancel()
        if self.pve_ws:
            try:
                await self.pve_ws.close()
            except Exception:
                pass
            self.pve_ws = None

    async def receive(self, text_data=None, bytes_data=None):
        if not self.pve_ws:
            return
        try:
            if bytes_data is not None:
                await self.pve_ws.send(bytes_data)
            elif text_data is not None:
                await self.pve_ws.send(text_data)
        except websockets.ConnectionClosed:
            logger.info("PVEConsoleConsumer: connection to PVE closed while sending, closing client ws")
            await self.close()

    async def _relay_from_pve(self):
        try:
            async for message in self.pve_ws:
                if isinstance(message, (bytes, bytearray)):
                    await self.send(bytes_data=message)
                else:
                    await self.send(text_data=message)
        except websockets.ConnectionClosed:
            logger.info("PVEConsoleConsumer: PVE websocket closed")
        finally:
            await self.close()

    def _get_query_token(self):
        query_string = self.scope.get("query_string", b"").decode()
        params = parse_qs(query_string)
        tokens = params.get("token")
        return tokens[0] if tokens else None

    @database_sync_to_async
    def _get_vm(self):
        try:
            return VirtualMachine.objects.select_related("server").get(pk=self.vmid)
        except VirtualMachine.DoesNotExist:
            return None


class LXCConsoleConsumer(AsyncWebsocketConsumer):
    """代理浏览器与PVE之间的LXC VNC WebSocket流量。"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.container = None
        self.session_data = None
        self.pve_ws = None
        self.pve_to_client_task = None

    async def connect(self):
        self.user = self.scope.get("user")
        if not self.user or not self.user.is_authenticated:
            logger.warning("LXCConsoleConsumer: unauthenticated user, closing")
            await self.close()
            return

        self.container_id = self.scope["url_route"]["kwargs"].get("container_id")
        token = self._get_query_token()
        if not token:
            logger.warning("LXCConsoleConsumer: missing token")
            await self.close()
            return

        cache_key = SESSION_CACHE_PREFIX + token
        session = cache.get(cache_key)
        cache.delete(cache_key)
        if not session:
            logger.warning("LXCConsoleConsumer: session not found or expired")
            await self.close()
            return

        websocket_url = session.get("websocket_url")
        if not websocket_url:
            logger.error("LXCConsoleConsumer: websocket_url missing in session data")
            await self.close()
            return

        container = await self._get_container()
        if not container:
            logger.error("LXCConsoleConsumer: Container not found for id %s", self.container_id)
            await self.close()
            return

        tls_context = ssl.create_default_context()
        tls_context.check_hostname = False
        tls_context.verify_mode = ssl.CERT_NONE

        try:
            extra_headers = {}
            origin = session.get('origin')
            if origin:
                extra_headers['Origin'] = origin
            # 使用与REST相同的Token认证头
            if container.server and container.server.token_id and container.server.token_secret:
                extra_headers['Authorization'] = f'PVEAPIToken={container.server.token_id}={container.server.token_secret}'

            logger.info(f'LXCConsoleConsumer: Connecting to {websocket_url}')
            
            self.pve_ws = await websockets.connect(
                websocket_url,
                ssl=tls_context,
                max_size=None,
                ping_interval=None,
                extra_headers=extra_headers or None,
                subprotocols=['binary'],
            )
            
            logger.info('LXCConsoleConsumer: Successfully connected to PVE WebSocket')
        except Exception as e:
            logger.exception("LXCConsoleConsumer: failed to connect to PVE VNC websocket: %s", e)
            await self.close()
            return

        await self.accept()
        self.pve_to_client_task = asyncio.create_task(self._relay_from_pve())
        logger.info('LXCConsoleConsumer: Client WebSocket accepted, relay task started')

    async def disconnect(self, close_code):
        logger.info(f'LXCConsoleConsumer: Disconnecting (code: {close_code})')
        if self.pve_to_client_task:
            self.pve_to_client_task.cancel()
        if self.pve_ws:
            try:
                await self.pve_ws.close()
            except Exception:
                pass
            self.pve_ws = None

    async def receive(self, text_data=None, bytes_data=None):
        if not self.pve_ws:
            return
        try:
            if bytes_data is not None:
                await self.pve_ws.send(bytes_data)
            elif text_data is not None:
                await self.pve_ws.send(text_data)
        except websockets.ConnectionClosed:
            logger.info("LXCConsoleConsumer: connection to PVE closed while sending, closing client ws")
            await self.close()

    async def _relay_from_pve(self):
        try:
            async for message in self.pve_ws:
                if isinstance(message, (bytes, bytearray)):
                    await self.send(bytes_data=message)
                else:
                    await self.send(text_data=message)
        except websockets.ConnectionClosed:
            logger.info("LXCConsoleConsumer: PVE websocket closed")
        except Exception as e:
            logger.exception(f"LXCConsoleConsumer: Error in relay: {e}")
        finally:
            await self.close()

    def _get_query_token(self):
        query_string = self.scope.get("query_string", b"").decode()
        params = parse_qs(query_string)
        tokens = params.get("token")
        return tokens[0] if tokens else None

    @database_sync_to_async
    def _get_container(self):
        from .models import LXCContainer
        try:
            return LXCContainer.objects.select_related("server").get(pk=self.container_id)
        except LXCContainer.DoesNotExist:
            return None


class SSHConsoleConsumer(AsyncWebsocketConsumer):
    """SSH 控制台 WebSocket Consumer"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ssh_conn = None
        self.ssh_process = None
        self.ssh_channel = None
        self.ssh_stdin = None
        self.ssh_stdout = None
        self.read_task = None
        self.container_id = None
        
    async def connect(self):
        """建立 WebSocket 连接"""
        # SSH Console 使用 session token 认证，不依赖 JWT 用户认证
        # 获取容器 ID 和 token
        self.container_id = self.scope['url_route']['kwargs'].get('container_id')
        token = self._get_query_token()
        
        if not token:
            logger.warning('SSHConsoleConsumer: 缺少 token')
            await self.close()
            return
        
        # 从缓存获取会话信息
        cache_key = f'ssh_console_session:{token}'
        session_data = cache.get(cache_key)
        
        if not session_data:
            logger.warning('SSHConsoleConsumer: 会话不存在或已过期')
            await self.close()
            return
        
        # 验证容器 ID 匹配
        if str(session_data.get('container_id')) != str(self.container_id):
            logger.warning('SSHConsoleConsumer: 容器 ID 不匹配')
            await self.close()
            return
        
        # 删除缓存（一次性使用）
        cache.delete(cache_key)
        
        # 接受 WebSocket 连接
        await self.accept()
        
        # 建立 SSH 连接
        try:
            ssh_host = session_data['host']
            ssh_port = session_data['port']
            ssh_username = session_data['username']
            
            # 获取容器密码（从数据库或配置）
            # 注意：生产环境建议使用 SSH 密钥而非密码
            ssh_password = await self._get_container_password(session_data['container_id'])
            
            if not ssh_password:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': '未配置容器 SSH 密码'
                }))
                await self.close()
                return
            
            # 尝试使用 asyncssh 连接
            try:
                import asyncssh
                
                self.ssh_conn = await asyncssh.connect(
                    ssh_host,
                    port=ssh_port,
                    username=ssh_username,
                    password=ssh_password,
                    known_hosts=None,  # 生产环境应配置 known_hosts
                )
                
                # 创建交互式 shell 进程
                # create_process 返回 SSHClientProcess 对象
                self.ssh_process = await self.ssh_conn.create_process(
                    term_type='xterm-256color',
                    term_size=(24, 80)  # (rows, cols)
                )
                
                # 保存 stdin 和 stdout
                self.ssh_stdin = self.ssh_process.stdin
                self.ssh_stdout = self.ssh_process.stdout
                self.ssh_channel = self.ssh_process  # 保存 process 对象
                
                # 启动读取任务
                self.read_task = asyncio.create_task(self._read_from_ssh())
                
                logger.info(f'SSH 连接建立成功: {ssh_host}')
                
            except ImportError:
                # 如果 asyncssh 不可用，尝试使用 paramiko
                logger.warning('asyncssh 不可用，尝试使用 paramiko')
                await self.send(text_data='提示: 正在使用 Paramiko 连接 (建议安装 asyncssh 以获得更好性能)\r\n\r\n')
                
                import paramiko
                from paramiko import SSHClient
                
                # 使用 paramiko (同步库，性能较差)
                ssh_client = SSHClient()
                ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh_client.connect(
                    hostname=ssh_host,
                    port=ssh_port,
                    username=ssh_username,
                    password=ssh_password,
                    timeout=10
                )
                
                # 创建交互式 shell
                channel = ssh_client.invoke_shell(term='xterm-256color', width=80, height=24)
                channel.settimeout(0.0)
                
                self.ssh_conn = ssh_client
                self.ssh_channel = channel
                
                # 启动读取任务（paramiko 需要特殊处理）
                self.read_task = asyncio.create_task(self._read_from_ssh_sync())
                
                logger.info(f'SSH 连接建立成功 (Paramiko): {ssh_host}')
            
        except Exception as e:
            logger.exception(f'SSH 连接失败: {e}')
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': f'SSH 连接失败: {str(e)}'
            }))
            await self.close()
    
    async def disconnect(self, close_code):
        """断开连接时清理资源"""
        if self.read_task:
            self.read_task.cancel()
        
        if self.ssh_channel:
            try:
                if hasattr(self.ssh_channel, 'close'):
                    self.ssh_channel.close()
            except Exception:
                pass
            
        if self.ssh_conn:
            try:
                if hasattr(self.ssh_conn, 'close'):
                    self.ssh_conn.close()
                if hasattr(self.ssh_conn, 'wait_closed'):
                    await self.ssh_conn.wait_closed()
            except Exception:
                pass
    
    async def receive(self, text_data=None, bytes_data=None):
        """接收前端消息"""
        if text_data:
            try:
                data = json.loads(text_data)
                msg_type = data.get('type')
                
                if msg_type == 'input':
                    # 用户输入
                    input_data = data.get('data', '')
                    if self.ssh_stdin:
                        # asyncssh - 使用 stdin 写入
                        self.ssh_stdin.write(input_data)
                    elif self.ssh_channel and hasattr(self.ssh_channel, 'send'):
                        # paramiko - 使用 channel.send
                        self.ssh_channel.send(input_data)
                        
                elif msg_type == 'resize':
                    # 终端大小调整
                    cols = data.get('cols', 80)
                    rows = data.get('rows', 24)
                    if self.ssh_process and hasattr(self.ssh_process, 'change_terminal_size'):
                        # asyncssh - 通过 process 对象调整
                        try:
                            self.ssh_process.change_terminal_size(cols, rows)
                        except Exception as e:
                            logger.warning(f'终端大小调整失败: {e}')
                    elif self.ssh_channel and hasattr(self.ssh_channel, 'resize_pty'):
                        # paramiko
                        self.ssh_channel.resize_pty(width=cols, height=rows)
                        
            except json.JSONDecodeError:
                logger.warning('SSHConsoleConsumer: 无效的 JSON 消息')
            except Exception as e:
                logger.exception(f'SSHConsoleConsumer: 处理消息失败: {e}')
    
    async def _read_from_ssh(self):
        """从 SSH 读取输出并发送到前端 (asyncssh)"""
        try:
            while True:
                # 使用 stdout 读取
                data = await self.ssh_stdout.read(4096)
                if not data:
                    break
                await self.send(text_data=data)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.exception(f'SSHConsoleConsumer: 读取 SSH 输出失败: {e}')
        finally:
            await self.close()
    
    async def _read_from_ssh_sync(self):
        """从 SSH 读取输出并发送到前端 (paramiko 同步版本)"""
        try:
            while True:
                if self.ssh_channel.recv_ready():
                    data = self.ssh_channel.recv(4096)
                    if data:
                        await self.send(text_data=data.decode('utf-8', errors='ignore'))
                else:
                    await asyncio.sleep(0.01)  # 避免 CPU 占用过高
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.exception(f'SSHConsoleConsumer: 读取 SSH 输出失败: {e}')
        finally:
            await self.close()
    
    def _get_query_token(self):
        """从查询字符串获取 token"""
        query_string = self.scope.get('query_string', b'').decode()
        params = parse_qs(query_string)
        tokens = params.get('token')
        return tokens[0] if tokens else None
    
    @database_sync_to_async
    def _get_container_password(self, container_id):
        """获取容器 SSH 密码（从数据库）"""
        from .models import LXCContainer
        try:
            container = LXCContainer.objects.get(id=container_id)
            # 从数据库 ssh_password 字段获取密码
            # 如果数据库中没有设置密码，可以返回 None 或默认值
            password = container.ssh_password
            if not password:
                # 如果数据库没有密码，可以从环境变量获取或返回 None
                import os
                password = os.getenv('LXC_DEFAULT_SSH_PASSWORD', '')
            return password if password else None
        except LXCContainer.DoesNotExist:
            return None
