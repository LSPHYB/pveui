<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import {
  Card,
  Row,
  Col,
  Statistic,
  Tag,
  Spin,
  Alert,
  Progress,
  Divider,
} from 'ant-design-vue';
import {
  ThunderboltOutlined,
  RobotOutlined,
  DollarOutlined,
  TeamOutlined,
  ApiOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
} from '@ant-design/icons-vue';
import { use } from 'echarts/core';
import { BarChart, LineChart, PieChart } from 'echarts/charts';
import {
  TooltipComponent,
  LegendComponent,
  GridComponent,
  TitleComponent,
} from 'echarts/components';
import { CanvasRenderer } from 'echarts/renderers';
import VChart from 'vue-echarts';
import { getAiStatsOverviewApi, getAiUsageTrendApi } from '#/api/ai';

use([
  BarChart,
  LineChart,
  PieChart,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  TitleComponent,
  CanvasRenderer,
]);

// ── 数据状态 ────────────────────────────────────────────────────────
const loading = ref(false);
const error = ref('');

const overview = ref<any>({
  total_tokens: 0,
  total_requests: 0,
  total_cost_usd: 0,
  active_users: 0,
  model_distribution: [],
  api_key_status: { total: 0, active: 0, error: 0 },
});

const trendDates = ref<string[]>([]);
const trendTokens = ref<number[]>([]);
const trendRequests = ref<number[]>([]);
const trendCosts = ref<number[]>([]);

// ── API调用 ─────────────────────────────────────────────────────────
const fetchData = async () => {
  loading.value = true;
  error.value = '';
  try {
    const [ovRes, trendRes] = await Promise.all([
      getAiStatsOverviewApi(),
      getAiUsageTrendApi(),
    ]);

    // --- 暴力提取算法，无视 Vben 拦截器到底剥了多少层皮 ---
    const getDeepData = (obj: any, targetKey: string): any => {
      if (!obj || typeof obj !== 'object') return null;
      if (obj[targetKey] !== undefined) return obj[targetKey];
      if (obj.data) return getDeepData(obj.data, targetKey);
      if (obj.result) return getDeepData(obj.result, targetKey);
      if (obj.items) return getDeepData(obj.items, targetKey);
      return null;
    };

    const ov_total_tokens = getDeepData(ovRes, 'total_tokens');
    const ov_total_requests = getDeepData(ovRes, 'total_requests');
    const ov_total_cost_usd = getDeepData(ovRes, 'total_cost_usd');
    const ov_active_users = getDeepData(ovRes, 'active_users');
    const ov_api_key_status = getDeepData(ovRes, 'api_key_status');
    const ov_model_distribution = getDeepData(ovRes, 'model_distribution');

    overview.value = {
      total_tokens: ov_total_tokens || 0,
      total_requests: ov_total_requests || 0,
      total_cost_usd: ov_total_cost_usd || 0,
      active_users: ov_active_users || 0,
      model_distribution: Array.isArray(ov_model_distribution) ? ov_model_distribution : [],
      api_key_status: ov_api_key_status || { total: 0, active: 0, error: 0 }
    };

    const tr_data_points = getDeepData(trendRes, 'data_points');
    const tr = Array.isArray(tr_data_points) ? tr_data_points : [];

    trendDates.value = tr.map((p: any) => p.date);
    trendTokens.value = tr.map((p: any) => p.tokens ?? 0);
    trendRequests.value = tr.map((p: any) => p.requests ?? 0);
    trendCosts.value = tr.map((p: any) => +(p.cost ?? 0).toFixed(4));

  } catch (e: any) {
    error.value = e?.message || '数据加载失败，请检查后端 stats 接口';
    // 显示 mock 数据让页面有内容
    useMockData();
  } finally {
    loading.value = false;
  }
};

