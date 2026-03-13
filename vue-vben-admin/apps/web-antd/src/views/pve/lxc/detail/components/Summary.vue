<script setup lang="ts">
import type { LxcContainerModel } from '#/api/pve/types';

import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue';

import {
  Card,
  Col,
  Descriptions,
  DescriptionsItem,
  message,
  Row,
  Select,
  Tag,
} from 'ant-design-vue';
import * as echarts from 'echarts';

import { getLxcRrdByIdApi, getLxcStatusByIdApi } from '#/api/pve/lxc';

defineOptions({ name: 'LxcSummary' });

const props = defineProps<{
  lxc: null | LxcContainerModel;
  lxcId: string;
}>();

const cpuChartRef = ref<HTMLDivElement | null>(null);
const memChartRef = ref<HTMLDivElement | null>(null);
const netChartRef = ref<HTMLDivElement | null>(null);

let cpuChart: echarts.ECharts | null = null;
let memChart: echarts.ECharts | null = null;
let netChart: echarts.ECharts | null = null;

const timeframe = ref('hour');
const statusData = ref<any>(null);
const rrdData = ref<any[]>([]);
const timer = ref<any>(null);

const statusItems = computed(() => {
  const s = statusData.value;
  const lxc = props.lxc;
  if (!s) return [];

  return [
    { label: '状态', value: s.status || 'unknown' },
    { label: 'HA状态', value: s.ha?.status || '无' },
    { label: '节点', value: lxc?.node || '-' },
    { label: '无特权', value: '是' }, // Typical for LXC, could be checked in config if needed
    {
      label: 'CPU使用率',
      value: s.cpu
        ? `${(s.cpu * 100).toFixed(2)}% of ${s.cpus || 1} CPU(s)`
        : '-',
    },
    {
      label: '内存使用率',
      value: s.mem
        ? `${((s.mem / s.maxmem) * 100).toFixed(2)}% (${formatBytes(s.mem)} / ${formatBytes(s.maxmem)})`
        : '-',
    },
    {
      label: 'SWAP 使用率',
      value: s.swap
        ? `${((s.swap / s.maxswap) * 100).toFixed(2)}% (${formatBytes(s.swap)} / ${formatBytes(s.maxswap)})`
        : '-',
    },
    { label: '引导盘大小', value: s.maxdisk ? formatBytes(s.maxdisk) : '-' },
    { label: 'IPs', value: lxc?.ip_address || '未配置' },
  ];
});

const formatBytes = (bytes: number, decimals = 2) => {
  if (!bytes) return '0 B';
  const k = 1024;
  const dm = Math.max(decimals, 0);
  const sizes = ['B', 'KiB', 'MiB', 'GiB', 'TiB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${Number.parseFloat((bytes / k ** i).toFixed(dm))} ${sizes[i]}`;
};

const fetchStatus = async () => {
  if (!props.lxcId) return;
  try {
    const res = await getLxcStatusByIdApi(props.lxcId);
    // Extract data from Axios response
    const data = (res as any).data || res;
    statusData.value = data;
  } catch (error: any) {
    console.error('Failed to fetch status:', error);
  }
};

const fetchRrd = async () => {
  if (!props.lxcId) return;
  try {
    const res = await getLxcRrdByIdApi(props.lxcId, timeframe.value);
    // Extract data from Axios response
    const data = Array.isArray(res) ? res : (res as any)?.data || [];
    if (Array.isArray(data)) {
      rrdData.value = data;
      updateCharts(data);
    }
  } catch (error: any) {
    console.error('Failed to fetch RRD data:', error);
    message.error('获取监控数据失败');
  }
};

const updateCharts = (data: any[]) => {
  const validData = data.filter((d) => d.time);
  if (validData.length === 0) return;

  const times = validData.map((d) =>
    new Date(d.time * 1000).toLocaleTimeString(),
  );

  // CPU Chart
  if (cpuChartRef.value) {
    if (!cpuChart) cpuChart = echarts.init(cpuChartRef.value);
    const cpuSeries = validData.map((d) => (d.cpu || 0) * 100);
    cpuChart.setOption({
      tooltip: { trigger: 'axis' },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '10%',
        top: '10%',
        containLabel: true,
      },
      xAxis: {
        type: 'category',
        boundaryGap: false,
        data: times,
        axisLabel: { rotate: 45 },
      },
      yAxis: {
        type: 'value',
        min: 0,
        max: 100,
        axisLabel: { formatter: '{value}%' },
      },
      series: [
        {
          name: 'CPU %',
          type: 'line',
          data: cpuSeries,
          areaStyle: { opacity: 0.3, color: '#91cc75' },
          itemStyle: { color: '#91cc75' },
          showSymbol: false,
          smooth: true,
        },
      ],
    });
  }

  // Memory Chart
  if (memChartRef.value) {
    if (!memChart) memChart = echarts.init(memChartRef.value);
    const memSeries = validData.map((d) => d.mem || 0);
    memChart.setOption({
      tooltip: {
        trigger: 'axis',
        valueFormatter: (val: any) => formatBytes(val),
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '10%',
        top: '10%',
        containLabel: true,
      },
      xAxis: {
        type: 'category',
        boundaryGap: false,
        data: times,
        axisLabel: { rotate: 45 },
      },
      yAxis: {
        type: 'value',
        axisLabel: { formatter: (val: any) => formatBytes(val, 0) },
      },
      series: [
        {
          name: '内存',
          type: 'line',
          data: memSeries,
          areaStyle: { opacity: 0.3, color: '#FAC858' },
          itemStyle: { color: '#FAC858' },
          showSymbol: false,
          smooth: true,
        },
      ],
    });
  }

  // Network Chart
  if (netChartRef.value) {
    if (!netChart) netChart = echarts.init(netChartRef.value);
    const netIn = validData.map((d) => d.netin || 0);
    const netOut = validData.map((d) => d.netout || 0);
    netChart.setOption({
      tooltip: {
        trigger: 'axis',
        valueFormatter: (val: any) => `${formatBytes(val)}/s`,
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '10%',
        top: '10%',
        containLabel: true,
      },
      xAxis: {
        type: 'category',
        boundaryGap: false,
        data: times,
        axisLabel: { rotate: 45 },
      },
      yAxis: {
        type: 'value',
        axisLabel: { formatter: (val: any) => `${formatBytes(val, 0)}/s` },
      },
      legend: { data: ['传入', '传出'] },
      series: [
        {
          name: '传入',
          type: 'line',
          data: netIn,
          areaStyle: { opacity: 0.3 },
          showSymbol: false,
          smooth: true,
        },
        {
          name: '传出',
          type: 'line',
          data: netOut,
          areaStyle: { opacity: 0.3 },
          showSymbol: false,
          smooth: true,
        },
      ],
    });
  }
};

