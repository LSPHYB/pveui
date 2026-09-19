<script setup lang="ts">
import type {
  PveNetworkInterface,
  PveNetworkType,
  PVEServerModel,
} from '#/api/pve/types';

import { computed, onMounted, ref, watch } from 'vue';

import {
  CheckCircleOutlined,
  ClusterOutlined,
  DownOutlined,
  PlusOutlined,
  ReloadOutlined,
  UndoOutlined,
} from '@ant-design/icons-vue';
import {
  Button,
  Card,
  Dropdown,
  Menu,
  MenuItem,
  message,
  Modal,
  Select,
  Space,
  Table,
  Tag,
} from 'ant-design-vue';

import {
  applyNodeNetworkApi,
  deleteNodeNetworkApi,
  getNodeListApi,
  getNodeNetworkApi,
  getPveNodesApi,
  revertNodeNetworkApi,
} from '#/api/pve/node';

import CreateNetworkModal from './CreateNetworkModal.vue';

defineOptions({
  name: 'PVENetwork',
});

// State
const loading = ref(false);
const servers = ref<PVEServerModel[]>([]);
const nodes = ref<any[]>([]);
const networkList = ref<PveNetworkInterface[]>([]);

const selectedServerId = ref<number | undefined>();
const selectedNode = ref<string | undefined>();

// Columns
const columns = [
  { title: '接口名称', dataIndex: 'iface', key: 'iface', width: 120 },
  { title: '类型', dataIndex: 'type', key: 'type', width: 100 },
  { title: '状态', key: 'active', width: 80 },
  { title: '自动启动', key: 'autostart', width: 90 },
  { title: '端口/从属', dataIndex: 'bridge_ports', key: 'bridge_ports' },
  { title: 'IP/CIDR', key: 'address', width: 150 },
  { title: '网关', dataIndex: 'gateway', key: 'gateway', width: 120 },
  { title: '备注', dataIndex: 'comments', key: 'comments' },
  { title: '操作', key: 'action', width: 130, fixed: 'right' as const },
];

/** 仅这三类由本系统管理，物理网卡等不提供编辑/删除 */
const EDITABLE_TYPES = new Set(['bond', 'bridge', 'vlan']);

// Actions
const fetchServers = async () => {
  try {
    const res = await getNodeListApi();
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

    // @ts-ignore
    servers.value = data.filter((s) => s.is_active);

    // Auto select first
    if (!selectedServerId.value && servers.value.length > 0) {
      selectedServerId.value = servers.value[0]?.id;
    }
  } catch {
    message.error('获取服务器列表失败');
  }
};

const fetchNodes = async (serverId: number) => {
  try {
    const res = await getPveNodesApi(serverId);
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

    nodes.value = data;
    if (data.length > 0) {
      selectedNode.value = data[0].node;
    } else {
      selectedNode.value = undefined;
      networkList.value = [];
    }
  } catch {
    message.error('获取节点列表失败');
    nodes.value = [];
  }
};

const fetchNetwork = async () => {
  if (!selectedServerId.value || !selectedNode.value) return;

  loading.value = true;
  try {
    const res = await getNodeNetworkApi(
      selectedServerId.value,
      selectedNode.value,
    );
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

    networkList.value = data;
  } catch (error: any) {
    message.error(`获取网络信息失败: ${error.message}`);
  } finally {
    loading.value = false;
  }
};

const filterType = ref<string>('all');

const uniqueTypes = computed(() => {
  const types = new Set(networkList.value.map((item) => item.type));
  // Map types to user friendly names if needed, but for now just use raw type
  return ['all', ...[...types].sort()];
});

const getTypeLabel = (type: string) => {
  const typeMap: Record<string, string> = {
    all: '全部类型',
    bridge: '桥接 (Bridge)',
    bond: '绑定 (Bond)',
    eth: '以太网 (Ethernet)',
    alias: '别名 (Alias)',
    vlan: 'VLAN',
    OVSBridge: 'OVS Bridge',
    OVSBond: 'OVS Bond',
    OVSPort: 'OVS Port',
    OVSIntPort: 'OVS IntPort',
  };
  return typeMap[type] || type;
};

const filteredList = computed(() => {
  if (filterType.value === 'all') {
    return networkList.value;
  }
  return networkList.value.filter((item) => item.type === filterType.value);
});

// --- 新增 / 应用配置 ---
const createOpen = ref(false);
const createType = ref<PveNetworkType>('bridge');
const applying = ref(false);

const CREATE_TYPES: { label: string; value: PveNetworkType }[] = [
  { label: 'Linux Bridge', value: 'bridge' },
  { label: 'Linux Bond', value: 'bond' },
  { label: 'Linux VLAN', value: 'vlan' },
];

const editMode = ref<'create' | 'edit'>('create');
const editRecord = ref<PveNetworkInterface | undefined>();

const openCreate = (type: PveNetworkType) => {
  editMode.value = 'create';
  editRecord.value = undefined;
  createType.value = type;
  createOpen.value = true;
};

// Table 的 bodyCell 插槽丢失了行类型，在入口处收敛一次
const openEdit = (row: Record<string, any>) => {
  const record = row as PveNetworkInterface;
  editMode.value = 'edit';
  editRecord.value = record;
  createType.value = record.type as PveNetworkType;
  createOpen.value = true;
};

const handleDelete = (row: Record<string, any>) => {
  const record = row as PveNetworkInterface;
  if (!selectedServerId.value || !selectedNode.value) return;
  Modal.confirm({
    title: `删除网络设备 ${record.iface}`,
    content:
      '删除后需点击「应用配置」才会真正生效。若该设备正被虚拟机或其他接口使用，PVE 会拒绝删除。',
    okText: '删除',
    okType: 'danger',
    cancelText: '取消',
    onOk: async () => {
      try {
        await deleteNodeNetworkApi(
          selectedServerId.value!,
          selectedNode.value!,
          record.iface,
        );
        message.success(`${record.iface} 已删除，需点击「应用配置」后生效`);
        await fetchNetwork();
      } catch (error: any) {
        message.error(`删除失败: ${error?.message || '未知错误'}`);
      }
    },
  });
};