const useMockData = () => {
  overview.value = {
    total_tokens: 1_543_021,
    total_requests: 5_240,
    total_cost_usd: 154.3,
    active_users: 342,
    model_distribution: [
      { model_key: 'gpt-3.5-turbo', usage_percent: 75.5, total_cost: 116.3 },
      { model_key: 'gpt-4', usage_percent: 24.5, total_cost: 38.0 },
    ],
    api_key_status: { total: 5, active: 4, error: 1 },
  };
  const today = new Date();
  trendDates.value = Array.from({ length: 14 }, (_, i) => {
    const d = new Date(today);
    d.setDate(today.getDate() - (13 - i));
    return d.toISOString().slice(0, 10);
  });
  trendTokens.value = trendDates.value.map(() =>
    Math.floor(Math.random() * 120_000 + 30_000),
  );
  trendRequests.value = trendDates.value.map(() =>
    Math.floor(Math.random() * 500 + 100),
  );
  trendCosts.value = trendDates.value.map(() =>
    +(Math.random() * 12 + 2).toFixed(2),
  );
};

// ── 图表配置 ─────────────────────────────────────────────────────────
const usageTrendOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  legend: { data: ['Token用量', '调用次数'], bottom: 0 },
  grid: { left: '3%', right: '4%', bottom: '14%', containLabel: true },
  xAxis: {
    type: 'category',
    data: trendDates.value,
    axisLabel: { rotate: 30, fontSize: 11 },
  },
  yAxis: [
    { type: 'value', name: 'Tokens', min: 0 },
    { type: 'value', name: '次数', min: 0 },
  ],
  series: [
    {
      name: 'Token用量',
      type: 'bar',
      data: trendTokens.value,
      itemStyle: { color: '#4f7fff' },
      yAxisIndex: 0,
    },
    {
      name: '调用次数',
      type: 'line',
      data: trendRequests.value,
      smooth: true,
      itemStyle: { color: '#36cfc9' },
      yAxisIndex: 1,
    },
  ],
}));

const costTrendOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  grid: { left: '3%', right: '4%', bottom: '8%', containLabel: true },
  xAxis: {
    type: 'category',
    data: trendDates.value,
    axisLabel: { rotate: 30, fontSize: 11 },
  },
  yAxis: { type: 'value', name: '费用($)', min: 0 },
  series: [
    {
      name: '每日费用',
      type: 'line',
      data: trendCosts.value,
      smooth: true,
      areaStyle: { opacity: 0.15 },
      itemStyle: { color: '#fa8c16' },
    },
  ],
}));

const modelDistOption = computed(() => {
  const dist = overview.value.model_distribution ?? [];
  return {
    tooltip: { trigger: 'item' },
    legend: { bottom: 0 },
    series: [
      {
        name: '用量分布',
        type: 'pie',
        radius: ['40%', '70%'],
        data: dist.map((m: any) => ({
          name: m.model_key,
          value: m.usage_percent,
        })),
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0,0,0,0.5)',
          },
        },
      },
    ],
  };
});

// ── API Key 健康度 ───────────────────────────────────────────────────
const apiKeyHealth = computed(() => {
  const s = overview.value.api_key_status ?? {};
  const total = s.total || 1;
  return {
    ...s,
    activePercent: Math.round(((s.active ?? 0) / total) * 100),
  };
});

onMounted(fetchData);
</script>

