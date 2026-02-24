<script setup lang="ts">
import type { SubmissionListItem } from '#/api/experiment/types';

import { onMounted, ref, watch } from 'vue';

import { FormOutlined, SearchOutlined } from '@ant-design/icons-vue';
import {
  Button,
  Card,
  Input,
  message,
  Select,
  Space,
  Table,
  Tag,
} from 'ant-design-vue';
import { useRoute, useRouter } from 'vue-router';

import { getSubmissionListApi } from '#/api/experiment';
import {
  formatDateTime,
  SUBMISSION_STATUS_COLOR,
  SUBMISSION_STATUS_LABEL,
} from '../utils';

defineOptions({ name: 'TeacherSubmissionList' });

const router = useRouter();
const route = useRoute();

const loading = ref(false);
const submissions = ref<SubmissionListItem[]>([]);
const total = ref(0);
const page = ref(1);
const pageSize = ref(20);

const experimentId = ref(route.query.experiment_id as string || '');
const statusFilter = ref(route.query.status as string || 'submitted');
const searchText = ref('');

const columns = [
  { title: '学生', dataIndex: ['student', 'name'], key: 'student_name' },
  { title: '用户名', dataIndex: ['student', 'username'], key: 'username' },
  { title: '状态', dataIndex: 'submission_status', key: 'status', width: 100 },
  { title: '提交时间', dataIndex: 'submit_time', key: 'submit_time', width: 180 },
  { title: '迟交', dataIndex: 'is_late', key: 'is_late', width: 80 },
  { title: '得分', dataIndex: 'score', key: 'score', width: 80 },
  { title: '操作', key: 'action', width: 120 },
];

const fetchData = async () => {
  loading.value = true;
  try {
    const params: Record<string, any> = {
      page: page.value,
      page_size: pageSize.value,
    };
    if (experimentId.value) params.experiment_id = experimentId.value;
    if (statusFilter.value) params.submission_status = statusFilter.value;
    if (searchText.value) params.search = searchText.value;

    const res = await getSubmissionListApi(params);
    submissions.value = res?.results ?? (Array.isArray(res) ? res : []);
    total.value = res?.count ?? submissions.value.length;
  } catch (e: any) {
    message.error('获取提交列表失败');
  } finally {
    loading.value = false;
  }
};

onMounted(fetchData);

watch([page, pageSize, statusFilter], fetchData);

const handleSearch = () => {
  page.value = 1;
  fetchData();
};
</script>

<template>
  <div class="p-5">
    <div class="mb-5 flex items-center justify-between">
      <h2 class="m-0 text-xl font-semibold">提交管理</h2>
    </div>

    <Card class="mb-4" :body-style="{ padding: '16px' }">
      <Space wrap>
        <Input
          v-model:value="searchText"
          placeholder="搜索学生姓名..."
          allow-clear
          style="width: 200px"
          @press-enter="handleSearch"
        >
          <template #prefix><SearchOutlined /></template>
        </Input>
        <Select
          v-model:value="statusFilter"
          placeholder="全部状态"
          allow-clear
          style="width: 140px"
          @change="fetchData"
        >
          <Select.Option value="submitted">待批改</Select.Option>
          <Select.Option value="graded">已批改</Select.Option>
          <Select.Option value="draft">草稿</Select.Option>
        </Select>
        <Button type="primary" :icon="h(SearchOutlined)" @click="handleSearch">搜索</Button>
      </Space>
    </Card>

    <Card>
      <Table
        :columns="columns"
        :data-source="submissions"
        :loading="loading"
        :pagination="{
          current: page,
          pageSize,
          total,
          showTotal: (t: number) => `共 ${t} 条`,
          onChange: (p: number, ps: number) => { page = p; pageSize = ps; },
        }"
        row-key="id"
        size="middle"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'status'">
            <Tag :color="SUBMISSION_STATUS_COLOR[record.submission_status]">
              {{ SUBMISSION_STATUS_LABEL[record.submission_status] }}
            </Tag>
          </template>
          <template v-else-if="column.key === 'submit_time'">
            {{ formatDateTime(record.submit_time) }}
          </template>
          <template v-else-if="column.key === 'is_late'">
            <Tag v-if="record.is_late" color="error">迟交</Tag>
            <span v-else class="text-gray-400">—</span>
          </template>
          <template v-else-if="column.key === 'score'">
            <span v-if="record.score !== null" class="font-medium text-green-600">
              {{ record.score }}
            </span>
            <span v-else class="text-gray-400">—</span>
          </template>
          <template v-else-if="column.key === 'action'">
            <Button
              type="link"
              size="small"
              :icon="h(FormOutlined)"
              @click="router.push(`/experiments/teacher/grade/${record.id}`)"
            >
              {{ record.submission_status === 'graded' ? '查看' : '批改' }}
            </Button>
          </template>
        </template>
      </Table>
    </Card>
  </div>
</template>

<script lang="ts">
import { h } from 'vue';
export { h };
</script>
