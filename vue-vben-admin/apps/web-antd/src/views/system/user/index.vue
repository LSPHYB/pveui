<script setup lang="ts">
import type { TableColumnsType } from 'ant-design-vue';

import type { UserManagement } from '#/api/user-management';

import { onMounted, reactive, ref } from 'vue';

import { PlusOutlined } from '@ant-design/icons-vue';
import {
  Button,
  Card,
  Form,
  Input,
  message,
  Modal,
  Popconfirm,
  Select,
  Space,
  Switch,
  Table,
  Tag,
  TreeSelect,
  Typography,
} from 'ant-design-vue';

import { getOrganizationList, getOrganizationTree } from '#/api/organization';
import { getRoleList } from '#/api/role';
import {
  createUser,
  deleteUser,
  getUserDetail,
  getUserList,
  updateUser,
} from '#/api/user-management';
import {
  createUserOrganization,
  deleteUserOrganization,
  getUserOrganizationList,
  updateUserOrganization,
} from '#/api/user-organization';
import {
  createUserRole,
  deleteUserRole,
  getUserRoleList,
} from '#/api/user-role';

defineOptions({
  name: 'SystemUser',
});

// Types
interface FormState {
  id: null | number;
  username: string;
  email: string;
  password?: string;
  first_name: string;
  last_name: string;
  is_active: boolean;
  is_staff: boolean;
  is_superuser: boolean;
}

// State
const loading = ref(false);
const tableData = ref<UserManagement[]>([]);
const searchText = ref('');
const pagination = reactive({
  current: 1,
  pageSize: 20,
  total: 0,
  showSizeChanger: true,
  showTotal: (total: number) => `共 ${total} 条`,
});

// Modals
const userModalVisible = ref(false);
const userFormRef = ref();
const userModalTitle = ref('新增用户');
const userFormState = reactive<FormState>({
  id: null,
  username: '',
  email: '',
  password: '',
  first_name: '',
  last_name: '',
  is_active: true,
  is_staff: false,
  is_superuser: false,
});

// Roles & Orgs Modal
const rolesOrgsModalVisible = ref(false);
const rolesLoading = ref(false);
const orgsLoading = ref(false);
const roleList = ref<any[]>([]);
const orgList = ref<any[]>([]);
const orgTree = ref<any[]>([]);
const selectedRoles = ref<number[]>([]);
const selectedOrgs = ref<number[]>([]);
const primaryOrg = ref<number | undefined>(undefined);
const currentEditUser = reactive<{ id: null | number; username: string }>({
  id: null,
  username: '',
});

// Columns
const columns: TableColumnsType<UserManagement> = [
  { title: 'ID', dataIndex: 'id', width: 60 },
  { title: '用户名', dataIndex: 'username', width: 120 },
  { title: '邮箱', dataIndex: 'email', width: 180 },
  {
    title: '姓名',
    key: 'fullname',
    width: 150,
    customRender: ({ record }: { record: UserManagement }) =>
      `${record.first_name || ''} ${record.last_name || ''}`.trim() || '-',
  },
  {
    title: '状态',
    dataIndex: 'is_active',
    width: 80,
    customRender: ({ record }: { record: UserManagement }) =>
      record.is_active ? '启用' : '禁用',
  },
  {
    title: '员工',
    dataIndex: 'is_staff',
    width: 80,
    customRender: ({ record }: { record: UserManagement }) =>
      record.is_staff ? '是' : '否',
  },
  {
    title: '管理员',
    dataIndex: 'is_superuser',
    width: 90,
    customRender: ({ record }: { record: UserManagement }) =>
      record.is_superuser ? '是' : '否',
  },
  {
    title: '注册时间',
    dataIndex: 'date_joined',
    width: 170,
    customRender: ({ record }: { record: UserManagement }) =>
      formatDate(record.date_joined),
  },
  {
    title: '最后登录',
    dataIndex: 'last_login',
    width: 170,
    customRender: ({ record }: { record: UserManagement }) =>
      record.last_login ? formatDate(record.last_login) : '-',
  },
  { title: '操作', key: 'action', width: 250, fixed: 'right' },
];

// Helper
const formatDate = (dateStr: string) => {
  if (!dateStr) return '-';
  return new Date(dateStr).toLocaleString('zh-CN');
};

const getOrgName = (id: number) => {
  const org = orgList.value.find((o) => o.id === id);
  return org ? org.name : `ID:${id}`;
};

