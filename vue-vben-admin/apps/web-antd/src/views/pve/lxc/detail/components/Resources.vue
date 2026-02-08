<script setup lang="ts">
import type { LxcContainerModel } from '#/api/pve/types';

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

import { getLxcConfigApi, updateLxcConfigApi } from '#/api/pve/lxc';
import { getNodeNetworkApi } from '#/api/pve/node';
import { getStorageListApi } from '#/api/pve/storage';

defineOptions({ name: 'LxcResources' });

const props = defineProps<{
  lxc: null | LxcContainerModel;
  lxcId: string;
}>();

const loading = ref(false);
const config = ref<Record<string, any>>({});
const editModalVisible = ref(false);
const editingItem = ref<any>(null);
const editForm = ref<any>({});

// 资源配置项定义
const resourceItems = computed(() => {
  const conf = config.value;
  if (!conf || Object.keys(conf).length === 0) return [];

  const items: any[] = [];

  // 1. Memory
  if (conf.memory !== undefined) {
    items.push({
      key: 'memory',
      type: '内存',
      device: 'memory',
      value: `${conf.memory} MB`,
      rawValue: conf.memory,
      editable: true,
      removable: false,
    });
  }

  // 2. Swap
  if (conf.swap !== undefined) {
    items.push({
      key: 'swap',
      type: '交换分区',
      device: 'swap',
      value: `${conf.swap} MB`,
      rawValue: conf.swap,
      editable: true,
      removable: false,
    });
  }

  // 3. Cores
  if (conf.cores !== undefined) {
    items.push({
      key: 'cores',
      type: '核心数',
      device: 'cores',
      value: conf.cores,
      rawValue: conf.cores,
      editable: true,
      removable: false,
    });
  }

  // 4. RootFS
  if (conf.rootfs) {
    items.push({
      key: 'rootfs',
      type: '根磁盘',
      device: 'rootfs',
      value: conf.rootfs,
      rawValue: conf.rootfs,
      editable: true, // Configurable size usually needs resize command, but simple edit might work for some properties. For size, usually separate resize api.
      removable: false,
    });
  }

  // 5. Mount Points
  Object.keys(conf).forEach((key) => {
    if (/^mp\d+$/.test(key)) {
      items.push({
        key,
        type: '挂载点',
        device: key,
        value: conf[key],
        rawValue: conf[key],
        editable: true,
        removable: true,
      });
    }
  });

  // 6. Network
  Object.keys(conf).forEach((key) => {
    if (/^net\d+$/.test(key)) {
      items.push({
        key,
        type: '网络接口',
        device: key,
        value: conf[key],
        rawValue: conf[key],
        editable: true,
        removable: true,
      });
    }
  });

  // 7. DNS
  if (conf.nameserver) {
    items.push({
      key: 'nameserver',
      type: 'DNS 服务器',
      device: 'nameserver',
      value: conf.nameserver,
      rawValue: conf.nameserver,
      editable: true,
      removable: true,
    });
  }
  if (conf.searchdomain) {
    items.push({
      key: 'searchdomain',
      type: 'DNS 搜索域',
      device: 'searchdomain',
      value: conf.searchdomain,
      rawValue: conf.searchdomain,
      editable: true,
      removable: true,
    });
  }

  return items;
});

const columns = [
  { title: '资源类型', dataIndex: 'type', key: 'type', width: 150 },
  { title: '设备/键', dataIndex: 'device', key: 'device', width: 120 },
  { title: '配置值', dataIndex: 'value', key: 'value', ellipsis: true },
  { title: '操作', key: 'action', width: 150, fixed: 'right' as const },
];

const loadConfig = async () => {
  if (!props.lxcId) return;
  loading.value = true;
  try {
    const res: any = await getLxcConfigApi(props.lxcId);
    const extractedConfig =
      res?.data?.config || res?.config || res?.data || res || {};
    config.value = extractedConfig;
  } catch (error: any) {
    console.error('加载配置失败:', error);
    message.error(error.message || '获取资源配置失败');
  } finally {
    loading.value = false;
  }
};

const handleEdit = (record: any) => {
  editingItem.value = record;
  editForm.value = { [record.device]: record.rawValue };
  editModalVisible.value = true;
};

const handleSaveEdit = async () => {
  if (!props.lxcId) return;

  try {
    const params: any = {};
    const key = editingItem.value.device;
    params[key] = editForm.value[key];

    await updateLxcConfigApi(props.lxcId, params);
    message.success('配置更新成功');
    editModalVisible.value = false;
    loadConfig();
  } catch (error: any) {
    console.error('配置更新失败:', error);
    message.error(error.message || '更新失败');
  }
};

