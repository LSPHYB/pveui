<script setup lang="ts">
import type { Permission } from '#/api/permission';

import { onMounted, reactive, ref } from 'vue';

import { Page } from '@vben/common-ui';

import {
  DeleteOutlined,
  EditOutlined,
  PlusOutlined,
} from '@ant-design/icons-vue';
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
} from 'ant-design-vue';

import { getMenuList } from '#/api/menu';
import {
  createPermission,
  deletePermission,
  getPermissionDetail,
  getPermissionList,
  updatePermission,
} from '#/api/permission';

defineOptions({ name: 'SystemPermission' });

// --- Types ---

// --- State ---
const searchText = ref('');
const loading = ref(false);
const tableData = ref<Permission[]>([]);
const pagination = reactive({
  current: 1,
  pageSize: 20,
  total: 0,
  showSizeChanger: true,
  showTotal: (total: number) => `共 ${total} 条`,
});
const confirmLoading = ref(false);

const formVisible = ref(false);
const formTitle = ref('新增权限');
const formRef = ref();

const formState = reactive({
  id: null as null | number,
  name: '',
  code: '',
  http_method: 'ANY',
  url_pattern: '',
  menu: null as null | number, // The API might return object or ID, we handle this
  is_active: true,
});

const rules: any = {
  name: [{ required: true, message: '请输入权限名称', trigger: 'blur' }],
  code: [{ required: true, message: '请输入权限编码', trigger: 'blur' }],
  url_pattern: [
    { required: true, message: '请输入URL匹配模式', trigger: 'blur' },
  ],
};

const menuList = ref<any[]>([]); // type as any to simplify, usually Menu model
const menuLoading = ref(false);

// --- Columns ---
const columns = [
  { title: '权限名称', dataIndex: 'name', key: 'name' },
  { title: '权限编码', dataIndex: 'code', key: 'code' },
  {
    title: 'HTTP方法',
    dataIndex: 'http_method',
    key: 'http_method',
    width: 100,
  },
  {
    title: 'URL匹配',
    dataIndex: 'url_pattern',
    key: 'url_pattern',
    ellipsis: true,
  },
  { title: '所属菜单', dataIndex: 'menu', key: 'menu' },
  { title: '状态', dataIndex: 'is_active', key: 'is_active', width: 100 },
  { title: '操作', key: 'action', width: 150, fixed: 'right' as const },
];

const httpMethodOptions = [
  { label: 'GET', value: 'GET' },
  { label: 'POST', value: 'POST' },
  { label: 'PUT', value: 'PUT' },
  { label: 'PATCH', value: 'PATCH' },
  { label: 'DELETE', value: 'DELETE' },
  { label: 'ANY', value: 'ANY' },
];

// --- Helpers ---
const getMethodColor = (method: string) => {
  const map: Record<string, string> = {
    GET: 'blue',
    POST: 'green',
    PUT: 'orange',
    PATCH: 'purple',
    DELETE: 'red',
    ANY: 'default',
  };
  return map[method] || 'default';
};

// --- Actions ---
const fetchData = async () => {
  loading.value = true;
  try {
    const params = {
      page: pagination.current,
      page_size: pagination.pageSize,
      search: searchText.value || undefined,
    };

    // API type defines results as Permission[], assuming DRF format
    const res: any = await getPermissionList(params);
    console.log('Permission List Response:', res);

    // Extract total count first (before checking for arrays)
    let totalCount = 0;
    switch ('number') {
      case typeof res?.count: {
        totalCount = res.count;

        break;
      }
      case typeof res?.data?.count: {
        totalCount = res.data.count;

        break;
      }
      case typeof res?.data?.total: {
        totalCount = res.data.total;

        break;
      }
      case typeof res?.total: {
        totalCount = res.total;

        break;
      }
      // No default
    }

    // Extract results array
    let results: any[] = [];
    if (Array.isArray(res)) {
      results = res;
      // If res is array directly, we can't get count from it, keep totalCount from above or use length
      if (!totalCount) totalCount = results.length;
    } else if (Array.isArray(res?.results)) {
      results = res.results;
    } else if (Array.isArray(res?.data?.results)) {
      results = res.data.results;
    } else if (Array.isArray(res?.data)) {
      results = res.data;
    }

    // Fallback to results length only if no count found
    if (!totalCount) totalCount = results.length;

    tableData.value = results;
    pagination.total = totalCount;

    console.log(
      'Extracted results:',
      results.length,
      'Total count:',
      totalCount,
    );
  } catch (error: any) {
    message.error(`获取列表失败: ${error.message || '未知错误'}`);
  } finally {
    loading.value = false;
  }
};

