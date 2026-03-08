<script setup lang="ts">
import { onMounted, reactive, ref, h } from 'vue';
import { SendOutlined } from '@ant-design/icons-vue';
import {
  Button,
  Card,
  Form,
  Select,
  InputNumber,
  Space,
  Table,
  Modal,
  Popconfirm,
  message,
  Tag,
  DatePicker,
} from 'ant-design-vue';
import type { TableColumnsType } from 'ant-design-vue';
import dayjs from 'dayjs';

import {
  getAiQuotasApi,
  batchSetAiQuotasApi,
  updateAiQuotaApi,
  deleteAiQuotaApi,
  resetAiQuotaApi,
} from '#/api/ai';
import { getUserList } from '#/api/user-management';

defineOptions({ name: 'AiUserQuotaConfig' });

const loading = ref(false);
const tableData = ref<any[]>([]);
const pagination = reactive({
  current: 1,
  pageSize: 20,
  total: 0,
});

const selectedRowKeys = ref<number[]>([]);
const batchVisible = ref(false);
const submitting = ref(false);
const batchFormRef = ref();
const sysUserList = ref<any[]>([]);

const editVisible = ref(false);
const editingId = ref<number | null>(null);

const formState = reactive({
  user_ids: [] as number[],
  quota_type: 'monthly',
  token_limit: 100000,
  reset_at: null as any,
});

const editFormState = reactive({
  quota_type: 'monthly',
  token_limit: 100000,
  reset_at: null as any,
});

const columns: TableColumnsType = [
  { 
    title: '用户', 
    dataIndex: 'user', 
    width: 120,
    customRender: ({ record }) => {
      if (record.username) return record.username;
      return record.user;
    }
  },
  {
    title: '配额类型',
    dataIndex: 'quota_type',
    width: 100,
    customRender: ({ text }) => {
      const typeMap: Record<string, string> = { total: '永久总额度', daily: '单日恢复', monthly: '单月恢复' };
      return typeMap[text] || text;
    },
  },
  {
    title: '允许调用上限',
    dataIndex: 'token_limit',
    sorter: true,
  },
  {
    title: '目前已用量',
    dataIndex: 'tokens_used',
    sorter: true,
  },
  {
    title: '额度重置时间',
    dataIndex: 'reset_at',
    width: 200,
    customRender: ({ text }) => {
      return text ? dayjs(text).format('YYYY-MM-DD HH:mm:ss') : '无';
    },
  },
  {
    title: '生效状态',
    dataIndex: 'is_active',
    width: 100,
    customRender: ({ text }) => {
      return text ? h(Tag, { color: 'success' }, () => '履约中') : h(Tag, { color: 'error' }, () => '停摆');
    },
  },
  { title: '操作', key: 'action', width: 120, fixed: 'right' },
];

const fetchData = async () => {
  loading.value = true;
  try {
    const res: any = await getAiQuotasApi({
      page: pagination.current,
      page_size: pagination.pageSize,
    });
    console.log('AI Quotas Response:', res);
    
    // Robust extraction logic
    if (res && res.results) {
      tableData.value = res.results;
      pagination.total = res.count || res.results.length;
    } else if (res?.data?.results) {
      tableData.value = res.data.results;
      pagination.total = res.data.count || res.data.results.length;
    } else if (res?.data?.data?.results) {
      tableData.value = res.data.data.results;
      pagination.total = res.data.data.count || res.data.data.results.length;
    } else if (Array.isArray(res)) {
      tableData.value = res;
      pagination.total = res.length;
    } else if (Array.isArray(res?.data)) {
      tableData.value = res.data;
      pagination.total = res.data.length;
    } else if (Array.isArray(res?.data?.data)) {
      tableData.value = res.data.data;
      pagination.total = res.data.data.length;
    } else if (res?.data?.items) {
      tableData.value = res.data.items;
      pagination.total = res.data.total || res.data.items.length;
    } else if (res?.data?.list) {
      tableData.value = res.data.list;
      pagination.total = res.data.total || res.data.list.length;
    } else {
      console.warn('Unexpected response structure', res);
      tableData.value = [];
      pagination.total = 0;
    }
  } catch (error) {
    console.error('Fetch error:', error);
    message.error('获取列表失败');
  } finally {
    loading.value = false;
  }
};

