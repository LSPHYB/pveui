<script setup lang="ts">
import type { TableColumnsType, TreeProps } from 'ant-design-vue';
import type { DataNode } from 'ant-design-vue/es/tree';

import type { Permission } from '#/api/permission';
import type { Role } from '#/api/role';
import type { UserManagement } from '#/api/user-management';

import { computed, onMounted, reactive, ref } from 'vue';

import { PlusOutlined } from '@ant-design/icons-vue';
import {
  Button,
  Card,
  Checkbox,
  Drawer,
  Empty,
  Form,
  Input,
  message,
  Modal,
  Popconfirm,
  Select,
  Space,
  Table,
  Tree,
  TreeSelect,
} from 'ant-design-vue';

import { getMenuTreeApi } from '#/api/menu';
import { getOrganizationTree } from '#/api/organization';
import { getPermissionList } from '#/api/permission';
import {
  createRole,
  deleteRole,
  getRoleDetail,
  getRoleList,
  updateRole,
} from '#/api/role';
import { getUserList } from '#/api/user-management';
import {
  createUserRole,
  deleteUserRole,
  getUserRoleList,
} from '#/api/user-role';

defineOptions({
  name: 'SystemRole',
});

console.log('[Role Component] Script loaded successfully');

// Types
interface FormState {
  id: null | number;
  name: string;
  code: string;
  description: string;
  data_scope: string;
  custom_data_organizations: number[];
  menus: number[];
  permissions: number[];
}

// State
const loading = ref(false);
const tableData = ref<Role[]>([]);
const searchText = ref('');
const pagination = reactive({
  current: 1,
  pageSize: 20,
  total: 0,
  showSizeChanger: true,
  showTotal: (total: number) => `共 ${total} 条`,
});

// Modals
const modalVisible = ref(false);
const formRef = ref();
const modalTitle = ref('新增角色');
const submitting = ref(false);

const formState = reactive<FormState>({
  id: null,
  name: '',
  code: '',
  description: '',
  data_scope: 'SELF',
  custom_data_organizations: [],
  menus: [],
  permissions: [],
});

const menuTreeData = ref<DataNode[]>([]);
const orgTreeData = ref<DataNode[]>([]);
const allPermissions = ref<Permission[]>([]);
const checkedMenuKeys = ref<number[]>([]);
const selectedMenuKeys = ref<number[]>([]);
const selectedMenuId = ref<null | number>(null);

// Get permissions for the selected menu
const currentMenuPermissions = computed(() => {
  if (!selectedMenuId.value) return [];

  // Permissions have `menu` ID.
  // Backend might serialize as 'menu' or 'menu_id'
  // Need to handle if `menu` is object or ID.
  const filtered = allPermissions.value.filter((p) => {
    // Try multiple possible field names
    let mId = null;

    // Check if permission has menu_id field (direct from backend)
    if ('menu_id' in p && p.menu_id !== undefined) {
      mId = p.menu_id;
    }
    // Check standard menu field
    else if (p.menu !== null && p.menu !== undefined) {
      // Handle if menu is an object with id
      mId = typeof p.menu === 'object' ? (p.menu as any).id : p.menu;
    }

    return mId === selectedMenuId.value;
  });

  return filtered;
});

// Get selected permission IDs for the current menu only
const currentMenuSelectedPermissions = computed({
  get: () => {
    if (!selectedMenuId.value) return [];
    // Get all permission IDs that belong to current menu
    const currentMenuPermIds = new Set(
      currentMenuPermissions.value.map((p) => p.id),
    );
    // Return only the selected permissions that belong to current menu
    return formState.permissions.filter((id) => currentMenuPermIds.has(id));
  },
  set: (newSelectedIds: number[]) => {
    // Get all permission IDs that belong to current menu
    const currentMenuPermIds = new Set(
      currentMenuPermissions.value.map((p) => p.id),
    );
    // Remove all current menu's permissions from formState
    const otherMenusPermissions = formState.permissions.filter(
      (id) => !currentMenuPermIds.has(id),
    );
    // Add the newly selected current menu's permissions
    formState.permissions = [...otherMenusPermissions, ...newSelectedIds];
  },
});

