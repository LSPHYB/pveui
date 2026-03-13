<script setup lang="ts">
import { onMounted, reactive, ref, h } from 'vue';
import { PlusOutlined, SyncOutlined } from '@ant-design/icons-vue';
import {
  Button,
  Card,
  Form,
  Input,
  InputNumber,
  Select,
  Space,
  Table,
  Modal,
  Popconfirm,
  message,
  Tag,
} from 'ant-design-vue';
import type { TableColumnsType } from 'ant-design-vue';
import {
  getAiApiKeysApi,
  createAiApiKeyApi,
  rotateAiApiKeyApi,
  disableAiApiKeyApi,
  deleteAiApiKeyApi,
} from '#/api/ai';

defineOptions({ name: 'AiApiKeyConfig' });

const loading = ref(false);
const tableData = ref<any[]>([]);
const pagination = reactive({
  current: 1,
  pageSize: 20,
  total: 0,
});

const formRef = ref();
const modalVisible = ref(false);
const submitting = ref(false);

const formState = reactive({
  provider: 'openai',
  key_name: '',
  base_url: '',
  api_key: '',
  priority: 0,
  daily_token_limit: 1000000,
});

const rotateVisible = ref(false);
const rotateState = reactive({
  id: null as null | number,
  new_api_key: '',
});

const columns: TableColumnsType = [
  { title: '所属平台', dataIndex: 'provider', width: 120 },
  { title: '密钥名称', dataIndex: 'key_name', width: 150 },
  { title: 'Base URL', dataIndex: 'base_url', width: 220, customRender: ({ text }) => text || h(Tag, {}, () => '默认直连') },
  { title: '掩码密钥', dataIndex: 'api_key_masked', width: 150 },
  {
    title: '权重优先级',
    dataIndex: 'priority',
    width: 100,
    sorter: true,
  },
  {
    title: '每日限额使用情况',
    key: 'usage',
    width: 200,
    customRender: ({ record }) => {
      const limit = record.daily_token_limit || 0;
      const used = record.daily_tokens_used || 0;
      let percent = 0;
      if (limit > 0) {
        percent = Number(((used / limit) * 100).toFixed(1));
      }
      return `${used} / ${limit !== 0 ? limit : '无限制'}` + (percent > 0 ? ` (${percent}%)` : '');
    },
  },
  {
    title: '状态',
    dataIndex: 'is_active',
    width: 100,
    customRender: ({ text }) => {
      return text ? h(Tag, { color: 'success' }, () => '正常') : h(Tag, { color: 'error' }, () => '禁用');
    },
  },
  {
    title: '错误计数',
    dataIndex: 'error_count',
    width: 100,
    customRender: ({ text }) => {
      return Number(text) > 0 ? h(Tag, { color: 'warning' }, () => `${text} 次`) : '0';
    },
  },
  { title: '操作', key: 'action', width: 200, fixed: 'right' },
];

