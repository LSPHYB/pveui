<script setup lang="ts">
import { onMounted, ref } from 'vue';

import { IconifyIcon } from '@vben/icons';

import {
  DownOutlined,
  DragOutlined,
  PlusOutlined,
  ReloadOutlined,
  SyncOutlined,
} from '@ant-design/icons-vue';
import {
  Button,
  Card,
  message,
  Popconfirm,
  Space,
  Tag,
  Tree,
} from 'ant-design-vue';

import { deleteMenu, getMenuList, updateMenu } from '#/api/menu';

import MenuDrawer from './menu-drawer.vue';

defineOptions({
  name: 'SystemMenu',
});

const loading = ref(false);
const treeData = ref<any[]>([]);
const drawerVisible = ref(false);
const currentRecord = ref<any>(null);
const expandedKeys = ref<number[]>([]);

// Helper to handle legacy icon names for display
const getIcon = (icon?: string) => {
  if (!icon) return '';
  if (icon.includes(':')) return icon;

  if (icon.startsWith('icon-')) {
    const name = icon.replace('icon-', '');
    if (name === 'dashboard') return 'ant-design:dashboard-outlined';
    if (name === 'settings') return 'ant-design:setting-outlined';
    if (name === 'apps') return 'ant-design:appstore-outlined';
    if (name === 'user') return 'ant-design:user-outlined';
    return `ant-design:${name}-outlined`;
  }
  return icon;
};

// 获取菜单的实际隐藏状态（考虑父菜单的影响）
// 如果父菜单被隐藏，子菜单也应该显示为隐藏状态
const getActualHiddenStatus = (menu: any, allMenusFlat: any[]): boolean => {
  // 如果菜单本身被隐藏，直接返回true
  if (menu.hidden || menu.is_hidden) {
    return true;
  }

  // 如果没有父菜单，返回自身的状态
  if (!menu.parent) {
    return false;
  }

  // 递归检查父菜单的状态
  const parent = allMenusFlat.find((m) => m.id === menu.parent);
  if (!parent) {
    return false;
  }

  // 如果父菜单被隐藏，则返回true
  return getActualHiddenStatus(parent, allMenusFlat);
};

// 存储平铺的菜单列表，用于查找父菜单
const allMenusFlat = ref<any[]>([]);

const fetchData = async () => {
  loading.value = true;
  try {
    // 使用 getMenuList 获取平铺列表，而不是 getMenuTreeApi
    // 这样可以确保所有菜单记录都能获取到，包括隐藏的父菜单
    const res: any = await getMenuList({ page_size: 1000 });

    let menuList: any[] = [];
    if (Array.isArray(res)) {
      menuList = res;
    } else if (res?.results) {
      menuList = res.results;
    } else if (res?.data) {
      menuList = Array.isArray(res.data) ? res.data : res.data?.results || [];
    }

    console.log('获取到的菜单列表:', menuList);

    // 存储平铺的菜单列表，用于计算级联隐藏状态
    allMenusFlat.value = menuList;

    // 在前端构建树形结构
    const buildTree = (items: any[], parentId: null | number = null): any[] => {
      const result: any[] = [];

      items
        .filter((item) => {
          // parent为null或0都视为顶级菜单
          const itemParent = item.parent === 0 ? null : item.parent;
          return itemParent === parentId;
        })
        .forEach((item) => {
          const node = { ...item };
          node.key = node.id;

          // 递归构建子菜单
          const children = buildTree(items, item.id);
          if (children.length > 0) {
            node.children = children;
          }

          result.push(node);
        });

      // 按 order 字段排序
      result.sort((a, b) => (a.order || 0) - (b.order || 0));

      return result;
    };

    const treeStructure = buildTree(menuList, null);
    console.log('构建的树形结构:', treeStructure);

    treeData.value = treeStructure;

    // Default expand all
    const keys: number[] = [];
    const collectKeys = (list: any[]) => {
      list.forEach((item) => {
        keys.push(item.id);
        if (item.children) collectKeys(item.children);
      });
    };
    collectKeys(treeStructure);
    expandedKeys.value = keys;
  } catch (error) {
    console.error('菜单管理页面 - 获取菜单失败:', error);
    message.error('获取菜单失败');
    treeData.value = [];
  } finally {
    loading.value = false;
  }
};

const handleCreate = () => {
  currentRecord.value = null;
  drawerVisible.value = true;
};

const handleEdit = (record: any) => {
  currentRecord.value = { ...record };
  drawerVisible.value = true;
};

const handleDelete = async (id: number) => {
  try {
    await deleteMenu(id);
    message.success('删除成功');
    fetchData();
  } catch {
    message.error('删除失败');
  }
};

