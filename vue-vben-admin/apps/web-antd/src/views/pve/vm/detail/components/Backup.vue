<script setup lang="ts">
import type { VirtualMachineModel } from '#/api/pve/types';

import { computed, onMounted, ref, watch } from 'vue';

import {
  CloseCircleOutlined,
  DeleteOutlined,
  DownloadOutlined,
  EditOutlined,
  MoreOutlined,
  PlusOutlined,
  ReloadOutlined,
  SafetyOutlined,
} from '@ant-design/icons-vue';
import {
  Button,
  Card,
  Dropdown,
  Form,
  FormItem,
  Input,
  Menu,
  MenuItem,
  message,
  Modal,
  Radio,
  RadioGroup,
  Select,
  Space,
  Spin,
  Switch,
  Table,
  Tag,
} from 'ant-design-vue';

import {
  createVmBackupApi,
  deleteVmBackupApi,
  getVmBackupsApi,
  restoreVmBackupApi,
  updateBackupNotesApi,
  updateBackupProtectionApi,
} from '#/api/pve/vm';

defineOptions({ name: 'VmBackup' });

const props = defineProps<{
  vm: null | VirtualMachineModel;
  vmId: string;
}>();

const loading = ref(false);
const backups = ref<any[]>([]);
const storages = ref<any[]>([]);
const createModalVisible = ref(false);
const createLoading = ref(false);
const restoreModalVisible = ref(false);
const restoreLoading = ref(false);
const restoringBackup = ref<any>(null);
const editNotesModalVisible = ref(false);
const editNotesLoading = ref(false);
const editingBackup = ref<any>(null);

const createForm = ref({
  storage: '',
  mode: 'snapshot',
  compress: 'zstd',
  notes: '',
  remove: false,
});

const editNotesForm = ref({
  notes: '',
});

const restoreForm = ref({
  force: false,
  unique: false,
});

const columns = [
  {
    title: '备份文件',
    dataIndex: 'volid',
    key: 'volid',
    ellipsis: true,
    width: 200,
  },
  { title: '存储', dataIndex: 'storage', key: 'storage', width: 100 },
  { title: '格式', dataIndex: 'format', key: 'format', width: 80 },
  { title: '保护', key: 'protected', width: 60, align: 'center' as const },
  { title: '大小', key: 'size', width: 100 },
  { title: '创建时间', key: 'ctime', width: 160 },
  {
    title: '备注',
    dataIndex: 'notes',
    key: 'notes',
    ellipsis: true,
    width: 150,
  },
  { title: '操作', key: 'action', width: 140, align: 'center' as const },
];