const fetchData = async () => {
  loading.value = true;
  try {
    const res: any = await getAiApiKeysApi({
      page: pagination.current,
      page_size: pagination.pageSize,
    });
    console.log('API Keys Response:', res);
    
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
  Object.assign(formState, {
    provider: 'openai',
    key_name: '',
    base_url: '',
    api_key: '',
    priority: 0,
    daily_token_limit: 1000000,
  });
  modalVisible.value = true;
};

const handleSubmit = async () => {
  try {
    await formRef.value.validate();
    submitting.value = true;
    await createAiApiKeyApi(formState);
    message.success('创建成功');
    modalVisible.value = false;
    fetchData();
  } catch (error: any) {
    if (!error.errorFields) message.error('提交失败');
  } finally {
    submitting.value = false;
  }
};

const handleRotate = (record: any) => {
  rotateState.id = record.id;
  rotateState.new_api_key = '';
  rotateVisible.value = true;
};

const submitRotate = async () => {
  if (!rotateState.new_api_key) {
    message.warning('请输入新的API Key');
    return;
  }
  try {
    submitting.value = true;
    await rotateAiApiKeyApi(rotateState.id as number, {
      new_api_key: rotateState.new_api_key,
    });
    message.success('轮换成功，旧密钥已禁用并创建了新密钥');
    rotateVisible.value = false;
    fetchData();
  } catch {
    message.error('轮换失败');
  } finally {
    submitting.value = false;
  }
};

const handleDisable = async (record: any) => {
  try {
    await disableAiApiKeyApi(record.id);
    message.success('已禁用');
    fetchData();
  } catch {
    message.error('操作失败');
  }
};

const handleDelete = async (record: any) => {
  try {
    await deleteAiApiKeyApi(record.id);
    message.success('已删除');
    fetchData();
  } catch {
    message.error('删除失败');
  }
};

const handleTableChange = (pag: any) => {
  pagination.current = pag.current;
  pagination.pageSize = pag.pageSize;
  fetchData();
};

onMounted(() => {
  fetchData();
});
</script>

<template>
  <div class="p-4">
    <Card title="API Key 收纳匣">
      <div class="mb-4 flex justify-between">
        <Space>
          <Button @click="fetchData"><template #icon><SyncOutlined /></template>刷新状态</Button>
        </Space>
        <Button type="primary" @click="handleCreate">
          <template #icon><PlusOutlined /></template>
          录入密钥
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
              <Button type="link" size="small" @click="handleRotate(record)" :disabled="!record.is_active">
                轮换(Rotate)
              </Button>
              <Popconfirm
                v-if="record.is_active"
                title="确定要禁用并剔除调度队列吗？"
                @confirm="handleDisable(record)"
              >
                <Button type="link" class="text-yellow-600" size="small">禁用</Button>
              </Popconfirm>
              <Popconfirm
                title="确定要永久删除此 API Key 记录吗？关联统计将保留"
                @confirm="handleDelete(record)"
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
      title="录入新的 API Key"
      @ok="handleSubmit"
      :confirm-loading="submitting"
    >
      <Form ref="formRef" :model="formState" layout="vertical">
        <Form.Item label="所属平台" name="provider" :rules="[{ required: true }]">
          <Select v-model:value="formState.provider">
            <Select.Option value="openai">OpenAI</Select.Option>
            <Select.Option value="anthropic">Anthropic</Select.Option>
            <Select.Option value="custom">Self-Hosted</Select.Option>
          </Select>
        </Form.Item>
        <Form.Item label="密钥助记名" name="key_name" :rules="[{ required: true }]">
          <Input v-model:value="formState.key_name" placeholder="如 '财务部主Key-01'" />
        </Form.Item>
        <Form.Item label="Base URL (自定义代理地址)" name="base_url">
          <Input v-model:value="formState.base_url" placeholder="如 https://api.openai-proxy.com/v1（为空代表默认官方直连）" />
        </Form.Item>
        <Form.Item label="API Key 明文" name="api_key" :rules="[{ required: true }]">
          <Input.Password v-model:value="formState.api_key" placeholder="输入明文密钥（平台将单向加密存储）" />
        </Form.Item>
        
        <div class="grid grid-cols-2 gap-4 mt-2">
          <Form.Item label="调度优先级 (优先用大数)">
            <InputNumber v-model:value="formState.priority" :min="0" style="width: 100%" />
          </Form.Item>
          <Form.Item label="单日 Token 消耗限制">
            <InputNumber v-model:value="formState.daily_token_limit" :min="0" style="width: 100%" />
          </Form.Item>
        </div>
      </Form>
    </Modal>

    <Modal
      v-model:open="rotateVisible"
      title="轮换(Rotate) API Key"
      @ok="submitRotate"
      :confirm-loading="submitting"
      ok-text="确认轮换"
    >
      <div class="mb-4 text-orange-500">
        轮换后，原密钥将被禁用不再参与分配。系统将保留原始使用量数据，并创建一个带有(Rotated)后缀的全新记录。
      </div>
      <Form layout="vertical">
        <Form.Item label="录入新的 API Key 明文" required>
          <Input.Password v-model:value="rotateState.new_api_key" placeholder="新的明文密钥" />
        </Form.Item>
      </Form>
    </Modal>
  </div>
</template>