// Helper to check if all permissions for current menu are selected
const isAllCurrentPermissionsChecked = computed(() => {
  const current = currentMenuPermissions.value;
  if (current.length === 0) return false;
  return currentMenuSelectedPermissions.value.length === current.length;
});

const isIndeterminatePermissions = computed(() => {
  const current = currentMenuPermissions.value;
  if (current.length === 0) return false;
  const checkedCount = currentMenuSelectedPermissions.value.length;
  return checkedCount > 0 && checkedCount < current.length;
});

const handleCheckAllPermissions = (e: any) => {
  const checked = e.target.checked;
  const currentIds = currentMenuPermissions.value.map((p) => p.id);
  if (checked) {
    // Select all permissions in current menu
    currentMenuSelectedPermissions.value = currentIds;
  } else {
    // Deselect all permissions in current menu
    currentMenuSelectedPermissions.value = [];
  }
};

// Constants
const dataScopeOptions = [
  { label: '全部数据', value: 'ALL' },
  { label: '本部门', value: 'DEPT' },
  { label: '本部门及下级', value: 'DEPT_AND_SUB' },
  { label: '仅本人', value: 'SELF' },
  { label: '自定义组织', value: 'CUSTOM' },
];

// Columns
const columns: TableColumnsType<Role> = [
  { title: 'ID', dataIndex: 'id', width: 60 },
  { title: '名称', dataIndex: 'name', width: 150 },
  { title: '编码', dataIndex: 'code', width: 150 },
  { title: '描述', dataIndex: 'description' },
  {
    title: '数据范围',
    dataIndex: 'data_scope',
    width: 150,
    customRender: ({ text }) => {
      const opt = dataScopeOptions.find((o) => o.value === text);
      return opt ? opt.label : text;
    },
  },
  { title: '操作', key: 'action', width: 180, fixed: 'right' },
];

// Actions
const fetchData = async () => {
  loading.value = true;
  try {
    const params = {
      page: pagination.current,
      page_size: pagination.pageSize,
      search: searchText.value || undefined,
    };
    const res: any = await getRoleList(params);

    // Robust parsing
    if (res.results) {
      tableData.value = res.results;
      pagination.total = res.count;
    } else if (res.data?.results) {
      tableData.value = res.data.results;
      pagination.total = res.data.count;
    } else {
      tableData.value = [];
    }
  } catch (error) {
    console.error(error);
    message.error('获取角色列表失败');
  } finally {
    loading.value = false;
  }
};

const handleSearch = () => {
  pagination.current = 1;
  fetchData();
};

const handleTableChange = (pag: any) => {
  pagination.current = pag.current;
  pagination.pageSize = pag.pageSize;
  fetchData();
};

// State
const roleUsersVisible = ref(false);
const roleUsersLoading = ref(false);
const currentRole = ref<null | Role>(null);
const roleUsersList = ref<any[]>([]);
const allUsers = ref<UserManagement[]>([]);
const userAddVisible = ref(false);
const selectedUserToAdd = ref<number | undefined>(undefined);
const userSearchText = ref('');

const filteredUsers = computed(() => {
  if (!userSearchText.value) return allUsers.value;
  const lower = userSearchText.value.toLowerCase();
  return allUsers.value.filter(
    (u) =>
      u.username.toLowerCase().includes(lower) ||
      (u.first_name && u.first_name.toLowerCase().includes(lower)) ||
      (u.last_name && u.last_name.toLowerCase().includes(lower)),
  );
});

// ... (previous code)

