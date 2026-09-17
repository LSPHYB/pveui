-- 菜单初始化数据
--
-- 原导出未包含 id 列，而 parent_id 用的是原库真实 id（2/4/80/90），
-- 在空表上直接执行会把子菜单挂到错误的父级，或因外键不存在而失败。
-- 这里改为按父菜单 path 关联，与自增 id 无关，可在任意空库上重放。
--
-- 重复执行安全：已存在同 path 的菜单会跳过，不覆盖已有配置。

-- 必须显式声明：docker-entrypoint-initdb.d 执行 SQL 时客户端字符集默认非 utf8mb4，
-- 缺少这行会让中文标题被 latin1 二次编码，前端读到乱码。
SET NAMES utf8mb4;

-- 顶级菜单
INSERT INTO rbac_menu (title, `path`, component, icon, `order`, is_hidden, parent_id)
SELECT * FROM (
  SELECT '仪表盘' AS title, 'dashboard' AS `path`, 'dashboard/index' AS component, 'ant-design:dashboard-twotone' AS icon, 0 AS `order`, 0 AS is_hidden, NULL AS parent_id
  UNION ALL SELECT '系统管理', 'system', '', 'icon-settings', 4, 0, NULL
  UNION ALL SELECT 'PVE管理', 'pve', '', 'icon-apps', 1, 0, NULL
  UNION ALL SELECT '实验管理', 'experiments', '', 'ant-design:experiment-outlined', 2, 0, NULL
  UNION ALL SELECT 'AI助手管理', 'ai', '', 'ant-design:robot-outlined', 3, 0, NULL
) AS t
WHERE NOT EXISTS (SELECT 1 FROM rbac_menu m WHERE m.`path` = t.`path`);

-- 子菜单：按父菜单 path 关联
INSERT INTO rbac_menu (title, `path`, component, icon, `order`, is_hidden, parent_id)
SELECT '用户管理', 'user', 'system/user/index', 'icon-user', 1, 0, m.id FROM rbac_menu m
WHERE m.`path` = 'system'
  AND NOT EXISTS (SELECT 1 FROM rbac_menu x WHERE x.`path` = 'user');
INSERT INTO rbac_menu (title, `path`, component, icon, `order`, is_hidden, parent_id)
SELECT '角色管理', 'role', 'system/role/index', 'icon-idcard', 2, 0, m.id FROM rbac_menu m
WHERE m.`path` = 'system'
  AND NOT EXISTS (SELECT 1 FROM rbac_menu x WHERE x.`path` = 'role');
INSERT INTO rbac_menu (title, `path`, component, icon, `order`, is_hidden, parent_id)
SELECT '菜单管理', 'menu', 'system/menu/index', 'ant-design:menu-outlined', 3, 0, m.id FROM rbac_menu m
WHERE m.`path` = 'system'
  AND NOT EXISTS (SELECT 1 FROM rbac_menu x WHERE x.`path` = 'menu');
INSERT INTO rbac_menu (title, `path`, component, icon, `order`, is_hidden, parent_id)
SELECT '权限管理', 'permission', 'system/permission/index', 'ant-design:property-safety-twotone', 4, 0, m.id FROM rbac_menu m
WHERE m.`path` = 'system'
  AND NOT EXISTS (SELECT 1 FROM rbac_menu x WHERE x.`path` = 'permission');
INSERT INTO rbac_menu (title, `path`, component, icon, `order`, is_hidden, parent_id)
SELECT '组织管理', 'organization', 'system/organization/index', 'icon-apps', 5, 0, m.id FROM rbac_menu m
WHERE m.`path` = 'system'
  AND NOT EXISTS (SELECT 1 FROM rbac_menu x WHERE x.`path` = 'organization');
INSERT INTO rbac_menu (title, `path`, component, icon, `order`, is_hidden, parent_id)
SELECT '操作日志', 'operation-log', 'system/operation-log/index', 'icon-file', 7, 0, m.id FROM rbac_menu m
WHERE m.`path` = 'system'
  AND NOT EXISTS (SELECT 1 FROM rbac_menu x WHERE x.`path` = 'operation-log');
