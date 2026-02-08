<script setup lang="ts">
import type { VirtualMachineModel } from '#/api/pve/types';

import { computed, onMounted, ref, watch } from 'vue';

import {
  DeleteOutlined,
  EditOutlined,
  PlusOutlined,
} from '@ant-design/icons-vue';
import {
  Button,
  Card,
  Checkbox,
  Dropdown,
  Form,
  FormItem,
  Input,
  InputNumber,
  Menu,
  MenuItem,
  message,
  Modal,
  Select,
  Space,
  Spin,
  Table,
  Tag,
} from 'ant-design-vue';

import { getNodeNetworkApi } from '#/api/pve/node';
import { getStorageListApi } from '#/api/pve/storage';
import { getVmConfigByIdApi, updateVmConfigApi } from '#/api/pve/vm';

defineOptions({ name: 'VmHardware' });

const props = defineProps<{
  vm: null | VirtualMachineModel;
  vmId: string;
}>();

const loading = ref(false);
const config = ref<Record<string, any>>({});
const editModalVisible = ref(false);
const editingItem = ref<any>(null);
const editForm = ref<any>({});

// 硬件配置项定义
const hardwareItems = computed(() => {
  const conf = config.value;
  if (!conf || Object.keys(conf).length === 0) return [];

  const items: any[] = [];

  // 1. Memory
  if (conf.memory) {
    items.push({
      key: 'memory',
      type: '内存',
      device: 'memory',
      value: `${(conf.memory / 1024).toFixed(2)} GiB`,
      rawValue: conf.memory,
      editable: true,
      removable: false,
    });
  }

  // 2. Processors
  if (conf.sockets || conf.cores || conf.cpu) {
    const sockets = conf.sockets || 1;
    const cores = conf.cores || 1;
    const cpuType = conf.cpu || 'kvm64';
    items.push({
      key: 'cpu',
      type: '处理器',
      device: 'cpu',
      value: `${cores * sockets} (${sockets} sockets, ${cores} cores) [${cpuType}]`,
      rawValue: { sockets, cores, cpu: cpuType },
      editable: true,
      removable: false,
    });
  }

  // 3. BIOS
  if (conf.bios) {
    items.push({
      key: 'bios',
      type: 'BIOS',
      device: 'bios',
      value: conf.bios === 'ovmf' ? 'OVMF (UEFI)' : 'SeaBIOS',
      rawValue: conf.bios,
      editable: true,
      removable: false,
    });
  }

  // 4. Machine Type
  if (conf.machine) {
    items.push({
      key: 'machine',
      type: '机型',
      device: 'machine',
      value: conf.machine,
      rawValue: conf.machine,
      editable: true,
      removable: false,
    });
  }

  // 5. SCSI Controller
  if (conf.scsihw) {
    items.push({
      key: 'scsihw',
      type: 'SCSI 控制器',
      device: 'scsihw',
      value: conf.scsihw,
      rawValue: conf.scsihw,
      editable: true,
      removable: false,
    });
  }

  // 6. Disks
  Object.keys(conf).forEach((key) => {
    const diskMatch = key.match(/^(scsi|sata|ide|virtio)(\d+)$/);
    if (diskMatch) {
      const value = conf[key];
      const isCdrom = value.includes('media=cdrom');
      items.push({
        key,
        type: isCdrom ? 'CD/DVD 驱动器' : '硬盘',
        device: key,
        value,
        rawValue: value,
        editable: true,
        removable: true,
      });
    }
  });

  // 7. Network Devices
  Object.keys(conf).forEach((key) => {
    if (/^net\d+$/.test(key)) {
      items.push({
        key,
        type: '网络设备',
        device: key,
        value: conf[key],
        rawValue: conf[key],
        editable: true,
        removable: true,
      });
    }
  });

  // 8. EFI Disk
  if (conf.efidisk0) {
    items.push({
      key: 'efidisk0',
      type: 'EFI 磁盘',
      device: 'efidisk0',
      value: conf.efidisk0,
      rawValue: conf.efidisk0,
      editable: false,
      removable: false,
    });
  }

  // 9. USB & PCI Devices
  Object.keys(conf).forEach((key) => {
    if (/^usb\d+$/.test(key)) {
      items.push({
        key,
        type: 'USB 设备',
        device: key,
        value: conf[key],
        rawValue: conf[key],
        editable: true,
        removable: true,
      });
    }
    if (/^hostpci\d+$/.test(key)) {
      items.push({
        key,
        type: 'PCI 设备',
        device: key,
        value: conf[key],
        rawValue: conf[key],
        editable: true,
        removable: true,
      });
    }
  });

  return items;
});