const handleSelectionChange = (selectedKeys: any[]) => {
  selectedRowKeys.value = selectedKeys as number[];
};

const handleBatchAction = () => {
  let initialUsers = [] as number[];
  if (selectedRowKeys.value.length > 0) {
    initialUsers = selectedRowKeys.value.map((id) => {
      const row: any = tableData.value.find((r: any) => r.id === id);
      return row ? row.user : id;
    });
  }

  Object.assign(formState, {
    user_ids: initialUsers,
    quota_type: 'monthly',
    token_limit: 500000,
    reset_at: dayjs().endOf('month'),
  });
  batchVisible.value = true;
};

const submitBatchReset = async () => {
  try {
    await batchFormRef.value.validate();
    submitting.value = true;

    await batchSetAiQuotasApi({
      user_ids: formState.user_ids,
      quota_type: formState.quota_type,
      token_limit: formState.token_limit,
      reset_at: formState.reset_at ? formState.reset_at.toISOString() : null,
    });
    
    message.success('批量更新用户配额成功');
    batchVisible.value = false;
    selectedRowKeys.value = [];
    fetchData();
  } catch (error: any) {
    if (!error.errorFields) message.error('提交失败');
  } finally {
    submitting.value = false;
  }
};

const handleEdit = (record: any) => {
  editingId.value = record.id;
  Object.assign(editFormState, {
    quota_type: record.quota_type || 'monthly',
    token_limit: record.token_limit || 100000,
    reset_at: record.reset_at ? dayjs(record.reset_at) : null,
  });
  editVisible.value = true;
};

const submitEdit = async () => {
  if (!editingId.value) return;
  try {
    submitting.value = true;
    await updateAiQuotaApi(editingId.value, {
      quota_type: editFormState.quota_type,
      token_limit: editFormState.token_limit,
      reset_at: editFormState.reset_at ? editFormState.reset_at.toISOString() : null,
    });
    message.success('配额已修改');
    editVisible.value = false;
    fetchData();
  } catch (err) {
    message.error('修改失败');
  } finally {
    submitting.value = false;
  }
};

const handleReset = async (record: any) => {
  try {
    await resetAiQuotaApi(record.id);
    message.success('用量已重置清零，用户可继续对话！');
    fetchData();
  } catch {
    message.error('操作失败');
  }
};

const handleDelete = async (record: any) => {
  try {
    await deleteAiQuotaApi(record.id);
    message.success('配额已移除');
    fetchData();
  } catch {
    message.error('删除配额失败');
  }
};

const handleTableChange = (pag: any) => {
  pagination.current = pag.current;
  pagination.pageSize = pag.pageSize;
  fetchData();
};

const fetchUsers = async () => {
  try {
    const res: any = await getUserList({ page_size: 1000 });
    const items = res?.results || res?.data?.results || res?.data?.data?.results || res?.data?.items || res?.data?.list || (Array.isArray(res) ? res : (Array.isArray(res?.data) ? res.data : []));
    sysUserList.value = items;
  } catch (err) {
    console.error('Failed to load users:', err);
  }
};

onMounted(() => {
  fetchUsers();
  fetchData();
});
</script>

