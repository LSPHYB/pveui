<script setup lang="ts">
import type { EchartsUIType } from '@vben/plugins/echarts';

import type { DashboardData } from '#/api/system';

import { markRaw, onMounted, onUnmounted, reactive, ref, watch } from 'vue';

import { AnalysisOverview, Page } from '@vben/common-ui';
import { EchartsUI, useEcharts } from '@vben/plugins/echarts';

import {
  FileTextOutlined,
  MenuOutlined,
  ReloadOutlined,
  TeamOutlined,
  UserOutlined,
} from '@ant-design/icons-vue';
import {
  Avatar,
  Button,
  Card,
  Col,
  InputNumber,
  List,
  Progress,
  Row,
  Space,
  Switch,
  Table,
  Tag,
  Typography,
} from 'ant-design-vue';

import { getDashboardDataApi } from '#/api/system';

defineOptions({ name: 'Dashboard' });

const { Text } = Typography;

// State
const loading = ref(false);
const autoRefresh = ref(false);
const intervalSec = ref(30);
let refreshTimer: null | ReturnType<typeof setInterval> = null;

const data = reactive<Partial<DashboardData>>({
  stats: { users: 0, roles: 0, menus: 0, operation_logs: 0 },
  recent_logs: [],
  daily_stats: [],
  recent_users: [],
  system_status: {
    cpu_percent: 0,
    memory_percent: 0,
    memory_used_gb: 0,
    memory_total_gb: 0,
  },
  error_count: 0,
  top_paths: [],
});

// Overview Items for AnalysisOverview
const overviewItems = ref<any[]>([]);

// Chart
const chartRef = ref<EchartsUIType>();
const { renderEcharts } = useEcharts(chartRef);

// Actions
const fetchData = async () => {
  loading.value = true;
  try {
    const res = await getDashboardDataApi();
    // API returns object directly or wrapped? Assume direct or check structure
    const result = (res as any).data || res;
    Object.assign(data, result);

    // Update Overview Items
    overviewItems.value = [
      {
        icon: markRaw(UserOutlined),
        title: '用户总数',
        value: data.stats?.users || 0,
        totalTitle: '总用户数',
        totalValue: data.stats?.users || 0,
      },
      {
        icon: markRaw(TeamOutlined),
        title: '角色总数',
        value: data.stats?.roles || 0,
        totalTitle: '总角色数',
        totalValue: data.stats?.roles || 0,
      },
      {
        icon: markRaw(MenuOutlined),
        title: '菜单总数',
        value: data.stats?.menus || 0,
        totalTitle: '总菜单数',
        totalValue: data.stats?.menus || 0,
      },
      {
        icon: markRaw(FileTextOutlined),
        title: '操作日志',
        value: data.stats?.operation_logs || 0,
        totalTitle: '总日志数',
        totalValue: data.stats?.operation_logs || 0,
      },
    ];

    updateChart();
  } catch (error: any) {
    console.error('获取仪表盘数据失败：', error);
  } finally {
    loading.value = false;
  }
};

const updateChart = () => {
  if (!data.daily_stats || data.daily_stats.length === 0) return;

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
      data: data.daily_stats.map((item) => item.date),
      axisTick: { alignWithLabel: true },
    },
    yAxis: { type: 'value' },
    series: [
      {
        name: '操作次数',
        type: 'bar',
        barWidth: '60%',
        data: data.daily_stats.map((item) => item.count),
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
      },
    ],
  });
};

