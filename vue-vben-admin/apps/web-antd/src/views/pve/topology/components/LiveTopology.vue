<script setup lang="ts">
import type { ElementDefinition } from 'cytoscape';
import type { PVEServerModel } from '#/api/pve/types';

import { onMounted, ref } from 'vue';

import {
  DownloadOutlined,
  ImportOutlined,
  ReloadOutlined,
} from '@ant-design/icons-vue';
import { Button, Descriptions, Drawer, message, Select, Space, Spin, Tag } from 'ant-design-vue';

import {
  getNodeListApi,
  getNodeLxcApi,
  getNodeNetworkApi,
  getNodeQemuApi,
  getNodeResourceConfigApi,
  getPveNodesApi,
} from '#/api/pve/node';

import { NODE_TYPES } from '../utils/cytoscape-style';
import { pveDataToCytoscape } from '../utils/pve-to-cytoscape';
import CytoscapeCanvas from './CytoscapeCanvas.vue';

const emit = defineEmits<{
  /** 点击「导入到设计器」，携带 elements */
  importToDesigner: [elements: ElementDefinition[]];
}>();

const loading = ref(false);
const servers = ref<PVEServerModel[]>([]);
const nodes = ref<any[]>([]);
const selectedServerId = ref<number | undefined>();
const selectedNode = ref<string | undefined>();
const elements = ref<ElementDefinition[]>([]);

const canvasRef = ref<InstanceType<typeof CytoscapeCanvas>>();

// ── 节点详情抽屉 ──────────────────────────────────────
const nodeDetailOpen = ref(false);
const selectedNodeData = ref<Record<string, any> | null>(null);

const handleNodeClick = (data: Record<string, any>) => {
  selectedNodeData.value = data;
  nodeDetailOpen.value = true;
};

// ── 数据加载 ──────────────────────────────────────────
const fetchServers = async () => {
  try {
    const res = await getNodeListApi();
    let data: any[] = [];
    if (Array.isArray(res)) data = res;
    else if ((res as any).results) data = (res as any).results;
    else if ((res as any).data)
      data = Array.isArray((res as any).data)
        ? (res as any).data
        : (res as any).data?.results || [];
    servers.value = data.filter((s) => s.is_active);
    if (servers.value.length > 0) {
      selectedServerId.value = servers.value[0]!.id;
      await fetchNodes(servers.value[0]!.id);
    }
  } catch {
    message.error('获取服务器列表失败');
  }
};

const fetchNodes = async (serverId: number) => {
  try {
    const res = await getPveNodesApi(serverId);
    let data: any[] = [];
    if (Array.isArray(res)) data = res;
    else if ((res as any).results) data = (res as any).results;
    else if ((res as any).data)
      data = Array.isArray((res as any).data)
        ? (res as any).data
        : (res as any).data?.results || [];
    nodes.value = data;
    if (data.length > 0) {
      selectedNode.value = data[0].node;
      await loadTopology();
    }
  } catch {
    message.error('获取节点列表失败');
  }
};

const loadTopology = async () => {
  if (!selectedServerId.value || !selectedNode.value) return;
  loading.value = true;
  try {
    const netRes = await getNodeNetworkApi(selectedServerId.value, selectedNode.value);
    let networks: any[] = Array.isArray(netRes)
      ? netRes
      : (netRes as any)?.data ?? [];
    if (!Array.isArray(networks)) networks = [];

    const [vmRes, lxcRes] = await Promise.all([
      getNodeQemuApi(selectedServerId.value, selectedNode.value),
      getNodeLxcApi(selectedServerId.value, selectedNode.value),
    ]);
    let vms: any[] = Array.isArray(vmRes) ? vmRes : (vmRes as any)?.data ?? [];
    let lxcs: any[] = Array.isArray(lxcRes) ? lxcRes : (lxcRes as any)?.data ?? [];

    const vmConfigs = await Promise.all(
      vms.map((vm) =>
        getNodeResourceConfigApi(
          selectedServerId.value!,
          selectedNode.value!,
          'qemu',
          vm.vmid,
        )
          .then((r) => ({ vmid: vm.vmid, name: vm.name, config: (r as any).data ?? r }))
          .catch(() => null),
      ),
    );
    const lxcConfigs = await Promise.all(
      lxcs.map((lxc) =>
        getNodeResourceConfigApi(
          selectedServerId.value!,
          selectedNode.value!,
          'lxc',
          lxc.vmid,
        )
          .then((r) => ({ vmid: lxc.vmid, name: lxc.name, config: (r as any).data ?? r }))
          .catch(() => null),
      ),
    );

    elements.value = pveDataToCytoscape({
      nodeName: selectedNode.value,
      networks,
      vmConfigs,
      lxcConfigs,
    });
  } catch (err: any) {
    message.error(`加载拓扑失败: ${err.message}`);
  } finally {
    loading.value = false;
  }
};

const handleServerChange = async (val: number) => {
  selectedServerId.value = val;
  selectedNode.value = undefined;
  nodes.value = [];
  elements.value = [];
  await fetchNodes(val);
};