INSERT INTO rbac_menu (title, `path`, component, icon, `order`, is_hidden, parent_id)
SELECT '登录日志', 'login-log', 'system/login-log/index', 'icon-user', 6, 0, m.id FROM rbac_menu m
WHERE m.`path` = 'system'
  AND NOT EXISTS (SELECT 1 FROM rbac_menu x WHERE x.`path` = 'login-log');
INSERT INTO rbac_menu (title, `path`, component, icon, `order`, is_hidden, parent_id)
SELECT 'PVE服务器管理', 'pve-server', 'pve/server/index', 'ant-design:hdd-filled', 1, 0, m.id FROM rbac_menu m
WHERE m.`path` = 'pve'
  AND NOT EXISTS (SELECT 1 FROM rbac_menu x WHERE x.`path` = 'pve-server');
INSERT INTO rbac_menu (title, `path`, component, icon, `order`, is_hidden, parent_id)
SELECT '虚拟机管理', 'pve-vm', 'pve/vm/index', 'icon-desktop', 2, 0, m.id FROM rbac_menu m
WHERE m.`path` = 'pve'
  AND NOT EXISTS (SELECT 1 FROM rbac_menu x WHERE x.`path` = 'pve-vm');
INSERT INTO rbac_menu (title, `path`, component, icon, `order`, is_hidden, parent_id)
SELECT '存储管理', 'pve-storage', 'pve/storage/index', 'ant-design:code-sandbox-outlined', 3, 0, m.id FROM rbac_menu m
WHERE m.`path` = 'pve'
  AND NOT EXISTS (SELECT 1 FROM rbac_menu x WHERE x.`path` = 'pve-storage');
INSERT INTO rbac_menu (title, `path`, component, icon, `order`, is_hidden, parent_id)
SELECT 'PVE节点监控', 'pve-node-monitor', 'pve/node-monitor/index', 'icon-bar-chart', 0, 0, m.id FROM rbac_menu m
WHERE m.`path` = 'pve'
  AND NOT EXISTS (SELECT 1 FROM rbac_menu x WHERE x.`path` = 'pve-node-monitor');
INSERT INTO rbac_menu (title, `path`, component, icon, `order`, is_hidden, parent_id)
SELECT '模板管理', 'pve-templates', 'pve/templates/index', 'icon-file', 6, 0, m.id FROM rbac_menu m
WHERE m.`path` = 'pve'
  AND NOT EXISTS (SELECT 1 FROM rbac_menu x WHERE x.`path` = 'pve-templates');
INSERT INTO rbac_menu (title, `path`, component, icon, `order`, is_hidden, parent_id)
SELECT '网络管理', 'pve-network', 'pve/network/index', 'icon-link', 7, 0, m.id FROM rbac_menu m
WHERE m.`path` = 'pve'
  AND NOT EXISTS (SELECT 1 FROM rbac_menu x WHERE x.`path` = 'pve-network');
INSERT INTO rbac_menu (title, `path`, component, icon, `order`, is_hidden, parent_id)
SELECT '网络拓扑', 'pve-topology', 'pve/topology/index', 'icon-share-alt', 8, 0, m.id FROM rbac_menu m
WHERE m.`path` = 'pve'
  AND NOT EXISTS (SELECT 1 FROM rbac_menu x WHERE x.`path` = 'pve-topology');
INSERT INTO rbac_menu (title, `path`, component, icon, `order`, is_hidden, parent_id)
SELECT 'LXC容器管理', 'pve-lxc', 'pve/lxc/index', 'icon-apps', 10, 0, m.id FROM rbac_menu m
WHERE m.`path` = 'pve'
  AND NOT EXISTS (SELECT 1 FROM rbac_menu x WHERE x.`path` = 'pve-lxc');