const fetchMetadata = async () => {
  console.log('[fetchMetadata] Starting to fetch metadata...');
  try {
    const [menuRes, orgRes, permRes] = await Promise.all([
      getMenuTreeApi(),
      getOrganizationTree(),
      getPermissionList({ page_size: 1000 }),
    ]);

    console.log('[fetchMetadata] Responses received:', {
      menuRes,
      orgRes,
      permRes,
    });

    // Robust parsing for Menu Tree
    const menuData =
      (menuRes as any).results || (menuRes as any).data || menuRes;
    menuTreeData.value = Array.isArray(menuData) ? menuData : [];
    console.log(
      '[fetchMetadata] Menu tree data loaded:',
      menuTreeData.value.length,
      'items',
    );

    // Robust parsing for Org Tree
    const orgData = (orgRes as any).results || (orgRes as any).data || orgRes;
    orgTreeData.value = Array.isArray(orgData) ? orgData : [];

    // Robust parsing for Permissions
    let permData;
    if (Array.isArray(permRes)) {
      permData = permRes;
    } else if (permRes.results && Array.isArray(permRes.results)) {
      permData = permRes.results;
    } else if (permRes.data?.results && Array.isArray(permRes.data.results)) {
      permData = permRes.data.results;
    } else if (permRes.data && Array.isArray(permRes.data)) {
      permData = permRes.data;
    } else {
      permData = [];
    }
    allPermissions.value = permData;
  } catch (error) {
    console.error('[fetchMetadata] Error:', error);
    message.error('加载基础数据失败');
  }
};

// ... (previous handleCreate, handleEdit, handleDelete, handleSubmit)

// User Assignment Actions
const handleAssignUsers = async (record: Role) => {
  currentRole.value = record;
  roleUsersVisible.value = true;
  loadRoleUsers();
  // Pre-load all users for the add dropdown
  if (allUsers.value.length === 0) {
    const res: any = await getUserList({ page_size: 1000 });
    allUsers.value = res.results || res.data?.results || [];
  }
};

const loadRoleUsers = async () => {
  if (!currentRole.value) return;
  roleUsersLoading.value = true;
  try {
    // Get UserRoles
    const res: any = await getUserRoleList({
      role: currentRole.value.id,
      page_size: 1000,
    });
    const userRoleData = res.results || res.data?.results || [];

    // We need user details. If logic implies we have all users, we map.
    // Ideally backend UserRole serializer should expand user.
    // If not, we rely on allUsers map (if loaded) or fetch users.
    if (allUsers.value.length === 0) {
      const uRes: any = await getUserList({ page_size: 1000 });
      allUsers.value = uRes.results || uRes.data?.results || [];
    }

    // Map existing UserRoles to display data
    roleUsersList.value = userRoleData.map((ur: any) => {
      const u = allUsers.value.find((user) => user.id === ur.user);
      return {
        id: ur.id, // UserRole ID
        userId: ur.user,
        username: u?.username || `User ${ur.user}`,
        realName: u ? `${u.first_name || ''} ${u.last_name || ''}` : '',
        email: u?.email || '',
      };
    });
  } catch {
    message.error('加载角色用户失败');
  } finally {
    roleUsersLoading.value = false;
  }
};

const handleAddUserToRole = async () => {
  if (!selectedUserToAdd.value || !currentRole.value) return;
  try {
    await createUserRole({
      user: selectedUserToAdd.value,
      role: currentRole.value.id,
    });
    message.success('添加成功');
    userAddVisible.value = false;
    selectedUserToAdd.value = undefined;
    loadRoleUsers();
  } catch (error: any) {
    message.error(error.response?.data?.detail || '添加失败');
  }
};

const handleRemoveUserFromRole = async (userRoleId: number) => {
  try {
    await deleteUserRole(userRoleId);
    message.success('移除成功');
    loadRoleUsers();
  } catch {
    message.error('移除失败');
  }
};

// ... (other handlers)

// Add to template:
// In Table columns actions:
// <Button type="link" size="small" @click="handleAssignUsers(record as any)">用户分配</Button>

const handleCreate = async () => {
  modalTitle.value = '新增角色';

  Object.assign(formState, {
    id: null,
    name: '',
    code: '',
    description: '',
    data_scope: 'SELF',
    custom_data_organizations: [],
    menus: [],
    permissions: [],
  });
  checkedMenuKeys.value = [];
  selectedMenuKeys.value = [];
  selectedMenuId.value = null;

  // Load permissions if not loaded yet
  if (allPermissions.value.length === 0) {
    try {
      const permRes: any = await getPermissionList({ page_size: 1000 });

      // Fix: Correctly extract results array
      let permData;
      if (Array.isArray(permRes)) {
        permData = permRes;
      } else if (permRes.results && Array.isArray(permRes.results)) {
        permData = permRes.results;
      } else if (permRes.data?.results && Array.isArray(permRes.data.results)) {
        permData = permRes.data.results;
      } else if (permRes.data && Array.isArray(permRes.data)) {
        permData = permRes.data;
      } else {
        permData = [];
      }

      allPermissions.value = permData;
    } catch (permError) {
      console.error('[handleCreate] Failed to load permissions:', permError);
      message.warning('权限数据加载失败，但不影响角色创建');
    }
  }

  modalVisible.value = true;
};

