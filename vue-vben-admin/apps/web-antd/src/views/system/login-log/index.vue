<script setup lang="ts">
import type { TableColumnsType } from 'ant-design-vue';
import type { Dayjs } from 'dayjs';

import type { LoginLog } from '#/api/audit';

import { onMounted, reactive, ref, watch } from 'vue';

import { ReloadOutlined, SearchOutlined } from '@ant-design/icons-vue';
import {
  Button,
  Card,
  Form,
  Input,
  message,
  RangePicker,
  Space,
  Table,
  Tag,
} from 'ant-design-vue';

import { getLoginLogList } from '#/api/audit';

defineOptions({
  name: 'SystemLoginLog',
});

// State
const loading = ref(false);
const tableData = ref<LoginLog[]>([]);
const dateRange = ref<[Dayjs, Dayjs] | undefined>(undefined);

const query = reactive({
  username: '',
  ip_address: '',
  created_at_start: undefined as string | undefined,
  created_at_end: undefined as string | undefined,
});

const pagination = reactive({
  current: 1,
  pageSize: 20,
  total: 0,
  showSizeChanger: true,
  showTotal: (total: number) => `共 ${total} 条`,
});

// Columns
const columns: TableColumnsType<LoginLog> = [
  { title: 'ID', dataIndex: 'id', width: 80 },
  {
    title: '用户名',
    dataIndex: 'username',
    width: 120,
    customRender: ({ record }) =>
      record.user_display || record.username || '匿名',
  },
  { title: '类型', dataIndex: 'action_type', width: 100 },
  { title: 'IP地址', dataIndex: 'ip_address', width: 150 },
  { title: '状态码', dataIndex: 'status_code', width: 100 },
  { title: 'User-Agent', dataIndex: 'user_agent', ellipsis: true },
  {
    title: '时间',
    dataIndex: 'created_at',
    width: 180,
    customRender: ({ record }) => formatDate(record.created_at),
  },
];

// Helper
const formatDate = (dateStr: string) => {
  if (!dateStr) return '-';
  return new Date(dateStr).toLocaleString('zh-CN');
};

const getStatusColor = (statusCode: number) => {
  if (!statusCode) return 'default';
  if (statusCode >= 200 && statusCode < 300) return 'green';
  if (statusCode >= 300 && statusCode < 400) return 'cyan';
  if (statusCode >= 400 && statusCode < 500) return 'orange';
  if (statusCode >= 500) return 'red';
  return 'default';
};

// Actions
const fetchData = async () => {
  loading.value = true;
  try {
    const params = {
      username: query.username || undefined,
      ip_address: query.ip_address || undefined,
      created_at_start: query.created_at_start,
      created_at_end: query.created_at_end,
      page: pagination.current,
      page_size: pagination.pageSize,
    };

    const res: any = await getLoginLogList(params);

    // Handle various response formats
    if (res.results) {
      tableData.value = res.results;
      pagination.total = res.count;
    } else if (res.data?.results) {
      tableData.value = res.data.results;
      pagination.total = res.data.count;
    } else {
      tableData.value = [];
      pagination.total = 0;
    }
  } catch (error) {
    console.error('Fetch login logs error:', error);
    message.error('获取登录日志失败');
  } finally {
    loading.value = false;
  }
};

const handleSearch = () => {
  pagination.current = 1;
  fetchData();
};

const handleReset = () => {
  query.username = '';
  query.ip_address = '';
  query.created_at_start = undefined;
  query.created_at_end = undefined;
  dateRange.value = undefined;
  handleSearch();
};

const handleTableChange = (pag: any) => {
  pagination.current = pag.current;
  pagination.pageSize = pag.pageSize;
  fetchData();
};

// Date range watcher
watch(dateRange, (val) => {
  if (val && val.length === 2) {
    query.created_at_start = val[0].format('YYYY-MM-DD HH:mm:ss');
    query.created_at_end = val[1].format('YYYY-MM-DD HH:mm:ss');
  } else {
    query.created_at_start = undefined;
    query.created_at_end = undefined;
  }
});

onMounted(() => {
  fetchData();
});
</script>

<template>
  <div class="p-4">
    <Card title="登录日志">
      <!-- Toolbar -->
      <div class="mb-4">
        <Form layout="inline">
          <Form.Item label="用户名">
            <Input
              v-model:value="query.username"
              placeholder="搜索用户名"
              allow-clear
              style="width: 150px"
              @press-enter="handleSearch"
            />
          </Form.Item>
          <Form.Item label="IP地址">
            <Input
              v-model:value="query.ip_address"
              placeholder="搜索IP"
              allow-clear
              style="width: 150px"
              @press-enter="handleSearch"
            />
          </Form.Item>
          <Form.Item label="时间范围">
            <RangePicker
              v-model:value="dateRange"
              show-time
              style="width: 350px"
            />
          </Form.Item>
          <Form.Item>
            <Space>
              <Button type="primary" @click="handleSearch">
                <template #icon><SearchOutlined /></template>
                查询
              </Button>
              <Button @click="handleReset">
                <template #icon><ReloadOutlined /></template>
                重置
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </div>

      <!-- Table -->
      <Table
        :columns="columns"
        :data-source="tableData"
        :loading="loading"
        :pagination="pagination"
        @change="handleTableChange"
        row-key="id"
        size="small"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.dataIndex === 'action_type'">
            <Tag
              :color="
                record.action_type === 'login'
                  ? 'green'
                  : record.action_type === 'failed'
                    ? 'red'
                    : 'blue'
              "
            >
              {{ record.action_type_display || record.action_type }}
            </Tag>
          </template>

          <template v-if="column.dataIndex === 'status_code'">
            <Tag :color="getStatusColor(record.status_code)">
              {{ record.status_code }}
            </Tag>
          </template>
        </template>
      </Table>
    </Card>
  </div>
</template>
