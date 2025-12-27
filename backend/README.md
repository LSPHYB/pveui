# Backend 项目说明文档

## 📋 项目概述

这是一个基于 **Django 5.2.8** + **Django REST Framework** + **Channels** 的后端服务，为 PVE（Proxmox Virtual Environment）管理系统提供 API 接口和 WebSocket 支持。

**项目名称**: `django_vue_adminx`  
**Python 版本**: 3.12+  
**主要功能**: PVE 服务器管理、虚拟机/容器管理、RBAC 权限控制、实时聊天、任务调度、操作审计

---

## 🏗️ 项目结构

```
backend/
├── django_vue_adminx/          # Django 主项目配置
│   ├── __init__.py
│   ├── settings.py             # 核心配置文件（数据库、中间件、应用等）
│   ├── urls.py                 # 主路由配置
│   ├── asgi.py                 # ASGI 配置（WebSocket 支持）
│   └── wsgi.py                 # WSGI 配置（HTTP 部署）
│
├── apps/                       # 业务应用模块
│   ├── pve/                    # PVE 管理模块
│   ├── rbac/                   # 权限控制模块
│   ├── audit/                  # 操作审计模块
│   ├── chat/                   # 实时聊天模块
│   ├── tasks/                  # 定时任务模块
│   ├── system/                 # 系统设置模块
│   └── common/                 # 公共工具模块
│
├── manage.py                   # Django 管理命令入口
├── requirements.txt            # Python 依赖清单
├── Dockerfile                  # Docker 镜像构建文件
├── run_daphne.sh              # Daphne ASGI 服务器启动脚本
├── fix_autobahn.sh            # Autobahn 兼容性修复脚本
└── db.sqlite3                  # SQLite 开发数据库（生产环境使用 MySQL）
```

---

## 🔧 核心技术栈

### 主要框架

| 技术 | 版本 | 用途 |
|------|------|------|
| Django | 5.2.8 | Web 框架 |
| Django REST Framework | 3.16.1 | RESTful API |
| Channels | 4.3.1 | WebSocket 支持 |
| Daphne | 4.2.1 | ASGI 服务器 |
| SimpleJWT | 5.3.1 | JWT 认证 |
| APScheduler | 3.11.1 | 定时任务调度 |
| MySQL Client | 2.2.4 | MySQL 数据库驱动 |

### 关键依赖

- **autobahn** (24.4.2): WebSocket 协议实现
- **Twisted** (25.5.0): 异步网络框架
- **django-cors-headers** (4.9.0): 跨域资源共享
- **django-filter** (25.2): API 过滤
- **psutil** (7.1.3): 系统资源监控
- **requests** (2.32.5): HTTP 客户端

---

## 📦 应用模块详解

### 1️⃣ PVE 模块 (`apps.pve`)

**功能**: Proxmox VE 服务器管理，虚拟机和容器的增删改查、状态控制、网络拓扑管理。

**核心模型**:
- `PVEServer`: PVE 服务器配置（主机、端口、Token 认证）
- `VirtualMachine`: 虚拟机信息（VMID、状态、资源配置）
- `LXCContainer`: LXC 容器信息
- `NetworkTopology`: 网络拓扑图数据（LogicFlow 格式）

**关键文件**:
- `pve_client.py`: PVE API 客户端封装（21KB，核心业务逻辑）
- `consumers.py`: WebSocket 消费者（实时状态推送）
- `views.py`: RESTful API 视图集（78KB，包含大量管理接口）
- `serializers.py`: 数据序列化器（11KB）

**路由前缀**: `/api/pve/`

---

### 2️⃣ RBAC 模块 (`apps.rbac`)

**功能**: 基于角色的访问控制（Role-Based Access Control），实现细粒度权限管理。

**核心模型**:
- `Menu`: 前端路由菜单（树形结构，控制页面可见性）
- `Permission`: 后端接口权限（HTTP 方法 + URL 匹配）
- `Role`: 角色（绑定权限和菜单，支持数据范围控制）
- `Organization`: 组织/部门（树形结构）
- `UserRole`: 用户-角色关联
- `UserOrganization`: 用户-组织关联（支持主组织标记）

