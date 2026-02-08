<script setup lang="ts">
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
  InputNumber,
  message,
  Modal,
  Popconfirm,
  Select,
  Space,
  Switch,
  Table,
  Tag,
} from 'ant-design-vue';

import {
  createOrganization,
  deleteOrganization,
  getOrganizationDetail,
  getOrganizationList,
  updateOrganization,
} from '#/api/organization';

defineOptions({ name: 'SystemOrganization' });

// --- Types ---
interface OrgItem {
  id: number;
  name: string;
  code: string;
  parent: null | number;
  leader: null | number | { username: string }; // Depending on backend response
  is_active: boolean;
  order: number;
  children?: OrgItem[];
}

// --- State ---
const searchText = ref('');
const loading = ref(false);
const tableData = ref<OrgItem[]>([]);
const formVisible = ref(false);
const formTitle = ref('新增组织');
const confirmLoading = ref(false);

const formState = reactive({
  id: null as null | number,
  name: '',
  code: '',
  parent: null as null | number,
  order: 0,
  leader: null as null | string, // Treating as string input for now or select if user list available
  is_active: true,
});

const formRef = ref();
const rules = {
  name: [{ required: true, message: '请输入组织名称', trigger: 'blur' }],
  code: [{ required: true, message: '请输入组织编码', trigger: 'blur' }],
};

const orgList = ref<OrgItem[]>([]); // For parent selection (flattened)
const orgLoading = ref(false);

// --- Columns ---
const columns = [
  { title: '组织名称', dataIndex: 'name', key: 'name' },
  { title: '组织编码', dataIndex: 'code', key: 'code' },
  { title: '负责人', dataIndex: 'leader', key: 'leader', width: 150 },
  { title: '排序', dataIndex: 'order', key: 'order', width: 100 },
  { title: '状态', dataIndex: 'is_active', key: 'is_active', width: 100 },
  { title: '操作', key: 'action', width: 200, fixed: 'right' as const },
];

// --- Actions ---

const fetchData = async () => {
  loading.value = true;
  try {
    // Check if existing legacy code uses getOrganizationList returning tree or list
    // The ref code used getOrganizationList and expected tree data if available
    // Let's assume getOrganizationList(params) returns a list or tree.
    // Ideally we want a tree for the table.

    const params: any = {};
    if (searchText.value) {
      params.search = searchText.value;
    }

    // If searching, we might get a flat list. If not, we hopefully get a tree.
    // If backend only provides flat list, handleToTree must be implemented.
    // For now, let's use the API and see structure.
    const res: any = await getOrganizationList(params);

    let data: any[] = [];
    if (Array.isArray(res)) {
      data = res;
    } else if (res?.results) {
      data = res.results;
    } else if (res?.data) {
      data = Array.isArray(res.data) ? res.data : res.data?.results || [];
    }

    // If backend returns flat list but we want tree:
    // Ideally backend '/rbac/organizations/' returns tree if configured, or use getOrganizationTree if different endpoint.
    // The front-end code used: await getOrganizationList(params)

    // If data is flat list, we might need to build tree, but let's assume table handles children if they exist
    tableData.value = data;
  } catch (error: any) {
    message.error(`获取列表失败: ${error.message || '未知错误'}`);
  } finally {
    loading.value = false;
  }
};

const loadOrgList = async () => {
  orgLoading.value = true;
  try {
    const res: any = await getOrganizationList({ page_size: 1000 }); // Get all for dropdown
    let data: any[] = [];
    if (Array.isArray(res)) {
      data = res;
    } else if (res?.results) {
      data = res.results;
    } else if (res?.data) {
      data = Array.isArray(res.data) ? res.data : res.data?.results || [];
    }
    orgList.value = flattenOrgTree(data);
  } catch (error) {
    console.error(error);
  } finally {
    orgLoading.value = false;
  }
};

const handleSearch = () => {
  fetchData();
};

const handleCreate = () => {
  formTitle.value = '新增组织';
  formState.id = null;
  formState.name = '';
  formState.code = '';
  formState.parent = null;
  formState.order = 0;
  formState.leader = null;
  formState.is_active = true;
  formVisible.value = true;
};

const handleEdit = async (record: OrgItem) => {
  formTitle.value = '编辑组织';
  try {
    // Fetch detail ensures freshness, or use record
    const res: any = await getOrganizationDetail(record.id);
    console.log('获取组织详情响应:', res);

    // 健壮的数据提取
    const data = res?.data || res;

    if (!data.id) {
      console.error('组织详情缺少id:', res);
      message.error('获取组织详情失败：数据格式异常');
      return;
    }

    formState.id = data.id;
    formState.name = data.name;
    formState.code = data.code || '';
    formState.parent = data.parent || null;
    // @ts-ignore
    formState.order = data.order || 0;
    // @ts-ignore
    formState.leader = data.leader
      ? typeof data.leader === 'object'
        ? data.leader.username
        : data.leader
      : null;
    // If leader is ID vs Object, need to handle. The reference code uses text input for ID.
    // Let's stick to text input for now as per ref.

    formState.is_active = data.is_active !== false;

    console.log('编辑表单状态:', { ...formState });
    formVisible.value = true;
  } catch (error) {
    console.error('获取组织详情错误:', error);
    message.error('获取详情失败');
  }
};