// Helpers
const formatDate = (dateStr: string) => {
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

const getActionTypeColor = (actionType: string) => {
  const colors: Record<string, string> = {
    create: 'green',
    update: 'blue',
    delete: 'red',
    view: 'cyan',
    list: 'purple',
    other: 'gray',
  };
  return colors[actionType] || 'default';
};

const getStatusColor = (
  value: number | undefined,
): 'active' | 'exception' | 'normal' | 'success' | undefined => {
  if (value === undefined) return 'normal';
  if (value < 50) return 'success';
  if (value < 80) return 'active';
  if (value >= 80) return 'exception';
  return 'normal';
};

const getStatusCodeColor = (code: number) => {
  if (!code) return 'default';
  if (code >= 200 && code < 300) return 'success';
  if (code >= 300 && code < 400) return 'processing'; // cyan/blue
  if (code >= 400 && code < 500) return 'warning';
  if (code >= 500) return 'error';
  return 'default';
};

// Watchers
watch(autoRefresh, (val) => {
  if (val) {
    refreshTimer = setInterval(fetchData, intervalSec.value * 1000);
  } else {
    if (refreshTimer) {
      clearInterval(refreshTimer);
      refreshTimer = null;
    }
  }
});

watch(intervalSec, (val) => {
  if (autoRefresh.value && refreshTimer) {
    clearInterval(refreshTimer);
    refreshTimer = setInterval(fetchData, val * 1000);
  }
});

// Lifecycle
onMounted(() => {
  fetchData();
});

onUnmounted(() => {
  if (refreshTimer) clearInterval(refreshTimer);
});
</script>

<template>
  <Page title="仪表盘">
    <div class="px-4 pb-4">
      <!-- Toolbar -->
      <div class="mb-4 flex items-center justify-end">
        <Space>
          <Button :loading="loading" type="primary" @click="fetchData">
            <template #icon><ReloadOutlined /></template>
            刷新
          </Button>
          <Switch
            v-model:checked="autoRefresh"
            checked-children="自动"
            un-checked-children="手动"
          />
          <InputNumber
            v-model:value="intervalSec"
            :max="300"
            :min="5"
            size="small"
            style="width: 70px"
          />
          <Text type="secondary">秒</Text>
        </Space>
      </div>

      <!-- Analysis Overview -->
      <AnalysisOverview
        :items="overviewItems"
        :loading="loading"
        class="mb-4"
      />

      <Row :gutter="[16, 16]">
        <!-- Chart -->
        <Col :lg="14" :md="24" :xs="24">
          <Card :bordered="false" title="每日操作统计（最近7天）">
            <div class="h-80 w-full">
              <EchartsUI ref="chartRef" />
            </div>
          </Card>
        </Col>

        <!-- System Status -->
        <Col :lg="10" :md="24" :xs="24">
          <Card :bordered="false" title="系统状态">
            <div v-if="data.system_status" class="py-4">
              <div class="mb-6">
                <div class="mb-2 flex justify-between">
                  <span>CPU使用率</span>
                  <span class="font-medium"
                    >{{ data.system_status.cpu_percent }}%</span
                  >
                </div>
                <Progress
                  :percent="data.system_status.cpu_percent"
                  :status="getStatusColor(data.system_status.cpu_percent)"
                  :stroke-width="10"
                />
              </div>
              <div class="mb-6">
                <div class="mb-2 flex justify-between">
                  <span>内存使用率</span>
                  <span class="font-medium"
                    >{{ data.system_status.memory_percent }}%</span
                  >
                </div>
                <Progress
                  :percent="data.system_status.memory_percent"
                  :status="getStatusColor(data.system_status.memory_percent)"
                  :stroke-width="10"
                />
                <div class="mt-2 text-right text-xs text-gray-500">
                  {{ data.system_status.memory_used_gb }}GB /
                  {{ data.system_status.memory_total_gb }}GB
                </div>
              </div>
              <div class="flex items-center justify-between border-t pt-4">
                <span class="text-gray-600">错误操作日志（7天）</span>
                <Tag :color="(data.error_count || 0) > 0 ? 'red' : 'green'">
                  {{ data.error_count || 0 }}
                </Tag>
              </div>
            </div>
          </Card>
        </Col>
      </Row>

      <Row :gutter="[16, 16]" class="mt-4">
        <!-- Recent Logs -->
        <Col :lg="14" :md="24" :xs="24">
          <Card :bordered="false" title="最近操作日志">
            <Table
              :data-source="data.recent_logs || []"
              :loading="loading"
              :pagination="false"
              row-key="id"
              size="small"
            >
              <Table.Column data-index="username" title="用户" :width="100" />
              <Table.Column
                data-index="action_type_display"
                title="操作"
                :width="100"
              >
                <template #default="{ record }">
                  <Tag :color="getActionTypeColor(record.action_type)">
                    {{ record.action_type_display }}
                  </Tag>
                </template>
              </Table.Column>
              <Table.Column data-index="request_path" ellipsis title="路径" />
              <Table.Column data-index="status_code" title="状态" :width="80">
                <template #default="{ record }">
                  <Tag :color="getStatusCodeColor(record.status_code)">
                    {{ record.status_code }}
                  </Tag>
                </template>
              </Table.Column>
              <Table.Column data-index="created_at" title="时间" :width="160">
                <template #default="{ record }">
                  {{ formatDate(record.created_at) }}
                </template>
              </Table.Column>
            </Table>
          </Card>
        </Col>

        <!-- Recent Users -->
        <Col :lg="10" :md="24" :xs="24">
          <Card :bordered="false" title="最近活跃用户（7天）">
            <List
              :data-source="data.recent_users || []"
              :loading="loading"
              item-layout="horizontal"
            >
              <template #renderItem="{ item }">
                <List.Item>
                  <List.Item.Meta>
                    <template #avatar>
                      <Avatar style="background-color: #165dff">
                        {{ item.username?.[0]?.toUpperCase() || 'U' }}
                      </Avatar>
                    </template>
                    <template #title>
                      <Space>
                        <span>{{ item.username }}</span>
                        <Tag size="small">{{ item.log_count }} 次操作</Tag>
                      </Space>
                    </template>
                    <template #description>
                      {{ item.email || '-' }}
                    </template>
                  </List.Item.Meta>
                </List.Item>
              </template>
            </List>
          </Card>
        </Col>
      </Row>

      <!-- Top Paths -->
      <Card :bordered="false" class="mt-4" title="最活跃的 API 路径（7天）">
        <Table
          :data-source="data.top_paths || []"
          :loading="loading"
          :pagination="false"
          row-key="path"
          size="small"
        >
          <Table.Column data-index="path" ellipsis title="路径" />
          <Table.Column data-index="count" title="访问次数" :width="120">
            <template #default="{ record }">
              <Tag color="blue">{{ record.count }}</Tag>
            </template>
          </Table.Column>
        </Table>
      </Card>
    </div>
  </Page>
</template>