**权限控制**:
- 页面级：通过 `Menu` 控制路由访问
- 接口级：通过 `Permission` + `RBACPermission` 类控制 API 调用
- 数据级：通过 `Role.data_scope` 控制数据可见范围（ALL/DEPT/DEPT_AND_SUB/SELF/CUSTOM）

**管理命令**:
- `python manage.py init_rbac`: 初始化权限数据
- `python manage.py init_rbac --create-superuser`: 创建超级管理员

**路由前缀**: `/api/rbac/`

---

### 3️⃣ Audit 模块 (`apps.audit`)

**功能**: 操作日志审计，记录所有用户操作行为。

**核心模型**:
- `OperationLog`: 操作日志（用户、时间、操作类型、请求信息、响应状态）

**操作类型**:
- `create`: 创建
- `update`: 更新
- `delete`: 删除
- `view`: 查看
- `list`: 列表查询
- `login`: 登录
- `logout`: 登出
- `other`: 其他

**中间件**:
- `OperationLogMiddleware`: 自动拦截 HTTP 请求并记录日志

**路由前缀**: `/api/audit/`

---

### 4️⃣ Chat 模块 (`apps.chat`)

**功能**: 员工间点对点实时聊天。

**核心模型**:
- `ChatMessage`: 聊天消息（发送者、接收者、内容、已读状态）

**WebSocket 支持**:
- `consumers.py`: WebSocket 消费者（实时消息推送）
- 路由: `ws/chat/`

**路由前缀**: `/api/chat/`

---

### 5️⃣ Tasks 模块 (`apps.tasks`)

**功能**: 定时任务调度（基于 APScheduler）。

**核心模型**:
- `Job`: 定时任务配置（Cron 表达式、调用目标、参数、状态）

**调度器**:
- `scheduler.py`: APScheduler 配置和任务管理
- `task.py`: 预定义任务函数

**路由前缀**: `/api/tasks/`

---

### 6️⃣ System 模块 (`apps.system`)

**功能**: 系统设置和配置管理。

**核心模型**:
- `SystemSetting`: 系统配置键值对（支持分类、加密、公开/私有）

**配置分类**:
- `ai`: AI 相关配置（OpenAI API Key 等）
- `email`: 邮件配置
- `storage`: 存储配置
- `general`: 通用配置

**路由前缀**: `/api/system/`

---

### 7️⃣ Common 模块 (`apps.common`)

**功能**: 公共工具和基础类。

**核心组件**:
- `BaseAuditModel`: 抽象基础模型（自动添加 created_at/updated_at）
- `JWTAuthMiddleware`: WebSocket JWT 认证中间件
- `mixins.py`: 视图集混入类
- `pagination.py`: 分页器
- `viewsets.py`: 自定义视图集基类

**路由前缀**: `/api/common/`

---

## ⚙️ 配置文件详解 (`settings.py`)

### 数据库配置

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.getenv('DB_NAME', 'pve'),
        'USER': os.getenv('DB_USER', 'pve'),
        'PASSWORD': os.getenv('DB_PASSWORD', 'root'),
        'HOST': os.getenv('DB_HOST', '106.55.160.167'),
        'PORT': os.getenv('DB_PORT', '3306'),
        'OPTIONS': {
            'charset': 'utf8mb4',
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}
```

**环境变量**:
- `DB_NAME`: 数据库名
- `DB_USER`: 数据库用户
- `DB_PASSWORD`: 数据库密码
- `DB_HOST`: 数据库主机
- `DB_PORT`: 数据库端口

---

### CORS 跨域配置

```python
CORS_ORIGIN_ALLOW_ALL = True  # 允许所有源（生产环境建议限制）
CORS_ALLOW_CREDENTIALS = True  # 允许携带 Cookie
CSRF_TRUSTED_ORIGINS = ['http://*', 'https://*']
```

---

### JWT 认证配置

```python
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=24),  # 访问令牌有效期 24 小时
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),   # 刷新令牌有效期 7 天
    'ROTATE_REFRESH_TOKENS': True,                 # 刷新时轮换令牌
    'BLACKLIST_AFTER_ROTATION': True,              # 旧令牌加入黑名单
    'ALGORITHM': 'HS256',                          # 加密算法
}
```

---

### WebSocket 配置（Channels）

```python
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer',  # 开发环境
    }
}

