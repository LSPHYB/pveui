# PVE-UI

基于 **Django 5 + Vue 3** 的 Proxmox VE 虚拟化管理与实验教学平台。

在 Web 端统一管理 PVE 集群的节点、虚拟机、LXC 容器、存储与网络拓扑，并在此之上叠加了 RBAC 权限、实验课程、AI 助手、操作审计与定时任务等模块。

## 功能模块

| 模块 | 子模块 | 说明 |
|---|---|---|
| **仪表盘** | — | 资源概览与统计图表 |
| **PVE 管理** | 节点监控、服务器管理、虚拟机、LXC 容器、存储、模板、网络、网络拓扑、拓扑管理、全局任务中心 | 对接 Proxmox VE，管理虚拟机与容器生命周期，noVNC 控制台，Cytoscape 网络拓扑编排 |
| **实验管理** | 实验管理（教师）、提交管理、我的实验（学生） | 面向教学：教师编排实验与批改提交，学生领取实验环境并提交作业 |
| **AI 助手管理** | 仪表盘、模型管理、API 管理、额度管理、智能体管理、知识库管理 | 对话式助手的模型接入、API Key、用量配额、智能体与知识库配置 |
| **系统管理** | 用户、角色、菜单、权限、组织、系统设置、监控概览、操作日志、登录日志、任务管理 | RBAC 三级权限（菜单/接口/数据）、组织树、审计日志与定时任务 |

底层能力：基于 Channels 的 WebSocket（PVE 状态推送、聊天）、APScheduler 定时调度、操作日志中间件。

## 技术栈

**后端**：Django 5.2 · Django REST Framework · Channels + Daphne · SimpleJWT · APScheduler · MySQL 8

**前端**：Vben Admin 5.5.9 monorepo（pnpm + Turborepo）· Vue 3 · Vite · Ant Design Vue · Pinia · Vue Router · ECharts · Cytoscape（网络拓扑）· xterm.js · noVNC

**编排**：Docker Compose 一体化部署（MySQL 8 + Django + Nginx），无需外部数据库

**其他**：MySQL MCP Server（`mysql-mcp-server/`，供 AI 助手访问数据库）

## 目录结构

```
.
├── vue-vben-admin/       前端 monorepo（Vben Admin 定制）
│   ├── apps/web-antd/      ★ 业务前端
│   │   └── src/              api · views（pve · ai · experiments · system · dashboard）· router · store · layouts
│   ├── packages/           Vben 框架包（access · layouts · request · stores 等）
│   ├── Dockerfile          多阶段构建（node 构建 → nginx 运行）
│   └── nginx.conf          SPA 回退 + /api 与 /ws 反向代理到后端
├── backend/              Django 后端（详见 backend/README.md）
│   ├── django_vue_adminx/  项目配置、路由、ASGI/WSGI
│   └── apps/               pve · rbac · audit · chat · experiments · tasks · system · common
├── mysql-mcp-server/     MySQL MCP Server（TypeScript）
├── pve.sql               数据库表结构（compose 首次启动自动导入）
└── docker-compose.yml    一键部署编排
```

## 快速开始

```bash
cp .env.example .env         # 填入 DB_PASSWORD、MYSQL_ROOT_PASSWORD、SECRET_KEY
docker compose up -d --build # MySQL + 后端 + 前端 :2208
```

前端为多阶段构建（容器内 `pnpm install && pnpm build:antd`），无需本地预先构建产物。
MySQL 首次启动会自动导入 `pve.sql` 建表，数据持久化在 `mysql-data` 卷中；
后端启动时自动执行 `init_rbac`，初始化菜单、权限、角色与超级管理员（已存在则跳过，不会重置密码）。

浏览器访问 `http://<主机>:2208`，默认账号 `admin` / `admin123`（可用 `.env` 中的 `ADMIN_USERNAME` / `ADMIN_PASSWORD` 指定）。

## 本地开发

环境要求：**Python 3.12+**、**Node.js 20.12+**、**pnpm 10+**

数据库直接复用编排里的 MySQL（已映射到 `127.0.0.1:3306`），不必单独安装：

```bash
cp .env.example .env
docker compose up -d mysql        # 只起数据库，首次会自动导入 pve.sql
```

```bash
# 后端
cd backend
pip install -r requirements.txt
set -a && source ../.env && set +a                     # 导出 DB_* 等变量
export DB_HOST=127.0.0.1
python manage.py init_rbac --create-superuser          # 初始化权限并创建超管（表由 pve.sql 建好）
daphne -b 0.0.0.0 -p 8000 django_vue_adminx.asgi:application

# 前端
cd vue-vben-admin
pnpm install && pnpm dev:antd                          # http://localhost:5666
```

后端必须用 Daphne（ASGI）启动，`runserver` 不支持 WebSocket，聊天与 PVE 状态推送会失效。

开发模式下前端不走 Nginx 反代，接口地址由 `apps/web-antd/.env.development` 的 `VITE_GLOB_API_URL` 指定，按需改成本机后端地址。

## 配置说明

所有配置集中在根目录 `.env`（由 `.env.example` 复制而来，已被 `.gitignore` 忽略，不要提交）：

| 变量 | 说明 |
|---|---|
| `DB_NAME` / `DB_USER` / `DB_PASSWORD` | 应用数据库名与凭据 |
| `MYSQL_ROOT_PASSWORD` | MySQL root 密码，仅容器内部使用 |
| `ADMIN_USERNAME` / `ADMIN_PASSWORD` | 初始超管账号，仅首次创建时生效 |
| `SECRET_KEY` | Django 密钥，**生产环境必须重新生成** |
| `DEBUG` | 调试模式，生产置为 `False` |
| `REDIS_URL` | 可选，配置后 Channels 使用 Redis Channel Layer |
| `BACKEND_PORT` / `FRONTEND_PORT` | 宿主机端口映射，默认 `8000` / `2208` |
| `MYSQL_PORT` | MySQL 映射端口，仅绑定 `127.0.0.1`，默认 `3306` |

`DB_HOST` / `DB_PORT` 由 compose 注入（容器内指向 `mysql` 服务），无需手动配置。数据库随编排一起启动，不依赖任何外部实例。

数据库结构见 `pve.sql`（41 张表，仅 DDL）。表结构变更后需重新导出，或提交对应的 Django migration。

生产环境还需收紧 `ALLOWED_HOSTS` 与 `CORS_ORIGIN_ALLOW_ALL`，详见 [`backend/README.md`](backend/README.md)。

## 注意事项

- **PVE API Token 权限**：创建 Token 时默认勾选了「特权分离」，必须取消勾选，否则接口只有受限权限。
