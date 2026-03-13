<script setup lang="ts">
import type { SystemSetting } from '#/api/system-setting';

import { computed, onMounted, reactive, ref } from 'vue';

import { PlusOutlined, SaveOutlined } from '@ant-design/icons-vue';
import {
  Button,
  Card,
  Form,
  Input,
  InputPassword,
  message,
  Modal,
  Popconfirm,
  Select,
  Space,
  Switch,
  Table,
  Tabs,
  Tag,
  Textarea,
} from 'ant-design-vue';

import {
  bulkUpdateSystemSettingsApi,
  createSystemSettingApi,
  deleteSystemSettingApi,
  getSystemSettingsApi,
  updateSystemSettingApi,
} from '#/api/system-setting';

defineOptions({ name: 'SystemSetting' });

const loading = ref(false);
const searchText = ref('');
const activeTab = ref('all');
const tableData = ref<SystemSetting[]>([]);
const changedSettings = ref<Set<number>>(new Set());

// Modal
const modalVisible = ref(false);
const modalTitle = ref('新增配置');
const isEdit = ref(false);
const formRef = ref();

const categories = [
  { key: 'all', label: '全部' },
  { key: 'ai', label: 'AI 配置' },
  { key: 'email', label: '邮件配置' },
  { key: 'storage', label: '存储配置' },
  { key: 'general', label: '通用配置' },
];

const columns = [
  { title: '配置键', dataIndex: 'key', width: 220 },
  { title: '配置值', dataIndex: 'value', key: 'value' },
  { title: '描述', dataIndex: 'description', width: 200 },
  {
    title: '加密',
    dataIndex: 'is_encrypted',
    width: 80,
    customRender: ({ record }: any) => (record.is_encrypted ? '是' : '否'),
  },
  {
    title: '公开',
    dataIndex: 'is_public',
    width: 80,
    customRender: ({ record }: any) => (record.is_public ? '是' : '否'),
  },
  { title: '操作', key: 'action', width: 150, fixed: 'right' as const },
];

const formData = reactive({
  id: undefined as number | undefined,
  key: '',
  value: '',
  description: '',
  category: 'general',
  is_encrypted: false,
  is_public: false,
  remark: '',
});

const getCategoryData = (category: string) => {
  let data = tableData.value;
  if (category !== 'all') {
    data = data.filter((item) => item.category === category);
  }
  if (searchText.value) {
    const search = searchText.value.toLowerCase();
    data = data.filter(
      (item) =>
        item.key.toLowerCase().includes(search) ||
        (item.description && item.description.toLowerCase().includes(search)),
    );
  }
  return data;
};

const hasChanges = computed(() => changedSettings.value.size > 0);

// Actions
const fetchData = async () => {
  loading.value = true;
  try {
    const res: any = await getSystemSettingsApi();
    if (Array.isArray(res)) {
      tableData.value = res;
    } else if (res.results) {
      tableData.value = res.results;
    } else {
      tableData.value = [];
    }
    changedSettings.value.clear();
  } catch {
    message.error('获取配置失败');
  } finally {
    loading.value = false;
  }
};

const handleCreate = () => {
  isEdit.value = false;
  modalTitle.value = '新增配置';
  Object.assign(formData, {
    id: undefined,
    key: '',
    value: '',
    description: '',
    category: 'general',
    is_encrypted: false,
    is_public: false,
    remark: '',
  });
  modalVisible.value = true;
};

const handleEdit = (record: SystemSetting) => {
  isEdit.value = true;
  modalTitle.value = '编辑配置';
  Object.assign(formData, {
    id: record.id,
    key: record.key,
    value: record.value,
    description: record.description,
    category: record.category,
    is_encrypted: record.is_encrypted,
    is_public: record.is_public,
    remark: record.remark || '',
  });
  modalVisible.value = true;
};

const handleDelete = async (id: number) => {
  try {
    await deleteSystemSettingApi(id);
    message.success('删除成功');
    fetchData();
  } catch {
    message.error('删除失败');
  }
};

const handleSubmit = async () => {
  try {
    await formRef.value.validate();
    if (isEdit.value && formData.id) {
      await updateSystemSettingApi(formData.id, formData);
      message.success('更新成功');
    } else {
      await createSystemSettingApi(formData);
      message.success('创建成功');
    }
    modalVisible.value = false;
    fetchData();
  } catch (error: any) {
    if (error.errorFields) return;
    message.error(`保存失败: ${error.response?.data?.detail || error.message}`);
  }
};

const handleValueChange = (record: SystemSetting) => {
  changedSettings.value.add(record.id);
};