const refreshAll = () => {
  if (props.lxcId) {
    fetchStatus();
    fetchRrd();
  }
};

onMounted(async () => {
  await nextTick();
  setTimeout(() => {
    refreshAll();
  }, 300);

  timer.value = setInterval(refreshAll, 10_000);

  window.addEventListener('resize', () => {
    cpuChart?.resize();
    memChart?.resize();
    netChart?.resize();
  });
});

onUnmounted(() => {
  if (timer.value) clearInterval(timer.value);
  cpuChart?.dispose();
  memChart?.dispose();
  netChart?.dispose();
});

watch([() => props.lxcId, timeframe], () => {
  refreshAll();
});
</script>

<template>
  <div class="h-full overflow-y-auto p-4">
    <div class="mb-4 text-right">
      <Select v-model:value="timeframe" style="width: 120px" size="small">
        <Select.Option value="hour">小时</Select.Option>
        <Select.Option value="day">天</Select.Option>
        <Select.Option value="week">周</Select.Option>
        <Select.Option value="month">月</Select.Option>
        <Select.Option value="year">年</Select.Option>
      </Select>
    </div>

    <Row :gutter="[16, 16]">
      <Col :span="24" :lg="12">
        <Card title="状态" :bordered="false" class="mb-4">
          <Descriptions :column="1" size="small" bordered>
            <DescriptionsItem
              v-for="item in statusItems"
              :key="item.label"
              :label="item.label"
            >
              <Tag
                v-if="item.label === '状态'"
                :color="item.value === 'running' ? 'green' : 'red'"
              >
                {{ item.value }}
              </Tag>
              <span v-else>{{ item.value }}</span>
            </DescriptionsItem>
          </Descriptions>
        </Card>
      </Col>

      <Col :span="24" :lg="12">
        <Card title="备注" :bordered="false" class="mb-4">
          <div
            class="flex h-32 items-center justify-center rounded border border-dashed text-gray-400"
          >
            {{ lxc?.description || '暂无备注' }}
          </div>
        </Card>
      </Col>

      <Col :span="24" :lg="8">
        <Card title="CPU利用率" :bordered="false" class="mb-4">
          <div ref="cpuChartRef" class="h-64 w-full"></div>
        </Card>
      </Col>

      <Col :span="24" :lg="8">
        <Card title="内存使用" :bordered="false" class="mb-4">
          <div ref="memChartRef" class="h-64 w-full"></div>
        </Card>
      </Col>

      <Col :span="24" :lg="8">
        <Card title="网络流量" :bordered="false" class="mb-4">
          <div ref="netChartRef" class="h-64 w-full"></div>
        </Card>
      </Col>
    </Row>
  </div>
</template>
