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
  Divider,
  Dropdown,
  Form,
  FormItem,
  Input,
  InputNumber,
  Menu,
  MenuItem,
  message,
  Modal,
  Radio,
  RadioGroup,
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

  // 7. Unused Disks
  Object.keys(conf).forEach((key) => {
    if (/^unused\d+$/.test(key)) {
      items.push({
        key,
        type: '未使用磁盘',
        device: key,
        value: conf[key],
        rawValue: conf[key],
        editable: false,
        removable: true,
      });
    }
  });

  // 8. DNS
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

const parseNetworkConfig = (configStr: string) => {
  const result: any = {
    name: '',
    bridge: '',
    hwaddr: '',
    ip: '',
    gw: '',
    ip6: '',
    gw6: '',
    firewall: false,
    mtu: '',
    rate: '',
    vlan: '',
    disconnect: false,
    
    // Modes for UI logic
    ipv4Mode: 'static',
    ipv6Mode: 'static',
  };
  
  if (!configStr) return result;
  
  const parts = configStr.split(',');
  parts.forEach((part) => {
    const [key, value] = part.split('=');
    if (key && value !== undefined) {
      const trimmedKey = key.trim();
      const trimmedValue = value.trim();
      
      if (trimmedKey === 'name') result.name = trimmedValue;
      else if (trimmedKey === 'bridge') result.bridge = trimmedValue;
      else if (trimmedKey === 'hwaddr') result.hwaddr = trimmedValue;
      else if (trimmedKey === 'ip') result.ip = trimmedValue;
      else if (trimmedKey === 'gw') result.gw = trimmedValue;
      else if (trimmedKey === 'ip6') result.ip6 = trimmedValue;
      else if (trimmedKey === 'gw6') result.gw6 = trimmedValue;
      else if (trimmedKey === 'firewall') result.firewall = trimmedValue === '1';
      else if (trimmedKey === 'mtu') result.mtu = trimmedValue;
      else if (trimmedKey === 'rate') result.rate = trimmedValue;
      else if (trimmedKey === 'tag') result.vlan = trimmedValue; // VLAN Tag
      else if (trimmedKey === 'link_down') result.disconnect = trimmedValue === '1'; // Disconnect
    }
  });

  // Determine IPv4 Mode
  if (result.ip === 'dhcp') {
    result.ipv4Mode = 'dhcp';
    result.ip = ''; // Clear IP field for UI if DHCP is selected
  } else if (result.ip === 'manual') { // Sometimes manual is used
     result.ipv4Mode = 'static'; 
  }

  // Determine IPv6 Mode
  if (result.ip6 === 'auto') {
    result.ipv6Mode = 'slaac';
    result.ip6 = '';
  } else if (result.ip6 === 'dhcp') {
    result.ipv6Mode = 'dhcp';
    result.ip6 = '';
  } else if (result.ip6 === 'manual') {
    result.ipv6Mode = 'static'; // Or keep as manual? PVE treats empty ip6 as 'manual' usually or explicit manual
    // If it is strictly manual, we might want a separate mode, but let's stick to Static/DHCP/SLAAC
  }

  return result;
};

const buildNetworkConfig = (formData: any) => {
  const parts: string[] = [];
  
  if (formData.name) parts.push(`name=${formData.name}`);
  if (formData.bridge) parts.push(`bridge=${formData.bridge}`);
  if (formData.hwaddr) parts.push(`hwaddr=${formData.hwaddr}`);
  
  // IPv4 Logic
  if (formData.ipv4Mode === 'dhcp') {
    parts.push('ip=dhcp');
  } else {
    if (formData.ip) parts.push(`ip=${formData.ip}`);
    if (formData.gw) parts.push(`gw=${formData.gw}`);
  }
  
  // IPv6 Logic
  if (formData.ipv6Mode === 'slaac') {
    parts.push('ip6=auto');
  } else if (formData.ipv6Mode === 'dhcp') {
    parts.push('ip6=dhcp');
  } else {
    // Static
    if (formData.ip6) parts.push(`ip6=${formData.ip6}`);
    if (formData.gw6) parts.push(`gw6=${formData.gw6}`);
  }

  if (formData.firewall) parts.push('firewall=1');
  if (formData.mtu) parts.push(`mtu=${formData.mtu}`);
  if (formData.rate) parts.push(`rate=${formData.rate}`);
  if (formData.vlan) parts.push(`tag=${formData.vlan}`);
  if (formData.disconnect) parts.push('link_down=1');
  
  return parts.join(',');
};