const handleDelete = async (record: OrgItem) => {
  try {
    await deleteOrganization(record.id);
    message.success('删除成功');
    fetchData();
    loadOrgList();
  } catch (error: any) {
    message.error(`删除失败: ${error.message || '未知错误'}`);
  }
};

const handleOk = async () => {
  console.log('handleOk 被调用，当前 formState:', { ...formState });
  console.log(
    '操作类型:',
    formState.id ? '更新' : '创建',
    '| ID:',
    formState.id,
  );

  try {
    await formRef.value.validate();
    confirmLoading.value = true;

    const data = { ...formState };
    // Clean up data
    if (!data.parent) data.parent = null;
    if (!data.leader) data.leader = null;

    // 删除 id 字段（创建时不需要，更新时通过URL传递）
    const payload: any = { ...data };
    delete payload.id;

    console.log('提交的组织数据:', payload);

    if (data.id) {
      const res = await updateOrganization(data.id, payload);
      console.log('更新组织响应:', res);
      message.success('更新成功');
    } else {
      const res = await createOrganization(payload);
      console.log('创建组织响应:', res);
      message.success('创建成功');
    }
    formVisible.value = false;
    fetchData();
    loadOrgList();
  } catch (error: any) {
    console.error('组织操作错误:', error);
    if (!error.errorFields) {
      // 不是表单验证错误
      const isUpdate = formState.id !== null;
      const errorMsg =
        error.response?.data?.detail ||
        error.response?.data?.message ||
        error.message ||
        (isUpdate ? '更新失败' : '创建失败');

      // 打印详细错误信息
      if (error.response?.data) {
        console.error('后端返回错误详情:', error.response.data);
        // 如果是字段验证错误，显示具体字段
        if (typeof error.response.data === 'object') {
          const fieldErrors = Object.entries(error.response.data)
            .map(([field, msg]) => `${field}: ${msg}`)
            .join('; ');
          message.error(`${isUpdate ? '更新' : '创建'}失败: ${fieldErrors}`);
          return;
        }
      }
      message.error(errorMsg);
    }
  } finally {
    confirmLoading.value = false;
  }
};

const flattenOrgTree = (nodes: any[]): OrgItem[] => {
  const result: OrgItem[] = [];
  const walk = (arr: any[]) => {
    if (!Array.isArray(arr)) return;
    for (const n of arr) {
      result.push({
        id: n.id,
        name: n.name,
        code: n.code,
        parent: n.parent,
        leader: n.leader,
        is_active: n.is_active,
        order: n.order,
      });
      if (n.children && n.children.length > 0) walk(n.children);
    }
  };
  walk(nodes);
  return result;
};

// --- Lifecycle ---
onMounted(() => {
  fetchData();
  loadOrgList();
});
</script>

<template>
  <Page title="组织管理">
    <div class="space-y-4 p-4">
      <Card :bordered="false">
        <div class="mb-4 flex justify-between">
          <Space>
            <Input.Search
              v-model:value="searchText"
              placeholder="搜索组织名称或编码"
              style="width: 300px"
              @search="handleSearch"
              allow-clear
            />
          </Space>
          <Button type="primary" @click="handleCreate">
            <template #icon><PlusOutlined /></template>
            新增组织
          </Button>
        </div>

        <Table
          :columns="columns"
          :data-source="tableData"
          :loading="loading"
          row-key="id"
          :pagination="false"
          :scroll="{ x: 1000 }"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'leader'">
              {{
                typeof record.leader === 'object' && record.leader
                  ? record.leader.username
                  : record.leader || '-'
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
                  title="确定要删除此组织吗？"
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
          <Form.Item label="组织名称" name="name">
            <Input
              v-model:value="formState.name"
              placeholder="请输入组织名称"
            />
          </Form.Item>
          <Form.Item label="组织编码" name="code">
            <Input
              v-model:value="formState.code"
              placeholder="请输入组织编码"
            />
          </Form.Item>
          <Form.Item label="上级组织" name="parent">
            <Select
              v-model:value="formState.parent"
              placeholder="请选择上级组织（可选）"
              allow-clear
              :loading="orgLoading"
              :options="
                orgList.map((item) => ({
                  label: item.name,
                  value: item.id,
                  disabled: item.id === formState.id,
                }))
              "
            />
          </Form.Item>
          <Form.Item label="排序" name="order">
            <InputNumber
              v-model:value="formState.order"
              :min="0"
              style="width: 100%"
            />
          </Form.Item>
          <Form.Item label="负责人" name="leader">
            <Input
              v-model:value="formState.leader"
              placeholder="请输入负责人用户名/ID (可选)"
            />
            <!-- Note: Ideally this should be a User Select, but following reference for now which handles it as input or simple display -->
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
