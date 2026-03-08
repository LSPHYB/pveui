<script setup lang="ts">
import { onMounted, reactive, ref, h } from 'vue';
import { PlusOutlined } from '@ant-design/icons-vue';
import {
  Button,
  Card,
  Form,
  Input,
  InputNumber,
  Select,
  Space,
  Switch,
  Table,
  Modal,
  Popconfirm,
  message,
} from 'ant-design-vue';
import type { TableColumnsType } from 'ant-design-vue';
import {
  getAiModelsApi,
  createAiModelApi,
  updateAiModelApi,
  deleteAiModelApi,
  toggleAiModelApi,
  getAiApiKeysApi,
  testAiModelConnectionApi,
} from '#/api/ai';

defineOptions({ name: 'AiModelConfig' });

const loading = ref(false);
const tableData = ref<any[]>([]);
const apiKeysList = ref<any[]>([]);
const searchText = ref('');
const testingIds = ref<number[]>([]);
const pagination = reactive({
  current: 1,
  pageSize: 20,
  total: 0,
});

const formRef = ref();
const modalVisible = ref(false);
const submitting = ref(false);
const modalTitle = ref('新增模型');

const formState = reactive({
  id: null as null | number,
  model_key: '',
  model_name: '',
  model_type: '',
  api_key: undefined as undefined | number,
  temperature_default: 0.7,
  max_tokens: 4000,
  is_enabled: true,
  is_default: false,
});

const columns: TableColumnsType = [
  { title: '模型标识', dataIndex: 'model_key', width: 150 },
  { title: '模型名称', dataIndex: 'model_name', width: 150 },
  { title: '最大Tokens', dataIndex: 'max_tokens', width: 120 },
  {
    title: '启用状态',
    dataIndex: 'is_enabled',
    width: 100,
    customRender: ({ record }) => {
      return h(Switch, {
        checked: record.is_enabled,
        onChange: (val: any) => handleToggleStatus(record.id, val as boolean),
      });
    },
  },
  {
    title: '默认',
    dataIndex: 'is_default',
    width: 80,
    customRender: ({ text }) => (text ? '是' : '否'),
  },
  { title: '操作', key: 'action', width: 120, fixed: 'right' },
];