<template>
  <div class="p-4">
    <Card title="用户策略下推表 (AI额度管控)">
      <div class="mb-4 flex gap-4 w-full">
        <Space>
          <Button @click="fetchData">刷新最新余量</Button>
        </Space>
        
        <div class="flex-grow flex justify-end">
          <Button type="primary" @click="handleBatchAction">
            <template #icon><SendOutlined /></template>
            批量发放空投额度
          </Button>
        </div>
      </div>

      <Table
        :columns="columns"
        :data-source="tableData"
        :loading="loading"
        :pagination="pagination"
        :row-selection="{ selectedRowKeys: selectedRowKeys, onChange: handleSelectionChange }"
        @change="handleTableChange"
        row-key="id"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'action'">
            <Space>
              <Button type="link" size="small" @click="handleEdit(record)">
                编辑
              </Button>
              <Popconfirm v-if="record.tokens_used >= record.token_limit" title="确定特许重置此人的配额用量清零吗？" @confirm="handleReset(record)">
                <Button type="link" danger size="small">解挂重置</Button>
              </Popconfirm>
              <Button v-else type="link" class="text-gray-500" size="small" @click="handleReset(record)">
                 清零用量
              </Button>
              <Popconfirm title="确定回收此人的配额并永久删除吗？" @confirm="handleDelete(record)">
                <Button type="link" danger size="small">删除</Button>
              </Popconfirm>
            </Space>
          </template>
        </template>
      </Table>
    </Card>

    <Modal
      v-model:open="batchVisible"
      title="配额批量下发"
      @ok="submitBatchReset"
      :confirm-loading="submitting"
    >
      <div class="mb-4 text-orange-500 text-sm">
        您正在将新的配额量统向下发应用到勾选的人群中（覆盖已有策略）。
      </div>
      <Form ref="batchFormRef" :model="formState" layout="vertical">
        <Form.Item label="选择下发用户" name="user_ids" :rules="[{ required: true, message: '请至少选择一个用户' }]">
          <Select
            v-model:value="formState.user_ids"
            mode="multiple"
            placeholder="请选择要赋权的用户"
            show-search
            :options="sysUserList.map(u => ({ value: u.id, label: u.username || u.name || `User ${u.id}` }))"
          />
        </Form.Item>
        <Form.Item label="配额周期" name="quota_type">
          <Select v-model:value="formState.quota_type">
            <Select.Option value="total">永久总用量上限</Select.Option>
            <Select.Option value="monthly">按月刷新单号上限</Select.Option>
            <Select.Option value="daily">按天单号上限</Select.Option>
          </Select>
        </Form.Item>

        <Form.Item label="万字 Token 额度设定 (包含问题与生成总体)" name="token_limit">
          <InputNumber v-model:value="formState.token_limit" :min="1000" :step="50000" style="width: 100%" />
        </Form.Item>

        <Form.Item label="何时清空用量重回巅峰" name="reset_at" v-if="formState.quota_type !== 'total'">
          <DatePicker show-time v-model:value="formState.reset_at" style="width: 100%" placeholder="选择额度恢复零的时间点" />
        </Form.Item>
      </Form>
    </Modal>
  
    <Modal
      v-model:open="editVisible"
      title="修改个人配额"
      @ok="submitEdit"
      :confirm-loading="submitting"
    >
      <Form :model="editFormState" layout="vertical">
        <Form.Item label="配额周期" name="quota_type">
          <Select v-model:value="editFormState.quota_type">
            <Select.Option value="total">永久总用量上限</Select.Option>
            <Select.Option value="monthly">按月刷新单号上限</Select.Option>
            <Select.Option value="daily">按天单号上限</Select.Option>
          </Select>
        </Form.Item>

        <Form.Item label="万字 Token 额度设定" name="token_limit">
          <InputNumber v-model:value="editFormState.token_limit" :min="1000" :step="50000" style="width: 100%" />
        </Form.Item>

        <Form.Item label="重置点" name="reset_at" v-if="editFormState.quota_type !== 'total'">
          <DatePicker show-time v-model:value="editFormState.reset_at" style="width: 100%" placeholder="修改额度恢复时间" />
        </Form.Item>
      </Form>
    </Modal>
  </div>
</template>
