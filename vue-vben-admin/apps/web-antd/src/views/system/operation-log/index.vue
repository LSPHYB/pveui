<script setup lang="ts">
import type { TableColumnsType } from 'ant-design-vue';
import type { Dayjs } from 'dayjs';

import type { OperationLog } from '#/api/audit';

import { onMounted, reactive, ref, watch } from 'vue';

import { ReloadOutlined, SearchOutlined } from '@ant-design/icons-vue';
import {
  Button,
  Card,
  Descriptions,
  Form,
  Input,
  message,
  Modal,
  RangePicker,
  Select,
  Space,
  Table,
  Tag,
  Typography,
} from 'ant-design-vue';

import { getOperationLogList } from '#/api/audit';

defineOptions({
  name: 'SystemOperationLog',
});

// State
const loading = ref(false);
const tableData = ref<OperationLog[]>([]);
const dateRange = ref<[Dayjs, Dayjs] | undefined>(undefined);

// Detail Modal State
const detailVisible = ref(false);
const currentDetail = ref<null | OperationLog>(null);

const query = reactive({
  username: '',
  action_type: undefined,
  request_method: undefined,
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
const columns: TableColumnsType<OperationLog> = [
  { title: 'ID', dataIndex: 'id', width: 80 },
  {
    title: '用户名',
    dataIndex: 'username',
    width: 120,
    customRender: ({ record }) =>
      record.user_display || record.username || '匿名',
  },
  { title: '操作类型', dataIndex: 'action_type', width: 100 },
  { title: '请求路径', dataIndex: 'request_path', ellipsis: true },
  { title: '请求方法', dataIndex: 'request_method', width: 100 },
  { title: 'IP地址', dataIndex: 'ip_address', width: 130 },
  { title: '状态码', dataIndex: 'status_code', width: 80 },
  {
    title: '时间',
    dataIndex: 'created_at',
    width: 170,
    customRender: ({ record }) => formatDate(record.created_at),
  },
  { title: '操作', key: 'action', width: 80, fixed: 'right' },
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

const getActionTypeColor = (type: string) => {
  const colors: Record<string, string> = {
    create: 'green',
    update: 'blue',
    delete: 'red',
    view: 'cyan',
    list: 'purple',
  };
  return colors[type] || 'default';
};

const getMethodColor = (method: string) => {
  const colors: Record<string, string> = {
    GET: 'blue',
    POST: 'green',
    PUT: 'orange',
    PATCH: 'cyan',
    DELETE: 'red',
  };
  return colors[method] || 'default';
};

const formatJson = (json: any) => {
  if (!json) return '无';
  try {
    return JSON.stringify(json, null, 2);
  } catch {
    return String(json);
  }
};

// Actions
const fetchData = async () => {
  loading.value = true;
  try {
    const params = {
      ...query,
      page: pagination.current,
      page_size: pagination.pageSize,
    };

    // Clean undefined params
    Object.keys(params).forEach((key) => {
      if ((params as any)[key] === '' || (params as any)[key] === undefined) {
        delete (params as any)[key];
      }
    });

    const res: any = await getOperationLogList(params);

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
    console.error('Fetch operation logs error:', error);
    message.error('获取操作日志失败');
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
  query.action_type = undefined;
  query.request_method = undefined;
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

const handleViewDetail = async (record: OperationLog) => {
  try {
    // Optimistic open with current record
    currentDetail.value = record;
    detailVisible.value = true;

    // Fetch full detail if needed (e.g. huge JSON params might be truncated in list)
    // const res = await getOperationLogDetail(record.id);
    // currentDetail.value = res.data || res;
  } catch {
    message.error('获取详情失败');
  }
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
    <Card title="操作日志">
      <!-- Toolbar -->
      <div class="mb-4">
        <Form layout="inline" class="gap-y-2">
          <Form.Item label="用户名">
            <Input
              v-model:value="query.username"
              placeholder="搜索用户名"
              allow-clear
              style="width: 120px"
              @press-enter="handleSearch"
            />
          </Form.Item>

          <Form.Item label="类型">
            <Select
              v-model:value="query.action_type"
              placeholder="全部"
              allow-clear
              style="width: 100px"
            >
              <Select.Option value="create">创建</Select.Option>
              <Select.Option value="update">更新</Select.Option>
              <Select.Option value="delete">删除</Select.Option>
              <Select.Option value="view">查看</Select.Option>
              <Select.Option value="list">列表</Select.Option>
              <Select.Option value="other">其他</Select.Option>
            </Select>
          </Form.Item>

          <Form.Item label="方法">
            <Select
              v-model:value="query.request_method"
              placeholder="全部"
              allow-clear
              style="width: 90px"
            >
              <Select.Option value="GET">GET</Select.Option>
              <Select.Option value="POST">POST</Select.Option>
              <Select.Option value="PUT">PUT</Select.Option>
              <Select.Option value="PATCH">PATCH</Select.Option>
              <Select.Option value="DELETE">DELETE</Select.Option>
            </Select>
          </Form.Item>

          <Form.Item label="IP">
            <Input
              v-model:value="query.ip_address"
              placeholder="搜索IP"
              allow-clear
              style="width: 120px"
              @press-enter="handleSearch"
            />
          </Form.Item>

          <Form.Item label="时间">
            <RangePicker
              v-model:value="dateRange"
              show-time
              style="width: 320px"
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
        :scroll="{ x: 1200 }"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.dataIndex === 'action_type'">
            <Tag :color="getActionTypeColor(record.action_type)">
              {{ record.action_type_display || record.action_type }}
            </Tag>
          </template>

          <template v-if="column.dataIndex === 'request_method'">
            <Tag :color="getMethodColor(record.request_method)">
              {{ record.request_method }}
            </Tag>
          </template>

          <template v-if="column.dataIndex === 'status_code'">
            <Tag :color="getStatusColor(record.status_code)">
              {{ record.status_code }}
            </Tag>
          </template>

          <template v-if="column.key === 'action'">
            <Button
              type="link"
              size="small"
              @click="handleViewDetail(record as any)"
            >
              详情
            </Button>
          </template>
        </template>
      </Table>
    </Card>

    <!-- Detail Modal -->
    <Modal
      v-model:open="detailVisible"
      title="操作日志详情"
      :footer="null"
      width="800px"
    >
      <Descriptions v-if="currentDetail" :column="1" bordered size="small">
        <Descriptions.Item label="ID">{{ currentDetail.id }}</Descriptions.Item>
        <Descriptions.Item label="操作人">
          {{ currentDetail.user_display || currentDetail.username }}
        </Descriptions.Item>
        <Descriptions.Item label="操作类型">
          <Tag :color="getActionTypeColor(currentDetail.action_type)">
            {{ currentDetail.action_type_display || currentDetail.action_type }}
          </Tag>
        </Descriptions.Item>
        <Descriptions.Item label="请求路径">
          {{ currentDetail.request_path }}
        </Descriptions.Item>
        <Descriptions.Item label="请求方法">
          <Tag :color="getMethodColor(currentDetail.request_method)">
            {{ currentDetail.request_method }}
          </Tag>
        </Descriptions.Item>
        <Descriptions.Item label="IP地址">
          {{ currentDetail.ip_address }}
        </Descriptions.Item>
        <Descriptions.Item label="User Agent">
          {{ currentDetail.user_agent }}
        </Descriptions.Item>
        <Descriptions.Item label="状态码">
          <Tag :color="getStatusColor(currentDetail.status_code)">
            {{ currentDetail.status_code }}
          </Tag>
        </Descriptions.Item>
        <Descriptions.Item label="操作时间">
          {{ formatDate(currentDetail.created_at) }}
        </Descriptions.Item>

        <Descriptions.Item label="错误信息" v-if="currentDetail.error_message">
          <Typography.Text type="danger">
            {{ currentDetail.error_message }}
          </Typography.Text>
        </Descriptions.Item>

        <Descriptions.Item label="请求参数">
          <div class="max-h-60 overflow-auto rounded bg-gray-50 p-2">
            <pre>{{ formatJson(currentDetail.request_params) }}</pre>
          </div>
        </Descriptions.Item>
      </Descriptions>
    </Modal>
  </div>
</template>
