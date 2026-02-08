<script setup lang="ts">
import type { PVEServerModel } from '#/api/pve/types';

import { onMounted, ref, watch } from 'vue';

import { EchartsUI, useEcharts } from '@vben/plugins/echarts';

import { DownloadOutlined, ReloadOutlined } from '@ant-design/icons-vue';
import { Button, Card, message, Select, Space, Spin } from 'ant-design-vue';

import {
  getNodeListApi,
  getNodeLxcApi,
  getNodeNetworkApi,
  getNodeQemuApi,
  getNodeResourceConfigApi,
  getPveNodesApi,
} from '#/api/pve/node';

defineOptions({
  name: 'PVETopology',
});

// State
const loading = ref(false);
const servers = ref<PVEServerModel[]>([]);
const nodes = ref<any[]>([]);
const selectedServerId = ref<number | undefined>();
const selectedNode = ref<string | undefined>();

const chartRef = ref();
const { renderEcharts, getInstance } = useEcharts(chartRef);

// Fetch Data helpers
const fetchServers = async () => {
  try {
    const res = await getNodeListApi();
    let data: any[] = [];
    if (Array.isArray(res)) data = res;
    else if ((res as any).results) data = (res as any).results;
    else if ((res as any).data)
      data = Array.isArray((res as any).data)
        ? (res as any).data
        : (res as any).data.results || [];

    servers.value = data.filter((s) => s.is_active);
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
    if (Array.isArray(res)) data = res;
    else if ((res as any).results) data = (res as any).results;
    else if ((res as any).data)
      data = Array.isArray((res as any).data)
        ? (res as any).data
        : (res as any).data.results || [];

    nodes.value = data;
    selectedNode.value = data.length > 0 ? data[0].node : undefined;
  } catch {
    message.error('获取节点列表失败');
    nodes.value = [];
  }
};