<template>
  <div class="p-4 space-y-4">
    <!-- 页面标题 -->
    <div class="flex items-center justify-between mb-2">
      <h2 class="text-xl font-bold flex items-center gap-2">
        <RobotOutlined class="text-blue-500" />
        AI 管理数据大盘
      </h2>
      <Tag color="blue" class="cursor-pointer" @click="fetchData">
        <template v-if="loading"><Spin size="small" class="mr-1" />刷新中</template>
        <template v-else>立即刷新</template>
      </Tag>
    </div>

    <!-- 后端未接入时的提示 -->
    <Alert
      v-if="error"
      type="warning"
      show-icon
      class="mb-2"
      :message="`后端 stats 接口暂未实现，当前显示模拟数据：${error}`"
    />

    <!-- 统计卡片 -->
    <Row :gutter="16">
      <Col :xs="24" :sm="12" :lg="6">
        <Card :bordered="false" class="shadow-sm">
          <Statistic
            title="本月总 Token 消耗"
            :value="overview.total_tokens"
            :precision="0"
            group-separator=","
            :value-style="{ color: '#1677ff', fontWeight: 'bold' }"
          >
            <template #prefix><ThunderboltOutlined /></template>
            <template #suffix><span class="text-xs text-gray-400 ml-1">tokens</span></template>
          </Statistic>
        </Card>
      </Col>
      <Col :xs="24" :sm="12" :lg="6">
        <Card :bordered="false" class="shadow-sm">
          <Statistic
            title="累计 AI 调用次数"
            :value="overview.total_requests"
            :precision="0"
            group-separator=","
            :value-style="{ color: '#36cfc9', fontWeight: 'bold' }"
          >
            <template #prefix><ApiOutlined /></template>
            <template #suffix><span class="text-xs text-gray-400 ml-1">次</span></template>
          </Statistic>
        </Card>
      </Col>
      <Col :xs="24" :sm="12" :lg="6">
        <Card :bordered="false" class="shadow-sm">
          <Statistic
            title="平台总费用估算"
            :value="overview.total_cost_usd"
            :precision="2"
            :value-style="{ color: '#fa8c16', fontWeight: 'bold' }"
          >
            <template #prefix><DollarOutlined /></template>
            <template #suffix><span class="text-xs text-gray-400 ml-1">USD</span></template>
          </Statistic>
        </Card>
      </Col>
      <Col :xs="24" :sm="12" :lg="6">
        <Card :bordered="false" class="shadow-sm">
          <Statistic
            title="本月活跃用户"
            :value="overview.active_users"
            :precision="0"
            :value-style="{ color: '#52c41a', fontWeight: 'bold' }"
          >
            <template #prefix><TeamOutlined /></template>
            <template #suffix><span class="text-xs text-gray-400 ml-1">人</span></template>
          </Statistic>
        </Card>
      </Col>
    </Row>

    <!-- 图表区 - 近30天趋势 + 费用曲线 -->
    <Row :gutter="16">
      <Col :span="16">
        <Card title="调用量 & Token 用量趋势（近30天）" :bordered="false" class="shadow-sm">
          <Spin :spinning="loading">
            <v-chart
              :option="usageTrendOption"
              style="height: 300px"
              autoresize
            />
          </Spin>
        </Card>
      </Col>
      <Col :span="8">
        <Card title="每日费用曲线" :bordered="false" class="shadow-sm">
          <Spin :spinning="loading">
            <v-chart
              :option="costTrendOption"
              style="height: 300px"
              autoresize
            />
          </Spin>
        </Card>
      </Col>
    </Row>

    <!-- API Key 健康度 + 模型分布 -->
    <Row :gutter="16">
      <Col :span="12">
        <Card title="API Key 池健康状态" :bordered="false" class="shadow-sm">
          <div class="space-y-4 p-2">
            <div class="flex items-center justify-between">
              <span class="text-gray-600">在线健康率</span>
              <span class="font-bold text-green-600">{{ apiKeyHealth.activePercent }}%</span>
            </div>
            <Progress
              :percent="apiKeyHealth.activePercent"
              :stroke-color="apiKeyHealth.activePercent < 60 ? '#ff4d4f' : '#52c41a'"
              status="active"
            />
            <Divider style="margin: 12px 0" />
            <div class="grid grid-cols-3 text-center gap-4">
              <div>
                <div class="text-2xl font-bold text-gray-700">{{ apiKeyHealth.total ?? 0 }}</div>
                <div class="text-xs text-gray-400 mt-1">Key 总数</div>
              </div>
              <div>
                <div class="text-2xl font-bold text-green-500">{{ apiKeyHealth.active ?? 0 }}</div>
                <div class="text-xs text-gray-400 mt-1 flex items-center justify-center gap-1">
                  <CheckCircleOutlined />正常
                </div>
              </div>
              <div>
                <div class="text-2xl font-bold text-red-500">{{ apiKeyHealth.error ?? 0 }}</div>
                <div class="text-xs text-gray-400 mt-1 flex items-center justify-center gap-1">
                  <ExclamationCircleOutlined />异常
                </div>
              </div>
            </div>
          </div>
        </Card>
      </Col>
      <Col :span="12">
        <Card title="模型用量占比分布" :bordered="false" class="shadow-sm">
          <Spin :spinning="loading">
            <v-chart
              :option="modelDistOption"
              style="height: 260px"
              autoresize
            />
          </Spin>
        </Card>
      </Col>
    </Row>
  </div>
</template>
