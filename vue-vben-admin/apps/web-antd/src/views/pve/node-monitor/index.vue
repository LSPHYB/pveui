<script setup lang="ts">
import type { PVEServerModel } from '#/api/pve/types';

import { computed, nextTick, onMounted, reactive, ref, watch } from 'vue';

import { Page } from '@vben/common-ui';
import { EchartsUI, useEcharts } from '@vben/plugins/echarts';

import { ReloadOutlined } from '@ant-design/icons-vue';
import {
  Alert,
  Button,
  Card,
  Col,
  Empty,
  message,
  Progress,
  Radio,
  Row,
  Select,
  Spin,
  Tag,
} from 'ant-design-vue';

import {
  getNodeListApi,
  getNodeMonitorApi,
  getPveNodesApi,
} from '#/api/pve/node';

defineOptions({ name: 'PVENodeMonitor' });

// --- State ---
const servers = ref<PVEServerModel[]>([]);
const nodes = ref<any[]>([]);
const selectedServer = ref<number | undefined>();
const selectedNode = ref<string | undefined>();
const timeframe = ref('hour');
const metrics = ref<any[]>([]);
const alerts = ref<any[]>([]);
const serverLoading = ref(false);
const nodeLoading = ref(false);
const monitorLoading = ref(false);
let monitorRequestId = 0;

const summary = reactive({
  cpu: { percent: 0, cores: 0, loadavg: null as any },
  memory: { total: 0, used: 0, percent: 0 },
  storage: { total: 0, used: 0, percent: 0 },
  network: { in: 0, out: 0 },
  uptime: 0,
  node: '',
  status: '',
  last_update: null as null | string,
});

const timeframeOptions = [
  { label: '1小时', value: 'hour' },
  { label: '1天', value: 'day' },
  { label: '1周', value: 'week' },
  { label: '1月', value: 'month' },
  { label: '1年', value: 'year' },
];

// --- Charts ---
const cpuChartRef = ref<any>(null);
const memoryChartRef = ref<any>(null);
const storageChartRef = ref<any>(null);
const networkChartRef = ref<any>(null);

const { renderEcharts: renderCpuChart } = useEcharts(cpuChartRef);
const { renderEcharts: renderMemoryChart } = useEcharts(memoryChartRef);
const { renderEcharts: renderStorageChart } = useEcharts(storageChartRef);
const { renderEcharts: renderNetworkChart } = useEcharts(networkChartRef);

// --- Computed ---
const serverOptions = computed(() =>
  servers.value.map((item) => ({
    label: `${item.name || item.host} (${item.host})`,
    value: item.id,
  })),
);

const nodeOptions = computed(() =>
  nodes.value.map((item) => ({
    label: item.node || item.name,
    value: item.node || item.name,
  })),
);

const formattedMetrics = computed(() => {
  if (!metrics.value?.length) return [];
  const memoryTotal = summary.memory.total || 0;
  const storageTotal = summary.storage.total || 0;

  return metrics.value.map((item) => {
    const time = item.time;
    const cpuPercent =
      typeof item.cpu === 'number' ? +(item.cpu * 100).toFixed(2) : 0;

    let memoryPercent = 0;
    if (item.maxmem && item.mem !== undefined) {
      memoryPercent = +((item.mem / item.maxmem) * 100).toFixed(2);
    } else if (memoryTotal > 0 && item.mem !== undefined) {
      memoryPercent = +((item.mem / memoryTotal) * 100).toFixed(2);
    } else if (summary.memory.percent > 0) {
      memoryPercent = summary.memory.percent;
    }

    let storagePercent = 0;
    if (item.maxdisk && item.disk !== undefined) {
      storagePercent = +((item.disk / item.maxdisk) * 100).toFixed(2);
    } else if (storageTotal > 0 && item.disk !== undefined) {
      storagePercent = +((item.disk / storageTotal) * 100).toFixed(2);
    } else if (summary.storage.percent > 0) {
      storagePercent = summary.storage.percent;
    }

    return {
      time,
      cpu: cpuPercent,
      memory: memoryPercent,
      storage: storagePercent,
      netIn: item.netin || 0,
      netOut: item.netout || 0,
    };
  });
});

