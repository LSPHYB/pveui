<script setup lang="ts">
import type { VirtualMachineModel } from '#/api/pve/types';

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
  Switch,
  Table,
  Tag,
} from 'ant-design-vue';

import {
  createVmSnapshotApi,
  deleteSnapshotApi,
  getVmSnapshotsApi,
  rollbackSnapshotApi,
  updateSnapshotApi,
} from '#/api/pve/vm';

defineOptions({ name: 'VmSnapshots' });

const props = defineProps<{
  vm: null | VirtualMachineModel;
  vmId: string;
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
  include_memory: false,
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

// 计算显示的快照列表（排除 current）
const displaySnapshots = computed(() => {
  return snapshots.value.filter((s) => s.name !== 'current');
});

const loadSnapshots = async () => {
  if (!props.vmId) return;

  loading.value = true;
  try {
    const res: any = await getVmSnapshotsApi(props.vmId);
    const data = res?.data || res || {};
    snapshots.value = data.snapshots || [];
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
    include_memory: false,
  };
  createModalVisible.value = true;
};

const handleConfirmCreate = async () => {
  if (!props.vmId) return;

  if (!createForm.value.name) {
    message.warning('请输入快照名称');
    return;
  }

  // 验证快照名称格式（只允许字母、数字、下划线、中划线）
  if (!/^[\w-]+$/.test(createForm.value.name)) {
    message.warning('快照名称只能包含字母、数字、下划线和中划线');
    return;
  }

  // 检查名称是否已存在
  if (snapshots.value.some((s) => s.name === createForm.value.name)) {
    message.warning('快照名称已存在');
    return;
  }

  createLoading.value = true;
  try {
    await createVmSnapshotApi(props.vmId, createForm.value);
    message.success('快照创建任务已提交，正在后台执行');
    createModalVisible.value = false;

    // 等待几秒后刷新列表
    setTimeout(() => {
      loadSnapshots();
    }, 3000);
  } catch (error: any) {
    message.error(error.message || '创建快照失败');
  } finally {
    createLoading.value = false;
  }
};

const handleRollback = (record: any) => {
  if (record.name === 'current') {
    message.warning('无法回滚到当前状态');
    return;
  }

  Modal.confirm({
    title: '确认回滚',
    content: `确定要回滚到快照 "${record.name}" 吗？这将恢复虚拟机到快照创建时的状态。`,
    okText: '确定',
    okType: 'primary',
    cancelText: '取消',
    onOk: async () => {
      if (!props.vmId) return;
      try {
        await rollbackSnapshotApi(props.vmId, { name: record.name });
        message.success('快照回滚任务已提交');

        setTimeout(() => {
          loadSnapshots();
        }, 2000);
      } catch (error: any) {
        message.error(error.message || '回滚失败');
      }
    },
  });
};

const handleDelete = (record: any) => {
  if (record.name === 'current') {
    message.warning('无法删除当前状态');
    return;
  }

  if (record.is_current) {
    message.warning('无法删除当前快照');
    return;
  }

  Modal.confirm({
    title: '确认删除',
    content: `确定要删除快照 "${record.name}" 吗？此操作不可恢复。`,
    okText: '确定',
    okType: 'danger',
    cancelText: '取消',
    onOk: async () => {
      if (!props.vmId) return;
      try {
        await deleteSnapshotApi(props.vmId, { name: record.name });
        message.success('快照删除任务已提交');

        setTimeout(() => {
          loadSnapshots();
        }, 2000);
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
  if (!props.vmId) return;

  editLoading.value = true;
  try {
    await updateSnapshotApi(props.vmId, editForm.value);
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

watch(() => props.vmId, loadSnapshots);
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
        <!-- 提示信息 -->
        <div class="mb-4 rounded bg-blue-50 p-3 dark:bg-blue-900">
          <div class="text-sm">
            <ClockCircleOutlined class="mr-2" />
            <span class="font-semibold">快照说明：</span
            >快照可以保存虚拟机在某一时刻的完整状态，方便快速恢复。
            创建快照时可以选择是否包含内存状态（适用于运行中的虚拟机）。
          </div>
        </div>

        <!-- 快照列表 -->
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
              <Tag v-if="record.is_current" color="green" class="ml-2">
                当前
              </Tag>
            </template>

            <template v-if="column.key === 'snaptime'">
              {{ formatTime(record.snaptime) }}
            </template>

            <template v-if="column.key === 'status'">
              <Tag v-if="record.vmstate" color="blue">含内存</Tag>
              <Tag v-else color="default">仅磁盘</Tag>
              <Tag v-if="record.running" color="green">运行中</Tag>
            </template>

            <template v-if="column.key === 'action'">
              <Space>
                <Button
                  type="link"
                  size="small"
                  :disabled="record.is_current"
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
                  :disabled="record.is_current"
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

    <!-- 创建快照模态框 -->
    <Modal
      v-model:open="createModalVisible"
      title="创建虚拟机快照"
      @ok="handleConfirmCreate"
      :confirm-loading="createLoading"
      ok-text="创建"
      cancel-text="取消"
      width="550px"
    >
      <Form layout="vertical">
        <FormItem label="快照名称" required>
          <Input
            v-model:value="createForm.name"
            placeholder="输入快照名称（只能包含字母、数字、下划线和中划线）"
            :maxlength="40"
          />
          <div class="mt-1 text-xs text-gray-500">
            建议使用有意义的名称，如：before-update、stable-v1.0 等
          </div>
        </FormItem>

        <FormItem label="描述">
          <Input.TextArea
            v-model:value="createForm.description"
            :rows="3"
            placeholder="输入快照描述信息（可选）"
            :maxlength="200"
          />
        </FormItem>

        <FormItem>
          <div class="flex items-center">
            <Switch v-model:checked="createForm.include_memory" />
            <span class="ml-2">包含内存状态（RAM）</span>
          </div>
          <div class="mt-2 text-xs text-gray-500">
            <div>
              • 开启后会保存虚拟机的内存状态，回滚时可以完全恢复到快照时刻
            </div>
            <div>• 仅适用于运行中的虚拟机，会占用更多存储空间</div>
            <div>• 关闭时仅保存磁盘状态，回滚后需要重新启动虚拟机</div>
          </div>
        </FormItem>
      </Form>
    </Modal>

    <!-- 编辑备注模态框 -->
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
