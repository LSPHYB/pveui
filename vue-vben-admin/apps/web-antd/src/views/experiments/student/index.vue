<script setup lang="ts">
import type { ExperimentListItem } from '#/api/experiment/types';

import { onMounted, ref } from 'vue';

import { SearchOutlined } from '@ant-design/icons-vue';
import {
  Button,
  Card,
  Col,
  Input,
  message,
  Progress,
  Row,
  Select,
  Spin,
  Tag,
} from 'ant-design-vue';
import { useRouter } from 'vue-router';

import { getExperimentListApi } from '#/api/experiment';
import {
  DIFFICULTY_COLOR,
  DIFFICULTY_LABEL,
  formatDateTime,
  remainingDays,
  SUBMISSION_STATUS_COLOR,
  SUBMISSION_STATUS_LABEL,
} from '../utils';

defineOptions({ name: 'StudentExperimentList' });

const router = useRouter();
const loading = ref(false);
const experiments = ref<ExperimentListItem[]>([]);
const total = ref(0);
const searchText = ref('');
const statusFilter = ref('published');
const page = ref(1);

const fetchData = async () => {
  loading.value = true;
  try {
    const params: Record<string, any> = {
      page: page.value,
      page_size: 20,
      status: statusFilter.value || undefined,
    };
    if (searchText.value) params.search = searchText.value;

    const res = await getExperimentListApi(params);
    experiments.value = res?.results ?? (Array.isArray(res) ? res : []);
    total.value = res?.count ?? experiments.value.length;
  } catch (e: any) {
    message.error('获取实验列表失败');
  } finally {
    loading.value = false;
  }
};

onMounted(fetchData);

const handleSearch = () => {
  page.value = 1;
  fetchData();
};

const getStatusColor = (exp: ExperimentListItem) => {
  const sub = exp.my_submission;
  if (!sub) return 'default';
  return SUBMISSION_STATUS_COLOR[sub.submission_status] ?? 'default';
};

const getStatusLabel = (exp: ExperimentListItem) => {
  const sub = exp.my_submission;
  if (!sub) return '未开始';
  return SUBMISSION_STATUS_LABEL[sub.submission_status] ?? sub.submission_status;
};

const getActionLabel = (exp: ExperimentListItem) => {
  const sub = exp.my_submission;
  if (!sub) return '开始实验';
  const status = sub.submission_status;
  if (status === 'draft') return '继续实验';
  if (status === 'submitted') return '查看提交';
  if (status === 'graded') return '查看成绩';
  return '查看详情';
};

const handleAction = (exp: ExperimentListItem) => {
  const sub = exp.my_submission;
  if (!sub) {
    router.push(`/experiments/student/${exp.id}`);
    return;
  }
  
  if (sub.submission_status === 'graded') {
    router.push(`/experiments/student/${exp.id}/grade`);
  } else if (sub.submission_status === 'draft' || sub.submission_status === 'submitted') {
    // Both draft and submitted can be opened directly in the editor (editor handles readonly logic)
    router.push(`/experiments/student/submissions/${sub.id}/edit`);
  } else {
    router.push(`/experiments/student/${exp.id}`);
  }
};
</script>

<template>
  <div class="p-5">
    <div class="mb-5 flex items-center justify-between">
      <h2 class="m-0 text-xl font-semibold">我的实验</h2>
    </div>

    <!-- 过滤 -->
    <Card class="mb-4" :body-style="{ padding: '12px 16px' }">
      <Row :gutter="12" align="middle">
        <Col :span="8">
          <Input
            v-model:value="searchText"
            placeholder="搜索实验标题..."
            allow-clear
            @press-enter="handleSearch"
          >
            <template #prefix><SearchOutlined /></template>
          </Input>
        </Col>
        <Col :span="6">
          <Select
            v-model:value="statusFilter"
            allow-clear
            placeholder="全部状态"
            style="width: 100%"
            @change="handleSearch"
          >
            <Select.Option value="published">进行中</Select.Option>
            <Select.Option value="archived">已结束</Select.Option>
          </Select>
        </Col>
        <Col>
          <Button type="primary" @click="handleSearch">搜索</Button>
        </Col>
      </Row>
    </Card>

    <!-- 列表 -->
    <Spin :spinning="loading">
      <Row :gutter="[16, 16]">
        <Col v-for="exp in experiments" :key="exp.id" :xs="24" :md="12" :xl="8">
          <Card hoverable :body-style="{ padding: '20px' }">
            <!-- 标题行 -->
            <div class="mb-2 flex items-start justify-between gap-2">
              <h3
                class="m-0 cursor-pointer truncate text-base font-semibold hover:text-blue-500"
                @click="router.push(`/experiments/student/${exp.id}`)"
              >
                {{ exp.title }}
              </h3>
              <Tag :color="getStatusColor(exp)" class="shrink-0">
                {{ getStatusLabel(exp) }}
              </Tag>
            </div>

            <!-- 元信息 -->
            <div class="mb-3 space-y-1 text-sm text-gray-500">
              <div v-if="exp.course_code">课程：{{ exp.course_code }}</div>
              <div>
                难度：
                <Tag :color="DIFFICULTY_COLOR[exp.difficulty]" size="small">
                  {{ DIFFICULTY_LABEL[exp.difficulty] ?? exp.difficulty }}
                </Tag>
              </div>
              <div class="flex items-center gap-3">
                <span>截止：{{ formatDateTime(exp.end_time).slice(0, 10) }}</span>
                <span
                  v-if="exp.status === 'published' && remainingDays(exp.end_time) > 0"
                  class="text-orange-500"
                >
                  剩余 {{ remainingDays(exp.end_time) }} 天
                </span>
                <Tag v-if="exp.status === 'archived'" color="purple" size="small">已结束</Tag>
              </div>
            </div>

            <!-- 得分（已批改时显示） -->
            <div
              v-if="exp.my_submission?.submission_status === 'graded' && exp.my_submission.score !== null"
              class="mb-3"
            >
              <div class="mb-1 flex justify-between text-sm">
                <span>得分</span>
                <span class="font-semibold text-green-600">
                  {{ exp.my_submission.score }} / {{ exp.total_score }}
                </span>
              </div>
              <Progress
                :percent="Math.round((exp.my_submission.score / exp.total_score) * 100)"
                :stroke-color="exp.my_submission.score >= 60 ? '#52c41a' : '#ff4d4f'"
                size="small"
              />
            </div>

            <!-- 操作按钮 -->
            <div class="flex items-center justify-between">
              <Button
                type="primary"
                size="small"
                @click="handleAction(exp)"
              >
                {{ getActionLabel(exp) }}
              </Button>
              <Button
                type="link"
                size="small"
                @click="router.push(`/experiments/student/${exp.id}`)"
              >
                查看详情 →
              </Button>
            </div>
          </Card>
        </Col>
      </Row>

      <div v-if="experiments.length === 0 && !loading" class="py-16 text-center text-gray-400">
        暂无实验
      </div>
    </Spin>
  </div>
</template>