const handleSuccess = () => {
  fetchData();
};

const onDrop = async (info: any) => {
  const dropKey = info.node.key;
  const dragKey = info.dragNode.key;
  const dropPos = info.node.pos.split('-');
  const dropPosition = info.dropPosition - Number(dropPos[dropPos.length - 1]);

  const dropNode = info.node;
  const dragNode = info.dragNode;

  // Determine new parent and order
  let parentId: null | number = null;
  let order = 0;

  // Drop on the node (become child)
  if (info.dropToGap) {
    // Drop before or after (become sibling)
    // Find the parent of the drop target
    // API doesn't give parent info directly in node, need to find in data?
    // Actually typically we rely on reloading, but we need ID to update.

    // If dropped at top level, parentId is null.
    // We need to traverse data to find parent of dropKey?
    // Or we can infer from the data structure if we had a flat map.
    // For now, let's look at the `dataRef` or similar prop if available, or search tree.
    const findParent = (data: any[], key: number, parent: any = null): any => {
      for (const item of data) {
        if (item.id === key) return parent;
        if (item.children) {
          const res = findParent(item.children, key, item);
          if (res !== undefined) return res;
        }
      }
      return undefined;
    };

    const parent = findParent(treeData.value, dropKey);
    parentId = parent ? parent.id : null;

    // Simple order logic: use the drop target's order, or +1
    // Since backend might not support float order, we just make a best effort update
    // Real implementation would batch update siblings.
    // Here we just notify the backend of the parent change and let it append or use provided order.
    // We'll trust the user to reorder precisely if needed.
    order = dropNode.order || 0;
  } else {
    parentId = dropKey;
    order = 0; // First child or append
  }

  try {
    // Optimistic UI update could happen here, but we'll reload.
    await updateMenu(dragKey, {
      parent: parentId,
      order,
      title: dragNode.title, // API requires required fields usually
      path: dragNode.path,
      // ... other fields might be needed if updateMenu is full-replace
      // Assuming partial update is supported or we fetch full data
      ...dragNode.dataRef, // merge original data
    });
    message.success('移动成功');
    fetchData();
  } catch (error) {
    message.error('拖拽调整失败');
    console.error(error);
  }
};

// 同步级联隐藏状态 - 将应该级联隐藏的菜单在数据库中也更新为隐藏
const syncCascadeHiddenStatus = async () => {
  try {
    loading.value = true;

    // 获取所有菜单
    if (allMenusFlat.value.length === 0) {
      message.warning('请先加载菜单数据');
      return;
    }

    const updates: Array<{
      currentHidden: boolean;
      id: number;
      shouldHide: boolean;
      title: string;
    }> = [];

    // 检查每个菜单的实际隐藏状态和数据库状态是否一致
    for (const menu of allMenusFlat.value) {
      const actualHidden = getActualHiddenStatus(menu, allMenusFlat.value);
      const dbHidden = menu.is_hidden || menu.hidden || false;

      // 如果实际应该隐藏但数据库中是显示的，添加到更新列表
      if (actualHidden && !dbHidden) {
        updates.push({
          id: menu.id,
          title: menu.title,
          shouldHide: true,
          currentHidden: dbHidden,
        });
      }
      // 如果实际应该显示但数据库中是隐藏的（父菜单已显示），也更新
      else if (!actualHidden && dbHidden && !menu.parent) {
        // 只更新顶级菜单，子菜单由父菜单决定
        updates.push({
          id: menu.id,
          title: menu.title,
          shouldHide: false,
          currentHidden: dbHidden,
        });
      }
    }

    if (updates.length === 0) {
      message.success('菜单隐藏状态已同步，无需更新');
      return;
    }

    console.log('需要同步的菜单:', updates);

    // 批量更新
    let successCount = 0;
    let failCount = 0;

    for (const update of updates) {
      try {
        const menu = allMenusFlat.value.find((m) => m.id === update.id);
        if (menu) {
          await updateMenu(update.id, {
            ...menu,
            is_hidden: update.shouldHide,
          });
          successCount++;
          console.log(
            `同步菜单 "${update.title}": ${update.shouldHide ? '隐藏' : '显示'}`,
          );
        }
      } catch (error) {
        failCount++;
        console.error(`同步菜单 "${update.title}" 失败:`, error);
      }
    }

    if (successCount > 0) {
      message.success(
        `成功同步 ${successCount} 个菜单的隐藏状态${failCount > 0 ? `，${failCount} 个失败` : ''}`,
      );
      // 重新加载数据
      await fetchData();
    } else {
      message.error('同步失败');
    }
  } catch (error) {
    console.error('同步级联隐藏状态失败:', error);
    message.error('同步失败');
  } finally {
    loading.value = false;
  }
};

