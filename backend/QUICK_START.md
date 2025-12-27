# 快速开始指南

## ⚡ 5 分钟快速启动

### 1. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 2. 配置数据库

**方式一：使用 MySQL（推荐）**

编辑环境变量或修改 `django_vue_adminx/settings.py`:

```env
DB_HOST=localhost
DB_NAME=pve
DB_USER=pve
DB_PASSWORD=your_password
DB_PORT=3306
```

**方式二：使用 SQLite（开发环境）**

修改 `settings.py` 中的 `DATABASES` 配置：

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
```

### 3. 初始化数据库

```bash
# 数据库迁移
python manage.py migrate

# 初始化 RBAC 权限系统并创建超级管理员
python manage.py init_rbac --create-superuser
```

**默认超级管理员账号**:
- 用户名: `admin`
- 密码: `admin123456`

### 4. 启动服务

**开发环境（仅 HTTP）**:
```bash
python manage.py runserver 0.0.0.0:8000
```

**生产环境（支持 WebSocket）**:
```bash
daphne -b 0.0.0.0 -p 8000 django_vue_adminx.asgi:application
```

或使用 Gunicorn（仅 HTTP）:
```bash
gunicorn --bind 0.0.0.0:8000 --workers 4 django_vue_adminx.wsgi:application
```

### 5. 访问测试

```bash
curl http://localhost:8000/api/rbac/login/ \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123456"}'
```

---

## 🐳 Docker 快速启动

```bash
# 构建镜像
docker build -t pveui-backend .

# 启动容器
docker run -d \
  -p 8000:8000 \
  -e DB_HOST=your_mysql_host \
  -e DB_NAME=pve \
  -e DB_USER=pve \
  -e DB_PASSWORD=your_password \
  --name pveui-backend \
  pveui-backend
```

---

## 📋 常用命令速查

### 数据库操作

```bash
# 创建迁移文件
python manage.py makemigrations

# 执行迁移
python manage.py migrate

# 回滚迁移
python manage.py migrate app_name migration_name

# 查看迁移状态
python manage.py showmigrations
```

### 用户管理

```bash
# 创建超级用户（Django 原生）
python manage.py createsuperuser

# 创建超级管理员（RBAC）
python manage.py init_rbac --create-superuser

# 进入 Django Shell
python manage.py shell
```

### 数据初始化

```bash
# 初始化 RBAC 权限
python manage.py init_rbac

# 收集静态文件
python manage.py collectstatic
```

---

## 🔧 开发调试技巧

### 1. 使用 Django Shell 测试代码

```bash
python manage.py shell
```

```python
# 导入模型
from apps.pve.models import PVEServer
from apps.rbac.models import User, Role

# 查询数据
servers = PVEServer.objects.all()
users = User.objects.filter(is_active=True)

# 创建数据
server = PVEServer.objects.create(
    name="Test PVE",
    host="192.168.1.100",
    port=8006,
    token_id="root@pam!test",
    token_secret="your-secret"
)
```

### 2. 查看 SQL 查询

```python
from django.db import connection

# 执行查询后
print(connection.queries)
```

### 3. 启用 DEBUG 模式查看详细错误

```python
# settings.py
DEBUG = True
```

### 4. 测试 API 接口

```bash
# 登录获取 Token
curl -X POST http://localhost:8000/api/rbac/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123456"}'

# 使用 Token 访问受保护接口
curl http://localhost:8000/api/pve/servers/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

---

## 🌐 API 接口速查

### 认证接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/rbac/login/` | 用户登录 |
| POST | `/api/rbac/logout/` | 用户登出 |
| POST | `/api/rbac/token/refresh/` | 刷新 Token |
| GET | `/api/rbac/userinfo/` | 获取当前用户信息 |

### PVE 管理接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/pve/servers/` | 获取 PVE 服务器列表 |
| POST | `/api/pve/servers/` | 创建 PVE 服务器 |
| GET | `/api/pve/servers/{id}/` | 获取服务器详情 |
| PUT | `/api/pve/servers/{id}/` | 更新服务器配置 |
| DELETE | `/api/pve/servers/{id}/` | 删除服务器 |
| GET | `/api/pve/vms/` | 获取虚拟机列表 |
| POST | `/api/pve/vms/{id}/start/` | 启动虚拟机 |
| POST | `/api/pve/vms/{id}/stop/` | 停止虚拟机 |
| POST | `/api/pve/vms/{id}/reboot/` | 重启虚拟机 |

