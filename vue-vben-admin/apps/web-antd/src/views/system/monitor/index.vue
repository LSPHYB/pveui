<script setup lang="ts">
import { onMounted, onUnmounted, reactive, ref, watch } from 'vue';

import { ReloadOutlined } from '@ant-design/icons-vue';
import {
  Button,
  Card,
  Col,
  Descriptions,
  Divider,
  InputNumber,
  Progress,
  Row,
  Space,
  Statistic,
  Switch,
  Table,
  Tag,
  Typography,
} from 'ant-design-vue';

import { getSystemMetricsApi } from '#/api/system';

defineOptions({
  name: 'SystemMonitor',
});

const { Text } = Typography;

// State
const loading = ref(false);
const autoRefresh = ref(true);
const intervalSec = ref(5);
let timer: null | ReturnType<typeof setInterval> = null;

const meta = reactive<any>({
  platform: { system: '-', release: '-', python: '-' },
  uptime_seconds: 0,
  cpu: { percent: 0, count_logical: 0, count_physical: 0, load_avg: [] },
  memory: { total: 0, available: 0, used: 0, free: 0, percent: 0 },
  swap: { total: 0, used: 0, free: 0, percent: 0 },
  disks: [],
  network: { bytes_sent: 0, bytes_recv: 0, packets_sent: 0, packets_recv: 0 },
});

// Helpers
const formatSeconds = (sec: number) => {
  const s = Number(sec || 0);
  const d = Math.floor(s / 86_400);
  const h = Math.floor((s % 86_400) / 3600);
  const m = Math.floor((s % 3600) / 60);
  const r = Math.floor(s % 60);
  const parts = [];
  if (d) parts.push(`${d}d`);
  if (h) parts.push(`${h}h`);
  if (m) parts.push(`${m}m`);
  parts.push(`${r}s`);
  return parts.join(' ');
};

const formatBytes = (n: number) => {
  if (!n && n !== 0) return '-';
  const units = ['B', 'KB', 'MB', 'GB', 'TB'];
  let v = Number(n);
  let i = 0;
  while (v >= 1024 && i < units.length - 1) {
    v /= 1024;
    i++;
  }
  return `${v.toFixed(2)} ${units[i]}`;
};

const getProgressStatus = (percent: number) => {
  if (percent >= 90) return 'exception';
  if (percent >= 75) return 'active';
  return 'success';
};

// Actions
const fetchData = async () => {
  loading.value = true;
  try {
    const res = await getSystemMetricsApi();
    Object.assign(meta, res);
  } catch {
    // Silent fail on auto refresh, or show toast on manual?
    // message.error('获取系统指标失败');
  } finally {
    loading.value = false;
  }
};

const startTimer = () => {
  stopTimer();
  if (autoRefresh.value) {
    timer = setInterval(fetchData, Math.max(2, intervalSec.value) * 1000);
  }
};

const stopTimer = () => {
  if (timer) {
    clearInterval(timer);
    timer = null;
  }
};

// Watch
watch([autoRefresh, intervalSec], () => {
  startTimer();
});

// Lifecycle
onMounted(() => {
  fetchData();
  startTimer();
});

onUnmounted(() => {
  stopTimer();
});
</script>