# 生产环境建议使用 Redis
# REDIS_URL = os.getenv('REDIS_URL', '')
# CHANNEL_LAYERS = {
#     'default': {
#         'BACKEND': 'channels_redis.core.RedisChannelLayer',
#         'CONFIG': {"hosts": [REDIS_URL]},
#     }
# }
```

---

### 反向代理/SSL 配置

```python
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_HOST = True
```

用于 Nginx 反向代理环境，让 Django 正确识别 HTTPS 请求。

---

## 🚀 部署指南

### 开发环境启动

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 数据库迁移
python manage.py makemigrations
python manage.py migrate

# 3. 初始化 RBAC 权限和超级用户
python manage.py init_rbac --create-superuser

# 4. 启动开发服务器（HTTP）
python manage.py runserver 0.0.0.0:8000

# 或启动 Daphne（支持 WebSocket）
daphne -b 0.0.0.0 -p 8000 django_vue_adminx.asgi:application
```

---

### 生产环境部署（Docker）

```bash
# 构建镜像
docker build -t pveui-backend .

# 运行容器
docker run -d \
  -p 8000:8000 \
  -e DB_HOST=mysql_host \
  -e DB_NAME=pve \
  -e DB_USER=pve \
  -e DB_PASSWORD=your_password \
  -e SECRET_KEY=your_secret_key \
  -e DEBUG=False \
  pveui-backend
```

**Dockerfile 说明**:
- 基础镜像: `python:3.12-slim`
- 自动执行: 数据库迁移、RBAC 初始化
- 启动命令: `gunicorn`（HTTP 部署）

**注意**: 如需 WebSocket 支持，需修改 `CMD` 为 `daphne` 启动命令。

---

### Nginx 反向代理配置示例

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # HTTP API 代理
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket 代理
    location /ws/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # 静态文件
    location /static/ {
        alias /path/to/backend/staticfiles/;
    }

    # 媒体文件
    location /media/ {
        alias /path/to/backend/media/;
    }
}
```

---

## 🔐 安全建议

### 生产环境必改配置

1. **SECRET_KEY**: 使用随机生成的密钥
   ```python
   SECRET_KEY = os.getenv('SECRET_KEY', 'your-secure-random-key')
   ```

2. **DEBUG**: 关闭调试模式
   ```python
   DEBUG = False
   ```

3. **ALLOWED_HOSTS**: 限制访问主机
   ```python
   ALLOWED_HOSTS = ['your-domain.com', 'www.your-domain.com']
   ```

4. **CORS_ORIGIN_ALLOW_ALL**: 限制跨域来源
   ```python
   CORS_ORIGIN_ALLOW_ALL = False
   CORS_ALLOWED_ORIGINS = [
       "https://your-frontend.com",
   ]
   ```

5. **数据库密码**: 使用强密码并通过环境变量配置

6. **SSL/HTTPS**: 生产环境启用 HTTPS
   ```python
   CSRF_COOKIE_SECURE = True
   SESSION_COOKIE_SECURE = True
   ```

---

## 📝 常用管理命令

```bash
# 创建超级用户
python manage.py createsuperuser

# 收集静态文件
python manage.py collectstatic

# 数据库迁移
python manage.py makemigrations
python manage.py migrate

# 初始化 RBAC 权限
python manage.py init_rbac

# 创建超级管理员（通过 RBAC）
python manage.py init_rbac --create-superuser

# 启动开发服务器
python manage.py runserver