const loadMenuList = async () => {
  menuLoading.value = true;
  try {
    const res: any = await getMenuList({ page_size: 1000 });
    // Assuming returns list or DRF paginated
    const results = res.results || res.data || (Array.isArray(res) ? res : []);
    menuList.value = results;
  } catch (error) {
    console.error(error);
  } finally {
    menuLoading.value = false;
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

const handleCreate = () => {
  formTitle.value = '新增权限';
  formState.id = null;
  formState.name = '';
  formState.code = '';
  formState.http_method = 'ANY';
  formState.url_pattern = '';
  formState.menu = null;
  formState.is_active = true;
  formVisible.value = true;
};

const handleEdit = async (record: Permission) => {
  formTitle.value = '编辑权限';
  try {
    const res = await getPermissionDetail(record.id);
    formState.id = res.id;
    formState.name = res.name;
    formState.code = res.code;
    formState.http_method = res.http_method || 'ANY';
    formState.url_pattern = res.url_pattern || '';
    // Assuming backend returns ID or Object logic similar to Org
    if (res.menu && typeof res.menu === 'object' && 'id' in (res.menu as any)) {
      // @ts-ignore
      formState.menu = res.menu.id;
    } else {
      formState.menu = res.menu as null | number;
    }

    formState.is_active = res.is_active !== false;
    formVisible.value = true;
  } catch {
    message.error('获取详情失败');
  }
};

const handleDelete = async (record: Permission) => {
  try {
    await deletePermission(record.id);
    message.success('删除成功');
    fetchData();
  } catch (error: any) {
    message.error(`删除失败: ${error.message}`);
  }
};

const handleOk = async () => {
  try {
    await formRef.value.validate();
    confirmLoading.value = true;

    const data = { ...formState };
    if (!data.menu) data.menu = null;

    if (data.id) {
      await updatePermission(data.id, data);
      message.success('更新成功');
    } else {
      await createPermission(data);
      message.success('创建成功');
    }
    formVisible.value = false;
    fetchData();
  } catch (error: any) {
    if (!error.errorFields)
      message.error(formState.id ? '更新失败' : '创建失败');
  } finally {
    confirmLoading.value = false;
  }
};

// --- Lifecycle ---
onMounted(() => {
  fetchData();
  loadMenuList();
});
</script>

<template>
  <Page title="权限管理">
    <div class="space-y-4 p-4">
      <Card :bordered="false">
        <div class="mb-4 flex justify-between">
          <Space>
            <Input.Search
              v-model:value="searchText"
              placeholder="搜索权限名称、编码或URL"
              style="width: 300px"
              @search="handleSearch"
              allow-clear
            />
          </Space>
          <Button type="primary" @click="handleCreate">
            <template #icon><PlusOutlined /></template>
            新增权限
          </Button>
        </div>

        <Table
          :columns="columns"
          :data-source="tableData"
          :loading="loading"
          row-key="id"
          :pagination="pagination"
          @change="handleTableChange"
          :scroll="{ x: 1000 }"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'http_method'">
              <Tag :color="getMethodColor(record.http_method)">
                {{ record.http_method }}
              </Tag>
            </template>

            <template v-if="column.key === 'menu'">
              {{
                record.menu?.title ||
                (typeof record.menu === 'number' ? record.menu : '-')
              }}
            </template>

            <template v-if="column.key === 'is_active'">
              <Tag :color="record.is_active ? 'green' : 'red'">
                {{ record.is_active ? '启用' : '禁用' }}
              </Tag>
            </template>

            <template v-if="column.key === 'action'">
              <Space>
                <Button type="link" size="small" @click="handleEdit(record)">
                  <template #icon><EditOutlined /></template>
                  编辑
                </Button>
                <Popconfirm
                  title="确定要删除此权限吗？"
                  @confirm="handleDelete(record)"
                >
                  <Button type="link" danger size="small">
                    <template #icon><DeleteOutlined /></template>
                    删除
                  </Button>
                </Popconfirm>
              </Space>
            </template>
          </template>
        </Table>
      </Card>

      <Modal
        v-model:open="formVisible"
        :title="formTitle"
        :confirm-loading="confirmLoading"
        @ok="handleOk"
        width="600px"
      >
        <Form
          ref="formRef"
          :model="formState"
          :rules="rules"
          layout="vertical"
          class="pt-4"
        >
          <Form.Item label="权限名称" name="name">
            <Input
              v-model:value="formState.name"
              placeholder="请输入权限名称"
            />
          </Form.Item>

          <Form.Item label="权限编码" name="code">
            <Input
              v-model:value="formState.code"
              placeholder="请输入权限编码，如：user:list"
            />
          </Form.Item>

          <Form.Item label="HTTP方法" name="http_method">
            <Select
              v-model:value="formState.http_method"
              :options="httpMethodOptions"
            />
          </Form.Item>

          <Form.Item label="URL匹配" name="url_pattern">
            <Input
              v-model:value="formState.url_pattern"
              placeholder="请输入URL匹配模式，如：/api/rbac/users/"
            />
          </Form.Item>

          <Form.Item label="所属菜单" name="menu">
            <Select
              v-model:value="formState.menu"
              placeholder="请选择所属菜单（可选）"
              allow-clear
              :loading="menuLoading"
              :options="
                menuList.map((item) => ({ label: item.title, value: item.id }))
              "
            />
          </Form.Item>

          <Form.Item label="状态" name="is_active">
            <Switch
              v-model:checked="formState.is_active"
              checked-children="启用"
              un-checked-children="禁用"
            />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  </Page>
</template>