// Actions
const fetchData = async () => {
  loading.value = true;
  try {
    const params = {
      page: pagination.current,
      page_size: pagination.pageSize,
      search: searchText.value || undefined,
    };
    const res: any = await getUserList(params);
    console.log('User List API Response:', res);

    if (res.results) {
      tableData.value = res.results;
      pagination.total = res.count;
    } else if (res.data?.results) {
      tableData.value = res.data.results;
      pagination.total = res.data.count;
    } else if (res.data?.data?.results) {
      // Doubly wrapped edge case
      tableData.value = res.data.data.results;
      pagination.total = res.data.data.count;
    } else {
      // Fallback: try to find an array in the object
      console.warn('Unexpected response structure', res);
      tableData.value = [];
    }
  } catch (error) {
    console.error('Fetch error:', error);
    message.error('获取用户列表失败');
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

// User Create/Edit
const handleCreate = () => {
  userModalTitle.value = '新增用户';
  Object.assign(userFormState, {
    id: null,
    username: '',
    email: '',
    password: '',
    first_name: '',
    last_name: '',
    is_active: true,
    is_staff: false,
    is_superuser: false,
  });
  userModalVisible.value = true;
};

const handleEdit = async (record: UserManagement) => {
  userModalTitle.value = '编辑用户';
  try {
    const res: any = await getUserDetail(record.id);
    const data = res && res.id ? res : res.data || {};

    if (!data.id) {
      console.warn('User detail missing ID', res);
      message.error('获取用户数据异常');
      return;
    }

    Object.assign(userFormState, {
      id: data.id,
      username: data.username,
      email: data.email,
      password: '', // Password not retrieved
      first_name: data.first_name || '',
      last_name: data.last_name || '',
      is_active: data.is_active,
      is_staff: data.is_staff,
      is_superuser: data.is_superuser,
    });
    userModalVisible.value = true;
  } catch (error) {
    console.error(error);
    message.error('获取用户详情失败');
  }
};

const handleDelete = async (record: UserManagement) => {
  try {
    await deleteUser(record.id);
    message.success('删除成功');
    fetchData();
  } catch {
    message.error('删除失败');
  }
};

const handleUserSubmit = async () => {
  try {
    await userFormRef.value.validate();

    if (userFormState.id) {
      // Update
      const data: any = { ...userFormState };
      if (!data.password) delete data.password;
      await updateUser(userFormState.id, data);
      message.success('更新成功');
    } else {
      // Create
      if (!userFormState.password || userFormState.password.length < 6) {
        message.error('密码至少6位');
        return;
      }
      await createUser(userFormState as any);
      message.success('创建成功');
    }
    userModalVisible.value = false;
    fetchData();
  } catch (error: any) {
    if (error.errorFields) {
      // Form validation error
      return;
    }
    console.error(error);
    message.error(`提交失败：${error.response?.data?.detail || '未知错误'}`);
  }
};

// Roles & Orgs Management
const handleManageRolesOrgs = async (record: UserManagement) => {
  currentEditUser.id = record.id;
  currentEditUser.username = record.username;
  rolesOrgsModalVisible.value = true;
  rolesLoading.value = true;
  orgsLoading.value = true;

  try {
    // Load metadata
    const [rolesRes, orgsRes, orgTreeRes] = await Promise.all([
      getRoleList({ page_size: 1000 }),
      getOrganizationList({ page_size: 1000 }),
      getOrganizationTree(),
    ]);

    console.log('角色/组织数据加载:', { rolesRes, orgsRes, orgTreeRes });

    // Robust data extraction
    const roleResults =
      (rolesRes as any).results || (rolesRes as any).data?.results || [];
    roleList.value = roleResults;
    const orgResults =
      (orgsRes as any).results || (orgsRes as any).data?.results || [];
    orgList.value = orgResults;
    // 对组织树数据也进行健壮提取
    const orgTreeData = (orgTreeRes as any) || [];
    // 如果返回的是包装对象，尝试提取实际数据
    if (orgTreeData.data) {
      orgTree.value = Array.isArray(orgTreeData.data) ? orgTreeData.data : [];
    } else if (Array.isArray(orgTreeData)) {
      orgTree.value = orgTreeData;
    } else {
      orgTree.value = [];
      console.warn('组织树数据格式异常:', orgTreeRes);
    }

    console.log('处理后的数据:', {
      roleList: roleList.value,
      orgList: orgList.value,
      orgTree: orgTree.value,
    });

    // Load user data
    const [userRolesRes, userOrgsRes] = await Promise.all([
      getUserRoleList({ user: record.id, page_size: 100 }),
      getUserOrganizationList({ user: record.id, page_size: 100 }),
    ]);

    const userRoles =
      (userRolesRes as any).results ||
      (userRolesRes as any).data?.results ||
      [];
    selectedRoles.value = userRoles.map((r: any) => r.role);

    const userOrgs =
      (userOrgsRes as any).results || (userOrgsRes as any).data?.results || [];
    selectedOrgs.value = userOrgs.map((o: any) => o.organization);
    const primary = userOrgs.find((o: any) => o.is_primary);
    primaryOrg.value = primary ? primary.organization : undefined;
  } catch (error) {
    console.error(error);
    message.error('加载数据失败');
  } finally {
    rolesLoading.value = false;
    orgsLoading.value = false;
  }
};

const handleRolesOrgsSubmit = async () => {
  if (!currentEditUser.id) return;
  const userId = currentEditUser.id;

  // Validate Primary Org
  if (selectedOrgs.value.length > 0 && !primaryOrg.value) {
    message.warning('选择了组织时，必须设置主组织');
    return;
  }
  if (
    selectedOrgs.value.length > 0 &&
    primaryOrg.value &&
    !selectedOrgs.value.includes(primaryOrg.value)
  ) {
    primaryOrg.value = undefined;
    message.warning('主组织必须属于已选组织');
    return;
  }

  try {
    // 1. Manage Roles
    const currentRolesRes: any = await getUserRoleList({
      user: userId,
      page_size: 1000,
    });
    const currentRoles =
      currentRolesRes.results || currentRolesRes.data?.results || [];
    const currentRoleIds = new Set(currentRoles.map((r: any) => r.role));
    const newRoleIds = new Set(selectedRoles.value);

    // Delete removed
    for (const r of currentRoles) {
      if (!newRoleIds.has(r.role)) {
        await deleteUserRole(r.id);
      }
    }
    // Add new
    for (const rid of selectedRoles.value) {
      if (!currentRoleIds.has(rid)) {
        await createUserRole({ user: userId, role: rid });
      }
    }

    // 2. Manage Orgs
    const currentOrgsRes: any = await getUserOrganizationList({
      user: userId,
      page_size: 1000,
    });
    const currentOrgs =
      currentOrgsRes.results || currentOrgsRes.data?.results || [];
    // const currentOrgIds = new Set(currentOrgs.map((o: any) => o.organization)); // unused
    const newOrgIds = new Set(selectedOrgs.value);

    // Delete removed
    for (const o of currentOrgs) {
      if (!newOrgIds.has(o.organization)) {
        await deleteUserOrganization(o.id);
      }
    }

    // Add new or Update primary
    for (const oid of selectedOrgs.value) {
      const isPrimary = oid === primaryOrg.value;
      const existing = currentOrgs.find((o: any) => o.organization === oid);

      if (existing) {
        if (existing.is_primary !== isPrimary) {
          await updateUserOrganization(existing.id, { is_primary: isPrimary });
        }
      } else {
        await createUserOrganization({
          user: userId,
          organization: oid,
          is_primary: isPrimary,
        });
      }
    }

    message.success('保存成功');
    rolesOrgsModalVisible.value = false;
  } catch (error: any) {
    console.error(error);
    message.error(`保存失败: ${error.response?.data?.detail || error.message}`);
  }
};

const handleOrgChange = (val: number[]) => {
  // If primary org is no longer in selected, clear it
  if (primaryOrg.value && !val.includes(primaryOrg.value)) {
    primaryOrg.value = undefined;
  }
};

onMounted(() => {
  fetchData();
});
</script>

<template>
  <div class="p-4">
    <Card title="用户管理">
      <!-- Toolbar -->
      <div class="mb-4 flex justify-between">
        <Space>
          <Input.Search
            v-model:value="searchText"
            placeholder="搜索用户名、邮箱或姓名"
            style="width: 300px"
            allow-clear
            @search="handleSearch"
          />
        </Space>
        <Button type="primary" @click="handleCreate">
          <template #icon><PlusOutlined /></template>
          新增用户
        </Button>
      </div>

      <!-- Table -->
      <Table
        :columns="columns"
        :data-source="tableData"
        :loading="loading"
        :pagination="pagination"
        @change="handleTableChange"
        row-key="id"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.dataIndex === 'is_active'">
            <Tag :color="record.is_active ? 'green' : 'red'">
              {{ record.is_active ? '启用' : '禁用' }}
            </Tag>
          </template>
          <template v-if="column.dataIndex === 'is_staff'">
            <Tag :color="record.is_staff ? 'blue' : 'default'">
              {{ record.is_staff ? '是' : '否' }}
            </Tag>
          </template>
          <template v-if="column.dataIndex === 'is_superuser'">
            <Tag :color="record.is_superuser ? 'volcano' : 'default'">
              {{ record.is_superuser ? '是' : '否' }}
            </Tag>
          </template>

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
                @click="handleManageRolesOrgs(record as any)"
              >
                角色/组织
              </Button>
              <Popconfirm
                title="确定要删除此用户吗？"
                @confirm="handleDelete(record as any)"
              >
                <Button type="link" danger size="small">删除</Button>
              </Popconfirm>
            </Space>
          </template>
        </template>
      </Table>
    </Card>

    <!-- User Modal -->
    <Modal
      v-model:open="userModalVisible"
      :title="userModalTitle"
      @ok="handleUserSubmit"
      width="600px"
    >
      <Form
        ref="userFormRef"
        :model="userFormState"
        layout="vertical"
        name="userForm"
      >
        <Form.Item
          label="用户名"
          name="username"
          :rules="[{ required: true, message: '请输入用户名' }]"
        >
          <Input
            v-model:value="userFormState.username"
            placeholder="请输入用户名"
          />
        </Form.Item>

        <Form.Item
          label="邮箱"
          name="email"
          :rules="[
            { required: true, type: 'email', message: '请输入有效的邮箱' },
          ]"
        >
          <Input v-model:value="userFormState.email" placeholder="请输入邮箱" />
        </Form.Item>

        <Form.Item
          label="密码"
          name="password"
          :extra="userFormState.id ? '留空则不修改密码' : '新建用户时必填'"
        >
          <Input.Password
            v-model:value="userFormState.password"
            placeholder="请输入密码（至少6位）"
          />
        </Form.Item>

        <Space style="display: flex; gap: 20px">
          <Form.Item label="名" name="first_name">
            <Input
              v-model:value="userFormState.first_name"
              placeholder="First Name"
            />
          </Form.Item>
          <Form.Item label="姓" name="last_name">
            <Input
              v-model:value="userFormState.last_name"
              placeholder="Last Name"
            />
          </Form.Item>
        </Space>

        <Space style="display: flex; gap: 20px">
          <Form.Item label="启用" name="is_active">
            <Switch v-model:checked="userFormState.is_active" />
          </Form.Item>
          <Form.Item label="员工状态" name="is_staff">
            <Switch v-model:checked="userFormState.is_staff" />
          </Form.Item>
          <Form.Item label="超级管理员" name="is_superuser">
            <Switch v-model:checked="userFormState.is_superuser" />
          </Form.Item>
        </Space>
      </Form>
    </Modal>

    <!-- Roles & Orgs Modal -->
    <Modal
      v-model:open="rolesOrgsModalVisible"
      title="管理角色和组织"
      @ok="handleRolesOrgsSubmit"
      width="700px"
      :confirm-loading="rolesLoading || orgsLoading"
    >
      <Form layout="vertical">
        <Form.Item label="当前用户">
          <Typography.Text strong>
            {{ currentEditUser.username }}
          </Typography.Text>
        </Form.Item>

        <Form.Item label="角色">
          <Select
            v-model:value="selectedRoles"
            mode="multiple"
            placeholder="选择角色"
            :options="
              roleList.map((r) => ({
                label: `${r.name} (${r.code})`,
                value: r.id,
              }))
            "
            :loading="rolesLoading"
            option-filter-prop="label"
          />
        </Form.Item>

        <Form.Item label="组织">
          <TreeSelect
            v-model:value="selectedOrgs"
            :tree-data="orgTree"
            tree-checkable
            multiple
            placeholder="选择组织"
            :loading="orgsLoading"
            :field-names="{ children: 'children', label: 'name', value: 'id' }"
            @change="handleOrgChange"
            style="width: 100%"
            search-placeholder="搜索组织"
            tree-default-expand-all
          />
        </Form.Item>

        <Form.Item label="主组织" v-if="selectedOrgs.length > 0">
          <Select
            v-model:value="primaryOrg"
            placeholder="选择主组织（必填）"
            allow-clear
          >
            <Select.Option
              v-for="orgId in selectedOrgs"
              :key="orgId"
              :value="orgId"
            >
              {{ getOrgName(orgId) }}
            </Select.Option>
          </Select>
          <div class="mt-1 text-xs text-gray-500">
            若选择了组织，必须指定其中一个为主组织
          </div>
        </Form.Item>
      </Form>
    </Modal>
  </div>
</template>