# 启动 Shell
python manage.py shell
```

---

## 🐛 常见问题

### 1. MySQL 5.7 兼容性问题

**问题**: Django 5.x 默认不支持 MySQL 5.7  
**解决**: `settings.py` 中已添加 Monkey Patch

```python
from django.db.backends.mysql.base import DatabaseWrapper
DatabaseWrapper.check_database_version_supported = lambda self: None
```

---

### 2. Autobahn C 扩展问题

**问题**: Windows 环境下 Autobahn 的 C 扩展可能导致崩溃  
**解决**: 
- 方案 1: 运行 `fix_autobahn.sh` 脚本（Linux/Mac）
- 方案 2: `asgi.py` 中已禁用 C 扩展

```python
os.environ['AUTOBAHN_USE_UVLOOP'] = '0'
os.environ['TWISTED_REACTOR'] = 'asyncio'
```

---

### 3. WebSocket 连接失败

**检查清单**:
1. 确保使用 Daphne 启动（不是 `runserver`）
2. 检查 Nginx 配置是否正确代理 WebSocket
3. 验证前端使用 `ws://` 或 `wss://` 协议
4. 确认 JWT Token 正确传递（在 URL 或 header）

---

### 4. CORS 跨域错误

**原因**: 前后端不同源（协议/域名/端口不同）  
**解决**: 
- 开发环境: `CORS_ORIGIN_ALLOW_ALL = True`
- 生产环境: 配置 `CORS_ALLOWED_ORIGINS` 白名单

---

## 📚 API 文档

各模块 API 接口详情请参考各应用的 `views.py` 和 `urls.py` 文件。

**主要路由前缀**:
- `/api/rbac/` - 权限管理
- `/api/pve/` - PVE 管理
- `/api/audit/` - 操作日志
- `/api/chat/` - 聊天消息
- `/api/tasks/` - 定时任务
- `/api/system/` - 系统设置
- `/api/common/` - 公共接口

**WebSocket 路由**:
- `/ws/chat/` - 聊天 WebSocket
- `/ws/pve/` - PVE 状态推送 WebSocket

---

## 🔄 数据库迁移注意事项

### 修改模型后的步骤

```bash
# 1. 生成迁移文件
python manage.py makemigrations

# 2. 查看迁移 SQL（可选）
python manage.py sqlmigrate app_name migration_name

# 3. 执行迁移
python manage.py migrate

# 4. 回滚迁移（如需）
python manage.py migrate app_name migration_name
```

### 生产环境迁移建议

1. **备份数据库**: 迁移前务必备份数据库
2. **测试迁移**: 先在测试环境验证
3. **查看 SQL**: 使用 `sqlmigrate` 检查生成的 SQL
4. **分步迁移**: 大型迁移分多个小步骤
5. **维护窗口**: 在低峰期执行迁移

---

## 🧪 测试

```bash
# 运行所有测试
python manage.py test

# 运行特定应用测试
python manage.py test apps.pve

# 运行特定测试类
python manage.py test apps.pve.tests.PVETestCase
```

---

## 📊 性能优化建议

### 1. 数据库优化
- 使用 `select_related()` 和 `prefetch_related()` 减少查询次数
- 为常用查询字段添加索引（已在模型 `Meta.indexes` 中定义）
- 使用数据库连接池（如 `django-db-pool`）

### 2. 缓存配置
```python
# settings.py
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
    }
}
```

### 3. 异步任务
- 使用 Celery 处理耗时任务（如批量操作、邮件发送）
- 或使用当前的 APScheduler 进行定时任务

### 4. WebSocket 优化
- 生产环境使用 Redis Channel Layer（见 `settings.py`）
- 限制每个用户的连接数
- 实现心跳检测和自动重连

---

## 🛠️ 维护指南

### 日志管理

**位置**: Django 默认日志输出到控制台  
**配置**: 可在 `settings.py` 添加 `LOGGING` 配置

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '/var/log/django/debug.log',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
```

### 定期维护任务

1. **清理过期日志**: 定期清理 `OperationLog` 表中的旧数据
2. **数据库备份**: 每日备份 MySQL 数据库
3. **监控磁盘空间**: 监控 `/media` 和日志目录
4. **更新依赖**: 定期更新 `requirements.txt` 中的安全补丁

---

## 📞 技术支持

如有问题，请参考：
- Django 官方文档: https://docs.djangoproject.com/
- DRF 官方文档: https://www.django-rest-framework.org/
- Channels 官方文档: https://channels.readthedocs.io/

---

## 📄 许可证

（根据实际情况添加许可证信息）

---

**最后更新**: 2025-12-28  
**维护者**: Backend Development Team