// --- Actions ---

function handleServerChange() {
  if (selectedServer.value) {
    loadNodes();
  } else {
    selectedNode.value = undefined;
    metrics.value = [];
    alerts.value = [];
    resetSummary();
  }
}

function handleNodeChange() {
  if (selectedNode.value) {
    loadMonitor();
  } else {
    metrics.value = [];
    alerts.value = [];
    resetSummary();
  }
}

function handleTimeframeChange() {
  if (selectedServer.value && selectedNode.value) {
    loadMonitor();
  }
}

function resetSummary(data: any = {}) {
  summary.cpu.percent = data.cpu?.percent ?? 0;
  summary.cpu.cores = data.cpu?.cores ?? 0;
  summary.cpu.loadavg = data.cpu?.loadavg ?? null;
  summary.memory.total = data.memory?.total ?? 0;
  summary.memory.used = data.memory?.used ?? 0;
  summary.memory.percent = data.memory?.percent ?? 0;
  summary.storage.total = data.storage?.total ?? 0;
  summary.storage.used = data.storage?.used ?? 0;
  summary.storage.percent = data.storage?.percent ?? 0;
  summary.network.in = data.network?.in ?? 0;
  summary.network.out = data.network?.out ?? 0;
  summary.uptime = data.uptime ?? 0;
  summary.node = data.node ?? '';
  summary.status = data.status ?? '';
  summary.last_update = data.last_update ?? null;
}

async function loadServers() {
  serverLoading.value = true;
  try {
    const res: any = await getNodeListApi({ page_size: 1000 });
    console.log('PVE Servers Response:', res);

    // Handle array or wrapped list (DRF support)
    let data: any[] = [];
    if (Array.isArray(res)) {
      data = res;
    } else if (res?.results) {
      data = res.results;
    } else if (res?.data) {
      // Possible Vben wrapper or other structure
      data = Array.isArray(res.data) ? res.data : res.data?.results || [];
    }

    // If data is still empty, try keys? No, overly complex.

    // Looser filter: keep unless explicitly inactive false
    servers.value = data.filter((item: any) => item.is_active !== false);

    if (!selectedServer.value && servers.value.length > 0) {
      selectedServer.value = servers.value[0].id;
      loadNodes();
    }
  } catch (error: any) {
    console.error('Failed to load servers:', error);
    message.error(`获取服务器列表失败：${error.message || '未知错误'}`);
  } finally {
    serverLoading.value = false;
  }
}

async function loadNodes() {
  if (!selectedServer.value) return;
  nodeLoading.value = true;
  try {
    const res: any = await getPveNodesApi(selectedServer.value);
    console.log('PVE Nodes Response:', res);

    let data: any[] = [];
    if (Array.isArray(res)) {
      data = res;
    } else if (res?.data) {
      // PVE API for nodes often returns { data: [...] }
      data = Array.isArray(res.data) ? res.data : res.data?.results || [];
    } else if (res?.results) {
      data = res.results;
    }

    nodes.value = data;

    if (nodes.value.length > 0 && !selectedNode.value) {
      selectedNode.value = nodes.value[0].node || nodes.value[0].name;
      loadMonitor();
    } else if (selectedNode.value) {
      const exists = nodes.value.some(
        (item) => (item.node || item.name) === selectedNode.value,
      );
      if (!exists) {
        selectedNode.value =
          nodes.value[0]?.node || nodes.value[0]?.name || undefined;
        if (selectedNode.value) loadMonitor();
      }
    } else {
      selectedNode.value = undefined;
      metrics.value = [];
      resetSummary();
    }
  } catch (error: any) {
    console.error('Failed to load nodes:', error);
    message.error(`获取节点列表失败：${error.message || '未知错误'}`);
    nodes.value = [];
    selectedNode.value = undefined;
  } finally {
    nodeLoading.value = false;
  }
}

