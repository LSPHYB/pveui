<script setup lang="ts">
import type { ExperimentListItem } from '#/api/experiment/types';

import { onMounted, ref } from 'vue';

import {
  AppstoreOutlined,
  DeleteOutlined,
  EditOutlined,
  ExportOutlined,
  EyeOutlined,
  FormOutlined,
  PlusOutlined,
  ReloadOutlined,
  SearchOutlined,
} from '@ant-design/icons-vue';
import {
  Button,
  Card,
  Col,
  Input,
  message,
  Modal,
  Popconfirm,
  Row,
  Select,
  Space,
  Spin,
  Statistic,
  Tag,
} from 'ant-design-vue';
import { useRouter } from 'vue-router';

import {
  archiveExperimentApi,
  deleteExperimentApi,
  getExperimentListApi,
  getExportGradesUrl,
  publishExperimentApi,
} from '#/api/experiment';
import {
  CATEGORY_LABEL,
  DIFFICULTY_COLOR,
  DIFFICULTY_LABEL,
  EXPERIMENT_STATUS_COLOR,
  EXPERIMENT_STATUS_LABEL,
  formatDateTime,
  remainingDays,
} from '../utils';

defineOptions({ name: 'TeacherExperimentList' });

const router = useRouter();
const loading = ref(false);
const experiments = ref<ExperimentListItem[]>([]);
const total = ref(0);

// 过滤条件
const searchText = ref('');
const statusFilter = ref('');
const page = ref(1);
const pageSize = ref(12);

const fetchData = async () => {
  loading.value = true;
  try {
    const params: Record<string, any> = {
      page: page.value,
      page_size: pageSize.value,
    };
    if (searchText.value) params.search = searchText.value;
    if (statusFilter.value) params.status = statusFilter.value;

    const res = await getExperimentListApi(params);
    // extractData 已修复，res 现在是 { count, results: [...] }
    experiments.value = res?.results ?? (Array.isArray(res) ? res : []);
    total.value = res?.count ?? experiments.value.length;
  } catch (e: any) {
    message.error(`获取实验列表失败: ${e?.message ?? '未知错误'}`);
  } finally {
    loading.value = false;
  }
};

onMounted(fetchData);

const handleSearch = () => {
  page.value = 1;
  fetchData();
};

const handlePublish = (exp: ExperimentListItem) => {
  Modal.confirm({
    title: `确认发布「${exp.title}」？`,
    content: '发布后学生即可查看，请确认已上传指导书并设置评分标准。',
    okText: '发布',
    okType: 'primary',
    cancelText: '取消',
    onOk: async () => {
      try {
        await publishExperimentApi(exp.id);
        message.success('实验已发布');
        fetchData();
      } catch (e: any) {
        message.error(e?.response?.data?.message ?? '发布失败');
      }
    },
  });
};

const handleArchive = (exp: ExperimentListItem) => {
  Modal.confirm({
    title: `确认归档「${exp.title}」？`,
    content: '归档后学生不可再提交，仅能查看历史记录。',
    okText: '归档',
    okType: 'default',
    cancelText: '取消',
    onOk: async () => {
      try {
        await archiveExperimentApi(exp.id);
        message.success('已归档');
        fetchData();
      } catch (e: any) {
        message.error(e?.response?.data?.message ?? '归档失败');
      }
    },
  });
};

const handleDelete = async (exp: ExperimentListItem) => {
  try {
    await deleteExperimentApi(exp.id);
    message.success('已删除');
    fetchData();
  } catch (e: any) {
    message.error('删除失败');
  }
};

const handleExport = (exp: ExperimentListItem) => {
  window.open(getExportGradesUrl(exp.id), '_blank');
};

const submissionRate = (exp: ExperimentListItem) => {
  const t = exp.stats.total_students;
  return t ? `${exp.stats.submitted_count}/${t}` : '0/0';
};

const gradedRate = (exp: ExperimentListItem) => {
  const s = exp.stats.submitted_count;
  return s ? `${exp.stats.graded_count}/${s}` : '0/0';
};
</script>