const handleRemove = async (record: any) => {
  if (!props.lxcId) return;

  Modal.confirm({
    title: '确认移除',
    content: `确定要移除 ${record.device} 吗？`,
    okText: '确定',
    cancelText: '取消',
    onOk: async () => {
      try {
        const params: any = { delete: record.device };
        await updateLxcConfigApi(props.lxcId, params);
        message.success('设备移除成功');
        loadConfig();
      } catch (error: any) {
        console.error('设备移除失败:', error);
        message.error(error.message || '移除失败');
      }
    },
  });
};

// Add Device Logic
const addModalVisible = ref(false);
const addDeviceType = ref<'network' | 'mountpoint'>('network');
const confirmLoading = ref(false);
const networkList = ref<any[]>([]);
const storageList = ref<any[]>([]);
const addForm = ref<any>({
  // Network
  netName: 'eth0',
  netBridge: 'vmbr0',
  netIp: 'dhcp',
  netGw: '',
  netFirewall: true,
  netIp6: 'auto',
  netGw6: '',

  // Mount Point
  mpId: 0,
  mpStorage: '',
  mpSize: 8,
  mpPath: '',
  mpBackup: true,
});

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

const handleAdd = async (type: string) => {
  if (type === '网络接口') {
    addDeviceType.value = 'network';
    addForm.value.netName = 'eth0'; // Usually eth0, eth1... but PVE standard is net0: name=eth0...
    // Actually PVE config key is net0, net1. The value contains "name=eth0".
    // We should simplify to adding a new net interface.
  } else if (type === '挂载点') {
    addDeviceType.value = 'mountpoint';
    addForm.value.mpId = getNextId('mp');
  } else {
    message.info('该类型添加功能暂未实现');
    return;
  }

  addModalVisible.value = true;

  // Load Dependencies
  const lxcData =
    props.lxc && (props.lxc as any).data ? (props.lxc as any).data : props.lxc;

  if (lxcData && lxcData.server && lxcData.node) {
    try {
      if (addDeviceType.value === 'network' && networkList.value.length === 0) {
        const networks: any = await getNodeNetworkApi(
          lxcData.server,
          lxcData.node,
        );
        const actualNetworks = Array.isArray(networks)
          ? networks
          : networks.data || networks.list || [];
        networkList.value = actualNetworks.filter(
          (n: any) => n.type === 'bridge',
        );
        if (networkList.value.length > 0) {
          addForm.value.netBridge = networkList.value[0].iface;
        }
      } else if (
        addDeviceType.value === 'mountpoint' &&
        storageList.value.length === 0
      ) {
         const storages: any = await getStorageListApi(
            lxcData.server,
            lxcData.node,
          );
          const actualStorages = Array.isArray(storages)
            ? storages
            : storages.data || storages.list || [];
          storageList.value = actualStorages.filter((s: any) => s.active);
          if (storageList.value.length > 0) {
            addForm.value.mpStorage = storageList.value[0].storage;
          }
      }
    } catch (e) {
      console.error('Failed to load dependencies', e);
    }
  }
};

const handleAddSave = async () => {
  if (!props.lxcId) return;
  confirmLoading.value = true;
  try {
    const params: any = {};
    if (addDeviceType.value === 'network') {
      const netId = getNextId('net');
      // PVE LXC Net format: name=<device_name>,bridge=<bridge>[,firewall=1][,ip=...][,gw=...]
      // Example: net0: name=eth0,bridge=vmbr0,firewall=1,ip=dhcp
      // We must provide a unique name for the interface inside the container, e.g. eth1, eth2 if eth0 exists.
      // But simplified: name=eth${netId} might be safe guess?
      const deviceName = `eth${netId}`;
      let value = `name=${deviceName},bridge=${addForm.value.netBridge}`;
      if (addForm.value.netFirewall) value += ',firewall=1';
      if (addForm.value.netIp) value += `,ip=${addForm.value.netIp}`;
      if (addForm.value.netGw) value += `,gw=${addForm.value.netGw}`;
      if (addForm.value.netIp6) value += `,ip6=${addForm.value.netIp6}`;
      if (addForm.value.netGw6) value += `,gw6=${addForm.value.netGw6}`;
      
      params[`net${netId}`] = value;
    } else if (addDeviceType.value === 'mountpoint') {
       // PVE LXC MP format: storage:size,mp=/path/to/mount
       // mp0: local-lvm:8,mp=/mnt/data,backup=1
       const key = `mp${addForm.value.mpId}`;
       let value = `${addForm.value.mpStorage}:${addForm.value.mpSize},mp=${addForm.value.mpPath}`;
       if (addForm.value.mpBackup) value += ',backup=1';
       params[key] = value;
    }

    await updateLxcConfigApi(props.lxcId, params);
    message.success('设备添加成功');
    addModalVisible.value = false;
    loadConfig();
  } catch (error: any) {
    message.error(error.message || '添加失败');
  } finally {
    confirmLoading.value = false;
  }
};