const handleApply = () => {
  if (!selectedServerId.value || !selectedNode.value) return;
  Modal.confirm({
    title: '应用网络配置',
    content:
      '将重载该节点的网络配置使待生效变更生效。若配置有误可能导致节点网络中断，确认继续？',
    okText: '应用',
    okType: 'danger',
    cancelText: '取消',
    onOk: async () => {
      applying.value = true;
      try {
        await applyNodeNetworkApi(selectedServerId.value!, selectedNode.value!);
        message.success('网络配置已应用');
        await fetchNetwork();
      } catch (error: any) {
        message.error(`应用失败: ${error?.message || '未知错误'}`);
      } finally {
        applying.value = false;
      }
    },
  });
};

const handleRevert = () => {
  if (!selectedServerId.value || !selectedNode.value) return;
  Modal.confirm({
    title: '回滚未应用的变更',
    content: '将丢弃所有尚未应用的网络配置变更，确认继续？',
    okText: '回滚',
    okType: 'danger',
    cancelText: '取消',
    onOk: async () => {
      try {
        await revertNodeNetworkApi(selectedServerId.value!, selectedNode.value!);
        message.success('已回滚未应用的变更');
        await fetchNetwork();
      } catch (error: any) {
        message.error(`回滚失败: ${error?.message || '未知错误'}`);
      }
    },
  });
};

// Lifecycle & Watch
onMounted(() => {
  fetchServers();
});

watch(selectedServerId, (newVal) => {
  if (newVal) {
    fetchNodes(newVal);
  }
});

watch(selectedNode, (newVal) => {
  if (newVal) {
    fetchNetwork();
  }
});
</script>

<template>
  <div class="p-5">
    <Card title="网络管理">
      <template #extra>
        <Space>
          <span class="text-gray-500">服务器:</span>
          <Select
            v-model:value="selectedServerId"
            style="width: 200px"
            placeholder="选择服务器"
            :options="servers.map((s) => ({ label: s.name, value: s.id }))"
          />

          <span class="ml-4 text-gray-500">节点:</span>
          <Select
            v-model:value="selectedNode"
            style="width: 150px"
            placeholder="选择节点"
            :options="nodes.map((n) => ({ label: n.node, value: n.node }))"
            :disabled="!selectedServerId"
          />

          <span class="ml-4 text-gray-500">类型:</span>
          <Select
            v-model:value="filterType"
            style="width: 150px"
            placeholder="选择类型"
            :options="
              uniqueTypes.map((t) => ({ label: getTypeLabel(t), value: t }))
            "
          />

          <Dropdown :disabled="!selectedNode">
            <Button type="primary">
              <template #icon><PlusOutlined /></template>
              新增
              <DownOutlined />
            </Button>
            <template #overlay>
              <Menu @click="({ key }) => openCreate(key as PveNetworkType)">
                <MenuItem v-for="t in CREATE_TYPES" :key="t.value">
                  {{ t.label }}
                </MenuItem>
              </Menu>
            </template>
          </Dropdown>

          <Button
            @click="handleApply"
            :disabled="!selectedNode"
            :loading="applying"
          >
            <template #icon><CheckCircleOutlined /></template>
            应用配置
          </Button>

          <Button @click="handleRevert" :disabled="!selectedNode">
            <template #icon><UndoOutlined /></template>
            回滚
          </Button>

          <Button
            @click="fetchNetwork"
            :disabled="!selectedNode"
            :loading="loading"
          >
            <template #icon><ReloadOutlined /></template>
            刷新
          </Button>
        </Space>
      </template>

      <Table
        :columns="columns"
        :data-source="filteredList"
        :loading="loading"
        :pagination="false"
        row-key="iface"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'iface'">
            <Space>
              <ClusterOutlined />
              <span class="font-medium">{{ record.iface }}</span>
            </Space>
          </template>

          <template v-else-if="column.key === 'active'">
            <Tag :color="record.active ? 'success' : 'default'">
              {{ record.active ? '活动' : '非活动' }}
            </Tag>
          </template>

          <template v-else-if="column.key === 'autostart'">
            <Tag :color="record.autostart ? 'blue' : 'default'">
              {{ record.autostart ? '是' : '否' }}
            </Tag>
          </template>

          <template v-else-if="column.key === 'address'">
            <span v-if="record.address"
              >{{ record.address
              }}<span v-if="record.cidr">/{{ record.cidr }}</span></span
            >
            <span v-else class="text-gray-400">-</span>
          </template>

          <template v-else-if="column.key === 'gateway'">
            <span v-if="record.gateway">{{ record.gateway }}</span>
            <span v-else class="text-gray-400">-</span>
          </template>

          <template v-else-if="column.key === 'action'">
            <Space v-if="EDITABLE_TYPES.has(record.type)">
              <Button type="link" size="small" @click="openEdit(record)">
                编辑
              </Button>
              <Button
                type="link"
                size="small"
                danger
                @click="handleDelete(record)"
              >
                删除
              </Button>
            </Space>
            <span v-else class="text-gray-400">-</span>
          </template>
        </template>
      </Table>
    </Card>

    <CreateNetworkModal
      v-model:open="createOpen"
      :mode="editMode"
      :type="createType"
      :record="editRecord"
      :server-id="selectedServerId"
      :node="selectedNode"
      @success="fetchNetwork"
    />
  </div>
</template>
