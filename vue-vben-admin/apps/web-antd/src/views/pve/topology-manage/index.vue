<script setup lang="ts">
import type { NetworkTopologyModel, NetworkTopologySaveParams } from '#/api/pve/types';

import { onMounted, reactive, ref } from 'vue';
import { useRouter } from 'vue-router';

import {
  DeleteOutlined,
  EditOutlined,
  EyeOutlined,
  SearchOutlined,
} from '@ant-design/icons-vue';
import {
  Button,
  Card,
  Form,
  Input,
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
  deleteTopologyApi,
  getTopologyListApi,
  updateTopologyApi,
} from '#/api/pve/topology-manage';

defineOptions({ name: 'PVETopologyManage' });

const router = useRouter();

const columns = [
  { title: 'ID', dataIndex: 'id', key: 'id', width: 60 },
  { title: '拓扑名称', dataIndex: 'name', key: 'name', width: 180 },
  { title: '描述', dataIndex: 'description', key: 'description', ellipsis: true, width: 200 },
  { title: '状态', dataIndex: 'is_active', key: 'is_active', width: 80 },
  { title: '创建时间', dataIndex: 'created_at', key: 'created_at', width: 160 },
  { title: '操作', key: 'action', width: 150 },
];

const loading = ref(false);
const tableData = ref<NetworkTopologyModel[]>([]);
const searchText = ref('');

const modalVisible = ref(false);
const modalLoading = ref(false);
const currentId = ref<number | string>('');

const formRef = ref();
const formState = reactive<Omit<NetworkTopologySaveParams, 'diagram_data' | 'metadata'>>({
  name: '',
  description: '',
  is_active: true,
  remark: '',
});
const rules: any = {
  name: [{ required: true, message: '请输入拓扑名称', trigger: 'blur' }],
};

const normalizeList = (res: any): NetworkTopologyModel[] => {
  if (Array.isArray(res)) return res;
  if (res?.results) return res.results;
  if (Array.isArray(res?.data)) return res.data;
  if (res?.data?.results) return res.data.results;
  return [];
};

const fetchData = async () => {
  loading.value = true;
  try {
    const res = await getTopologyListApi(
      searchText.value ? { search: searchText.value } : undefined,
    );
    tableData.value = normalizeList(res);
  } catch (error: any) {
    message.error(`获取拓扑列表失败: ${error.message}`);
  } finally {
    loading.value = false;
  }
};

const handleEdit = (record: any) => {
  currentId.value = record.id;
  Object.assign(formState, {
    name: record.name,
    description: record.description ?? '',
    is_active: record.is_active,
    remark: record.remark ?? '',
  });
  modalVisible.value = true;
};

const handleDelete = async (record: any) => {
  try {
    await deleteTopologyApi(record.id);
    message.success('删除成功');
    fetchData();
  } catch (error: any) {
    message.error(`删除失败: ${error.message}`);
  }
};

const handlePreview = (record: any) => {
  router.push({ path: '/pve/topology', query: { id: String(record.id) } });
};

const handleModalOk = () => {
  formRef.value.validate().then(async () => {
    modalLoading.value = true;
    try {
      await updateTopologyApi(currentId.value, { ...formState });
      message.success('更新成功');
      modalVisible.value = false;
      fetchData();
    } catch (error: any) {
      message.error(`操作失败: ${error.message}`);
    } finally {
      modalLoading.value = false;
    }
  });
};

onMounted(() => fetchData());
</script>

<template>
  <div class="p-5">
    <Card title="拓扑管理" :bordered="false">
      <div class="mb-4">
        <Input
          v-model:value="searchText"
          placeholder="搜索拓扑名称或描述"
          style="width: 250px"
          allow-clear
          @change="fetchData"
        >
          <template #prefix><SearchOutlined /></template>
        </Input>
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
              <Button size="small" type="link" @click="handlePreview(record)">
                <template #icon><EyeOutlined /></template>
                预览
              </Button>
              <Button size="small" type="link" @click="handleEdit(record)">
                <template #icon><EditOutlined /></template>
                编辑
              </Button>
              <Popconfirm
                title="确定要删除此拓扑吗？"
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

    <!-- 编辑弹窗 -->
    <Modal
      v-model:open="modalVisible"
      title="编辑拓扑信息"
      :confirm-loading="modalLoading"
      @ok="handleModalOk"
      @cancel="modalVisible = false"
    >
      <Form ref="formRef" :model="formState" :rules="rules" layout="vertical" class="mt-4">
        <Form.Item label="拓扑名称" name="name">
          <Input v-model:value="formState.name" placeholder="请输入拓扑名称" />
        </Form.Item>
        <Form.Item label="描述" name="description">
          <Textarea
            v-model:value="formState.description"
            placeholder="描述（可选）"
            :rows="3"
          />
        </Form.Item>
        <Form.Item label="状态">
          <Switch
            v-model:checked="formState.is_active"
            checked-children="启用"
            un-checked-children="禁用"
          />
        </Form.Item>
        <Form.Item label="备注">
          <Input v-model:value="formState.remark" placeholder="备注（可选）" />
        </Form.Item>
      </Form>
    </Modal>
  </div>
</template>