onMounted(() => {
  fetchData();
});
</script>

<template>
  <div class="p-4">
    <Card title="菜单管理">
      <template #extra>
        <Space>
          <Button type="primary" @click="handleCreate">
            <template #icon><PlusOutlined /></template>
            新增菜单
          </Button>
          <Button
            @click="syncCascadeHiddenStatus"
            :loading="loading"
            type="dashed"
          >
            <template #icon><SyncOutlined /></template>
            同步级联状态
          </Button>
          <Button @click="fetchData" :loading="loading">
            <template #icon><ReloadOutlined /></template>
            刷新
          </Button>
        </Space>
      </template>

      <!-- Fake Table Header -->
      <div
        class="flex items-center border-b border-gray-200 bg-gray-50 p-3 text-sm font-medium text-gray-700"
      >
        <div class="flex-1 pl-8">菜单名称</div>
        <div class="w-32 text-center">图标</div>
        <div class="w-20 text-center">排序</div>
        <div class="w-48">路由路径</div>
        <div class="w-48">组件路径</div>
        <div class="w-24 text-center">状态</div>
        <div class="w-40 text-center">操作</div>
      </div>

      <Tree
        v-if="treeData.length > 0"
        class="dragging-tree w-full"
        :tree-packet="treeData"
        :tree-data="treeData"
        :field-names="{ title: 'title', key: 'id', children: 'children' }"
        draggable
        block-node
        @drop="onDrop"
        v-model:expanded-keys="expandedKeys"
      >
        <template #title="{ dataRef }">
          <div
            class="group flex h-10 w-full items-center rounded transition-colors hover:bg-gray-50"
          >
            <!-- Title Column (Flex Grow) -->
            <div class="flex min-w-0 flex-1 items-center pr-4">
              <DragOutlined class="mr-2 cursor-move text-gray-400" />
              <span class="truncate" :title="dataRef.title">{{
                dataRef.title
              }}</span>
            </div>

            <!-- Fixed Columns (Right Aligned) -->
            <!-- Note: These widths must match the header -->
            <div class="flex flex-shrink-0 items-center text-sm text-gray-600">
              <!-- Icon -->
              <div class="flex w-32 items-center justify-center">
                <Space v-if="dataRef.icon">
                  <IconifyIcon :icon="getIcon(dataRef.icon)" class="size-4" />
                  <span
                    class="ml-1 max-w-[80px] truncate text-xs text-gray-400"
                    >{{ dataRef.icon }}</span
                  >
                </Space>
                <span v-else class="text-gray-300">-</span>
              </div>

              <!-- Order -->
              <div class="w-20 text-center">{{ dataRef.order }}</div>

              <!-- Path -->
              <div class="w-48 truncate" :title="dataRef.path">
                {{ dataRef.path }}
              </div>

              <!-- Component -->
              <div class="w-48 truncate" :title="dataRef.component">
                {{ dataRef.component }}
              </div>

              <!-- Status -->
              <div class="w-24 text-center">
                <Tag
                  :color="
                    getActualHiddenStatus(dataRef, allMenusFlat)
                      ? 'orange'
                      : 'green'
                  "
                >
                  {{
                    getActualHiddenStatus(dataRef, allMenusFlat)
                      ? '隐藏'
                      : '显示'
                  }}
                </Tag>
              </div>

              <!-- Action -->
              <div class="flex w-40 justify-center">
                <Space size="small" @click.stop>
                  <Button type="link" size="small" @click="handleEdit(dataRef)">
                    编辑
                  </Button>
                  <Popconfirm
                    title="确定删除吗？"
                    @confirm="handleDelete(dataRef.id)"
                  >
                    <Button type="link" danger size="small">删除</Button>
                  </Popconfirm>
                </Space>
              </div>
            </div>
          </div>
        </template>

        <template #switcherIcon>
          <DownOutlined />
        </template>
      </Tree>

      <div v-else class="py-8 text-center text-gray-400">暂无数据</div>
    </Card>

    <MenuDrawer
      v-model:open="drawerVisible"
      :record="currentRecord"
      @success="handleSuccess"
    />
  </div>
</template>

<style scoped>
/* Ensure the tree node content takes full width to support the grid-like layout */
:deep(.ant-tree-node-content-wrapper) {
  display: block !important;
  width: 100%;
  padding: 0 !important;
}

:deep(.ant-tree-treenode) {
  align-items: center;
  width: 100%;
  padding-bottom: 0 !important;
}

:deep(.ant-tree-switcher) {
  align-self: center;
}
</style>