### 权限管理接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/rbac/users/` | 获取用户列表 |
| POST | `/api/rbac/users/` | 创建用户 |
| GET | `/api/rbac/roles/` | 获取角色列表 |
| GET | `/api/rbac/permissions/` | 获取权限列表 |
| GET | `/api/rbac/menus/` | 获取菜单树 |
| GET | `/api/rbac/organizations/` | 获取组织树 |

### 其他接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/audit/logs/` | 操作日志列表 |
| GET | `/api/chat/messages/` | 聊天消息列表 |
| GET | `/api/tasks/jobs/` | 定时任务列表 |
| GET | `/api/system/settings/` | 系统设置列表 |

---

## 🔐 权限系统快速配置

### 1. 创建角色

```python
from apps.rbac.models import Role, Permission

# 创建角色
role = Role.objects.create(
    name="PVE 管理员",
    code="pve_admin",
    description="PVE 虚拟机管理员",
    data_scope="ALL"  # 数据范围：ALL/DEPT/DEPT_AND_SUB/SELF/CUSTOM
)

# 分配权限
permissions = Permission.objects.filter(code__startswith='pve')
role.permissions.add(*permissions)
```

### 2. 分配角色给用户

```python
from apps.rbac.models import UserRole
from django.contrib.auth.models import User

user = User.objects.get(username='admin')
role = Role.objects.get(code='pve_admin')

UserRole.objects.create(user=user, role=role)
```

### 3. 创建组织结构

```python
from apps.rbac.models import Organization

# 创建根组织
root = Organization.objects.create(
    name="总公司",
    code="root",
    order=0
)

# 创建子组织
dept = Organization.objects.create(
    name="技术部",
    code="tech",
    parent=root,
    order=1
)
```

---

## 🐛 常见错误及解决方案

### 错误 1: `ModuleNotFoundError: No module named 'MySQLdb'`

**解决**:
```bash
pip install mysqlclient
```

Windows 用户如安装失败，尝试：
```bash
pip install pymysql
```

然后在 `__init__.py` 添加：
```python
import pymysql
pymysql.install_as_MySQLdb()
```

---

### 错误 2: `django.db.utils.OperationalError: (2003, "Can't connect to MySQL server")`

**检查**:
1. MySQL 服务是否启动
2. 数据库配置是否正确（主机、端口、用户名、密码）
3. 防火墙是否阻止连接

---

### 错误 3: WebSocket 连接失败

**原因**: 使用 `runserver` 启动不支持 WebSocket

**解决**: 使用 Daphne 启动
```bash
daphne -b 0.0.0.0 -p 8000 django_vue_adminx.asgi:application
```

---

### 错误 4: `CSRF verification failed`

**原因**: 跨域请求缺少 CSRF Token

**解决方案 1**: 在请求头添加 Token
```javascript
headers: {
  'X-CSRFToken': getCookie('csrftoken')
}
```

**解决方案 2**: 使用 JWT 认证（推荐）
```javascript
headers: {
  'Authorization': `Bearer ${accessToken}`
}
```

---

## 📊 监控和日志

### 查看操作日志

```python
from apps.audit.models import OperationLog

# 查看最近 10 条日志
logs = OperationLog.objects.all()[:10]
for log in logs:
    print(f"{log.created_at} - {log.username} - {log.action_type} - {log.request_path}")
```

### 查看定时任务状态

```python
from apps.tasks.models import Job

jobs = Job.objects.filter(status=1)  # 1=启用
for job in jobs:
    print(f"{job.job_name} - Next: {job.next_valid_time}")
```

---

## 🎯 下一步

1. **配置前端**: 连接前端 Vue 应用
2. **配置 Nginx**: 设置反向代理
3. **配置 SSL**: 启用 HTTPS
4. **配置 Redis**: 用于 Channels 和缓存
5. **配置 Celery**: 处理异步任务（可选）
6. **设置监控**: 使用 Prometheus + Grafana
7. **配置日志**: 集中式日志管理

---

## 📚 更多文档

- [完整文档](./README.md)
- [Django 官方文档](https://docs.djangoproject.com/)
- [DRF 官方文档](https://www.django-rest-framework.org/)

---

**如有问题，请查阅完整文档或联系开发团队**
