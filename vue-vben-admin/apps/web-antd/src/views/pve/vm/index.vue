<script setup lang="ts">
import type { VirtualMachineModel } from '#/api/pve/types';

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
  Checkbox,
  Dropdown,
  InputNumber,
  Menu,
  MenuItem,
  message,
  Modal,
  Space,
  Table,
  Tag,
} from 'ant-design-vue';

import {
  deleteVmApi,
  getVmListApi,
  operateVmApi,
  syncAllVmsApi,
} from '#/api/pve/vm';

import CreateVmModal from './CreateVmModal.vue';

defineOptions({
  name: 'PVEVirtualMachine',
});

const loading = ref(false);
const tableData = ref<VirtualMachineModel[]>([]);
const createModalRef = ref();
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
    const res = await getVmListApi();
    let data: any[] = [];
    if (Array.isArray(res)) {
      data = res;
    } else if (res && Array.isArray((res as any).results)) {
      data = (res as any).results;
    } else if (
      res &&
      (res as any).data &&
      Array.isArray((res as any).data.results)
    ) {
      data = (res as any).data.results;
    } else if (res && Array.isArray((res as any).data)) {
      data = (res as any).data;
    }

    // Normalise status for paused VMs
    tableData.value = data.map((vm: any) => {
      if (vm.status === 'running' && vm.pve_config?.qmpstatus === 'paused') {
        return { ...vm, status: 'paused' };
      }
      return vm;
    });
  } catch (error: any) {
    message.error(`获取虚拟机列表失败: ${error.message || '未知错误'}`);
  } finally {
    loading.value = false;
  }
};

const handleSyncAll = async () => {
  loading.value = true;
  try {
    const res: any = await syncAllVmsApi();
    message.success(`同步完成: 新增 ${res.created}, 更新 ${res.updated}`);
    fetchData();
  } catch (error: any) {
    message.error(`同步失败: ${error.message || '未知错误'}`);
  } finally {
    loading.value = false;
  }
};

const handleCreate = () => {
  createModalRef.value?.open();
};

const handleAction = async (record: any, action: string) => {
  try {
    loading.value = true;
    await operateVmApi(record.id, action);
    message.success(`发送 ${action} 指令成功`);
    // 稍后刷新状态
    setTimeout(() => fetchData(), 2000);
  } catch (error: any) {
    message.error(`操作失败: ${error.message}`);
  } finally {
    loading.value = false;
  }
};

const handleEnter = (record: any) => {
  router.push({ name: 'PVE_VM_Detail', params: { id: record.id } });
};

// Safe Delete Logic
const deleteModalVisible = ref(false);
const deleteConfirmVmid = ref<number | undefined>(undefined);
const deleteRecord = ref<any>(null);
const isPurge = ref(true);

const handleDelete = (record: any) => {
  deleteRecord.value = record;
  deleteConfirmVmid.value = undefined; // Reset confirmation input
  isPurge.value = true;
  deleteModalVisible.value = true;
};

const performDelete = async () => {
  if (!deleteRecord.value) return;

  // Double check client side (button is also disabled, but safe to check)
  if (deleteConfirmVmid.value !== deleteRecord.value.vmid) {
    message.error('VMID 不匹配');
    return;
  }

  try {
    loading.value = true;
    await deleteVmApi(deleteRecord.value.id, { purge: isPurge.value });
    message.success('删除成功');
    deleteModalVisible.value = false;
    fetchData();
  } catch (error: any) {
    message.error(`删除失败: ${error.message}`);
  } finally {
    loading.value = false;
  }
};

onMounted(() => {
  fetchData();
});
</script>

<template>
  <div class="p-5">
    <Card title="虚拟机管理">
      <template #extra>
        <Space>
          <Button :loading="loading" type="primary" @click="fetchData">
            <template #icon><SyncOutlined /></template>
            刷新
          </Button>
          <Button :loading="loading" @click="handleSyncAll">
            <template #icon><CloudSyncOutlined /></template>
            同步PVE
          </Button>
          <Button type="primary" @click="handleCreate"> 创建虚拟机 </Button>
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
    <CreateVmModal ref="createModalRef" @success="fetchData" />

    <!-- Confirm Delete Modal -->
    <Modal
      v-model:open="deleteModalVisible"
      title="确认删除虚拟机"
      :confirm-loading="loading"
      ok-type="danger"
      @ok="performDelete"
      :ok-button-props="{ disabled: deleteConfirmVmid !== deleteRecord?.vmid }"
    >
      <div v-if="deleteRecord">
        <div class="mb-4 text-gray-700">
          正在删除虚拟机 <b>{{ deleteRecord.name }}</b> (VMID:
          {{ deleteRecord.vmid }})。
          <br />
          此操作不可逆，将永久删除虚拟机及其数据！
        </div>

        <div
          class="mb-4 rounded border border-red-200 bg-red-50 p-3 text-red-700"
        >
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