const handleEdit = async (record: Role) => {
  modalTitle.value = '编辑角色';
  try {
    const res: any = await getRoleDetail(record.id);
    // Robust extraction: direct, or inside data
    const data = res && res.id ? res : res.data || {};

    if (!data.id) {
      console.warn('Get detail failed to find ID', res);
      message.error('获取详情数据异常');
      return;
    }

    Object.assign(formState, {
      id: data.id,
      name: data.name,
      code: data.code,
      description: data.description || '',
      data_scope: data.data_scope || 'SELF',
      custom_data_organizations: data.custom_data_organizations || [],
      menus: data.menus || [],
      permissions: data.permissions || [],
    });
    // Set checked keys for tree
    checkedMenuKeys.value = data.menus || [];

    // Load permissions if not loaded yet
    if (allPermissions.value.length === 0) {
      try {
        const permRes: any = await getPermissionList({ page_size: 1000 });

        // Fix: Correctly extract results array from nested structure
        let permData;
        if (Array.isArray(permRes)) {
          permData = permRes;
        } else if (permRes.results && Array.isArray(permRes.results)) {
          permData = permRes.results;
        } else if (
          permRes.data?.results &&
          Array.isArray(permRes.data.results)
        ) {
          permData = permRes.data.results;
        } else if (permRes.data && Array.isArray(permRes.data)) {
          permData = permRes.data;
        } else {
          permData = [];
        }

        allPermissions.value = permData;
      } catch (permError: any) {
        console.error('[handleEdit] Failed to load permissions:', permError);
        message.warning('权限数据加载失败，但不影响角色编辑');
        // Continue anyway, user can still edit role without seeing permissions
      }
    }

    // Auto-select the first checked menu to show its permissions immediately
    if (checkedMenuKeys.value.length > 0) {
      const firstMenuId = checkedMenuKeys.value[0];
      selectedMenuKeys.value = [firstMenuId];
      selectedMenuId.value = firstMenuId;
    } else {
      // No menus assigned, clear selection
      selectedMenuKeys.value = [];
      selectedMenuId.value = null;
    }

    modalVisible.value = true;
  } catch (error) {
    console.error(error);
    message.error('获取角色详情失败');
  }
};

const handleDelete = async (record: Role) => {
  try {
    await deleteRole(record.id);
    message.success('删除成功');
    fetchData();
  } catch {
    message.error('删除失败');
  }
};

const handleSubmit = async () => {
  try {
    await formRef.value.validate();
    submitting.value = true;

    const data: any = {
      name: formState.name,
      code: formState.code,
      description: formState.description,
      data_scope: formState.data_scope,
      custom_data_organizations: formState.custom_data_organizations,
      menus: checkedMenuKeys.value, // Use tree checked keys
      permissions: formState.permissions,
    };

    if (formState.id) {
      await updateRole(formState.id, data);
      message.success('更新成功');
    } else {
      await createRole(data);
      message.success('创建成功');
    }
    modalVisible.value = false;
    fetchData();
  } catch (error: any) {
    if (error.errorFields) return; // Validation error
    console.error(error);
    message.error(`提交失败: ${error.response?.data?.detail || error.message}`);
  } finally {
    submitting.value = false;
  }
};

// Tree check handler
const handleMenuCheck: TreeProps['onCheck'] = (checkedKeys) => {
  // checkedKeys can be {checked: [], halfChecked: []} or []
  checkedMenuKeys.value = Array.isArray(checkedKeys)
    ? (checkedKeys as number[])
    : (checkedKeys as any).checked;
};

const handleMenuSelect: TreeProps['onSelect'] = (selectedKeys) => {
  if (selectedKeys && selectedKeys.length > 0) {
    selectedMenuId.value = selectedKeys[0] as number;
    selectedMenuKeys.value = selectedKeys as number[];
  } else {
    selectedMenuId.value = null;
    selectedMenuKeys.value = [];
  }
};

