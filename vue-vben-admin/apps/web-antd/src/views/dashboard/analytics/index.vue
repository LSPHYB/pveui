<script lang="ts" setup>
import type { EchartsUIType } from '@vben/plugins/echarts';

import type { DashboardData } from '#/api/system';

import { markRaw, onMounted, onUnmounted, reactive, ref, watch } from 'vue';

import { AnalysisOverview } from '@vben/common-ui';
import { SvgBellIcon, SvgCardIcon, SvgDownloadIcon } from '@vben/icons';
import { EchartsUI, useEcharts } from '@vben/plugins/echarts';

import {
  Avatar,
  Button,
  Card,
  Col,
  Descriptions,
  InputNumber,
  List,
  Progress,
  Row,
  Space,
  Switch,
  Table,
  Tag,
  TypographyText,
} from 'ant-design-vue';

import { getDashboardDataApi } from '#/api/system';

// State
const loading = ref(false);
const autoRefresh = ref(false);
const intervalSec = ref(30);
let refreshTimer: any = null;

const data = reactive<Partial<DashboardData>>({});

// Chart
const chartRef = ref<EchartsUIType>();
const { renderEcharts } = useEcharts(chartRef);

// Overview Items for AnalysisOverview
const overviewItems = ref<any[]>([]);

// Columns for Logs Table
const logColumns = [
  { dataIndex: 'username', key: 'username', title: '用户', width: 100 },
  {
    dataIndex: 'action_type_display',
    key: 'action',
    title: '操作',
    width: 100,
  },
  { dataIndex: 'request_path', ellipsis: true, key: 'path', title: '路径' },
  { dataIndex: 'status_code', key: 'status', title: '状态', width: 80 },
  { dataIndex: 'created_at', key: 'time', title: '时间', width: 160 },
];

const topPathColumns = [
  { dataIndex: 'path', key: 'path', title: '路径', ellipsis: true },
  { dataIndex: 'count', key: 'count', title: '访问次数', width: 120 },
];

// Helper functions
const getStatusColor = (val: number) => {
  if (val < 200) return 'default';
  if (val < 300) return 'success';
  if (val < 400) return 'warning';
  return 'error';
};

const getCpuStatus = (val: number) => {
  if (val < 50) return 'success';
  if (val < 80) return 'active';
  return 'exception';
};

const getActionTypeColor = (actionType: string) => {
  const colors: Record<string, string> = {
    create: 'green',
    update: 'blue',
    delete: 'red',
    view: 'cyan',
    list: 'purple',
  };
  return colors[actionType] || 'default';
};

const formatDate = (dateStr?: string) => {
  if (!dateStr) return '-';
  const date = new Date(dateStr);
  return date
    .toLocaleString('zh-CN', {
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    })
    .replaceAll('/', '-');
};

// Fetch Data
const fetchData = async () => {
  loading.value = true;
  try {
    const res = await getDashboardDataApi();
    Object.assign(data, res);

    // Update Overview
    overviewItems.value = [
      {
        icon: markRaw(SvgCardIcon),
        title: '用户总数',
        value: res.stats?.users || 0,
        totalTitle: '从数据库统计',
        totalValue: res.stats?.users || 0,
      },
      {
        icon: markRaw(SvgBellIcon),
        title: '角色总数',
        value: res.stats?.roles || 0,
        totalTitle: '从数据库统计',
        totalValue: res.stats?.roles || 0,
      },
      {
        icon: markRaw(SvgCardIcon),
        title: '菜单总数',
        value: res.stats?.menus || 0,
        totalTitle: '从数据库统计',
        totalValue: res.stats?.menus || 0,
      },
      {
        icon: markRaw(SvgDownloadIcon),
        title: '日志总数',
        value: res.stats?.operation_logs || 0,
        totalTitle: '从数据库统计',
        totalValue: res.stats?.operation_logs || 0,
      },
    ];

    // Update Chart
    if (res.daily_stats) {
      updateChart(res.daily_stats);
    }
  } catch (error) {
    console.error('Failed to fetch dashboard data:', error);
  } finally {
    loading.value = false;
  }
};

const updateChart = (dailyStats: { count: number; date: string }[]) => {
  renderEcharts({
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      data: dailyStats.map((item) => item.date),
      axisTick: { alignWithLabel: true },
    },
    yAxis: { type: 'value' },
    series: [
      {
        name: '操作次数',
        type: 'bar',
        barWidth: '60%',
        data: dailyStats.map((item) => item.count),
        itemStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: '#83bff6' },
              { offset: 0.5, color: '#188df0' },
              { offset: 1, color: '#188df0' },
            ],
          },
        },
        emphasis: {
          itemStyle: {
            color: {
              type: 'linear',
              x: 0,
              y: 0,
              x2: 0,
              y2: 1,
              colorStops: [
                { offset: 0, color: '#2378f7' },
                { offset: 0.7, color: '#2378f7' },
                { offset: 1, color: '#83bff6' },
              ],
            },
          },
        },
      },
    ],
  });
};

// Lifecycle
onMounted(() => {
  fetchData();
});