async function loadMonitor() {
  if (!selectedServer.value || !selectedNode.value) return;

  const requestId = ++monitorRequestId;
  monitorLoading.value = true;
  try {
    const res: any = await getNodeMonitorApi(
      selectedServer.value,
      selectedNode.value,
      { timeframe: timeframe.value },
    );
    if (requestId !== monitorRequestId) return;

    const result = res?.data || res || {};
    resetSummary(result.summary || {});
    metrics.value = Array.isArray(result.metrics) ? result.metrics : [];
    alerts.value = Array.isArray(result.alerts) ? result.alerts : [];

    if (
      result.status?.memory &&
      (!summary.memory.total || summary.memory.total === 0)
    ) {
      const statusMem = result.status.memory;
      if (statusMem.total && statusMem.used !== undefined) {
        summary.memory.total = statusMem.total;
        summary.memory.used = statusMem.used;
        summary.memory.percent =
          statusMem.total > 0
            ? +((statusMem.used / statusMem.total) * 100).toFixed(2)
            : 0;
      }
    }

    await nextTick();
    updateCharts();
  } catch (error: any) {
    if (requestId !== monitorRequestId) return;
    message.error(`获取节点监控数据失败：${error.message || '未知错误'}`);
    metrics.value = [];
    alerts.value = [];
    resetSummary();
  } finally {
    if (requestId === monitorRequestId) {
      monitorLoading.value = false;
    }
  }
}

// --- Chart Rendering ---
function updateCharts() {
  const data = formattedMetrics.value;

  const commonGrid = {
    left: '3%',
    right: '4%',
    bottom: '3%',
    top: '10%',
    containLabel: true,
  } as const;
  const commonXAxis = {
    type: 'category' as const,
    boundaryGap: false,
    data: data.map((item) => item.time),
    axisLabel: { formatter: (val: any) => formatTime(val, true) },
  };
  const commonTooltip = {
    trigger: 'axis' as const,
    axisPointer: { type: 'line' as const },
    formatter: (params: any) => {
      if (!params?.length) return '';
      const time = formatTime(params[0].axisValue);
      const lines = params.map((item: any) => {
        let val = item.value;
        val =
          item.componentSubType === 'line' && item.seriesName.includes('网络')
            ? formatThroughput(val, true)
            : `${val}%`;
        return `<div style="display:flex;align-items:center;">
             <span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:${item.color};margin-right:5px;"></span>
             ${item.seriesName}: ${val}
           </div>`;
      });
      return `<div>${time}</div>${lines.join('')}`;
    },
  };

  // CPU
  renderCpuChart({
    tooltip: commonTooltip,
    grid: commonGrid,
    xAxis: commonXAxis,
    yAxis: { type: 'value' as const, axisLabel: { formatter: '{value}%' } },
    series: [
      {
        name: 'CPU使用率',
        type: 'line',
        smooth: true,
        data: data.map((item) => item.cpu),
        itemStyle: { color: '#165DFF' },
        areaStyle: { opacity: 0.1 },
      },
    ],
  });

  // Memory
  renderMemoryChart({
    tooltip: commonTooltip,
    grid: commonGrid,
    xAxis: commonXAxis,
    yAxis: { type: 'value' as const, axisLabel: { formatter: '{value}%' } },
    series: [
      {
        name: '内存使用率',
        type: 'line',
        smooth: true,
        data: data.map((item) => item.memory),
        itemStyle: { color: '#00B42A' },
        areaStyle: { opacity: 0.1 },
      },
    ],
  });

  // Storage
  renderStorageChart({
    tooltip: commonTooltip,
    grid: commonGrid,
    xAxis: commonXAxis,
    yAxis: { type: 'value' as const, axisLabel: { formatter: '{value}%' } },
    series: [
      {
        name: '存储使用率',
        type: 'line',
        smooth: true,
        data: data.map((item) => item.storage),
        itemStyle: { color: '#F77234' },
        areaStyle: { opacity: 0.1 },
      },
    ],
  });

  // Network
  const maxNet = Math.max(
    ...data.map((item) => Math.max(item.netIn, item.netOut)),
  );
  const netUnit = maxNet >= 1024 * 1024 ? 'MB' : maxNet >= 1024 ? 'KB' : 'B';
  const formatNetAxis = (val: number) => {
    if (netUnit === 'MB') return `${(val / (1024 * 1024)).toFixed(1)} MB`;
    if (netUnit === 'KB') return `${(val / 1024).toFixed(1)} KB`;
    return `${val} B`;
  };

  renderNetworkChart({
    tooltip: {
      trigger: 'axis' as const,
      formatter: (params: any) => {
        if (!params?.length) return '';
        const time = formatTime(params[0].axisValue);
        const lines = params.map((item: any) => {
          const val = formatThroughput(item.value, true);
          return `<div style="display:flex;align-items:center;">
                 <span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:${item.color};margin-right:5px;"></span>
                 ${item.seriesName}: ${val}
               </div>`;
        });
        return `<div>${time}</div>${lines.join('')}`;
      },
    },
    grid: commonGrid,
    xAxis: commonXAxis,
    yAxis: { type: 'value' as const, axisLabel: { formatter: formatNetAxis } },
    series: [
      {
        name: '网络入站',
        type: 'line',
        smooth: true,
        data: data.map((item) => item.netIn),
        itemStyle: { color: '#14C9C9' },
        areaStyle: { opacity: 0.1 },
      },
      {
        name: '网络出站',
        type: 'line',
        smooth: true,
        data: data.map((item) => item.netOut),
        itemStyle: { color: '#F53F3F' },
        areaStyle: { opacity: 0.1 },
      },
    ],
  });
}

