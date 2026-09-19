# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

PVE-UI：Django 5 + Vue 3（Vben Admin）的 Proxmox VE 虚拟化管理与实验教学平台。

环境搭建、`.env` 变量、Docker 编排、功能模块清单见 `README.md` 与 `backend/README.md`，此处不重复。下面只记那些需要跨多个文件才能看明白的东西。

## 常用命令

```bash
# 前端（工作目录 vue-vben-admin/）
pnpm dev:antd                        # 开发服务器 http://localhost:5666
pnpm build:antd                      # 生产构建
pnpm -F @vben/web-antd run typecheck # vue-tsc 类型检查（改完 TS 跑这个）
pnpm lint                            # vsh lint
pnpm format                          # 自动修复

# 后端（工作目录 backend/）
daphne -b 0.0.0.0 -p 8000 django_vue_adminx.asgi:application   # 必须 Daphne
python manage.py init_rbac --create-superuser                   # 初始化菜单/权限/角色/超管，幂等
```

**后端不能用 `python manage.py runserver`** —— 它不支持 ASGI，VNC/LXC/SSH 控制台和 PVE 状态推送会全部失效。本地起不来时先跑 `backend/run_daphne.sh`，它带了必需的 `AUTOBAHN_USE_UVLOOP=0` 和 `TWISTED_REACTOR=asyncio`。

**测试现状**：`backend/apps/*/tests.py` 全是 3 行 Django 样板，没有任何实际测试；`apps/web-antd` 也没有测试文件。根目录 `pnpm test:unit` 跑的是 Vben 上游自己的测试，与业务代码无关。不要假设改动有测试兜底。

## 架构要点

### 路由的真相源是数据库，不是代码

`preferences.ts` 硬编码 `accessMode: 'backend'`。在这个模式下 `generateRoutes` 直接用 `generateRoutesByBackend(options)` 覆盖结果，而后者只读 `fetchMenuListAsync` 和 `pageMap`，**从不读 `options.routes`**。

因此：

- `apps/web-antd/src/router/routes/modules/*.ts`（ai / dashboard / experiments / pve / system，共 278 行）**全部是死代码**，改它们不会有任何效果。
- 菜单和路由由 `rbac_menu` 表驱动，种子数据在 `seed-menu.sql`，运行时可在「系统管理 → 菜单」里改。
- 加页面的正确姿势：在 `src/views/` 下建 `.vue`，然后在菜单管理里加一条记录，`component` 填相对 `views/` 的路径（如 `system/user/index`）。
- `component` 填错时 `convertRoutes` 只 `console.error` 一句就 fallback 到 not-found 页，界面上只表现为空白，排查时先看控制台。

`src/api/core/menu.ts`（400 行）是 Django 菜单模型 → Vben 路由的适配器，前后端菜单模型的所有差异（图标名重映射、hidden 继承、父级 BasicLayout 推导）都收敛在这一个文件里。菜单显示异常先查这儿。

### 前端请求统一出口

`src/api/request.ts` 是唯一的 HTTP 出口：`requestClient`（注入 Bearer、401 → `refreshTokenApi` → 重试）和 `baseRequestClient`（免鉴权，登录/注册用）。约 24 个 API 模块都经过它。加拦截器、改鉴权、调超时都只动这里。

例外：`AiChatDrawer.vue` 绕开 requestClient 用原生 `fetch` 读 `ReadableStream` 消费流式回复——这是有意为之，不要"修正"成 requestClient。

### 后端 RBAC 是三级的

菜单权限 / 接口权限 / **数据范围**。前两级走常规 DRF 权限类，第三级的公共基座是 `backend/apps/common/data_mixins.py` 的 `DataScopeFilterMixin`，被 pve、system、tasks 的 ViewSet 继承。`backend/apps/common/models.py` 的 `BaseAuditModel` 提供审计字段与软删除。

**接口权限的 url_pattern 不支持裸正则。** `RBACPermission._url_pattern_to_regex`（`backend/apps/rbac/permissions.py`）对 pattern 做 `re.escape`，只把 `*` 还原成 `.*`、把 `{id}` 转成 `\d+`。所以 `init_rbac.py` 里大量写成 `\\d+` / `[^/]+` 的 pattern 会被整体转义，**永不匹配**。

配合 `has_permission` 里"无匹配记录则默认放行"的向后兼容分支，后果是：这些细粒度权限实际不生效，请求转而落到能匹配的粗粒度记录上（`/api/pve/servers/` 会因 `(?:/.*)?$` 吃掉所有子路径，于是 PVE 下的 POST 一律按「PVE服务器创建」鉴权）。**新增权限一律用 `{id}` 和 `*` 语法**，别照抄旧行的 `\\d+`。