watch([autoRefresh, intervalSec], ([auto, sec]) => {
  if (refreshTimer) {
    clearInterval(refreshTimer);
    refreshTimer = null;
  }
  if (auto) {
    refreshTimer = setInterval(fetchData, (sec as number) * 1000);
  }
});

onUnmounted(() => {
  if (refreshTimer) clearInterval(refreshTimer);
});
</script>

<template>
  <div class="p-5">
    <!-- Analysis Overview -->
    <AnalysisOverview :items="overviewItems" :loading="loading" />

    <!-- Toolbar -->
    <div class="mb-4 mt-4 flex items-center justify-end">
      <Space>
        <Button :loading="loading" type="primary" @click="fetchData">
          刷新
        </Button>
        <Switch
          v-model:checked="autoRefresh"
          checked-children="自动刷新"
          un-checked-children="手动"
        />
        <InputNumber
          v-model:value="intervalSec"
          :max="300"
          :min="5"
          style="width: 70px"
        />
        <TypographyText type="secondary">秒</TypographyText>
      </Space>
    </div>

    <!-- Main Content -->
    <Row :gutter="[16, 16]">
      <!-- Daily Chart -->
      <Col :lg="16" :md="24" :xs="24">
        <Card title="每日操作统计 (近7天)">
          <div class="h-80 w-full">
            <EchartsUI ref="chartRef" />
          </div>
        </Card>
      </Col>

      <!-- System Status -->
      <Col :lg="8" :md="24" :xs="24">
        <Card title="系统状态">
          <div v-if="data.system_status" class="py-4">
            <div class="mb-4">
              <div class="mb-1 flex justify-between">
                <span>CPU 使用率</span>
                <span>{{ data.system_status.cpu_percent }}%</span>
              </div>
              <Progress
                :percent="data.system_status.cpu_percent"
                :status="getCpuStatus(data.system_status.cpu_percent)"
                :show-info="false"
              />
            </div>

            <div class="mb-4">
              <div class="mb-1 flex justify-between">
                <span>内存 使用率</span>
                <span>{{ data.system_status.memory_percent }}%</span>
              </div>
              <Progress
                :percent="data.system_status.memory_percent"
                :status="getCpuStatus(data.system_status.memory_percent)"
                :show-info="false"
              />
              <div class="mt-1 text-right text-xs text-gray-500">
                {{ data.system_status.memory_used_gb }}GB /
                {{ data.system_status.memory_total_gb }}GB
              </div>
            </div>

            <Descriptions :column="1" bordered size="small">
              <Descriptions.Item label="错误操作 (7天)">
                <Tag :color="data.error_count! > 0 ? 'red' : 'green'">
                  {{ data.error_count || 0 }}
                </Tag>
              </Descriptions.Item>
            </Descriptions>
          </div>
          <div v-else class="py-10 text-center text-gray-400">暂无数据</div>
        </Card>
      </Col>

      <!-- Recent Logs -->
      <Col :lg="14" :md="24" :xs="24">
        <Card title="最近操作日志">
          <Table
            :columns="logColumns"
            :data-source="data.recent_logs"
            :loading="loading"
            :pagination="false"
            row-key="id"
            size="small"
          >
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'action'">
                <Tag :color="getActionTypeColor(record.action_type)">
                  {{ record.action_type_display }}
                </Tag>
              </template>
              <template v-if="column.key === 'status'">
                <Tag :color="getStatusColor(record.status_code)">
                  {{ record.status_code }}
                </Tag>
              </template>
              <template v-if="column.key === 'time'">
                {{ formatDate(record.created_at) }}
              </template>
            </template>
          </Table>
        </Card>
      </Col>

      <!-- Recent Active Users -->
      <Col :lg="10" :md="24" :xs="24">
        <Card title="最近活跃用户 (近7天)">
          <List
            item-layout="horizontal"
            :data-source="data.recent_users || []"
            :loading="loading"
            :locale="{ emptyText: '暂无数据' }"
          >
            <template #renderItem="{ item }">
              <List.Item>
                <List.Item.Meta :description="item.email || '-'">
                  <template #title>
                    <span>{{ item.username }}</span>
                    <Tag class="ml-2" size="small">
                      {{ item.log_count }} 次操作
                    </Tag>
                  </template>
                  <template #avatar>
                    <Avatar style="background-color: #1890ff">
                      {{ item.username?.[0]?.toUpperCase() || 'U' }}
                    </Avatar>
                  </template>
                </List.Item.Meta>
              </List.Item>
            </template>
          </List>
        </Card>
      </Col>

      <!-- Top Paths -->
      <Col :span="24">
        <Card title="最活跃的 API 路径 (近7天)">
          <Table
            :columns="topPathColumns"
            :data-source="data.top_paths"
            :loading="loading"
            :pagination="false"
            row-key="path"
            size="small"
          >
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'count'">
                <Tag color="blue">
                  {{ record.count }}
                </Tag>
              </template>
            </template>
          </Table>
        </Card>
      </Col>
    </Row>
  </div>
</template>
