<script setup lang="ts">
import type { LxcContainerModel } from '#/api/pve/types';

import { onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';

import {
  CloudSyncOutlined,
  LoginOutlined,
  PlayCircleOutlined,
  PoweroffOutlined,
  RedoOutlined,
  StopOutlined,
  SyncOutlined,
} from '@ant-design/icons-vue';
import {
  Button,
  Card,
  Dropdown,
  Menu,
  MenuItem,
  message,
  Table,
  Tag,
  Modal,
  InputNumber,
  Checkbox,
} from 'ant-design-vue';

import { getLxcListApi, operateLxcApi, syncLxcListApi, deleteLxcApi } from '#/api/pve/lxc';
import { PlusOutlined } from '@ant-design/icons-vue';
import CreateLxcModal from './CreateLxcModal.vue';

defineOptions({
  name: 'PVELxc',
});

const loading = ref(false);
const tableData = ref<LxcContainerModel[]>([]);
const router = useRouter();

const columns = [
  { dataIndex: 'vmid', key: 'vmid', title: 'VMID', width: 80 },
  { dataIndex: 'server_name', key: 'server_name', title: '服务器', width: 120 },
  { dataIndex: 'node', key: 'node', title: '节点', width: 100 },
  { dataIndex: 'name', key: 'name', title: '名称' },
  { dataIndex: 'status', key: 'status', title: '状态', width: 100 },
  { dataIndex: 'cpu_cores', key: 'cpu_cores', title: 'CPU核心', width: 100 },
  { dataIndex: 'memory_mb', key: 'memory_mb', title: '内存', width: 120 },
  { dataIndex: 'disk_gb', key: 'disk_gb', title: '磁盘', width: 120 },
  { key: 'action', title: '操作', width: 220 },
];

const getStatusColor = (status: string) => {
  const colorMap: Record<string, string> = {
    paused: 'orange',
    running: 'green',
    stopped: 'red',
    unknown: 'default',
  };
  return colorMap[status] || 'default';
};

const getStatusText = (status: string) => {
  const textMap: Record<string, string> = {
    paused: '已暂停',
    running: '运行中',
    stopped: '已停止',
    unknown: '未知',
  };
  return textMap[status] || status;
};

const formatMemory = (mb?: number) => {
  if (!mb) return '-';
  if (mb >= 1024) {
    return `${(mb / 1024).toFixed(2)} GB`;
  }
  return `${mb} MB`;
};

const formatDisk = (gb?: number) => {
  if (!gb) return '-';
  return `${gb} GB`;
};

const fetchData = async () => {
  loading.value = true;
  try {
    const res = await getLxcListApi();
    if (Array.isArray(res)) {
      tableData.value = res;
    } else if (res && Array.isArray((res as any).results)) {
      tableData.value = (res as any).results;
    } else if (
      res &&
      (res as any).data &&
      Array.isArray((res as any).data.results)
    ) {
      tableData.value = (res as any).data.results;
    } else if (res && Array.isArray((res as any).data)) {
      tableData.value = (res as any).data;
    } else {
      tableData.value = [];
    }
  } catch (error: any) {
    message.error(`获取容器列表失败: ${error.message || '未知错误'}`);
  } finally {
    loading.value = false;
  }
};

const handleSyncAll = async () => {
  loading.value = true;
  try {
    const res: any = await syncLxcListApi();
    message.success(`同步完成: 新增 ${res.created}, 更新 ${res.updated}`);
    fetchData();
  } catch (error: any) {
    message.error(`同步失败: ${error.message || '未知错误'}`);
  } finally {
    loading.value = false;
  }
};

const handleAction = async (record: any, action: string) => {
  try {
    loading.value = true;
    await operateLxcApi(record.id, action);
    message.success(`发送 ${action} 指令成功`);
    setTimeout(() => fetchData(), 2000);
  } catch (error: any) {
    message.error(`操作失败: ${error.message}`);
  } finally {
    loading.value = false;
  }
};

const handleEnter = (record: any) => {
  router.push({ name: 'PVE_LXC_Detail', params: { id: record.id } });
};

// Safe Delete Logic
const deleteModalVisible = ref(false);
const deleteConfirmVmid = ref<number | undefined>(undefined);
const deleteRecord = ref<any>(null);
const isPurge = ref(true);

const handleDelete = (record: any) => {
  deleteRecord.value = record;
  deleteConfirmVmid.value = undefined;
  isPurge.value = true;
  deleteModalVisible.value = true;
};

const performDelete = async () => {
  if (!deleteRecord.value) return;

  if (deleteConfirmVmid.value !== deleteRecord.value.vmid) {
    message.error('VMID 不匹配');
    return;
  }

  try {
    loading.value = true;
    await deleteLxcApi(deleteRecord.value.id, { purge: isPurge.value });
    message.success('删除成功');
    deleteModalVisible.value = false;
    handleSyncAll(); // Auto sync
  } catch (error: any) {
    message.error(`删除失败: ${error.message}`);
    loading.value = false;
  }
};

onMounted(() => {
  fetchData();
});


// Create LXC Modal Logic
const createModalVisible = ref(false);

const openCreateModal = () => {
  createModalVisible.value = true;
};

const handleCreateSuccess = () => {
  fetchData();
};
</script>

<template>
  <div class="p-5">
    <Card title="LXC容器管理">
      <template #extra>
        <Space>
          <Button type="primary" @click="openCreateModal">
            <template #icon><PlusOutlined /></template>
            创建容器
          </Button>
          <Button :loading="loading" @click="fetchData">
            <template #icon><SyncOutlined /></template>
            刷新
          </Button>
          <Button :loading="loading" @click="handleSyncAll">
            <template #icon><CloudSyncOutlined /></template>
            同步
          </Button>
        </Space>
      </template>

      <Table
        :columns="columns"
        :data-source="tableData"
        :loading="loading"
        :pagination="{ pageSize: 15 }"
        row-key="id"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'status'">
            <Tag :color="getStatusColor(record.status)">
              {{ getStatusText(record.status) }}
            </Tag>
          </template>

          <template v-else-if="column.key === 'memory_mb'">
            {{ formatMemory(record.memory_mb) }}
          </template>

          <template v-else-if="column.key === 'disk_gb'">
            {{ formatDisk(record.disk_gb) }}
          </template>

          <template v-else-if="column.key === 'action'">
            <Space>
              <Button size="small" type="link" @click="handleEnter(record)">
                <template #icon><LoginOutlined /></template>
                进入
              </Button>
              <Dropdown>
                <template #overlay>
                  <Menu>
                    <MenuItem
                      v-if="record.status === 'stopped'"
                      @click="handleAction(record, 'start')"
                    >
                      <template #icon><PlayCircleOutlined /></template>
                      启动
                    </MenuItem>

                    <MenuItem
                      v-if="record.status === 'running'"
                      @click="handleAction(record, 'shutdown')"
                    >
                      <template #icon><PoweroffOutlined /></template>
                      关机
                    </MenuItem>

                    <MenuItem
                      v-if="record.status === 'running'"
                      @click="handleAction(record, 'stop')"
                    >
                      <template #icon><StopOutlined /></template>
                      停止(强制)
                    </MenuItem>

                    <MenuItem
                      v-if="record.status === 'running'"
                      @click="handleAction(record, 'reboot')"
                    >
                      <template #icon><RedoOutlined /></template>
                      重启
                    </MenuItem>

                    <MenuItem danger @click="handleDelete(record)">
                      删除
                    </MenuItem>
                  </Menu>
                </template>
                <Button size="small" type="link"> 电源操作 </Button>
              </Dropdown>
            </Space>
          </template>
        </template>
      </Table>
    </Card>

    <CreateLxcModal v-model:open="createModalVisible" @success="handleCreateSuccess" />
    
    <!-- Confirm Delete Modal -->
    <Modal
      v-model:open="deleteModalVisible"
      title="确认删除容器"
      :confirm-loading="loading"
      ok-type="danger"
      @ok="performDelete"
      :ok-button-props="{ disabled: deleteConfirmVmid !== deleteRecord?.vmid }"
    >
      <div v-if="deleteRecord">
        <div class="mb-4 text-gray-700">
          正在删除容器 <b>{{ deleteRecord.name }}</b> (VMID: {{ deleteRecord.vmid }})。
          <br />
          此操作不可逆，将永久删除容器及其数据！
        </div>

        <div class="mb-4 rounded border border-red-200 bg-red-50 p-3 text-red-700">
          <div class="mb-1 font-bold">危险操作确认</div>
          请输入 VMID <b>{{ deleteRecord.vmid }}</b> 以确认删除。
        </div>

        <InputNumber
          v-model:value="deleteConfirmVmid"
          placeholder="请输入 VMID"
          class="mb-4 w-full"
          :min="1"
        />

        <Checkbox v-model:checked="isPurge">
          同时删除关联的存储磁盘 (Purge)
        </Checkbox>
        <div class="ml-6 mt-1 text-xs text-gray-400">
          如果不勾选，磁盘将被保留为未使用状态。
        </div>
      </div>
    </Modal>
  </div>
</template>