const handleBulkUpdate = async () => {
  if (changedSettings.value.size === 0) return;

  const settingsToUpdate = tableData.value
    .filter((item) => changedSettings.value.has(item.id))
    .map((item) => ({
      key: item.key,
      value: item.value,
    }));

  try {
    await bulkUpdateSystemSettingsApi({ settings: settingsToUpdate });
    message.success(`成功保存 ${settingsToUpdate.length} 个配置`);
    changedSettings.value.clear();
    fetchData();
  } catch {
    message.error('批量更新失败');
  }
};

onMounted(() => {
  fetchData();
});
</script>

<template>
  <div class="p-4">
    <Card title="系统设置">
      <template #extra>
        <Space>
          <Input.Search
            v-model:value="searchText"
            placeholder="搜索配置键或描述"
            style="width: 250px"
            allow-clear
          />
          <Button type="primary" @click="handleCreate">
            <template #icon><PlusOutlined /></template>
            新增配置
          </Button>
          <Button :disabled="!hasChanges" @click="handleBulkUpdate">
            <template #icon><SaveOutlined /></template>
            保存所有更改
          </Button>
        </Space>
      </template>

      <Tabs v-model:active-key="activeTab" type="card">
        <Tabs.TabPane v-for="cat in categories" :key="cat.key" :tab="cat.label">
          <Table
            :columns="columns"
            :data-source="getCategoryData(cat.key)"
            :loading="loading"
            row-key="id"
            :pagination="false"
            size="small"
          >
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'value'">
                <!-- Inline Editing -->
                <InputPassword
                  v-if="record.is_encrypted"
                  v-model:value="record.value"
                  @change="handleValueChange(record)"
                />
                <Input
                  v-else
                  v-model:value="record.value"
                  @change="handleValueChange(record)"
                />
              </template>

              <template v-if="column.dataIndex === 'is_encrypted'">
                <Tag :color="record.is_encrypted ? 'orange' : 'blue'">
                  {{ record.is_encrypted ? '加密' : '明文' }}
                </Tag>
              </template>

              <template v-if="column.dataIndex === 'is_public'">
                <Tag :color="record.is_public ? 'green' : 'red'">
                  {{ record.is_public ? '公开' : '私有' }}
                </Tag>
              </template>

              <template v-if="column.key === 'action'">
                <Space>
                  <Button type="link" size="small" @click="handleEdit(record)">
                    编辑
                  </Button>
                  <Popconfirm
                    title="确定删除吗？"
                    @confirm="handleDelete(record.id)"
                  >
                    <Button type="link" danger size="small">删除</Button>
                  </Popconfirm>
                </Space>
              </template>
            </template>
          </Table>
        </Tabs.TabPane>
      </Tabs>
    </Card>

    <Modal
      v-model:open="modalVisible"
      :title="modalTitle"
      @ok="handleSubmit"
      width="600px"
    >
      <Form ref="formRef" :model="formData" layout="vertical">
        <Form.Item
          label="配置键"
          name="key"
          :rules="[
            { required: true, message: '请输入配置键' },
            {
              pattern: /^[a-z_][a-z0-9_]*$/,
              message: '只能包含小写字母、数字和下划线',
            },
          ]"
        >
          <Input
            v-model:value="formData.key"
            :disabled="isEdit"
            placeholder="例如: ai_openai_api_key"
          />
        </Form.Item>

        <Form.Item
          label="配置值"
          name="value"
          :rules="[{ required: true, message: '请输入配置值' }]"
        >
          <Textarea v-model:value="formData.value" :rows="3" />
        </Form.Item>

        <Form.Item label="描述" name="description">
          <Input v-model:value="formData.description" />
        </Form.Item>

        <Form.Item
          label="分类"
          name="category"
          :rules="[{ required: true, message: '请选择分类' }]"
        >
          <Select v-model:value="formData.category">
            <Select.Option value="general">通用配置</Select.Option>
            <Select.Option value="ai">AI 配置</Select.Option>
            <Select.Option value="email">邮件配置</Select.Option>
            <Select.Option value="storage">存储配置</Select.Option>
          </Select>
        </Form.Item>

        <Form.Item label="属性">
          <Space size="large">
            <Space>
              <span>是否加密:</span>
              <Switch v-model:checked="formData.is_encrypted" />
            </Space>
            <Space>
              <span>是否公开:</span>
              <Switch v-model:checked="formData.is_public" />
            </Space>
          </Space>
          <div class="mt-2 text-xs text-gray-400">
            加密：用于敏感信息（如API Key）；公开：可暴露给前端使用。
          </div>
        </Form.Item>
      </Form>
    </Modal>
  </div>
</template>