<template>
  <div class="p-5">
    <!-- Header -->
    <div class="mb-5 flex items-center justify-between">
      <h2 class="m-0 text-xl font-semibold">实验管理</h2>
      <Space>
        <Button
          type="primary"
          :icon="h(PlusOutlined)"
          @click="router.push('/experiments/teacher/create')"
        >
          新建实验
        </Button>
        <Button :icon="h(ReloadOutlined)" @click="fetchData">刷新</Button>
      </Space>
    </div>

    <!-- 过滤栏 -->
    <Card class="mb-4" :body-style="{ padding: '16px' }">
      <Row :gutter="12" align="middle">
        <Col :span="8">
          <Input
            v-model:value="searchText"
            placeholder="搜索实验标题或课程代码..."
            allow-clear
            @press-enter="handleSearch"
          >
            <template #prefix><SearchOutlined /></template>
          </Input>
        </Col>
        <Col :span="6">
          <Select
            v-model:value="statusFilter"
            placeholder="全部状态"
            allow-clear
            style="width: 100%"
            @change="handleSearch"
          >
            <Select.Option value="draft">草稿</Select.Option>
            <Select.Option value="published">已发布</Select.Option>
            <Select.Option value="archived">已归档</Select.Option>
          </Select>
        </Col>
        <Col>
          <Button type="primary" :icon="h(SearchOutlined)" @click="handleSearch">搜索</Button>
        </Col>
      </Row>
    </Card>

    <!-- 列表 -->
    <Spin :spinning="loading">
      <div v-if="experiments.length === 0 && !loading" class="py-20 text-center text-gray-400">
        <AppstoreOutlined style="font-size: 48px" />
        <p class="mt-3">暂无实验，点击「新建实验」开始创建</p>
      </div>

      <Row :gutter="[16, 16]">
        <Col v-for="exp in experiments" :key="exp.id" :xs="24" :sm="24" :md="12" :xl="8">
          <Card
            hoverable
            class="experiment-card h-full"
            :body-style="{ padding: '20px' }"
          >
            <!-- 顶部：标题 + 状态 -->
            <div class="mb-3 flex items-start justify-between gap-2">
              <h3
                class="m-0 cursor-pointer truncate text-base font-semibold hover:text-blue-500"
                :title="exp.title"
                @click="router.push(`/experiments/teacher/edit/${exp.id}`)"
              >
                {{ exp.title }}
              </h3>
              <Tag :color="EXPERIMENT_STATUS_COLOR[exp.status]" class="shrink-0">
                {{ EXPERIMENT_STATUS_LABEL[exp.status] }}
              </Tag>
            </div>

            <!-- 元信息 -->
            <div class="mb-3 space-y-1 text-sm text-gray-500">
              <div v-if="exp.course_code">课程代码：{{ exp.course_code }}</div>
              <div>
                分类：{{ CATEGORY_LABEL[exp.category] ?? exp.category }}
                &nbsp;|&nbsp;
                难度：
                <Tag :color="DIFFICULTY_COLOR[exp.difficulty]" size="small">
                  {{ DIFFICULTY_LABEL[exp.difficulty] ?? exp.difficulty }}
                </Tag>
              </div>
              <div>
                时间：{{ formatDateTime(exp.start_time).slice(0, 10) }}
                &nbsp;~&nbsp;
                {{ formatDateTime(exp.end_time).slice(0, 10) }}
                <span
                  v-if="exp.status === 'published' && remainingDays(exp.end_time) > 0"
                  class="ml-1 text-orange-500"
                >（剩余 {{ remainingDays(exp.end_time) }} 天）</span>
              </div>
            </div>

            <!-- 统计数据 -->
            <Row :gutter="8" class="mb-4 rounded-md bg-gray-50 py-2">
              <Col :span="8" class="text-center">
                <Statistic
                  title="提交率"
                  :value="submissionRate(exp)"
                  :value-style="{ fontSize: '16px' }"
                />
              </Col>
              <Col :span="8" class="text-center">
                <Statistic
                  title="已批改"
                  :value="gradedRate(exp)"
                  :value-style="{ fontSize: '16px' }"
                />
              </Col>
              <Col :span="8" class="text-center">
                <Statistic
                  title="总分"
                  :value="exp.total_score"
                  :value-style="{ fontSize: '16px' }"
                />
              </Col>
            </Row>

            <!-- 操作按钮 -->
            <div class="flex flex-wrap gap-1">
              <Button
                size="small"
                type="link"
                :icon="h(EyeOutlined)"
                @click="router.push(`/experiments/teacher/edit/${exp.id}?mode=view`)"
              >
                详情
              </Button>
              <Button
                size="small"
                type="link"
                :icon="h(FormOutlined)"
                @click="router.push(`/experiments/teacher/submissions?experiment_id=${exp.id}`)"
              >
                批改
              </Button>
              <Button
                v-if="exp.status === 'draft'"
                size="small"
                type="link"
                style="color: #52c41a"
                @click="handlePublish(exp)"
              >
                发布
              </Button>
              <Button
                v-if="exp.status === 'published'"
                size="small"
                type="link"
                style="color: #722ed1"
                @click="handleArchive(exp)"
              >
                归档
              </Button>
              <Button
                size="small"
                type="link"
                :icon="h(EditOutlined)"
                @click="router.push(`/experiments/teacher/edit/${exp.id}`)"
              >
                编辑
              </Button>
              <Button
                size="small"
                type="link"
                :icon="h(ExportOutlined)"
                @click="handleExport(exp)"
              >
                导出
              </Button>
              <Popconfirm
                title="确认删除该实验？"
                ok-text="删除"
                ok-type="danger"
                cancel-text="取消"
                @confirm="handleDelete(exp)"
              >
                <Button size="small" type="link" danger :icon="h(DeleteOutlined)">删除</Button>
              </Popconfirm>
            </div>
          </Card>
        </Col>
      </Row>
    </Spin>
  </div>
</template>

<script lang="ts">
import { h } from 'vue';
export { h };
</script>

<style scoped>
.experiment-card :deep(.ant-card-body) {
  display: flex;
  flex-direction: column;
  height: 100%;
}
</style>
