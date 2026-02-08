<script setup lang="ts">
import type { CreateNodeParams, PVEServerModel } from '#/api/pve/types';

import { onMounted, reactive, ref } from 'vue';

import {
  DeleteOutlined,
  EditOutlined,
  PlusOutlined,
  SearchOutlined,
  ThunderboltOutlined,
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
  Space,
  Switch,
  Table,
  Tag,
  Textarea,
} from 'ant-design-vue';

import {
  createNodeApi,
  deleteNodeApi,
  getNodeListApi,
  testNodeConnectionApi,
  updateNodeApi,
} from '#/api/pve/node';
import { usePermission } from '#/hooks/usePermission';

defineOptions({
  name: 'PVEServer',
});

// Permission checking
const { hasPermission } = usePermission();

const columns = [
  { title: 'ID', dataIndex: 'id', key: 'id', width: 80 },
  { title: '服务器名称', dataIndex: 'name', key: 'name' },
  { title: '服务器地址', dataIndex: 'host', key: 'host' },
  { title: '端口', dataIndex: 'port', key: 'port', width: 80 },
  { title: 'Token ID', dataIndex: 'token_id', key: 'token_id' },
  { title: '状态', dataIndex: 'is_active', key: 'is_active', width: 100 },
  { title: '创建时间', dataIndex: 'created_at', key: 'created_at', width: 200 },
  { title: '操作', key: 'action', width: 250 },
];

const loading = ref(false);
const tableData = ref<PVEServerModel[]>([]);
const searchText = ref('');

// Modal state
const modalVisible = ref(false);
const modalLoading = ref(false);
const isEdit = ref(false);
const currentId = ref<number | string>('');

const formRef = ref();
const formState = reactive<CreateNodeParams>({
  name: '',
  host: '',
  port: 8006,
  token_id: '',
  token_secret: '',
  verify_ssl: false,
  remark: '',
  is_active: true,
});

const rules: any = {
  name: [{ required: true, message: '请输入服务器名称', trigger: 'blur' }],
  host: [{ required: true, message: '请输入服务器地址', trigger: 'blur' }],
  port: [{ required: true, message: '请输入端口', trigger: 'blur' }],
  token_id: [{ required: true, message: '请输入 Token ID', trigger: 'blur' }],
  token_secret: [
    { required: true, message: '请输入 Token Secret', trigger: 'blur' },
  ],
};

const fetchData = async () => {
  loading.value = true;
  try {
    const res = await getNodeListApi();
    if (Array.isArray(res)) {
      tableData.value = res;
    } else if (res && Array.isArray((res as any).results)) {
      tableData.value = (res as any).results;
    } else if (
      res &&
      (res as any).data &&
      Array.isArray((res as any).data.results)
    ) {
      // Handle case where response object might be returned instead of data
      tableData.value = (res as any).data.results;
    } else if (res && Array.isArray((res as any).data)) {
      tableData.value = (res as any).data;
    } else {
      tableData.value = [];
    }
  } catch (error: any) {
    message.error(`获取服务器列表失败: ${error.message || '未知错误'}`);
  } finally {
    loading.value = false;
  }
};

const handleAdd = () => {
  isEdit.value = false;
  currentId.value = '';
  Object.assign(formState, {
    name: '',
    host: '',
    port: 8006,
    token_id: '',
    token_secret: '',
    verify_ssl: false,
    remark: '',
    is_active: true,
  });
  modalVisible.value = true;
};

const handleEdit = (record: any) => {
  isEdit.value = true;
  currentId.value = record.id;
  // 这里需要注意，如果是编辑，Token Secret 可能不需要回显或者处理为空不修改
  Object.assign(formState, {
    name: record.name,
    host: record.host,
    port: record.port,
    token_id: record.token_id,
    token_secret: '', // 通常不回显敏感信息，或者留空表示不修改
    verify_ssl: record.verify_ssl,
    remark: record.remark,
    is_active: record.is_active,
  });
  modalVisible.value = true;
};

const handleDelete = async (record: any) => {
  try {
    await deleteNodeApi(record.id);
    message.success('删除成功');
    fetchData();
  } catch (error: any) {
    message.error(`删除失败: ${error.message}`);
  }
};

const handleTestConnection = async (record: any) => {
  try {
    loading.value = true;
    await testNodeConnectionApi(record.id);
    message.success('连接测试成功');
    fetchData(); // 刷新状态
  } catch (error: any) {
    message.error(`连接测试失败: ${error.message}`);
  } finally {
    loading.value = false;
  }
};

