<script setup lang="ts">
import type { PveNetworkInterface, PVEServerModel } from '#/api/pve/types';

import { computed, onMounted, ref, watch } from 'vue';

import { ClusterOutlined, ReloadOutlined } from '@ant-design/icons-vue';
import {
  Button,
  Card,
  message,
  Select,
  Space,
  Table,
  Tag,
} from 'ant-design-vue';

import {
  getNodeListApi,
  getNodeNetworkApi,
  getPveNodesApi,
} from '#/api/pve/node';

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
];

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
      selectedServerId.value = servers.value[0].id;
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
        </template>
      </Table>
    </Card>
  </div>
</template>