const handleEdit = async (record: any) => {
  editingItem.value = record;
  
  // For network interfaces, parse the config string
  if (record.device && /^net\d+$/.test(record.device)) {
    editForm.value = parseNetworkConfig(record.rawValue);
    editForm.value._deviceKey = record.device;
    
    // Load network list for bridge selection
    const lxcData =
      props.lxc && (props.lxc as any).data ? (props.lxc as any).data : props.lxc;
    
    if (lxcData && lxcData.server && lxcData.node && networkList.value.length === 0) {
      try {
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
      } catch (e) {
        console.error('Failed to load network list', e);
      }
    }
  } else {
    editForm.value = { [record.device]: record.rawValue };
  }
  
  editModalVisible.value = true;
};

const handleSaveEdit = async () => {
  if (!props.lxcId) return;

  try {
    const params: any = {};
    
    // For network interfaces, build the config string
    if (editingItem.value.device && /^net\d+$/.test(editingItem.value.device)) {
      const key = editForm.value._deviceKey || editingItem.value.device;
      params[key] = buildNetworkConfig(editForm.value);
    } else {
      const key = editingItem.value.device;
      params[key] = editForm.value[key];
    }

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

  // 检查是否是挂载点
  const isMountPoint = /^mp\d+$/.test(record.device);
  // 检查是否是未使用的磁盘
  const isUnusedDisk = /^unused\d+$/.test(record.device);
  
  if (isMountPoint) {
    // 对于挂载点，提供两个选项
    Modal.confirm({
      title: '删除挂载点',
      content: '请选择删除方式：\n\n• 点击"删除磁盘"：卸载并永久删除磁盘数据（不可恢复）\n• 点击"仅卸载"：解除挂载，磁盘数据保留为"未使用"状态',
      okText: '删除磁盘',
      okType: 'danger',
      cancelText: '仅卸载',
      onOk: async () => {
        // 删除磁盘数据 - 先卸载，然后删除所有 unused
        try {
          // 第一步：卸载挂载点
          const params: any = { delete: record.device };
          await updateLxcConfigApi(props.lxcId, params);
          
          // 等待配置更新
          await new Promise(resolve => setTimeout(resolve, 1000));
          
          // 第二步：重新加载配置获取 unused 磁盘
          const res: any = await getLxcConfigApi(props.lxcId);
          const extractedConfig = res?.data?.config || res?.config || res?.data || res || {};
          
          console.log('配置信息:', extractedConfig);
          
          // 第三步：查找并删除所有 unused 磁盘
          const unusedKeys = Object.keys(extractedConfig).filter(key => /^unused\d+$/.test(key));
          console.log('找到的 unused 磁盘:', unusedKeys);
          
          if (unusedKeys.length > 0) {
            // 逐个删除 unused 磁盘
            for (const unusedKey of unusedKeys) {
              const deleteParams: any = { delete: unusedKey };
              await updateLxcConfigApi(props.lxcId, deleteParams);
              console.log(`已删除: ${unusedKey}`);
            }
            message.success('挂载点已删除，磁盘数据已清除');
          } else {
            message.success('挂载点已删除');
          }
          
          loadConfig();
        } catch (error: any) {
          console.error('删除失败:', error);
          message.error(error.message || '删除失败');
        }
      },
      onCancel: async () => {
        // 仅卸载
        try {
          const params: any = { delete: record.device };
          await updateLxcConfigApi(props.lxcId, params);
          message.success('挂载点已卸载，磁盘数据保留为"未使用"状态');
          loadConfig();
        } catch (error: any) {
          console.error('卸载失败:', error);
          message.error(error.message || '卸载失败');
        }
      },
    });
  } else if (isUnusedDisk) {
    // 对于未使用的磁盘，直接删除
    Modal.confirm({
      title: '删除未使用的磁盘',
      content: `确定要永久删除磁盘 ${record.device} 吗？\n\n磁盘数据: ${record.value}\n\n此操作不可恢复！`,
      okText: '删除',
      okType: 'danger',
      cancelText: '取消',
      onOk: async () => {
        try {
          const params: any = { delete: record.device };
          await updateLxcConfigApi(props.lxcId, params);
          message.success('未使用的磁盘已删除');
          loadConfig();
        } catch (error: any) {
          console.error('删除失败:', error);
          message.error(error.message || '删除失败');
        }
      },
    });
  } else {
    // 对于其他资源（网络接口等），直接删除
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
  }
};

// Add Device Logic
const addModalVisible = ref(false);
const addDeviceType = ref<'network' | 'mountpoint'>('network');
const confirmLoading = ref(false);
const networkList = ref<any[]>([]);
const storageList = ref<any[]>([]);
const addForm = ref<any>({
  // Network - 使用与编辑表单一致的字段名
  name: 'eth0',
  bridge: 'vmbr0',
  hwaddr: '',
  ip: '',
  gw: '',
  ip6: '',
  gw6: '',
  firewall: false,
  mtu: '',
  rate: '',
  vlan: '',
  disconnect: false,
  
  // Modes for UI logic
  ipv4Mode: 'dhcp',
  ipv6Mode: 'slaac',

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
          addForm.value.bridge = networkList.value[0].iface;
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
      // 使用与编辑表单相同的 buildNetworkConfig 函数
      params[`net${netId}`] = buildNetworkConfig(addForm.value);
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
      :width="editingItem?.device && /^net\d+$/.test(editingItem.device) ? 800 : 520"
    >
      <Form layout="vertical" v-if="editingItem">
        <!-- Network Interface Editing (PVE Style) -->
        <template v-if="editingItem.device && /^net\d+$/.test(editingItem.device)">
          <div class="grid grid-cols-2 gap-x-6">
            <!-- Left Column -->
            <div>
              <FormItem label="名称">
                <Input v-model:value="editForm.name" placeholder="eth0" />
              </FormItem>
              
              <FormItem label="MAC 地址">
                <Input v-model:value="editForm.hwaddr" placeholder="自动生成" />
              </FormItem>
              
              <FormItem label="网桥">
                <Select v-model:value="editForm.bridge" placeholder="选择网桥">
                  <Select.Option v-for="n in networkList" :key="n.iface" :value="n.iface">
                    {{ n.iface }}
                  </Select.Option>
                </Select>
              </FormItem>
              
              <FormItem label="VLAN 标签">
                 <InputNumber v-model:value="editForm.vlan" :min="1" :max="4094" placeholder="无 VLAN" style="width: 100%" />
              </FormItem>
              
              <FormItem>
                <Checkbox v-model:checked="editForm.firewall">防火墙</Checkbox>
              </FormItem>
            </div>
            
            <!-- Right Column -->
            <div>
              <!-- IPv4 -->
              <div class="mb-4">
                 <div class="mb-2 font-medium">IPv4</div>
                 <RadioGroup v-model:value="editForm.ipv4Mode" class="mb-2">
                    <Radio value="static">静态</Radio>
                    <Radio value="dhcp">DHCP</Radio>
                 </RadioGroup>
                 <template v-if="editForm.ipv4Mode === 'static'">
                     <FormItem label="IPv4/CIDR" class="mb-2">
                       <Input v-model:value="editForm.ip" placeholder="192.168.1.10/24" />
                     </FormItem>
                     <FormItem label="网关 (IPv4)" class="mb-0">
                       <Input v-model:value="editForm.gw" placeholder="192.168.1.1" />
                     </FormItem>
                 </template>
              </div>
              
              <Divider class="my-4" />
              
              <!-- IPv6 -->
              <div class="mb-0">
                 <div class="mb-2 font-medium">IPv6</div>
                 <RadioGroup v-model:value="editForm.ipv6Mode" class="mb-2">
                    <Radio value="static">静态</Radio>
                    <Radio value="dhcp">DHCP</Radio>
                    <Radio value="slaac">SLAAC</Radio>
                 </RadioGroup>
                 <template v-if="editForm.ipv6Mode === 'static'">
                     <FormItem label="IPv6/CIDR" class="mb-2">
                       <Input v-model:value="editForm.ip6" placeholder="IPv6 地址" />
                     </FormItem>
                     <FormItem label="网关 (IPv6)" class="mb-0">
                       <Input v-model:value="editForm.gw6" placeholder="IPv6 网关" />
                     </FormItem>
                 </template>
              </div>
            </div>
          </div>
          
          <Divider class="my-4" />
          
          <div class="grid grid-cols-2 gap-x-6">
              <div>
                 <FormItem class="mb-0">
                     <Checkbox v-model:checked="editForm.disconnect">断开</Checkbox>
                 </FormItem>
                 <FormItem label="MTU" class="mt-2 mb-0">
                    <Select v-model:value="editForm.mtu" placeholder="=当前网桥" allow-clear>
                      <Select.Option value="">= 当前网桥</Select.Option>
                      <Select.Option value="1500">1500</Select.Option>
                      <Select.Option value="9000">9000 (Jumbo Frames)</Select.Option>
                    </Select>
                 </FormItem>
              </div>
              <div>
                 <FormItem label="速率限制 (MB/s)" class="mb-0">
                    <Select v-model:value="editForm.rate" placeholder="unlimited" allow-clear>
                      <Select.Option value="">unlimited</Select.Option>
                      <Select.Option value="1">1 MB/s</Select.Option>
                      <Select.Option value="10">10 MB/s</Select.Option>
                      <Select.Option value="100">100 MB/s</Select.Option>
                      <Select.Option value="1000">1000 MB/s</Select.Option>
                    </Select>
                 </FormItem>
              </div>
          </div>
        </template>
        
        <!-- Memory/Swap Editing -->
        <template v-else-if="editingItem.device === 'memory' || editingItem.device === 'swap'">
           <FormItem :label="editingItem.type + ' (MB)'">
             <InputNumber v-model:value="editForm[editingItem.device]" :min="128" :step="128" style="width: 100%" />
           </FormItem>
        </template>
        
        <!-- Cores Editing -->
        <template v-else-if="editingItem.device === 'cores'">
           <FormItem label="核心数">
             <InputNumber v-model:value="editForm.cores" :min="1" :max="128" style="width: 100%" />
           </FormItem>
        </template>
        
        <!-- Generic Editing -->
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
      :width="addDeviceType === 'network' ? 800 : 600"
      ok-text="添加"
      cancel-text="取消"
    >
      <Form layout="vertical" :model="addForm">
        <template v-if="addDeviceType === 'network'">
          <div class="grid grid-cols-2 gap-x-6">
            <!-- Left Column -->
            <div>
              <FormItem label="名称">
                <Input v-model:value="addForm.name" placeholder="eth0" />
              </FormItem>
              
              <FormItem label="MAC 地址">
                <Input v-model:value="addForm.hwaddr" placeholder="自动生成" />
              </FormItem>
              
              <FormItem label="网桥">
                <Select v-model:value="addForm.bridge" placeholder="选择网桥">
                  <Select.Option v-for="n in networkList" :key="n.iface" :value="n.iface">
                    {{ n.iface }}
                  </Select.Option>
                </Select>
              </FormItem>

              <FormItem label="VLAN 标签">
                 <InputNumber v-model:value="addForm.vlan" :min="1" :max="4094" placeholder="无 VLAN" style="width: 100%" />
              </FormItem>

              <FormItem>
                 <Checkbox v-model:checked="addForm.firewall">防火墙</Checkbox>
              </FormItem>
            </div>

            <!-- Right Column -->
            <div>
               <!-- IPv4 -->
               <div class="mb-4">
                  <div class="mb-2 font-medium">IPv4</div>
                  <RadioGroup v-model:value="addForm.ipv4Mode" class="mb-2">
                     <Radio value="static">静态</Radio>
                     <Radio value="dhcp">DHCP</Radio>
                  </RadioGroup>
                  <template v-if="addForm.ipv4Mode === 'static'">
                      <FormItem label="IPv4/CIDR" class="mb-2">
                        <Input v-model:value="addForm.ip" placeholder="192.168.1.10/24" />
                      </FormItem>
                      <FormItem label="网关 (IPv4)" class="mb-0">
                        <Input v-model:value="addForm.gw" placeholder="192.168.1.1" />
                      </FormItem>
                  </template>
               </div>

               <Divider class="my-4" />

               <!-- IPv6 -->
               <div class="mb-0">
                  <div class="mb-2 font-medium">IPv6</div>
                  <RadioGroup v-model:value="addForm.ipv6Mode" class="mb-2">
                     <Radio value="static">静态</Radio>
                     <Radio value="dhcp">DHCP</Radio>
                     <Radio value="slaac">SLAAC</Radio>
                  </RadioGroup>
                  <template v-if="addForm.ipv6Mode === 'static'">
                      <FormItem label="IPv6/CIDR" class="mb-2">
                        <Input v-model:value="addForm.ip6" placeholder="IPv6 地址" />
                      </FormItem>
                      <FormItem label="网关 (IPv6)" class="mb-0">
                        <Input v-model:value="addForm.gw6" placeholder="IPv6 网关" />
                      </FormItem>
                  </template>
               </div>
            </div>
          </div>

          <Divider class="my-4" />

          <div class="grid grid-cols-2 gap-x-6">
              <div>
                 <FormItem class="mb-0">
                     <Checkbox v-model:checked="addForm.disconnect">断开</Checkbox>
                 </FormItem>
                 <FormItem label="MTU" class="mt-2 mb-0">
                    <Select v-model:value="addForm.mtu" placeholder="=当前网桥" allow-clear>
                      <Select.Option value="">= 当前网桥</Select.Option>
                      <Select.Option value="1500">1500</Select.Option>
                      <Select.Option value="9000">9000 (Jumbo Frames)</Select.Option>
                    </Select>
                 </FormItem>
              </div>
              <div>
                 <FormItem label="速率限制 (MB/s)" class="mb-0">
                    <Select v-model:value="addForm.rate" placeholder="unlimited" allow-clear>
                      <Select.Option value="">unlimited</Select.Option>
                      <Select.Option value="1">1 MB/s</Select.Option>
                      <Select.Option value="10">10 MB/s</Select.Option>
                      <Select.Option value="100">100 MB/s</Select.Option>
                      <Select.Option value="1000">1000 MB/s</Select.Option>
                    </Select>
                 </FormItem>
              </div>
          </div>
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