// Topology Generation
const fetchAndRenderTopology = async () => {
  if (!selectedServerId.value || !selectedNode.value) return;

  loading.value = true;
  try {
    // 1. Fetch Network Interfaces (Bridges & Physical)
    const netRes = await getNodeNetworkApi(
      selectedServerId.value,
      selectedNode.value,
    );
    let networks: any[] = [];
    if (Array.isArray(netRes)) networks = netRes;
    else if ((netRes as any).data)
      networks = Array.isArray((netRes as any).data)
        ? (netRes as any).data
        : [];

    // 2. Fetch VMs & LXCs
    const [vmRes, lxcRes] = await Promise.all([
      getNodeQemuApi(selectedServerId.value, selectedNode.value),
      getNodeLxcApi(selectedServerId.value, selectedNode.value),
    ]);

    let vms: any[] = Array.isArray(vmRes) ? vmRes : (vmRes as any)?.data || [];
    if (!Array.isArray(vms)) vms = [];

    let lxcs: any[] = Array.isArray(lxcRes)
      ? lxcRes
      : (lxcRes as any)?.data || [];
    if (!Array.isArray(lxcs)) lxcs = [];

    // 3. Build Graph Nodes & Links
    const graphNodes: any[] = [];
    const graphLinks: any[] = [];
    const categories = [
      { name: 'Gateway/Node' },
      { name: 'Bridge' },
      { name: 'Interface' },
      { name: 'VM' },
      { name: 'LXC' },
    ];

    // Icons (Material Design Paths)
    const icons = {
      server:
        'path://M2,2H22V6H2V2M2,10H22V14H2V10M2,18H22V22H2V18M4,4H8V4H4V4M4,12H8V12H4V12M4,20H8V20H4V20Z',
      bridge:
        'path://M12,2C6.48,2 2,6.48 2,12C2,17.52 6.48,22 12,22C17.52,22 22,17.52 22,12C22,6.48 17.52,2 12,2M12,20C7.59,20 4,16.41 4,12C4,7.59 7.59,4 12,4C16.41,4 20,7.59 20,12C20,16.41 16.41,20 12,20M13,6H11V10H7V12H11V17H13V12H17V10H13V6Z',
      interface: 'path://M7,2v15h10V2H7z M15,15H9V4h6V15z M11,17h2v5h-2V17z',
      vm: 'path://M21,2H3C1.89,2 1,2.89 1,4V16C1,17.11 1.89,18 3,18H10V20H8V22H16V20H14V18H21C22.11,18 23,17.11 23,16V4C23,2.89 22.11,2 21,2M21,16H3V4H21V16Z',
      lxc: 'path://M21,16.5C21,16.88 20.79,17.21 20.47,17.38L12.57,21.82C12.41,21.94 12.21,22 12,22C11.79,22 11.59,21.94 11.43,21.82L3.53,17.38C3.21,17.21 3,16.88 3,16.5V7.5C3,7.12 3.21,6.79 3.53,6.62L11.43,2.18C11.59,2.06 11.79,2 12,2C12.21,2 12.41,2.06 12.57,2.18L20.47,6.62C20.79,6.79 21,7.12 21,7.5V16.5M12,4.15L6.04,7.5L12,10.85L17.96,7.5L12,4.15M5,15.91L11,19.29V12.58L5,9.21V15.91M19,15.91V9.21L13,12.58V19.29L19,15.91Z',
    };

    // Add Node/Gateway root
    const rootName = selectedNode.value;
    graphNodes.push({
      id: rootName,
      name: rootName,
      symbol: icons.server,
      symbolSize: 60,
      category: 0,
      itemStyle: { color: '#5470c6' },
      label: { show: true, position: 'bottom', fontWeight: 'bold' },
    });

    // Process Network Interfaces
    const bridges: string[] = [];
    networks.forEach((net) => {
      if (net.type === 'bridge') {
        bridges.push(net.iface);
        graphNodes.push({
          id: net.iface,
          name: `${net.iface}\n(${net.address || 'No IP'})`,
          symbol: icons.bridge,
          symbolSize: 45,
          category: 1, // Bridge
          itemStyle: { color: '#91cc75' },
          label: { show: true, position: 'right' },
        });
        // Connect Bridge to Node (Virtual connection)
        // graphLinks.push({ source: net.iface, target: rootName });

        // Process Bridge Ports (Physical Interfaces)
        if (net.bridge_ports) {
          const ports = net.bridge_ports.split(/\s+/);
          ports.forEach((port: string) => {
            if (!graphNodes.find((n) => n.id === port)) {
              graphNodes.push({
                id: port,
                name: port,
                symbol: icons.interface,
                symbolSize: 30,
                category: 2, // Interface
                itemStyle: { color: '#fac858' },
                label: { show: true, position: 'bottom' },
              });
            }
            graphLinks.push({ source: port, target: net.iface });
          });
        }
      } else if (!graphNodes.find((n) => n.id === net.iface) && net.active) {
        graphNodes.push({
          id: net.iface,
          name: net.iface,
          symbol: icons.interface,
          symbolSize: 30,
          category: 2,
          itemStyle: { color: '#fac858' },
          label: { show: true },
        });
        // Connect to Root just to show membership
        graphLinks.push({
          source: net.iface,
          target: rootName,
          lineStyle: { type: 'dashed' },
        });
      }
    });

    // 4. Fetch Configs for VMs/LXCs to find connections
    const findBridge = (config: any) => {
      const bridgesFound: string[] = [];
      for (const key in config) {
        if (key.startsWith('net')) {
          const match = config[key].match(/bridge=([\w\-]+)/);
          if (match && match[1]) {
            bridgesFound.push(match[1]);
          }
        }
      }
      return bridgesFound;
    };

    const vmConfigs = await Promise.all(
      vms.map((vm) =>
        getNodeResourceConfigApi(
          selectedServerId.value!,
          selectedNode.value!,
          'qemu',
          vm.vmid,
        )
          .then((res) => ({
            vmid: vm.vmid,
            name: vm.name,
            config: (res as any).data || res,
          }))
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
          .then((res) => ({
            vmid: lxc.vmid,
            name: lxc.name,
            config: (res as any).data || res,
          }))
          .catch(() => null),
      ),
    );

    // Process VMs
    vmConfigs.forEach((vm) => {
      if (!vm) return;
      const id = `VM ${vm.vmid}`;
      graphNodes.push({
        id,
        name: `${id}\n${vm.name}`,
        symbol: icons.vm,
        symbolSize: 35,
        category: 3, // VM
        itemStyle: { color: '#ee6666' },
        label: { show: true, position: 'right' },
      });

      const bridges = findBridge(vm.config);
      if (bridges.length > 0) {
        bridges.forEach((br) => {
          if (!graphNodes.find((n) => n.id === br)) {
            graphNodes.push({
              id: br,
              name: br,
              category: 1,
              symbol: icons.bridge,
              symbolSize: 30,
            });
          }
          graphLinks.push({ source: id, target: br });
        });
      }
    });

    // Process LXCs
    lxcConfigs.forEach((lxc) => {
      if (!lxc) return;
      const id = `LXC ${lxc.vmid}`;
      graphNodes.push({
        id,
        name: `${id}\n${lxc.name}`,
        symbol: icons.lxc,
        symbolSize: 35,
        category: 4, // LXC
        itemStyle: { color: '#73c0de' },
        label: { show: true, position: 'right' },
      });

      const bridges = findBridge(lxc.config);
      bridges.forEach((br) => {
        if (!graphNodes.find((n) => n.id === br)) {
          graphNodes.push({
            id: br,
            name: br,
            category: 1,
            symbol: icons.bridge,
            symbolSize: 30,
          });
        }
        graphLinks.push({ source: id, target: br });
      });
    });

    // Render Logic
    renderEcharts({
      tooltip: {},
      legend: {
        data: categories.map((a) => a.name),
      },
      animationDuration: 1500,
      animationEasingUpdate: 'quinticInOut',
      series: [
        {
          name: 'Network Topology',
          type: 'graph',
          layout: 'force',
          data: graphNodes,
          links: graphLinks,
          categories,
          roam: true,
          label: {
            show: true,
            position: 'right',
            formatter: '{b}',
          },
          lineStyle: {
            color: 'source',
            curveness: 0.3,
          },
          emphasis: {
            focus: 'adjacency',
            lineStyle: {
              width: 4,
            },
          },
          force: {
            repulsion: 800,
            edgeLength: 150,
            gravity: 0.05,
          },
        },
      ],
    });
  } catch (error: any) {
    message.error(`加载拓扑失败: ${error.message}`);
  } finally {
    loading.value = false;
  }
};