const handleModalOk = () => {
  formRef.value
    .validate()
    .then(async () => {
      modalLoading.value = true;
      try {
        if (isEdit.value) {
          // 如果是编辑且 secret 为空，可能需要移除该字段以免覆盖（视后端逻辑而定）
          // 这里简单处理，假设后端支持 partial update 或忽略空 secret
          const payload = { ...formState };
          if (!payload.token_secret) delete (payload as any).token_secret;

          await updateNodeApi(currentId.value, payload);
          message.success('更新成功');
        } else {
          await createNodeApi(formState);
          message.success('创建成功');
        }
        modalVisible.value = false;
        fetchData();
      } catch (error: any) {
        console.error(error);
        // message.error(`操作失败: ${error.message || '未知错误'}`);
      } finally {
        modalLoading.value = false;
      }
    })
    .catch((error: any) => {
      console.log('Validate Failed:', error);
    });
};

const handleModalCancel = () => {
  modalVisible.value = false;
};

onMounted(() => {
  fetchData();
});
</script>

<template>
  <div class="p-5">
    <Card title="PVE服务器管理" :bordered="false">
      <div class="mb-4 flex items-center justify-between">
        <Space>
          <Input
            v-model:value="searchText"
            placeholder="搜索服务器名称或地址"
            style="width: 250px"
            allow-clear
          >
            <template #prefix><SearchOutlined /></template>
          </Input>
          <Button
            v-if="hasPermission('pve_server:create')"
            type="primary"
            @click="handleAdd"
          >
            <template #icon><PlusOutlined /></template>
            新增服务器
          </Button>
        </Space>
      </div>

      <Table
        :columns="columns"
        :data-source="tableData"
        :loading="loading"
        :pagination="{ pageSize: 20 }"
        row-key="id"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'is_active'">
            <Tag :color="record.is_active ? 'success' : 'error'">
              {{ record.is_active ? '启用' : '禁用' }}
            </Tag>
          </template>

          <template v-else-if="column.key === 'action'">
            <Space>
              <Button
                v-if="hasPermission('pve_server:test_connection')"
                size="small"
                type="link"
                @click="handleTestConnection(record)"
              >
                <template #icon><ThunderboltOutlined /></template>
                测试连接
              </Button>
              <Button
                v-if="hasPermission('pve_server:update')"
                size="small"
                type="link"
                @click="handleEdit(record)"
              >
                <template #icon><EditOutlined /></template>
                编辑
              </Button>
              <Popconfirm
                v-if="hasPermission('pve_server:delete')"
                title="确定要删除此服务器吗？"
                ok-text="确定"
                cancel-text="取消"
                @confirm="handleDelete(record)"
              >
                <Button size="small" type="link" danger>
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
      v-model:open="modalVisible"
      :title="isEdit ? '编辑服务器' : '新增服务器'"
      @ok="handleModalOk"
      @cancel="handleModalCancel"
      :confirm-loading="modalLoading"
      width="600px"
    >
      <Form ref="formRef" :model="formState" :rules="rules" layout="vertical">
        <Form.Item label="服务器名称" name="name">
          <Input
            v-model:value="formState.name"
            placeholder="请输入服务器名称"
          />
        </Form.Item>

        <div class="grid grid-cols-2 gap-4">
          <Form.Item label="服务器地址" name="host">
            <Input
              v-model:value="formState.host"
              placeholder="如: 192.168.1.100"
            />
          </Form.Item>
          <Form.Item label="端口" name="port">
            <InputNumber
              v-model:value="formState.port"
              :min="1"
              :max="65535"
              style="width: 100%"
            />
          </Form.Item>
        </div>

        <div class="grid grid-cols-2 gap-4">
          <Form.Item label="Token ID" name="token_id">
            <Input
              v-model:value="formState.token_id"
              placeholder="API Token ID (User@Realm!TokenName)"
            />
          </Form.Item>
          <Form.Item label="Token Secret" name="token_secret">
            <Input.Password
              v-model:value="formState.token_secret"
              placeholder="API Token Secret"
              allow-clear
            />
          </Form.Item>
        </div>

        <div class="mb-4 flex items-center gap-8">
          <Form.Item label="验证SSL" name="verify_ssl" class="mb-0">
            <Switch v-model:checked="formState.verify_ssl" />
          </Form.Item>
          <Form.Item label="启用状态" name="is_active" class="mb-0">
            <Switch v-model:checked="formState.is_active" />
          </Form.Item>
        </div>

        <Form.Item label="备注" name="remark">
          <Textarea
            v-model:value="formState.remark"
            placeholder="请输入备注信息"
            :rows="3"
          />
        </Form.Item>
      </Form>
    </Modal>
  </div>
</template>