// --- Utils ---
function formatBytes(value: any) {
  if (!value && value !== 0) return '-';
  const units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB'];
  let index = 0;
  let num = Number(value);
  while (num >= 1024 && index < units.length - 1) {
    num /= 1024;
    index++;
  }
  return `${num.toFixed(num >= 10 || num < 1 ? 1 : 2)} ${units[index]}`;
}

function formatThroughput(value: any, short = false) {
  if (!value && value !== 0) return '-';
  const units = [
    { unit: 'B', scale: 1 },
    { unit: 'KB', scale: 1024 },
    { unit: 'MB', scale: 1024 ** 2 },
    { unit: 'GB', scale: 1024 ** 3 },
  ];
  let num = Number(value);
  let idx = 0;
  while (num >= 1024 && idx < units.length - 1) {
    num /= 1024;
    idx++;
  }
  const fixed = num >= 10 || short ? 1 : 2;
  return `${num.toFixed(fixed)} ${units[idx].unit}${short ? '' : '/s'}`;
}

function formatDuration(seconds: any) {
  const sec = Number(seconds || 0);
  if (!sec) return '-';
  const days = Math.floor(sec / 86_400);
  const hours = Math.floor((sec % 86_400) / 3600);
  const minutes = Math.floor((sec % 3600) / 60);
  if (days > 0) return `${days}天${hours}小时`;
  if (hours > 0) return `${hours}小时${minutes}分钟`;
  if (minutes > 0) return `${minutes}分钟`;
  return `${sec}s`;
}

function formatTime(timestamp: any, short = false) {
  if (!timestamp) return '-';
  const date = new Date(Number(timestamp));
  if (Number.isNaN(date.getTime())) return '-';
  if (short) {
    return date.toLocaleTimeString('zh-CN', {
      hour: '2-digit',
      minute: '2-digit',
    });
  }
  return date
    .toLocaleString('zh-CN', {
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    })
    .replaceAll('/', '-');
}

