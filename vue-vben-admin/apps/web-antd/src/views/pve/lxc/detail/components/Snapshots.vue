<script setup lang="ts">
import type { LxcContainerModel } from '#/api/pve/types';

import { computed, onMounted, ref, watch } from 'vue';

import {
  ClockCircleOutlined,
  DeleteOutlined,
  EditOutlined,
  PlusOutlined,
  ReloadOutlined,
  RollbackOutlined,
} from '@ant-design/icons-vue';
import {
  Button,
  Card,
  Form,
  FormItem,
  Input,
  message,
  Modal,
  Space,
  Spin,
  Table,
  Tag,
} from 'ant-design-vue';

import {
  createLxcSnapshotApi,
  deleteLxcSnapshotApi,
  getLxcSnapshotsApi,
  rollbackLxcSnapshotApi,
  updateLxcSnapshotApi,
} from '#/api/pve/lxc';

defineOptions({ name: 'LxcSnapshots' });

const props = defineProps<{
  lxc: null | LxcContainerModel;
  lxcId: string;
}>();

const loading = ref(false);
const snapshots = ref<any[]>([]);
const createModalVisible = ref(false);
const createLoading = ref(false);
const editModalVisible = ref(false);
const editLoading = ref(false);

const createForm = ref({
  name: '',
  description: '',
});

const editForm = ref({
  name: '',
  description: '',
});

const columns = [
  { title: '快照名称', dataIndex: 'name', key: 'name', width: 200 },
  {
    title: '描述',
    dataIndex: 'description',
    key: 'description',
    ellipsis: true,
  },
  { title: '创建时间', key: 'snaptime', width: 180 },
  { title: '状态', key: 'status', width: 120 },
  { title: '操作', key: 'action', width: 200, fixed: 'right' as const },
];

const formatTime = (timestamp: number) => {
  if (!timestamp) return '-';
  const date = new Date(timestamp * 1000);
  return date.toLocaleString('zh-CN');
};

// Exclude current
const displaySnapshots = computed(() => {
  return snapshots.value.filter((s) => s.name !== 'current');
});

const loadSnapshots = async () => {
  if (!props.lxcId) return;

  loading.value = true;
  try {
    const res: any = await getLxcSnapshotsApi(props.lxcId);
    const data = res?.data || res || {};
    // LXC snapshots structure - usually it is in `data` or `snapshots`
    snapshots.value = data.data || data.snapshots || data || []; 
  } catch (error: any) {
    message.error(error.message || '获取快照列表失败');
  } finally {
    loading.value = false;
  }
};

const handleCreateSnapshot = () => {
  createForm.value = {
    name: '',
    description: '',
  };
  createModalVisible.value = true;
};

const handleConfirmCreate = async () => {
  if (!props.lxcId) return;

  if (!createForm.value.name) {
    message.warning('请输入快照名称');
    return;
  }

  if (!/^[\w-]+$/.test(createForm.value.name)) {
    message.warning('快照名称只能包含字母、数字、下划线和中划线');
    return;
  }

  createLoading.value = true;
  try {
    await createLxcSnapshotApi(props.lxcId, createForm.value);
    message.success('快照创建任务已提交');
    createModalVisible.value = false;
    setTimeout(loadSnapshots, 3000);
  } catch (error: any) {
    message.error(error.message || '创建快照失败');
  } finally {
    createLoading.value = false;
  }
};

const handleRollback = (record: any) => {
  Modal.confirm({
    title: '确认回滚',
    content: `确定要回滚到快照 "${record.name}" 吗？`,
    okText: '确定',
    okType: 'primary',
    cancelText: '取消',
    onOk: async () => {
      if (!props.lxcId) return;
      try {
        await rollbackLxcSnapshotApi(props.lxcId, { name: record.name });
        message.success('快照回滚任务已提交');
        setTimeout(loadSnapshots, 2000);
      } catch (error: any) {
        message.error(error.message || '回滚失败');
      }
    },
  });
};

const handleDelete = (record: any) => {
  Modal.confirm({
    title: '确认删除',
    content: `确定要删除快照 "${record.name}" 吗？`,
    okText: '确定',
    okType: 'danger',
    cancelText: '取消',
    onOk: async () => {
      if (!props.lxcId) return;
      try {
        await deleteLxcSnapshotApi(props.lxcId, { name: record.name });
        message.success('快照删除任务已提交');
        setTimeout(loadSnapshots, 2000);
      } catch (error: any) {
        message.error(error.message || '删除失败');
      }
    },
  });
};