const handleNodeChange = async (val: string) => {
  selectedNode.value = val;
  await loadTopology();
};

const handleExport = () => {
  const png = canvasRef.value?.exportPng();
  if (!png) return;
  const link = document.createElement('a');
  link.download = `topology-${selectedNode.value ?? 'live'}.png`;
  link.href = png;
  link.click();
};

const handleImport = () => {
  if (!elements.value.length) {
    message.warning('请先加载拓扑后再导入');
    return;
  }
  emit('importToDesigner', elements.value);
};

const getTypeLabel = (type: string) =>
  NODE_TYPES[type as keyof typeof NODE_TYPES]?.label ?? type ?? '-';

const getTypeColor = (type: string) =>
  NODE_TYPES[type as keyof typeof NODE_TYPES]?.color ?? '#999';

onMounted(() => fetchServers());
</script>

<template>
  <div class="flex h-full flex-col gap-3">
    <!-- 工具栏 -->
    <div class="flex items-center gap-3 flex-wrap">
      <Space>
        <span class="text-sm text-gray-500">服务器:</span>
        <Select
          :value="selectedServerId"
          style="width: 180px"
          placeholder="选择服务器"
          :options="servers.map((s) => ({ label: s.name, value: s.id }))"
          @change="(val: any) => handleServerChange(val)"
        />
        <span class="text-sm text-gray-500">节点:</span>
        <Select
          :value="selectedNode"
          style="width: 140px"
          placeholder="选择节点"
          :options="nodes.map((n) => ({ label: n.node, value: n.node }))"
          :disabled="!selectedServerId"
          @change="(val: any) => handleNodeChange(val)"
        />
        <Button :loading="loading" :disabled="!selectedNode" @click="loadTopology">
          <template #icon><ReloadOutlined /></template>
          刷新
        </Button>
        <Button :disabled="!elements.length || loading" @click="handleExport">
          <template #icon><DownloadOutlined /></template>
          导出图片
        </Button>
        <Button
          type="primary"
          :disabled="!elements.length || loading"
          @click="handleImport"
        >
          <template #icon><ImportOutlined /></template>
          导入到设计器
        </Button>
      </Space>
    </div>

    <!-- 画布 -->
    <div class="relative" style="height: 600px">
      <Spin :spinning="loading" tip="正在加载实时拓扑..." style="height: 100%">
        <CytoscapeCanvas
          ref="canvasRef"
          :elements="elements"
          :readonly="true"
          style="height: 600px; width: 100%"
          @node-click="handleNodeClick"
        />
      </Spin>
      <div
        v-if="!selectedNode && !loading"
        class="pointer-events-none absolute inset-0 flex items-center justify-center text-gray-400"
      >
        请选择服务器和节点以加载实时拓扑
      </div>
    </div>
  </div>

  <!-- 节点详情抽屉 -->
  <Drawer
    v-model:open="nodeDetailOpen"
    :title="selectedNodeData?.label || '节点详情'"
    width="360"
    placement="right"
  >
    <template v-if="selectedNodeData">
      <Descriptions :column="1" bordered size="small">
        <Descriptions.Item label="节点名称">
          {{ selectedNodeData.label || '-' }}
        </Descriptions.Item>
        <Descriptions.Item label="节点类型">
          <Tag :color="getTypeColor(selectedNodeData.type)">
            {{ getTypeLabel(selectedNodeData.type) }}
          </Tag>
        </Descriptions.Item>
        <Descriptions.Item v-if="selectedNodeData.ip" label="IP / 网段">
          {{ selectedNodeData.ip }}
        </Descriptions.Item>
        <Descriptions.Item v-if="selectedNodeData.interface" label="接口">
          {{ selectedNodeData.interface }}
        </Descriptions.Item>
        <Descriptions.Item v-if="selectedNodeData.bridge" label="网桥">
          {{ selectedNodeData.bridge }}
        </Descriptions.Item>
        <!-- VM 网卡列表（MAC + 网桥，无 Guest Agent 时的备选信息） -->
        <Descriptions.Item
          v-if="selectedNodeData.nics?.length"
          :label="`网卡 (${selectedNodeData.nics.length})`"
        >
          <div v-for="(nic, i) in selectedNodeData.nics" :key="i" class="text-xs leading-5">
            <span class="text-gray-400">{{ nic.bridge || '无网桥' }}</span>
            <span class="ml-2 font-mono text-gray-500">{{ nic.mac }}</span>
          </div>
        </Descriptions.Item>
        <Descriptions.Item v-if="selectedNodeData.description" label="备注">
          {{ selectedNodeData.description }}
        </Descriptions.Item>
        <Descriptions.Item label="节点 ID">
          <span class="text-xs text-gray-400">{{ selectedNodeData.id }}</span>
        </Descriptions.Item>
      </Descriptions>
    </template>
  </Drawer>
</template>

<style scoped>
:deep(.ant-spin-container) {
  height: 100%;
}
</style>