function formatLoad(loadavg: any) {
  if (!loadavg && loadavg !== 0) return '-';
  if (Array.isArray(loadavg)) {
    return loadavg.map((item) => Number(item || 0).toFixed(2)).join(' / ');
  }
  return Number(loadavg).toFixed(2);
}

function getProgressColor(percent: number, thresholds = [75, 90]) {
  if (percent >= thresholds[1]) return '#ff4d4f';
  if (percent >= thresholds[0]) return '#faad14';
  return '#52c41a';
}

function getStatusTag(status: string) {
  if (!status) return { color: 'default', text: '未知' };
  const lower = status.toLowerCase();
  if (lower === 'online' || lower === 'running')
    return { color: 'success', text: '在线' };
  if (lower === 'offline') return { color: 'error', text: '离线' };
  return { color: 'warning', text: status };
}

// --- Lifecycle ---
onMounted(() => {
  loadServers();
});

watch(selectedServer, handleServerChange);
watch(selectedNode, handleNodeChange);
</script>

<template>
  <Page title="节点监控">
    <div class="space-y-4 p-4">
      <!-- Filter Card -->
      <Card :bordered="false" class="filter-card">
        <div class="flex flex-wrap items-end gap-4">
          <div class="filter-item">
            <div class="mb-1 text-xs text-gray-500">PVE服务器</div>
            <Select
              v-model:value="selectedServer"
              placeholder="请选择服务器"
              allow-clear
              :loading="serverLoading"
              style="width: 200px"
              :options="serverOptions"
            />
          </div>
          <div class="filter-item">
            <div class="mb-1 text-xs text-gray-500">所属节点</div>
            <Select
              v-model:value="selectedNode"
              placeholder="请选择节点"
              allow-clear
              :disabled="!selectedServer"
              :loading="nodeLoading"
              style="width: 200px"
              :options="nodeOptions"
            />
          </div>
          <div class="filter-item">
            <div class="mb-1 text-xs text-gray-500">时间范围</div>
            <Radio.Group
              v-model:value="timeframe"
              button-style="solid"
              size="small"
              @change="handleTimeframeChange"
            >
              <Radio.Button
                v-for="opt in timeframeOptions"
                :key="opt.value"
                :value="opt.value"
              >
                {{ opt.label }}
              </Radio.Button>
            </Radio.Group>
          </div>

          <div class="ml-auto flex items-center gap-4">
            <div class="text-xs text-gray-500" v-if="summary.node">
              <span class="mr-2">状态:</span>
              <Tag :color="getStatusTag(summary.status).color">
                {{ getStatusTag(summary.status).text }}
              </Tag>
            </div>
            <div class="text-xs text-gray-500" v-if="summary.last_update">
              <span class="mr-1">最近更新:</span>
              <span>{{ formatTime(summary.last_update) }}</span>
            </div>
            <Button
              type="primary"
              size="small"
              @click="loadMonitor"
              :loading="monitorLoading"
            >
              <template #icon><ReloadOutlined /></template>
              刷新
            </Button>
          </div>
        </div>
      </Card>

      <!-- Summary Stats -->
      <Row :gutter="16">
        <Col :span="6">
          <Card :bordered="false" class="stat-card">
            <div class="stat-header mb-2 flex justify-between">
              <span class="text-gray-500">CPU使用率</span>
              <Tag size="small">{{ summary.cpu.cores || '-' }} 核</Tag>
            </div>
            <div class="mb-2 text-2xl font-bold">
              {{ summary.cpu.percent.toFixed(1) }}%
            </div>
            <Progress
              :percent="summary.cpu.percent"
              :stroke-color="getProgressColor(summary.cpu.percent)"
              :show-info="false"
              size="small"
            />
            <div class="mt-2 text-xs text-gray-500">
              负载：{{ formatLoad(summary.cpu.loadavg) }}
            </div>
          </Card>
        </Col>
        <Col :span="6">
          <Card :bordered="false" class="stat-card">
            <div class="stat-header mb-2 flex justify-between">
              <span class="text-gray-500">内存使用率</span>
              <Tag size="small">
                {{ formatBytes(summary.memory.used) }}/{{
                  formatBytes(summary.memory.total)
                }}
              </Tag>
            </div>
            <div class="mb-2 text-2xl font-bold">
              {{ summary.memory.percent.toFixed(1) }}%
            </div>
            <Progress
              :percent="summary.memory.percent"
              :stroke-color="getProgressColor(summary.memory.percent, [80, 90])"
              :show-info="false"
              size="small"
            />
            <div class="mt-2 text-xs text-gray-500">
              NUMA：{{ summary.memory.total ? '已启用/默认' : '-' }}
            </div>
          </Card>
        </Col>
        <Col :span="6">
          <Card :bordered="false" class="stat-card">
            <div class="stat-header mb-2 flex justify-between">
              <span class="text-gray-500">存储使用率</span>
              <Tag size="small">
                {{ formatBytes(summary.storage.used) }}/{{
                  formatBytes(summary.storage.total)
                }}
              </Tag>
            </div>
            <div class="mb-2 text-2xl font-bold">
              {{ summary.storage.percent.toFixed(1) }}%
            </div>
            <Progress
              :percent="summary.storage.percent"
              :stroke-color="
                getProgressColor(summary.storage.percent, [80, 90])
              "
              :show-info="false"
              size="small"
            />
            <div class="mt-2 text-xs text-gray-500">根存储使用</div>
          </Card>
        </Col>
        <Col :span="6">
          <Card :bordered="false" class="stat-card">
            <div class="stat-header mb-2 flex justify-between">
              <span class="text-gray-500">网络吞吐</span>
              <Tag size="small">实时</Tag>
            </div>
            <div class="mb-1 text-2xl font-bold">
              {{ formatThroughput(summary.network.in) }}/s
            </div>
            <div class="mb-2 text-xs text-gray-500">
              出：{{ formatThroughput(summary.network.out) }}/s
            </div>
            <div class="mt-0 text-xs text-gray-500">
              运行时长：{{ formatDuration(summary.uptime) }}
            </div>
          </Card>
        </Col>
      </Row>

      <!-- Charts -->
      <Card title="资源走势" :bordered="false">
        <Spin :spinning="monitorLoading">
          <div v-if="metrics.length > 0" class="grid grid-cols-2 gap-4">
            <Card title="CPU使用率" size="small" :bordered="true">
              <!-- Used EchartsUI component -->
              <EchartsUI ref="cpuChartRef" class="h-64 w-full" />
            </Card>
            <Card title="内存使用率" size="small" :bordered="true">
              <EchartsUI ref="memoryChartRef" class="h-64 w-full" />
            </Card>
            <Card title="存储使用率" size="small" :bordered="true">
              <EchartsUI ref="storageChartRef" class="h-64 w-full" />
            </Card>
            <Card title="网络吞吐" size="small" :bordered="true">
              <EchartsUI ref="networkChartRef" class="h-64 w-full" />
            </Card>
          </div>
          <Empty v-else description="暂无监控数据" />
        </Spin>
      </Card>

      <!-- Alerts -->
      <Card title="健康告警" :bordered="false">
        <template #extra>
          <span v-if="alerts.length > 0">共 {{ alerts.length }} 条</span>
        </template>
        <div v-if="alerts.length > 0" class="space-y-2">
          <Alert
            v-for="(item, idx) in alerts"
            :key="idx"
            :type="item.level === 'danger' ? 'error' : 'warning'"
            show-icon
            :message="item.message"
          />
        </div>
        <Empty v-else description="一切正常，暂无告警" />
      </Card>
    </div>
  </Page>
</template>

<style scoped>
.filter-card :deep(.ant-card-body) {
  padding: 16px 24px;
}

.stat-card {
  height: 100%;
}
</style>