const handleEditDescription = (record: any) => {
  editForm.value = {
    name: record.name,
    description: record.description || '',
  };
  editModalVisible.value = true;
};

const handleConfirmEdit = async () => {
  if (!props.lxcId) return;

  editLoading.value = true;
  try {
    await updateLxcSnapshotApi(props.lxcId, editForm.value);
    message.success('快照描述已更新');
    editModalVisible.value = false;
    loadSnapshots();
  } catch (error: any) {
    message.error(error.message || '更新失败');
  } finally {
    editLoading.value = false;
  }
};

onMounted(() => {
  loadSnapshots();
});

watch(() => props.lxcId, loadSnapshots);
</script>

<template>
  <div class="h-full p-4">
    <Card title="快照管理" :bordered="false" class="h-full">
      <template #extra>
        <Space>
          <Button type="primary" @click="handleCreateSnapshot">
            <PlusOutlined /> 创建快照
          </Button>
          <Button @click="loadSnapshots" :loading="loading">
            <ReloadOutlined /> 刷新
          </Button>
        </Space>
      </template>

      <Spin :spinning="loading">
        <div class="mb-4 rounded bg-blue-50 p-3 dark:bg-blue-900">
          <div class="text-sm">
            <ClockCircleOutlined class="mr-2" />
            <span class="font-semibold">快照说明：</span>
            快照可以保存容器在某一时刻的完整状态。
          </div>
        </div>

        <Table
          :columns="columns"
          :data-source="displaySnapshots"
          :pagination="false"
          :row-key="(record) => record.name"
          :scroll="{ y: 'calc(100vh - 400px)' }"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'name'">
              <span class="font-mono">{{ record.name }}</span>
            </template>
             <template v-if="column.key === 'snaptime'">
              {{ formatTime(record.snaptime) }}
            </template>
            <template v-if="column.key === 'status'">
              <Tag v-if="record.running" color="green">运行中</Tag>
              <Tag v-else color="default">已停止</Tag>
            </template>
            <template v-if="column.key === 'action'">
               <Space>
                <Button
                  type="link"
                  size="small"
                  @click="handleRollback(record)"
                >
                  <RollbackOutlined /> 回滚
                </Button>
                <Button
                  type="link"
                  size="small"
                  @click="handleEditDescription(record)"
                >
                  <EditOutlined /> 编辑备注
                </Button>
                <Button
                  type="link"
                  danger
                  size="small"
                  @click="handleDelete(record)"
                >
                  <DeleteOutlined /> 删除
                </Button>
               </Space>
            </template>
          </template>
          <template #emptyText>
             <div class="py-8">
               <p class="text-gray-400">暂无快照</p>
               <Button type="primary" @click="handleCreateSnapshot" class="mt-4">
                 <PlusOutlined /> 创建第一个快照
               </Button>
             </div>
          </template>
        </Table>
      </Spin>
    </Card>

    <Modal
      v-model:open="createModalVisible"
      title="创建容器快照"
      @ok="handleConfirmCreate"
      :confirm-loading="createLoading"
      ok-text="创建"
      cancel-text="取消"
      width="550px"
    >
      <Form layout="vertical">
        <FormItem label="快照名称" required>
           <Input v-model:value="createForm.name" placeholder="输入快照名称" :maxlength="40" />
        </FormItem>
        <FormItem label="描述">
           <Input.TextArea v-model:value="createForm.description" :rows="3" placeholder="可选描述" :maxlength="200" />
        </FormItem>
      </Form>
    </Modal>

     <Modal
      v-model:open="editModalVisible"
      title="编辑快照备注"
      @ok="handleConfirmEdit"
      :confirm-loading="editLoading"
      ok-text="保存"
      cancel-text="取消"
      width="500px"
    >
      <Form layout="vertical">
        <FormItem label="快照名称">
          <Input :value="editForm.name" disabled />
        </FormItem>

        <FormItem label="描述">
          <Input.TextArea
            v-model:value="editForm.description"
            :rows="4"
            placeholder="输入快照描述信息"
            :maxlength="500"
          />
        </FormItem>
      </Form>
    </Modal>
  </div>
</template>

<style scoped>
:deep(.ant-table) {
  font-size: 13px;
}
</style>