onMounted(() => {
  fetchData();
  fetchMetadata();
});
</script>

<template>
  <div class="p-4">
    <Card title="角色管理">
      <div class="mb-4 flex justify-between">
        <Space>
          <Input.Search
            v-model:value="searchText"
            placeholder="搜索角色名称或编码"
            style="width: 300px"
            allow-clear
            @search="handleSearch"
          />
        </Space>
        <Button type="primary" @click="handleCreate">
          <template #icon><PlusOutlined /></template>
          新增角色
        </Button>
      </div>

      <Table
        :columns="columns"
        :data-source="tableData"
        :loading="loading"
        :pagination="pagination"
        @change="handleTableChange"
        row-key="id"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'action'">
            <Space>
              <Button
                type="link"
                size="small"
                @click="handleEdit(record as any)"
              >
                编辑
              </Button>
              <Button
                type="link"
                size="small"
                @click="handleAssignUsers(record as any)"
              >
                用户分配
              </Button>
              <Popconfirm
                title="确定要删除此角色吗？"
                @confirm="handleDelete(record as any)"
              >
                <Button type="link" danger size="small">删除</Button>
              </Popconfirm>
            </Space>
          </template>
        </template>
      </Table>
    </Card>

    <Modal
      v-model:open="modalVisible"
      :title="modalTitle"
      @ok="handleSubmit"
      width="700px"
      :confirm-loading="submitting"
    >
      <Form ref="formRef" :model="formState" layout="vertical" name="roleForm">
        <div class="grid grid-cols-2 gap-4">
          <Form.Item
            label="角色名称"
            name="name"
            :rules="[{ required: true, message: '请输入角色名称' }]"
          >
            <Input
              v-model:value="formState.name"
              placeholder="请输入角色名称"
            />
          </Form.Item>

          <Form.Item
            label="角色编码"
            name="code"
            :rules="[{ required: true, message: '请输入角色编码' }]"
          >
            <Input
              v-model:value="formState.code"
              placeholder="请输入角色编码"
            />
          </Form.Item>
        </div>

        <Form.Item label="描述" name="description">
          <Input.TextArea
            v-model:value="formState.description"
            placeholder="请输入描述"
            :rows="2"
          />
        </Form.Item>

        <Form.Item label="数据范围" name="data_scope">
          <Select
            v-model:value="formState.data_scope"
            :options="dataScopeOptions"
          />
        </Form.Item>

        <Form.Item
          v-if="formState.data_scope === 'CUSTOM'"
          label="自定义数据权限"
          name="custom_data_organizations"
          :rules="[{ required: true, message: '请选择组织', type: 'array' }]"
        >
          <TreeSelect
            v-model:value="formState.custom_data_organizations"
            :tree-data="orgTreeData"
            tree-checkable
            multiple
            placeholder="请选择组织"
            :field-names="{ children: 'children', label: 'name', value: 'id' }"
            style="width: 100%"
            tree-default-expand-all
          />
        </Form.Item>

        <Form.Item label="系统权限">
          <div class="flex h-[400px] rounded border">
            <!-- Left: Menu Tree -->
            <div class="w-1/2 overflow-auto border-r p-2">
              <div
                class="mb-2 border-b pb-1 text-center text-xs font-medium text-gray-500"
              >
                菜单结构
                <span class="text-blue-500">(点击查看权限，勾选分配菜单)</span>
              </div>
              <Tree
                v-if="menuTreeData.length > 0"
                v-model:checked-keys="checkedMenuKeys"
                v-model:selected-keys="selectedMenuKeys"
                checkable
                :tree-data="menuTreeData"
                :field-names="{
                  children: 'children',
                  title: 'title',
                  key: 'id',
                }"
                default-expand-all
                @check="handleMenuCheck"
                @select="handleMenuSelect"
              />
              <div v-else class="py-4 text-center text-gray-400">
                暂无菜单数据
              </div>
            </div>

            <!-- Right: Permissions -->
            <div class="w-1/2 overflow-auto bg-gray-50/50 p-2">
              <div
                class="mb-2 flex h-[24px] items-center justify-between border-b pb-1 text-xs font-medium text-gray-500"
              >
                <span>功能权限</span>
                <Checkbox
                  v-if="currentMenuPermissions.length > 0"
                  :checked="isAllCurrentPermissionsChecked"
                  :indeterminate="isIndeterminatePermissions"
                  @change="handleCheckAllPermissions"
                  class="text-xs"
                >
                  全选
                </Checkbox>
              </div>

              <div v-if="selectedMenuId">
                <div
                  v-if="currentMenuPermissions.length > 0"
                  class="flex flex-col gap-2 p-1"
                >
                  <Checkbox.Group
                    v-model:value="currentMenuSelectedPermissions"
                  >
                    <div class="flex flex-col gap-2">
                      <Checkbox
                        v-for="p in currentMenuPermissions"
                        :key="p.id"
                        :value="p.id"
                      >
                        {{ p.name }}
                        <span v-if="p.code" class="ml-1 text-xs text-gray-400"
                          >({{ p.code }})</span
                        >
                      </Checkbox>
                    </div>
                  </Checkbox.Group>
                </div>
                <div v-else class="py-10 text-center text-sm text-gray-400">
                  该菜单下暂无配置权限
                </div>
              </div>
              <div
                v-else
                class="flex h-full flex-col items-center justify-center py-10 text-center text-sm text-gray-400"
              >
                <Empty
                  :image="Empty.PRESENTED_IMAGE_SIMPLE"
                  description="请点击左侧菜单查看对应权限"
                />
              </div>
            </div>
          </div>
        </Form.Item>
      </Form>
    </Modal>

    <!-- Role Users Modal -->
    <Modal
      v-model:open="roleUsersVisible"
      title="用户分配"
      width="800px"
      :footer="null"
    >
      <div class="mb-4">
        <Space>
          <Button type="primary" @click="userAddVisible = true">
            <template #icon><PlusOutlined /></template>
            添加用户
          </Button>
          <span class="ml-2 text-gray-500"
            >当前角色: {{ currentRole?.name }} (ID: {{ currentRole?.id }})</span
          >
        </Space>
      </div>

      <Table
        :data-source="roleUsersList"
        :loading="roleUsersLoading"
        :pagination="{ pageSize: 10 }"
        row-key="id"
        size="small"
      >
        <Table.Column title="用户名" data-index="username" />
        <Table.Column title="姓名" data-index="realName" />
        <Table.Column title="邮箱" data-index="email" />
        <Table.Column title="操作" key="action">
          <template #default="{ record }">
            <Popconfirm
              title="确定要移除该用户吗？"
              @confirm="handleRemoveUserFromRole(record.id)"
            >
              <Button type="link" danger size="small">移除</Button>
            </Popconfirm>
          </template>
        </Table.Column>
      </Table>
    </Modal>

    <!-- Add User Drawer -->
    <Drawer v-model:open="userAddVisible" title="选择用户" width="400">
      <div class="flex h-full flex-col">
        <div class="mb-4">
          <Input.Search
            v-model:value="userSearchText"
            placeholder="输入用户名搜索"
            allow-clear
          />
        </div>
        <div class="flex-1 overflow-y-auto rounded border">
          <div
            v-for="user in filteredUsers"
            :key="user.id"
            class="flex cursor-pointer items-center justify-between border-b p-2 transition-colors last:border-b-0 hover:bg-gray-50"
            :class="{
              'bg-primary/5 text-primary': selectedUserToAdd === user.id,
            }"
            @click="selectedUserToAdd = user.id"
          >
            <div class="flex flex-col">
              <span class="font-medium">{{ user.username }}</span>
              <span class="text-xs text-gray-500"
                >{{ user.first_name }} {{ user.last_name }}</span
              >
            </div>
            <div v-if="selectedUserToAdd === user.id" class="text-primary">
              ✓
            </div>
          </div>
          <div
            v-if="filteredUsers.length === 0"
            class="p-4 text-center text-gray-400"
          >
            暂无数据
          </div>
        </div>
      </div>

      <template #footer>
        <div style="text-align: right">
          <Button style="margin-right: 8px" @click="userAddVisible = false">
            取消
          </Button>
          <Button type="primary" @click="handleAddUserToRole">确定</Button>
        </div>
      </template>
    </Drawer>
  </div>
</template>