onMounted(() => {
  loadConfig();
});

watch(() => props.lxcId, loadConfig);
</script>

<template>
  <div class="h-full p-4">
    <Card title="资源配置" :bordered="false" class="h-full">
      <template #extra>
        <Space>
          <Dropdown>
            <template #overlay>
              <Menu>
                <MenuItem key="network" @click="handleAdd('网络接口')">
                  <PlusOutlined /> 添加网络接口
                </MenuItem>
                <MenuItem key="mountpoint" @click="handleAdd('挂载点')">
                  <PlusOutlined /> 添加挂载点
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
          :data-source="resourceItems"
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

    <!-- Edit Modal -->
    <Modal
      v-model:open="editModalVisible"
      :title="`编辑 ${editingItem?.type || ''}`"
      @ok="handleSaveEdit"
      ok-text="保存"
      cancel-text="取消"
    >
      <Form layout="vertical" v-if="editingItem">
        <template v-if="editingItem.device === 'memory' || editingItem.device === 'swap'">
           <FormItem :label="editingItem.type + ' (MB)'">
             <InputNumber v-model:value="editForm[editingItem.device]" :min="128" :step="128" style="width: 100%" />
           </FormItem>
        </template>
        <template v-else-if="editingItem.device === 'cores'">
           <FormItem label="核心数">
             <InputNumber v-model:value="editForm.cores" :min="1" :max="128" style="width: 100%" />
           </FormItem>
        </template>
        <template v-else>
           <FormItem :label="editingItem.type + ' 配置'">
             <Input v-model:value="editForm[editingItem.device]" />
           </FormItem>
             <div class="mt-2 text-xs text-gray-500">
            提示：请按照 PVE 格式输入配置字符串
          </div>
        </template>
      </Form>
    </Modal>

    <!-- Add Modal -->
     <Modal
      v-model:open="addModalVisible"
      :title="`添加: ${addDeviceType === 'network' ? '网络接口' : '挂载点'}`"
      @ok="handleAddSave"
      :confirm-loading="confirmLoading"
      width="600px"
      ok-text="添加"
      cancel-text="取消"
    >
      <Form layout="vertical" :model="addForm">
        <template v-if="addDeviceType === 'network'">
           <FormItem label="桥接接口">
              <Select v-model:value="addForm.netBridge">
                 <Select.Option v-for="n in networkList" :key="n.iface" :value="n.iface">
                   {{ n.iface }} ({{ n.active ? 'Active' : 'Inactive' }})
                 </Select.Option>
              </Select>
           </FormItem>
           <FormItem label="IPv4">
             <Input v-model:value="addForm.netIp" placeholder="dhcp 或 192.168.1.10/24" />
           </FormItem>
           <FormItem label="IPv4 网关">
             <Input v-model:value="addForm.netGw" placeholder="192.168.1.1" />
           </FormItem>
           <FormItem label="防火墙">
              <Checkbox v-model:checked="addForm.netFirewall">启用防火墙</Checkbox>
           </FormItem>
        </template>
        <template v-else-if="addDeviceType === 'mountpoint'">
           <FormItem label="存储" required>
              <Select v-model:value="addForm.mpStorage">
                 <Select.Option v-for="s in storageList" :key="s.storage" :value="s.storage">
                   {{ s.storage }} ({{ s.type }})
                 </Select.Option>
              </Select>
           </FormItem>
           <FormItem label="大小 (GiB)" required>
              <InputNumber v-model:value="addForm.mpSize" :min="1" style="width: 100%" />
           </FormItem>
           <FormItem label="挂载路径" required>
              <Input v-model:value="addForm.mpPath" placeholder="/mnt/data" />
           </FormItem>
        </template>
      </Form>
    </Modal>
  </div>
</template>