<template>
  <div class="p-4">
    <Card>
      <template #title>
        <Space>
          <span class="text-lg font-bold">系统监控</span>
          <Tag color="blue">
            {{ meta.platform.system }} {{ meta.platform.release }}
          </Tag>
          <Tag color="cyan">Python {{ meta.platform.python }}</Tag>
          <Tag color="green">
            Uptime: {{ formatSeconds(meta.uptime_seconds) }}
          </Tag>
        </Space>
      </template>
      <template #extra>
        <Space>
          <Button type="primary" :loading="loading" @click="fetchData">
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
            :min="2"
            :max="120"
            style="width: 70px"
            size="small"
          />
          <Text type="secondary">秒</Text>
        </Space>
      </template>

      <Row :gutter="[16, 16]">
        <Col :span="6" :xs="24" :sm="12" :md="6">
          <Card size="small" title="CPU">
            <Statistic
              title="使用率"
              :value="meta.cpu.percent"
              suffix="%"
              :value-style="{ color: '#1890ff' }"
            />
            <Progress
              :percent="meta.cpu.percent"
              :status="getProgressStatus(meta.cpu.percent)"
              :show-info="false"
            />
            <Divider style="margin: 12px 0" />
            <Descriptions :column="1" size="small" :bordered="false">
              <Descriptions.Item label="逻辑核">
                {{ meta.cpu.count_logical }}
              </Descriptions.Item>
              <Descriptions.Item label="物理核">
                {{ meta.cpu.count_physical }}
              </Descriptions.Item>
              <Descriptions.Item label="Load Avg">
                {{ meta.cpu.load_avg?.join(' / ') || '-' }}
              </Descriptions.Item>
            </Descriptions>
          </Card>
        </Col>

        <Col :span="6" :xs="24" :sm="12" :md="6">
          <Card size="small" title="内存">
            <Statistic
              title="使用率"
              :value="meta.memory.percent"
              suffix="%"
              :value-style="{ color: '#52c41a' }"
            />
            <Progress
              :percent="meta.memory.percent"
              :status="getProgressStatus(meta.memory.percent)"
              :show-info="false"
            />
            <Divider style="margin: 12px 0" />
            <Descriptions :column="1" size="small" :bordered="false">
              <Descriptions.Item label="总量">
                {{ formatBytes(meta.memory.total) }}
              </Descriptions.Item>
              <Descriptions.Item label="已用">
                {{ formatBytes(meta.memory.used) }}
              </Descriptions.Item>
              <Descriptions.Item label="可用">
                {{ formatBytes(meta.memory.available) }}
              </Descriptions.Item>
            </Descriptions>
          </Card>
        </Col>

        <Col :span="6" :xs="24" :sm="12" :md="6">
          <Card size="small" title="Swap">
            <Statistic
              title="使用率"
              :value="meta.swap.percent"
              suffix="%"
              :value-style="{ color: '#faad14' }"
            />
            <Progress
              :percent="meta.swap.percent"
              :status="getProgressStatus(meta.swap.percent)"
              :show-info="false"
            />
            <Divider style="margin: 12px 0" />
            <Descriptions :column="1" size="small" :bordered="false">
              <Descriptions.Item label="总量">
                {{ formatBytes(meta.swap.total) }}
              </Descriptions.Item>
              <Descriptions.Item label="已用">
                {{ formatBytes(meta.swap.used) }}
              </Descriptions.Item>
              <Descriptions.Item label="空闲">
                {{ formatBytes(meta.swap.free) }}
              </Descriptions.Item>
            </Descriptions>
          </Card>
        </Col>

        <Col :span="6" :xs="24" :sm="12" :md="6">
          <Card size="small" title="网络">
            <div class="flex h-[130px] flex-col justify-center">
              <Descriptions :column="1" size="small" :bordered="false">
                <Descriptions.Item label="发送">
                  {{ formatBytes(meta.network.bytes_sent) }}
                </Descriptions.Item>
                <Descriptions.Item label="接收">
                  {{ formatBytes(meta.network.bytes_recv) }}
                </Descriptions.Item>
                <Descriptions.Item label="发送包">
                  {{ meta.network.packets_sent }}
                </Descriptions.Item>
                <Descriptions.Item label="接收包">
                  {{ meta.network.packets_recv }}
                </Descriptions.Item>
              </Descriptions>
            </div>
          </Card>
        </Col>
      </Row>

      <Card title="磁盘状态" style="margin-top: 16px" :bordered="false">
        <Table
          :data-source="meta.disks"
          :pagination="false"
          row-key="mountpoint"
          size="small"
        >
          <Table.Column title="设备" data-index="device" width="150" />
          <Table.Column title="挂载点" data-index="mountpoint" width="150" />
          <Table.Column title="类型" data-index="fstype" width="100" />
          <Table.Column title="总量" data-index="total">
            <template #default="{ record }">
              {{ formatBytes(record.total) }}
            </template>
          </Table.Column>
          <Table.Column title="已用" data-index="used">
            <template #default="{ record }">
              {{ formatBytes(record.used) }}
            </template>
          </Table.Column>
          <Table.Column title="可用" data-index="free">
            <template #default="{ record }">
              {{ formatBytes(record.free) }}
            </template>
          </Table.Column>
          <Table.Column title="使用率" width="200">
            <template #default="{ record }">
              <Progress
                :percent="record.percent"
                :status="getProgressStatus(record.percent)"
              />
            </template>
          </Table.Column>
        </Table>
      </Card>
    </Card>
  </div>
</template>