INSERT INTO rbac_menu (title, `path`, component, icon, `order`, is_hidden, parent_id)
SELECT '实验管理', 'teacher', 'experiments/teacher/index', 'ant-design:unordered-list-outlined', 0, 0, m.id FROM rbac_menu m
WHERE m.`path` = 'experiments'
  AND NOT EXISTS (SELECT 1 FROM rbac_menu x WHERE x.`path` = 'teacher');
INSERT INTO rbac_menu (title, `path`, component, icon, `order`, is_hidden, parent_id)
SELECT '提交管理', 'teacher/submissions', 'experiments/teacher/SubmissionList', 'ant-design:check-square-outlined', 1, 0, m.id FROM rbac_menu m
WHERE m.`path` = 'experiments'
  AND NOT EXISTS (SELECT 1 FROM rbac_menu x WHERE x.`path` = 'teacher/submissions');
INSERT INTO rbac_menu (title, `path`, component, icon, `order`, is_hidden, parent_id)
SELECT '我的实验', 'student', 'experiments/student/index', 'ant-design:home-filled', 2, 0, m.id FROM rbac_menu m
WHERE m.`path` = 'experiments'
  AND NOT EXISTS (SELECT 1 FROM rbac_menu x WHERE x.`path` = 'student');
INSERT INTO rbac_menu (title, `path`, component, icon, `order`, is_hidden, parent_id)
SELECT '模型管理', 'models', 'ai/models/index', 'ant-design:android-outlined', 1, 0, m.id FROM rbac_menu m
WHERE m.`path` = 'ai'
  AND NOT EXISTS (SELECT 1 FROM rbac_menu x WHERE x.`path` = 'models');
INSERT INTO rbac_menu (title, `path`, component, icon, `order`, is_hidden, parent_id)
SELECT 'API管理', 'api-keys', 'ai/api-keys/index', 'ant-design:key-outlined', 2, 0, m.id FROM rbac_menu m
WHERE m.`path` = 'ai'
  AND NOT EXISTS (SELECT 1 FROM rbac_menu x WHERE x.`path` = 'api-keys');
INSERT INTO rbac_menu (title, `path`, component, icon, `order`, is_hidden, parent_id)
SELECT '额度管理', 'quotas', 'ai/quotas/index', 'ant-design:dot-chart-outlined', 3, 0, m.id FROM rbac_menu m
WHERE m.`path` = 'ai'
  AND NOT EXISTS (SELECT 1 FROM rbac_menu x WHERE x.`path` = 'quotas');
INSERT INTO rbac_menu (title, `path`, component, icon, `order`, is_hidden, parent_id)
SELECT '智能体管理', 'agents', 'ai/agents/index', 'ant-design:robot-filled', 4, 0, m.id FROM rbac_menu m
WHERE m.`path` = 'ai'
  AND NOT EXISTS (SELECT 1 FROM rbac_menu x WHERE x.`path` = 'agents');
INSERT INTO rbac_menu (title, `path`, component, icon, `order`, is_hidden, parent_id)
SELECT '知识库管理', 'knowledge', 'ai/knowledge/index', 'ant-design:book-outlined', 6, 0, m.id FROM rbac_menu m
WHERE m.`path` = 'ai'
  AND NOT EXISTS (SELECT 1 FROM rbac_menu x WHERE x.`path` = 'knowledge');
INSERT INTO rbac_menu (title, `path`, component, icon, `order`, is_hidden, parent_id)
SELECT '仪表盘', 'AIdashboard', 'ai/dashboard/index', 'ant-design:dashboard-outlined', 0, 0, m.id FROM rbac_menu m
WHERE m.`path` = 'ai'
  AND NOT EXISTS (SELECT 1 FROM rbac_menu x WHERE x.`path` = 'AIdashboard');
INSERT INTO rbac_menu (title, `path`, component, icon, `order`, is_hidden, parent_id)
SELECT '拓补管理', 'topology-manage', 'pve/topology-manage/index', 'ant-design:kubernetes-outlined', 9, 0, m.id FROM rbac_menu m
WHERE m.`path` = 'pve'
  AND NOT EXISTS (SELECT 1 FROM rbac_menu x WHERE x.`path` = 'topology-manage');