新增业务 ViewSet 时照抄 `backend/apps/pve/views.py` 的 mixin 叠法（该文件 3229 行，是全项目最大文件，四个 ViewSet 统一叠三层 mixin）。

### WebSocket 链路

`django_vue_adminx/asgi.py` → `backend/apps/common/middleware.py` 的 `JWTAuthMiddleware`（scope 级鉴权）→ `backend/apps/pve/consumers.py`（VNC / LXC / SSH 三类控制台）。生产环境由 `vue-vben-admin/nginx.conf` 把 `/ws/` 反代过来，该文件用 `$http_host` 而非 `$host` 是为了保留端口，改动时别退回去。

### 数据库没有 Django migration

`backend/apps/*/migrations/` 下**只有 `__init__.py`**，一个迁移文件都没有。表结构的唯一来源是根目录 `pve.sql`（41 张表，纯 DDL，compose 首次启动时导入）。

改 model 后不要习惯性 `makemigrations` —— 需要同步手工更新 `pve.sql`，否则新部署建不出表。

### vue-vben-admin/packages/ 是 vendored 上游代码

整个 `vue-vben-admin/` 是 Vben Admin 5.5.9 的完整 monorepo，以普通目录（非 submodule）并入本仓库。`packages/`、`playground/`、`docs/`、`internal/` 历史上只被动过两次（其中一次是改网页标题），基本保持上游原样。

业务代码全部在 `apps/web-antd/`。改 `packages/` 会在升级 Vben 时丢失，需要定制时优先在 `apps/web-antd/src/adapter/` 里做适配。

## 几个看着像 bug 但不是的地方

- `asgi.py` 在导入 autobahn 之前往 `sys.modules` 注入伪模块，用来绕开 `_nvx_utf8validator` C 扩展。`requirements.txt` 里 autobahn 锁死 `24.4.2` 也是同一原因。别删。
- `apps/web-antd/.env.development` 的 `VITE_GLOB_API_URL` 直连 `http://localhost:8000/api`，生产环境的 `.env.production` 改成同源 `/api` 交给 Nginx 反代。两者不一致是设计如此。

## 已知问题（未修）

**定时任务模块目前是死的。** `TasksConfig.ready()`（`backend/apps/tasks/apps.py:12`）整段逻辑被一个守卫包着，要求 `RUN_MAIN` / `WERKZEUG_RUN_MAIN` / `DJANGO_MAIN_PROCESS` 三者之一为 `'true'`。但：

- `DJANGO_MAIN_PROCESS` 在全仓库只出现在这个 `if` 里，**没有任何地方设置它**（compose、`run_daphne.sh`、Dockerfile 都没有）
- `RUN_MAIN` 是 `runserver` 自动重载器专用的，而本项目用 Daphne 启动

`apps.py` 里的 `start_scheduler()` 是唯一调用点，`scheduler.py` 也没有别的自启动路径。所以在实际部署和文档给出的本地开发流程下，APScheduler 从不启动：用户在「任务管理」接口建的任务会存进库，但永远不会被执行。要启用得显式设 `DJANGO_MAIN_PROCESS=true`。

（原先这段守卫里还注册了每 30 秒把 admin 密码重置为 `admin123` 的 `reset_admin_password`，已删除。现在打开守卫只会启动正常的任务调度，不再有副作用。）

任务管理、系统设置、监控概览三个**前端页面已删除**，对应菜单由 `init_rbac` 的清理块从库中移除；后端 `apps/tasks`、`apps/system` 与相关表仍保留，接口可访问。

其他：

- `backend/Dockerfile` 的 `CMD` 是 `gunicorn ... wsgi:application`，被 `docker-compose.yml` 的 `command:` 覆盖成 daphne + ASGI。绕开 compose 直接 `docker run` 该镜像会让所有 WebSocket 功能静默失效。
- `store/auth.ts`、`router/guard.ts`、`router/access.ts` 残留较多 `console.log` 调试输出。

## 代码导航

本仓库已生成知识图谱（`.ua/knowledge-graph.json`，688 节点 / 1205 边 / 9 层）。查模块位置、调用关系、改动影响面时，用 `/understand-chat`、`/understand-explain`、`/understand-diff` 查询，比全仓库 grep 快得多。

不要直接读那个 JSON——660K，塞进上下文纯属浪费。

图谱钉在生成时的 commit 上，会过期；`.ua/` 已被 gitignore，是本地产物。代码有较多改动后跑 `/understand` 做增量更新。图谱不含 Vben 框架自身代码（`packages/` 等已排除）。