const formatBytes = (bytes: number) => {
  if (!bytes) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${Math.round((bytes / k ** i) * 100) / 100} ${sizes[i]}`;
};

const formatTime = (timestamp: number) => {
  if (!timestamp) return '-';
  const date = new Date(timestamp * 1000);
  return date.toLocaleString('zh-CN');
};

const storageOptions = computed(() => {
  return storages.value.map((s) => ({
    label: `${s.storage} (${formatBytes(s.avail)} 可用)`,
    value: s.storage,
  }));
});

const loadBackups = async () => {
  if (!props.vmId) return;

  loading.value = true;
  try {
    const res: any = await getVmBackupsApi(props.vmId);
    const data = res?.data || res || {};
    backups.value = data.backups || [];
    storages.value = data.storages || [];
  } catch (error: any) {
    message.error(error.message || '获取备份列表失败');
  } finally {
    loading.value = false;
  }
};

const handleCreateBackup = () => {
  if (storages.value.length === 0) {
    message.warning('没有可用的备份存储');
    return;
  }
  createForm.value.storage = storages.value[0]?.storage || '';
  createModalVisible.value = true;
};

const handleConfirmCreate = async () => {
  if (!props.vmId) return;

  if (!createForm.value.storage) {
    message.warning('请选择存储');
    return;
  }

  createLoading.value = true;
  try {
    await createVmBackupApi(props.vmId, createForm.value);
    message.success('备份任务已创建，正在后台执行');
    createModalVisible.value = false;

    // 等待几秒后刷新列表
    setTimeout(() => {
      loadBackups();
    }, 3000);
  } catch (error: any) {
    message.error(error.message || '创建备份失败');
  } finally {
    createLoading.value = false;
  }
};

const handleDeleteBackup = (record: any) => {
  Modal.confirm({
    title: '确认删除',
    content: `确定要删除备份 ${record.volid} 吗？此操作不可恢复。`,
    okText: '确定',
    okType: 'danger',
    cancelText: '取消',
    onOk: async () => {
      if (!props.vmId) return;
      try {
        await deleteVmBackupApi(props.vmId, {
          storage: record.storage,
          volid: record.volid,
        });
        message.success('备份已删除');
        loadBackups();
      } catch (error: any) {
        message.error(error.message || '删除失败');
      }
    },
  });
};

const handleRestoreBackup = (record: any) => {
  restoringBackup.value = record;
  restoreForm.value = {
    force: false,
    unique: false,
  };
  restoreModalVisible.value = true;
};

const handleConfirmRestore = async () => {
  if (!props.vmId || !restoringBackup.value) return;

  restoreLoading.value = true;
  try {
    await restoreVmBackupApi(props.vmId, {
      storage: restoringBackup.value.storage,
      archive: restoringBackup.value.volid,
      force: restoreForm.value.force,
      unique: restoreForm.value.unique,
    });
    message.success('备份还原任务已提交，正在后台执行');
    restoreModalVisible.value = false;
  } catch (error: any) {
    message.error(error.message || '还原失败');
  } finally {
    restoreLoading.value = false;
  }
};

const handleEditNotes = (record: any) => {
  editingBackup.value = record;
  editNotesForm.value.notes = record.notes || '';
  editNotesModalVisible.value = true;
};

const handleConfirmEditNotes = async () => {
  if (!props.vmId || !editingBackup.value) return;

  editNotesLoading.value = true;
  try {
    await updateBackupNotesApi(props.vmId, {
      storage: editingBackup.value.storage,
      volid: editingBackup.value.volid,
      notes: editNotesForm.value.notes,
    });
    message.success('备份备注已更新');
    editNotesModalVisible.value = false;
    loadBackups();
  } catch (error: any) {
    message.error(error.message || '更新失败');
  } finally {
    editNotesLoading.value = false;
  }
};

const handleToggleProtection = async (record: any) => {
  if (!props.vmId) return;

  const newProtection = !record.protected;
  try {
    await updateBackupProtectionApi(props.vmId, {
      storage: record.storage,
      volid: record.volid,
      protected: newProtection,
    });
    message.success(`备份已${newProtection ? '启用' : '禁用'}保护`);
    loadBackups();
  } catch (error: any) {
    message.error(error.message || '更新失败');
  }
};

onMounted(() => {
  loadBackups();
});

watch(() => props.vmId, loadBackups);
</script>

<template>
  <div class="h-full p-4">
    <Card title="备份管理" :bordered="false" class="h-full">
      <template #extra>
        <Space>
          <Button type="primary" @click="handleCreateBackup">
            <PlusOutlined /> 立即备份
          </Button>
          <Button @click="loadBackups" :loading="loading">
            <ReloadOutlined /> 刷新
          </Button>
        </Space>
      </template>

      <Spin :spinning="loading">
        <!-- 存储信息 -->
        <div
          v-if="storages.length > 0"
          class="mb-4 rounded bg-blue-50 p-3 dark:bg-blue-900"
        >
          <div class="mb-2 font-semibold">可用备份存储：</div>
          <Space wrap>
            <Tag
              v-for="storage in storages"
              :key="storage.storage"
              color="blue"
            >
              {{ storage.storage }} - {{ storage.type }} ({{
                formatBytes(storage.avail)
              }}
              / {{ formatBytes(storage.total) }})
            </Tag>
          </Space>
        </div>

        <!-- 备份列表 -->
        <Table
          :columns="columns"
          :data-source="backups"
          :pagination="{ pageSize: 10 }"
          :row-key="(record) => record.volid"
          :scroll="{ y: 'calc(100vh - 400px)' }"
          size="small"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'size'">
              {{ formatBytes(record.size) }}
            </template>
            <template v-if="column.key === 'ctime'">
              {{ formatTime(record.ctime) }}
            </template>
            <template v-if="column.key === 'protected'">
              <SafetyOutlined
                v-if="record.protected"
                class="text-lg text-orange-500"
                title="已保护"
              />
              <CloseCircleOutlined
                v-else
                class="text-lg text-gray-400"
                title="未保护"
              />
            </template>

            <template v-if="column.key === 'action'">
              <Space :size="4">
                <Button
                  type="link"
                  size="small"
                  @click="handleRestoreBackup(record)"
                >
                  <DownloadOutlined /> 还原
                </Button>
                <Button
                  type="link"
                  danger
                  size="small"
                  :disabled="record.protected"
                  @click="handleDeleteBackup(record)"
                >
                  <DeleteOutlined /> 删除
                </Button>
                <Dropdown>
                  <template #overlay>
                    <Menu>
                      <MenuItem key="edit" @click="handleEditNotes(record)">
                        <EditOutlined /> 编辑备注
                      </MenuItem>
                      <MenuItem
                        key="protect"
                        @click="handleToggleProtection(record)"
                      >
                        <SafetyOutlined v-if="!record.protected" />
                        <CloseCircleOutlined v-else />
                        {{ record.protected ? '取消保护' : '变更保护' }}
                      </MenuItem>
                    </Menu>
                  </template>
                  <Button type="link" size="small">
                    <MoreOutlined />
                  </Button>
                </Dropdown>
              </Space>
            </template>
          </template>

          <template #emptyText>
            <div class="py-8">
              <p class="text-gray-400">暂无备份</p>
              <Button type="primary" @click="handleCreateBackup" class="mt-4">
                <PlusOutlined /> 创建第一个备份
              </Button>
            </div>
          </template>
        </Table>
      </Spin>
    </Card>

    <!-- 创建备份模态框 -->
    <Modal
      v-model:open="createModalVisible"
      title="创建虚拟机备份"
      @ok="handleConfirmCreate"
      :confirm-loading="createLoading"
      ok-text="开始备份"
      cancel-text="取消"
      width="600px"
    >
      <Form layout="vertical">
        <FormItem label="存储" required>
          <Select
            v-model:value="createForm.storage"
            :options="storageOptions"
            placeholder="选择备份存储位置"
          />
        </FormItem>

        <FormItem label="备份模式" required>
          <RadioGroup v-model:value="createForm.mode">
            <Radio value="snapshot">快照模式 (推荐)</Radio>
            <Radio value="suspend">暂停模式</Radio>
            <Radio value="stop">停止模式</Radio>
          </RadioGroup>
          <div class="mt-2 text-xs text-gray-500">
            <div>• 快照模式：对运行中的虚拟机创建快照进行备份，不中断运行</div>
            <div>• 暂停模式：暂停虚拟机后备份，完成后恢复运行</div>
            <div>• 停止模式：停止虚拟机后备份</div>
          </div>
        </FormItem>

        <FormItem label="压缩算法">
          <Select v-model:value="createForm.compress">
            <Select.Option value="zstd">ZSTD (推荐，快速压缩)</Select.Option>
            <Select.Option value="lzo">LZO (快速)</Select.Option>
            <Select.Option value="gzip">GZIP (高压缩率)</Select.Option>
            <Select.Option value="0">不压缩</Select.Option>
          </Select>
        </FormItem>

        <FormItem label="备注">
          <Input.TextArea
            v-model:value="createForm.notes"
            :rows="3"
            placeholder="输入备份备注信息（可选）"
          />
        </FormItem>
      </Form>
    </Modal>

    <!-- 还原备份模态框 -->
    <Modal
      v-model:open="restoreModalVisible"
      title="还原虚拟机备份"
      @ok="handleConfirmRestore"
      :confirm-loading="restoreLoading"
      ok-text="开始还原"
      ok-type="danger"
      cancel-text="取消"
      width="550px"
    >
      <div class="mb-4 rounded bg-yellow-50 p-3 dark:bg-yellow-900">
        <div class="text-sm text-yellow-800 dark:text-yellow-200">
          ⚠️
          <span class="font-semibold">警告：</span
          >还原备份将覆盖当前虚拟机配置，此操作不可逆！
        </div>
      </div>

      <Form layout="vertical">
        <FormItem label="备份文件">
          <Input :value="restoringBackup?.volid" disabled />
        </FormItem>

        <FormItem label="存储">
          <Input :value="restoringBackup?.storage" disabled />
        </FormItem>

        <FormItem label="格式">
          <Input :value="restoringBackup?.format" disabled />
        </FormItem>

        <FormItem>
          <div class="space-y-2">
            <div class="flex items-center">
              <Switch v-model:checked="restoreForm.force" />
              <span class="ml-2">强制覆盖</span>
            </div>
            <div class="ml-6 text-xs text-gray-500">
              强制覆盖现有虚拟机配置和数据
            </div>

            <div class="mt-3 flex items-center">
              <Switch v-model:checked="restoreForm.unique" />
              <span class="ml-2">创建为新虚拟机</span>
            </div>
            <div class="ml-6 text-xs text-gray-500">
              使用新的VM ID创建虚拟机副本，不覆盖现有虚拟机
            </div>
          </div>
        </FormItem>
      </Form>
    </Modal>

    <!-- 编辑备份备注模态框 -->
    <Modal
      v-model:open="editNotesModalVisible"
      title="编辑备份备注"
      @ok="handleConfirmEditNotes"
      :confirm-loading="editNotesLoading"
      ok-text="保存"
      cancel-text="取消"
      width="500px"
    >
      <Form layout="vertical">
        <FormItem label="备份文件">
          <Input :value="editingBackup?.volid" disabled />
        </FormItem>

        <FormItem label="备注">
          <Input.TextArea
            v-model:value="editNotesForm.notes"
            :rows="4"
            placeholder="输入备份备注信息"
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