const fetchData = async () => {
  loading.value = true;
  try {
    const res: any = await getAiModelsApi({
      page: pagination.current,
      page_size: pagination.pageSize,
      search: searchText.value || undefined,
    });
    console.log('AI Models Response:', res);
    
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

const handleCreate = () => {
  modalTitle.value = '新增模型';
  Object.assign(formState, {
    id: null,
    model_key: '',
    model_name: '',
    model_type: 'chat',
    api_key: apiKeysList.value.length > 0 ? apiKeysList.value[0].id : undefined,
    temperature_default: 0.7,
    max_tokens: 4000,
    is_enabled: true,
    is_default: false,
  });
  modalVisible.value = true;
};

const handleEdit = (record: any) => {
  modalTitle.value = '编辑模型';
  Object.assign(formState, record);
  modalVisible.value = true;
};

const handleDelete = async (record: any) => {
  try {
    await deleteAiModelApi(record.id);
    message.success('删除成功');
    fetchData();
  } catch {
    message.error('删除失败');
  }
};

const handleTestConnection = async (record: any) => {
  testingIds.value.push(record.id);
  try {
    const res: any = await testAiModelConnectionApi(record.id);
    const msg = res?.message || res?.data?.message || '测试成功';
    message.success(msg);
  } catch (error: any) {
    const msg = error?.response?.data?.message || error?.message || '连通性测试失败';
    message.error(msg);
  } finally {
    testingIds.value = testingIds.value.filter(id => id !== record.id);
  }
};

const handleToggleStatus = async (id: number, status: boolean) => {
  try {
    await toggleAiModelApi(id, status);
    message.success('状态更新成功');
    fetchData();
  } catch {
    message.error('状态更新失败');
  }
};

const handleSubmit = async () => {
  try {
    await formRef.value.validate();
    submitting.value = true;

    if (formState.id) {
      await updateAiModelApi(formState.id, formState);
      message.success('更新成功');
    } else {
      await createAiModelApi(formState);
      message.success('创建成功');
    }
    modalVisible.value = false;
    fetchData();
  } catch (error: any) {
    if (!error.errorFields) {
      message.error('提交失败');
    }
  } finally {
    submitting.value = false;
  }
};

const handleTableChange = (pag: any) => {
  pagination.current = pag.current;
  pagination.pageSize = pag.pageSize;
  fetchData();
};

const fetchApiKeys = async () => {
  try {
    const res: any = await getAiApiKeysApi({ page_size: 1000 });
    const items = res?.results || res?.data?.results || res?.data?.data?.results || res?.data?.items || res?.data?.list || (Array.isArray(res) ? res : (Array.isArray(res?.data) ? res.data : []));
    apiKeysList.value = items.filter((k: any) => k.is_active);
  } catch (err) {
    console.error('Failed to load API keys:', err);
  }
};

onMounted(() => {
  fetchApiKeys();
  fetchData();
});
</script>

<template>
  <div class="p-4">
    <Card title="AI 模型配置">
      <div class="mb-4 flex justify-between">
        <Space>
          <Input.Search
            v-model:value="searchText"
            placeholder="搜索模型名称"
            style="width: 250px"
            allow-clear
            @search="fetchData"
          />
        </Space>
        <Button type="primary" @click="handleCreate">
          <template #icon><PlusOutlined /></template>
          新增模型
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
                :loading="testingIds.includes(record.id)"
                @click="handleTestConnection(record)"
              >测试</Button>
              <Button type="link" size="small" @click="handleEdit(record)">编辑</Button>
              <Popconfirm title="确定要删除吗？" @confirm="handleDelete(record)">
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
      :confirm-loading="submitting"
    >
      <Form ref="formRef" :model="formState" layout="vertical">
        <div class="grid grid-cols-2 gap-4">
          <Form.Item label="绑定的 API Key (通道)" name="api_key" :rules="[{ required: true, message: '请选择 API Key' }]">
            <Select v-model:value="formState.api_key" placeholder="选择通道">
              <Select.Option v-for="k in apiKeysList" :key="k.id" :value="k.id">
                [{{ k.provider }}] {{ k.key_name }}
              </Select.Option>
            </Select>
          </Form.Item>
          <Form.Item label="API 调用模型名 (Model ID)" name="model_key" :rules="[{ required: true }]" tooltip="填写实际给代理接口发送的模型 ID。如：gpt-4o, claude-3-5-sonnet">
            <Input v-model:value="formState.model_key" placeholder="如 gpt-4o" />
          </Form.Item>
        </div>
        
        <div class="grid grid-cols-2 gap-4">
          <Form.Item label="前台显示名称" name="model_name" :rules="[{ required: true }]" tooltip="展示给用户看的友好名称">
            <Input v-model:value="formState.model_name" placeholder="如 GPT-4 Omni" />
          </Form.Item>
        </div>

        <div class="grid grid-cols-2 gap-4">
          <Form.Item label="默认 Temperature">
            <InputNumber v-model:value="formState.temperature_default" :min="0" :max="2" :step="0.1" style="width: 100%" />
          </Form.Item>
          <Form.Item label="最大 Tokens">
            <InputNumber v-model:value="formState.max_tokens" :min="1" style="width: 100%" />
          </Form.Item>
        </div>

        <div class="grid grid-cols-2 gap-4 mt-2">
          <Form.Item label="是否启用">
            <Switch v-model:checked="formState.is_enabled" />
          </Form.Item>
          <Form.Item label="是否为系统默认">
            <Switch v-model:checked="formState.is_default" />
          </Form.Item>
        </div>
      </Form>
    </Modal>
  </div>
</template>