const handleExport = () => {
  const instance = getInstance();
  if (instance) {
    const url = instance.getDataURL({
      type: 'png',
      pixelRatio: 2,
      backgroundColor: '#fff',
    });
    const link = document.createElement('a');
    link.download = `topology-${selectedNode.value}.png`;
    link.href = url;
    document.body.append(link);
    link.click();
    link.remove();
  }
};

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
    fetchAndRenderTopology();
  }
});
</script>

<template>
  <div class="flex h-full flex-col p-5">
    <Card title="网络拓扑" class="flex h-full flex-col shadow-sm">
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

          <Button
            @click="fetchAndRenderTopology"
            :disabled="!selectedNode"
            :loading="loading"
          >
            <template #icon><ReloadOutlined /></template>
            刷新
          </Button>

          <Button @click="handleExport" :disabled="!selectedNode || loading">
            <template #icon><DownloadOutlined /></template>
            导出图片
          </Button>
        </Space>
      </template>

      <div class="relative min-h-[600px] w-full flex-1">
        <Spin :spinning="loading" tip="正在生成拓扑图..." class="h-full w-full">
          <EchartsUI ref="chartRef" class="h-full w-full" />
        </Spin>
      </div>
    </Card>
  </div>
</template>

<style scoped>
:deep(.ant-card-body) {
  display: flex;
  flex: 1;
  flex-direction: column;
  padding: 0;
}

:deep(.ant-card) {
  display: flex;
  flex-direction: column;
}
</style>