const columns = [
  { title: '设备类型', dataIndex: 'type', key: 'type', width: 150 },
  { title: '设备', dataIndex: 'device', key: 'device', width: 120 },
  { title: '配置值', dataIndex: 'value', key: 'value', ellipsis: true },
  { title: '操作', key: 'action', width: 150, fixed: 'right' as const },
];

const loadConfig = async () => {
  console.log('[Hardware] loadConfig 调用 - VM ID:', props.vmId);
  if (!props.vmId) return;
  loading.value = true;
  try {
    const res: any = await getVmConfigByIdApi(props.vmId);
    const extractedConfig =
      res?.data?.config || res?.config || res?.data || res || {};
    console.log('[Hardware] 加载配置成功:', extractedConfig);
    config.value = extractedConfig;
  } catch (error: any) {
    console.error('[Hardware] 加载配置失败:', error);
    message.error(error.message || '获取硬件配置失败');
  } finally {
    loading.value = false;
  }
};

const handleEdit = (record: any) => {
  console.log('[Hardware] handleEdit 调用 - 编辑设备:', record);
  editingItem.value = record;

  // 根据设备类型预填表单
  switch (record.device) {
    case 'bios': {
      editForm.value = { bios: record.rawValue };

      break;
    }
    case 'cpu': {
      editForm.value = { ...record.rawValue };

      break;
    }
    case 'machine': {
      editForm.value = { machine: record.rawValue };

      break;
    }
    case 'memory': {
      editForm.value = { memory: record.rawValue };

      break;
    }
    case 'scsihw': {
      editForm.value = { scsihw: record.rawValue };

      break;
    }
    default: {
      // 磁盘、网卡等
      editForm.value = { [record.device]: record.rawValue };
    }
  }

  console.log('[Hardware] 编辑表单数据:', editForm.value);
  editModalVisible.value = true;
};

const handleSaveEdit = async () => {
  console.log('[Hardware] handleSaveEdit 调用 - VM ID:', props.vmId);
  console.log('[Hardware] 编辑项:', editingItem.value);
  console.log('[Hardware] 表单数据:', editForm.value);
  if (!props.vmId) return;

  try {
    const params: any = {};

    switch (editingItem.value.device) {
      case 'bios': {
        params.bios = editForm.value.bios;

        break;
      }
      case 'cpu': {
        params.sockets = editForm.value.sockets;
        params.cores = editForm.value.cores;
        params.cpu = editForm.value.cpu;

        break;
      }
      case 'machine': {
        params.machine = editForm.value.machine;

        break;
      }
      case 'memory': {
        params.memory = editForm.value.memory;

        break;
      }
      case 'scsihw': {
        params.scsihw = editForm.value.scsihw;

        break;
      }
      default: {
        params[editingItem.value.device] =
          editForm.value[editingItem.value.device];
      }
    }

    console.log('[Hardware] 提交参数:', params);
    await updateVmConfigApi(props.vmId, { params });
    console.log('[Hardware] 配置更新成功');
    message.success('硬件配置更新成功');
    editModalVisible.value = false;
    loadConfig();
  } catch (error: any) {
    console.error('[Hardware] 配置更新失败:', error);
    message.error(error.message || '更新失败');
  }
};

// 恢复被误删的 handleRemove 函数
const handleRemove = async (record: any) => {
  console.log('[Hardware] handleRemove 调用 - 移除设备:', record);
  if (!props.vmId) return;

  Modal.confirm({
    title: '确认移除',
    content: `确定要移除 ${record.device} 吗？`,
    okText: '确定',
    cancelText: '取消',
    onOk: async () => {
      try {
        const params: any = { delete: record.device };

        console.log('[Hardware] 移除设备请求参数:', params);
        await updateVmConfigApi(props.vmId, { params });
        console.log('[Hardware] 设备移除成功');
        message.success('设备移除成功');
        loadConfig();
      } catch (error: any) {
        console.error('[Hardware] 设备移除失败:', error);
        message.error(error.message || '移除失败');
      }
    },
  });
};

// 添加设备相关状态
const addModalVisible = ref(false);
const addDeviceType = ref<'disk' | 'network'>('disk');
const confirmLoading = ref(false);
const storageList = ref<any[]>([]);
const networkList = ref<any[]>([]);
const addForm = ref<any>({
  // Disk defaults
  diskBus: 'scsi',
  diskId: 0,
  diskSize: 32,
  diskFormat: 'qcow2',
  cache: '',
  discard: false,
  iothread: true,
  ssd: false,
  ronly: false,
  skipReplication: false,
  aio: '',
  storage: '',

  // Network defaults
  netBridge: 'vmbr0',
  netModel: 'virtio',
  netFirewall: true,
  netDisconnect: false,
  netMac: '',
  netVlan: null,
  netMtu: null,
  netRate: null,
  netQueues: null,
});

// 计算下一个可用的 ID
const getNextId = (type: string) => {
  const conf = config.value;
  let maxId = -1;
  const regex = new RegExp(String.raw`^${type}(\d+)$`);

  Object.keys(conf).forEach((key) => {
    const match = key.match(regex);
    if (match && match[1]) {
      const id = Number.parseInt(match[1]);
      if (id > maxId) maxId = id;
    }
  });

  return maxId + 1;
};

// 自动更新磁盘 ID
const updateNextDiskId = () => {
  addForm.value.diskId = getNextId(addForm.value.diskBus);
};

// 格式化字节大小
const formatBytes = (bytes: number) => {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${Number.parseFloat((bytes / k ** i).toFixed(2))} ${sizes[i]}`;
};

const handleAdd = async (type: string) => {
  console.log('[Hardware] handleAdd 调用 - 设备类型:', type);

  // 设置设备类型
  if (type === '硬盘') {
    addDeviceType.value = 'disk';
    addForm.value.diskBus = 'scsi';
    addForm.value.diskId = getNextId('scsi');
    addForm.value.diskSize = 32;
  } else if (type === '网络设备') {
    addDeviceType.value = 'network';
    addForm.value.netModel = 'virtio';
    addForm.value.netId = getNextId('net');
  } else {
    message.info(
      `添加 ${type} 功能正在开发中，请使用 PVE 原生界面进行添加操作`,
    );
    return;
  }

  addModalVisible.value = true;

  // 加载依赖数据
  // 处理 vm 数据可能被包括在 response 对象中的情况
  const vmData =
    props.vm && (props.vm as any).data ? (props.vm as any).data : props.vm;

  if (vmData && vmData.server && vmData.node) {
    console.log('[Hardware] 准备加载依赖数据, VM信息:', vmData);
    try {
      if (addDeviceType.value === 'disk') {
        if (storageList.value.length === 0) {
          console.log('[Hardware] 开始加载存储列表...');
          const storages: any = await getStorageListApi(
            vmData.server,
            vmData.node,
          );
          console.log('[Hardware] 存储列表原始返回:', storages);

          // 处理可能的嵌套数据结构
          const actualStorages = Array.isArray(storages)
            ? storages
            : storages.data || storages.list || [];

          // 过滤出激活的存储
          storageList.value = actualStorages.filter((s: any) => s.active);
          console.log('[Hardware] 过滤后的存储列表:', storageList.value);

          // 默认选中第一个
          if (storageList.value.length > 0) {
            addForm.value.storage = storageList.value[0].storage;
          }
        }
      } else if (
        addDeviceType.value === 'network' &&
        networkList.value.length === 0
      ) {
        console.log('[Hardware] 开始加载网络列表...');
        const networks: any = await getNodeNetworkApi(
          vmData.server,
          vmData.node,
        );
        console.log('[Hardware] 网络列表原始返回:', networks);

        // 处理可能的嵌套数据结构
        const actualNetworks = Array.isArray(networks)
          ? networks
          : networks.data || networks.list || [];

        // 过滤出桥接接口
        networkList.value = actualNetworks.filter(
          (n: any) => n.type === 'bridge',
        );
        console.log('[Hardware] 过滤后的网桥列表:', networkList.value);

        if (networkList.value.length > 0) {
          addForm.value.netBridge = networkList.value[0].iface;
        }
      }
    } catch (error: any) {
      console.error('[Hardware] 加载依赖数据失败:', error);
      message.warning('无法加载部分选项数据，请检查网络连接');
    }
  } else {
    console.warn('[Hardware] 无法加载依赖数据: VM信息不完整', vmData);
  }
};

const handleAddSave = async () => {
  if (!props.vmId) return;
  confirmLoading.value = true;

  try {
    const params: any = {};

    if (addDeviceType.value === 'disk') {
      // 构造磁盘参数
      // scsi0: local-lvm:32,cache=writeback,discard=on,...
      // 或者 local-lvm:vm-100-disk-0,size=32G... (这里简化处理，让 PVE 自动分配卷名)
      // 简单格式: storage:size_in_G
      // 完整格式: [storage]:[size],option=val,...

      const key = `${addForm.value.diskBus}${addForm.value.diskId}`;
      let value = `${addForm.value.storage}:${addForm.value.diskSize}`;

      const options = [];
      if (addForm.value.cache) options.push(`cache=${addForm.value.cache}`);
      if (addForm.value.discard) options.push('discard=on');
      if (addForm.value.iothread) options.push('iothread=1');
      if (addForm.value.ssd) options.push('ssd=1');
      if (addForm.value.ronly) options.push('ro=1');
      // 根据存储类型，format 可能需要加。但如果在创建新盘，通常 storage:size 就够了，format 由 storage 决定或默认
      // 如果是文件存储(dir, nfs)，可能需要 format=qcow2
      if (addForm.value.diskFormat)
        options.push(`format=${addForm.value.diskFormat}`);
      if (addForm.value.aio) options.push(`aio=${addForm.value.aio}`);

      if (options.length > 0) {
        value += `,${options.join(',')}`;
      }

      params[key] = value;
    } else if (addDeviceType.value === 'network') {
      // 构造网络参数
      // net0: virtio=AA:BB:CC:DD:EE:FF,bridge=vmbr0,firewall=1...
      // 或者 net0: model=virtio,macaddr=...,bridge=... (PVE API 格式比较灵活，有时也是 model=mac,bridge...)
      // 常见的添加格式: netN: model,bridge=vmbr0

      const netId = getNextId('net');
      const key = `net${netId}`;
      let value = `${addForm.value.netModel}`;

      if (addForm.value.netMac) {
        value += `=${addForm.value.netMac}`;
      }

      value += `,bridge=${addForm.value.netBridge}`;

      value += addForm.value.netFirewall ? ',firewall=1' : ',firewall=0'; // 显式关闭

      if (addForm.value.netVlan) value += `,tag=${addForm.value.netVlan}`;
      if (addForm.value.netDisconnect) value += ',link_down=1';
      if (addForm.value.netMtu) value += `,mtu=${addForm.value.netMtu}`;
      if (addForm.value.netRate) value += `,rate=${addForm.value.netRate}`;
      if (addForm.value.netQueues)
        value += `,queues=${addForm.value.netQueues}`;

      params[key] = value;
    }

    console.log('[Hardware] 添加设备参数:', params);
    await updateVmConfigApi(props.vmId, { params });
    message.success('设备添加成功');
    addModalVisible.value = false;
    loadConfig();
  } catch (error: any) {
    console.error('[Hardware] 添加设备失败:', error);
    message.error(error.message || '添加失败');
  } finally {
    confirmLoading.value = false;
  }
};

onMounted(() => {
  loadConfig();
});

watch(() => props.vmId, loadConfig);
</script>

<template>
  <div class="h-full p-4">
    <Card title="硬件配置" :bordered="false" class="h-full">
      <template #extra>
        <Space>
          <Dropdown>
            <template #overlay>
              <Menu>
                <MenuItem key="disk" @click="handleAdd('硬盘')">
                  <PlusOutlined /> 添加硬盘
                </MenuItem>
                <MenuItem key="network" @click="handleAdd('网络设备')">
                  <PlusOutlined /> 添加网络设备
                </MenuItem>
              </Menu>
            </template>
            <Button type="primary"> <PlusOutlined /> 添加 </Button>
          </Dropdown>
          <Button @click="loadConfig" :loading="loading">刷新</Button>
        </Space>
      </template>

      <Spin :spinning="loading">
        <Table
          :columns="columns"
          :data-source="hardwareItems"
          :pagination="false"
          :row-key="(record) => record.key"
          :scroll="{ y: 'calc(100vh - 300px)' }"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'type'">
              <Tag color="blue">{{ record.type }}</Tag>
            </template>
            <template v-if="column.key === 'action'">
              <Space>
                <Button
                  v-if="record.editable"
                  type="link"
                  size="small"
                  @click="handleEdit(record)"
                >
                  <EditOutlined /> 编辑
                </Button>
                <Button
                  v-if="record.removable"
                  type="link"
                  danger
                  size="small"
                  @click="handleRemove(record)"
                >
                  <DeleteOutlined /> 移除
                </Button>
              </Space>
            </template>
          </template>
        </Table>
      </Spin>
    </Card>

    <!-- 编辑模态框 -->
    <Modal
      v-model:open="editModalVisible"
      :title="`编辑 ${editingItem?.device || ''}`"
      @ok="handleSaveEdit"
      ok-text="保存"
      cancel-text="取消"
    >
      <Form layout="vertical" v-if="editingItem">
        <!-- Memory -->
        <template v-if="editingItem.device === 'memory'">
          <FormItem label="内存 (MB)">
            <InputNumber
              v-model:value="editForm.memory"
              :min="512"
              :step="1024"
              style="width: 100%"
            />
          </FormItem>
        </template>

        <!-- CPU -->
        <template v-if="editingItem.device === 'cpu'">
          <FormItem label="Sockets">
            <InputNumber
              v-model:value="editForm.sockets"
              :min="1"
              :max="4"
              style="width: 100%"
            />
          </FormItem>
          <FormItem label="Cores">
            <InputNumber
              v-model:value="editForm.cores"
              :min="1"
              :max="128"
              style="width: 100%"
            />
          </FormItem>
          <FormItem label="CPU 类型">
            <Select v-model:value="editForm.cpu">
              <Select.Option value="host">host</Select.Option>
              <Select.Option value="kvm64">kvm64</Select.Option>
              <Select.Option value="qemu64">qemu64</Select.Option>
              <Select.Option value="x86-64-v2-AES">x86-64-v2-AES</Select.Option>
            </Select>
          </FormItem>
        </template>

        <!-- BIOS -->
        <template v-if="editingItem.device === 'bios'">
          <FormItem label="BIOS">
            <Select v-model:value="editForm.bios">
              <Select.Option value="seabios">SeaBIOS</Select.Option>
              <Select.Option value="ovmf">OVMF (UEFI)</Select.Option>
            </Select>
          </FormItem>
        </template>

        <!-- Machine Type -->
        <template v-if="editingItem.device === 'machine'">
          <FormItem label="机型">
            <Input v-model:value="editForm.machine" />
          </FormItem>
        </template>

        <!-- SCSI Controller -->
        <template v-if="editingItem.device === 'scsihw'">
          <FormItem label="SCSI 控制器">
            <Select v-model:value="editForm.scsihw">
              <Select.Option value="virtio-scsi-single">
                VirtIO SCSI single
              </Select.Option>
              <Select.Option value="virtio-scsi-pci">VirtIO SCSI</Select.Option>
              <Select.Option value="lsi">LSI 53C895A</Select.Option>
              <Select.Option value="lsi53c810">LSI 53C810</Select.Option>
              <Select.Option value="megasas">
                MegaRAID SAS 8708EM2
              </Select.Option>
              <Select.Option value="pvscsi">VMware PVSCSI</Select.Option>
            </Select>
          </FormItem>
        </template>

        <!-- Other devices (disk, network, etc) -->
        <template
          v-if="
            !['memory', 'cpu', 'bios', 'machine', 'scsihw'].includes(
              editingItem.device,
            )
          "
        >
          <FormItem :label="`${editingItem.device} 配置`">
            <Input v-model:value="editForm[editingItem.device]" />
          </FormItem>
          <div class="mt-2 text-xs text-gray-500">
            提示：请按照 PVE
            格式输入配置字符串，例如：local-lvm:vm-100-disk-0,size=32G
          </div>
        </template>
      </Form>
    </Modal>

    <!-- 添加设备模态框 -->
    <Modal
      v-model:open="addModalVisible"
      :title="`添加: ${addDeviceType === 'disk' ? '硬盘' : '网络设备'}`"
      @ok="handleAddSave"
      :confirm-loading="confirmLoading"
      width="800px"
      ok-text="添加"
      cancel-text="取消"
    >
      <Form layout="vertical" :model="addForm">
        <!-- 添加硬盘表单 -->
        <template v-if="addDeviceType === 'disk'">
          <div class="grid grid-cols-2 gap-4">
            <FormItem label="总线/设备">
              <Space.Compact style="width: 100%">
                <Select
                  v-model:value="addForm.diskBus"
                  style="width: 120px"
                  @change="updateNextDiskId"
                >
                  <Select.Option value="scsi">SCSI</Select.Option>
                  <Select.Option value="sata">SATA</Select.Option>
                  <Select.Option value="virtio">VirtIO</Select.Option>
                  <Select.Option value="ide">IDE</Select.Option>
                </Select>
                <Select v-model:value="addForm.diskId" style="width: 80px">
                  <Select.Option v-for="i in 32" :key="i - 1" :value="i - 1">
                    {{ i - 1 }}
                  </Select.Option>
                </Select>
              </Space.Compact>
            </FormItem>

            <FormItem label="存储" required>
              <Select v-model:value="addForm.storage" placeholder="选择存储">
                <Select.Option
                  v-for="s in storageList"
                  :key="s.storage"
                  :value="s.storage"
                >
                  {{ s.storage }} ({{ s.type }}) [{{ formatBytes(s.avail) }}
                  可用]
                </Select.Option>
              </Select>
            </FormItem>

            <FormItem label="磁盘大小 (GiB)" required>
              <InputNumber
                v-model:value="addForm.diskSize"
                :min="1"
                :step="1"
                style="width: 100%"
              />
            </FormItem>

            <FormItem label="格式">
              <!-- 只有文件级存储才需要选格式，这里简单列出，实际应根据存储类型联动 -->
              <Select v-model:value="addForm.diskFormat">
                <Select.Option value="qcow2">
                  QEMU 映像格式 (qcow2)
                </Select.Option>
                <Select.Option value="raw">原始磁盘映像 (raw)</Select.Option>
                <Select.Option value="vmdk">
                  VMware 映像格式 (vmdk)
                </Select.Option>
              </Select>
            </FormItem>

            <FormItem label="缓存">
              <Select v-model:value="addForm.cache">
                <Select.Option value="">默认 (无缓存)</Select.Option>
                <Select.Option value="directsync">Direct Sync</Select.Option>
                <Select.Option value="writethrough">
                  Write Through
                </Select.Option>
                <Select.Option value="writeback">Write Back</Select.Option>
                <Select.Option value="writeback_unsafe">
                  Write Back (不安全)
                </Select.Option>
                <Select.Option value="none">无 (None)</Select.Option>
              </Select>
            </FormItem>

            <FormItem label="丢弃 (Discard)">
              <Checkbox v-model:checked="addForm.discard">启用</Checkbox>
            </FormItem>
            <FormItem
              label="IO Thread"
              v-if="addForm.diskBus === 'scsi' || addForm.diskBus === 'virtio'"
            >
              <Checkbox v-model:checked="addForm.iothread">启用</Checkbox>
            </FormItem>

            <FormItem label="SSD 仿真">
              <Checkbox v-model:checked="addForm.ssd">启用</Checkbox>
            </FormItem>

            <FormItem label="只读">
              <Checkbox v-model:checked="addForm.ronly">启用</Checkbox>
            </FormItem>

            <FormItem label="跳过复制">
              <Checkbox v-model:checked="addForm.skipReplication">
                启用
              </Checkbox>
            </FormItem>

            <FormItem label="异步 IO">
              <Select v-model:value="addForm.aio">
                <Select.Option value="">默认 (io_uring)</Select.Option>
                <Select.Option value="native">Native</Select.Option>
                <Select.Option value="threads">Threads</Select.Option>
                <Select.Option value="io_uring">io_uring</Select.Option>
              </Select>
            </FormItem>
          </div>
        </template>

        <!-- 添加网络设备表单 -->
        <template v-if="addDeviceType === 'network'">
          <div class="grid grid-cols-2 gap-4">
            <FormItem label="桥接" required>
              <Select v-model:value="addForm.netBridge" placeholder="选择网桥">
                <Select.Option
                  v-for="net in networkList"
                  :key="net.iface"
                  :value="net.iface"
                >
                  {{ net.iface }} ({{ net.type }})
                  {{ net.comments ? `- ${net.comments}` : '' }}
                </Select.Option>
              </Select>
            </FormItem>

            <FormItem label="VLAN 标签">
              <InputNumber
                v-model:value="addForm.netVlan"
                placeholder="无 VLAN"
                style="width: 100%"
                :min="1"
                :max="4094"
              />
            </FormItem>

            <FormItem label="模型">
              <Select v-model:value="addForm.netModel">
                <Select.Option value="virtio">VirtIO (半虚拟化)</Select.Option>
                <Select.Option value="e1000">Intel E1000</Select.Option>
                <Select.Option value="rtl8139">Realtek RTL8139</Select.Option>
                <Select.Option value="vmxnet3">VMware vmxnet3</Select.Option>
              </Select>
            </FormItem>

            <FormItem label="MAC 地址">
              <Input v-model:value="addForm.netMac" placeholder="自动生成" />
            </FormItem>

            <FormItem label="防火墙">
              <Checkbox v-model:checked="addForm.netFirewall">启用</Checkbox>
            </FormItem>

            <FormItem label="断开">
              <Checkbox v-model:checked="addForm.netDisconnect">启用</Checkbox>
            </FormItem>

            <FormItem label="MTU">
              <InputNumber
                v-model:value="addForm.netMtu"
                placeholder="默认"
                style="width: 100%"
              />
            </FormItem>

            <FormItem label="速率限制 (MB/s)">
              <InputNumber
                v-model:value="addForm.netRate"
                placeholder="无限制"
                style="width: 100%"
              />
            </FormItem>
            <FormItem label="Multiqueue">
              <InputNumber
                v-model:value="addForm.netQueues"
                placeholder="默认"
                style="width: 100%"
              />
            </FormItem>
          </div>
        </template>
      </Form>
    </Modal>
  </div>
</template>

<style scoped>
:deep(.ant-table) {
  font-size: 13px;
}
</style>
