<script setup lang="ts">
import type { ExperimentDetail, GuidebookListItem } from '#/api/experiment/types';

import { computed, onMounted, ref } from 'vue';

import {
  ArrowLeftOutlined,
  BookOutlined,
  DownloadOutlined,
  EyeOutlined,
  FileOutlined,
} from '@ant-design/icons-vue';
import {
  Alert,
  Button,
  Card,
  Col,
  Descriptions,
  Empty,
  Image,
  List,
  message,
  Modal,
  Row,
  Space,
  Spin,
  Statistic,
  Tabs,
  Tag,
} from 'ant-design-vue';
import { useRoute, useRouter } from 'vue-router';

import {
  getExperimentDetailApi,
  getGuidebookDownloadUrl,
  getMySubmissionApi,
  previewGuidebookApi,
} from '#/api/experiment';
import {
  DIFFICULTY_COLOR,
  DIFFICULTY_LABEL,
  DOC_TYPE_LABEL,
  formatDateTime,
  formatFileSize,
  remainingDays,
  SUBMISSION_STATUS_COLOR,
  SUBMISSION_STATUS_LABEL,
} from '../utils';

defineOptions({ name: 'StudentExperimentDetail' });

const router = useRouter();
const route = useRoute();
const experimentId = route.params.id as string;

const loading = ref(false);
const experiment = ref<ExperimentDetail | null>(null);
const activeTab = ref('intro');

// 指导书预览
const previewVisible = ref(false);
const previewLoading = ref(false);
const previewData = ref<{ type: string; content?: string; html?: string; url?: string } | null>(null);
const previewTitle = ref('');

// 我的提交状态
const mySubmission = computed(() => experiment.value?.my_submission ?? null);

const isExpired = computed(() => {
  if (!experiment.value) return false;
  return new Date(experiment.value.end_time).getTime() < Date.now();
});

const canSubmit = computed(() => {
  if (!experiment.value) return false;
  if (experiment.value.status !== 'published') return false;
  const sub = mySubmission.value;
  if (!sub) return true;
  const s = sub.submission_status;
  return s === 'draft' || (s === 'graded' && experiment.value.late_submission_allowed);
});

const loadData = async () => {
  loading.value = true;
  try {
    experiment.value = await getExperimentDetailApi(experimentId);
  } catch (e: any) {
    message.error('加载实验信息失败');
  } finally {
    loading.value = false;
  }
};

onMounted(loadData);

// 预览指导书
const handlePreview = async (gb: GuidebookListItem) => {
  previewTitle.value = gb.title;
  previewVisible.value = true;
  previewLoading.value = true;
  previewData.value = null;
  try {
    const result = await previewGuidebookApi(gb.id);
    previewData.value = {
      type: result.file_type,
      content: result.content,
      html: result.html,
      url: toAbsUrl(result.preview_url ?? result.media_url),
    };
  } catch {
    message.error('预览失败');
    previewVisible.value = false;
  } finally {
    previewLoading.value = false;
  }
};

// 开始/继续实验（获取 or 创建草稿，跳转编辑器）
const handleStart = async () => {
  try {
    const sub = await getMySubmissionApi(experimentId);
    router.push(`/experiments/student/submissions/${sub.id}/edit`);
  } catch (e: any) {
    message.error('创建实验草稿失败，请重试');
  }
};

const getFileIcon = (gb: GuidebookListItem) => {
  const t = gb.file_type?.toLowerCase();
  if (t === 'pdf') return '📄';
  if (['mp4', 'avi', 'mkv', 'mov'].includes(t)) return '🎬';
  if (t === 'md') return '📝';
  return '📎';
};

// 附件 URL 辅助
function toAbsUrl(url: string | null | undefined): string {
  if (!url) return '';
  if (url.startsWith('http')) return url;
  const base = (import.meta.env.VITE_GLOB_API_URL as string ?? 'http://127.0.0.1:8000/api').replace(/\/api\/?$/, '');
  return `${base}${url.startsWith('/') ? '' : '/'}${url}`;
}
</script>

<template>
  <div class="p-5">
    <!-- 顶部返回 -->
    <div class="mb-4 flex items-center gap-3">
      <Button :icon="h(ArrowLeftOutlined)" @click="router.push('/experiments/student')" />
      <h2 class="m-0 truncate text-xl font-semibold">
        {{ experiment?.title ?? '加载中...' }}
      </h2>
    </div>

    <Spin :spinning="loading">
      <template v-if="experiment">
        <!-- 状态栏 -->
        <Card class="mb-4" :body-style="{ padding: '16px 20px' }">
          <Row :gutter="24" align="middle">
            <Col :flex="1">
              <Space wrap>
                <Tag
                  :color="experiment.status === 'published' ? 'success' : 'purple'"
                  class="text-sm"
                >
                  {{ experiment.status === 'published' ? '进行中' : '已结束' }}
                </Tag>
                <span class="text-gray-500 text-sm">
                  截止：{{ formatDateTime(experiment.end_time) }}
                </span>
                <span
                  v-if="!isExpired && experiment.status === 'published'"
                  class="font-medium text-orange-500 text-sm"
                >
                  剩余 {{ remainingDays(experiment.end_time) }} 天
                </span>
                <span v-else-if="isExpired" class="text-red-500 text-sm">已截止</span>
              </Space>
            </Col>
            <Col>
              <Space>
                <template v-if="mySubmission">
                  <Tag :color="SUBMISSION_STATUS_COLOR[mySubmission.submission_status]">
                    {{ SUBMISSION_STATUS_LABEL[mySubmission.submission_status] }}
                  </Tag>
                  <Button
                    v-if="mySubmission.submission_status === 'graded'"
                    type="primary"
                    size="small"
                    @click="router.push(`/experiments/student/${experimentId}/grade`)"
                  >
                    查看成绩
                  </Button>
                  <Button
                    v-else-if="canSubmit || mySubmission.submission_status === 'submitted'"
                    type="primary"
                    size="small"
                    @click="handleStart"
                  >
                    {{ mySubmission.submission_status === 'draft' ? '继续实验' : '查看提交' }}
                  </Button>
                </template>
                <Button v-else-if="canSubmit" type="primary" @click="handleStart">
                  开始实验
                </Button>
              </Space>
            </Col>
          </Row>
        </Card>

        <!-- Tabs -->
        <Card>
          <Tabs v-model:active-key="activeTab">
            <!-- ─── 实验介绍 ─── -->
            <Tabs.TabPane key="intro" tab="实验介绍">
              <div class="max-w-3xl">
                <!-- 基本信息 -->
                <Descriptions :column="3" bordered size="small" class="mb-6">
                  <Descriptions.Item label="课程代码">
                    {{ experiment.course_code || '—' }}
                  </Descriptions.Item>
                  <Descriptions.Item label="难度">
                    <Tag :color="DIFFICULTY_COLOR[experiment.difficulty]">
                      {{ DIFFICULTY_LABEL[experiment.difficulty] ?? experiment.difficulty }}
                    </Tag>
                  </Descriptions.Item>
                  <Descriptions.Item label="预计时长">
                    {{ experiment.estimated_hours }} 小时
                  </Descriptions.Item>
                  <Descriptions.Item label="总分" :span="1">
                    {{ experiment.total_score }} 分
                  </Descriptions.Item>
                  <Descriptions.Item label="发布教师" :span="2">
                    {{ experiment.teacher?.name ?? '—' }}
                  </Descriptions.Item>
                </Descriptions>

                <!-- 实验描述 -->
                <section v-if="experiment.description" class="mb-6">
                  <h4 class="mb-2 flex items-center gap-2 font-semibold">
                    <FileOutlined /> 实验描述
                  </h4>
                  <div
                    class="rounded-md bg-gray-50 p-4 text-sm leading-relaxed text-gray-700"
                    style="white-space: pre-wrap"
                  >
                    {{ experiment.description }}
                  </div>
                </section>

                <!-- 实验目标 -->
                <section v-if="experiment.objectives?.length" class="mb-6">
                  <h4 class="mb-2 flex items-center gap-2 font-semibold">
                    <BookOutlined /> 实验目标
                  </h4>
                  <List size="small" bordered>
                    <List.Item v-for="(obj, idx) in experiment.objectives" :key="idx">
                      <span class="mr-2 text-blue-500">{{ idx + 1 }}.</span>{{ obj }}
                    </List.Item>
                  </List>
                </section>

                <!-- 评分标准 -->
                <section v-if="experiment.scoring_criteria && Object.keys(experiment.scoring_criteria).length" class="mb-6">
                  <h4 class="mb-2 font-semibold">📊 评分标准（总分 {{ experiment.total_score }} 分）</h4>
                  <Row :gutter="[8, 8]">
                    <Col
                      v-for="(score, name) in experiment.scoring_criteria"
                      :key="name"
                      :span="8"
                    >
                      <Card size="small" class="text-center">
                        <Statistic
                          :title="name"
                          :value="score"
                          suffix="分"
                          :value-style="{ fontSize: '18px', color: '#1677ff' }"
                        />
                      </Card>
                    </Col>
                  </Row>
                </section>

                <!-- 注意事项 -->
                <section v-if="experiment.late_submission_allowed" class="mb-6">
                  <Alert
                    type="warning"
                    show-icon
                    :message="`允许迟交，迟交将扣除 ${((experiment.late_penalty_rate ?? 0) * 100).toFixed(0)}% 分数`"
                  />
                </section>

                <!-- 开始按钮 -->
                <div class="mt-6 text-center">
                  <Button
                    v-if="canSubmit"
                    type="primary"
                    size="large"
                    style="width: 200px"
                    @click="handleStart"
                  >
                    {{ mySubmission?.submission_status === 'draft' ? '继续实验' : '开始实验' }}
                  </Button>
                  <Alert
                    v-else-if="isExpired"
                    type="error"
                    message="实验已截止，无法提交"
                    show-icon
                    class="inline-block"
                  />
                </div>
              </div>
            </Tabs.TabPane>

            <!-- ─── 指导书 ─── -->
            <Tabs.TabPane key="guide" tab="指导书">
              <div v-if="experiment.guidebooks?.length === 0" class="py-8">
                <Empty description="教师暂未上传指导书" />
              </div>
              <List v-else :data-source="experiment.guidebooks" :bordered="false">
                <template #renderItem="{ item: gb }">
                  <List.Item>
                    <List.Item.Meta>
                      <template #avatar>
                        <span class="text-2xl">{{ getFileIcon(gb) }}</span>
                      </template>
                      <template #title>
                        <span class="font-medium">{{ gb.title }}</span>
                        <Tag class="ml-2" size="small">{{ DOC_TYPE_LABEL[gb.doc_type] ?? gb.doc_type }}</Tag>
                      </template>
                      <template #description>
                        {{ gb.file_name }}
                        <span class="ml-3 text-gray-400">{{ formatFileSize(gb.file_size) }}</span>
                      </template>
                    </List.Item.Meta>
                    <Space>
                      <Button
                        size="small"
                        :icon="h(EyeOutlined)"
                        @click="handlePreview(gb)"
                      >
                        预览
                      </Button>
                      <Button
                        size="small"
                        :icon="h(DownloadOutlined)"
                        :href="getGuidebookDownloadUrl(gb.id)"
                        target="_blank"
                      >
                        下载
                      </Button>
                    </Space>
                  </List.Item>
                </template>
              </List>
            </Tabs.TabPane>

            <!-- ─── 我的报告 ─── -->
            <Tabs.TabPane key="report" tab="我的报告">
              <div v-if="!mySubmission" class="py-8 text-center">
                <Empty description="还没有提交记录" />
                <Button v-if="canSubmit" type="primary" class="mt-4" @click="handleStart">
                  开始实验
                </Button>
              </div>
              <div v-else class="max-w-2xl">
                <!-- 当前状态 -->
                <Card size="small" class="mb-4">
                  <Descriptions :column="2" size="small">
                    <Descriptions.Item label="状态">
                      <Tag :color="SUBMISSION_STATUS_COLOR[mySubmission.submission_status]">
                        {{ SUBMISSION_STATUS_LABEL[mySubmission.submission_status] }}
                      </Tag>
                    </Descriptions.Item>
                    <Descriptions.Item label="提交时间">
                      {{ formatDateTime(mySubmission.submit_time) }}
                    </Descriptions.Item>
                    <Descriptions.Item v-if="mySubmission.score !== null" label="得分">
                      <span class="font-semibold text-green-600 text-lg">
                        {{ mySubmission.score }} / {{ experiment.total_score }}
                      </span>
                    </Descriptions.Item>
                    <Descriptions.Item v-if="mySubmission.is_late" label="备注">
                      <Tag color="orange">迟交</Tag>
                    </Descriptions.Item>
                  </Descriptions>
                </Card>

                <!-- 操作 -->
                <Space class="mb-6">
                  <Button
                    v-if="(mySubmission.submission_status === 'draft' && canSubmit) || mySubmission.submission_status === 'submitted'"
                    type="primary"
                    @click="handleStart"
                  >
                    {{ mySubmission.submission_status === 'draft' ? '继续编辑报告' : '查看提交报告' }}
                  </Button>
                  <Button
                    v-if="mySubmission.submission_status === 'graded'"
                    type="primary"
                    @click="router.push(`/experiments/student/${experimentId}/grade`)"
                  >
                    查看批改成绩
                  </Button>
                </Space>
              </div>
            </Tabs.TabPane>
          </Tabs>
        </Card>
      </template>
    </Spin>

    <!-- 指导书预览弹窗 -->
    <Modal
      v-model:open="previewVisible"
      :title="previewTitle"
      :footer="null"
      width="1280px"
      style="top: 20px"
      :body-style="{ maxHeight: '85vh', overflow: 'auto', padding: previewData?.url && !previewData.html && !previewData.content ? 0 : '24px' }"
    >
      <Spin :spinning="previewLoading">
        <div v-if="previewData">
          <!-- Markdown / HTML -->
          <div
            v-if="previewData.html"
            class="prose max-w-none text-sm overflow-x-auto"
            v-html="previewData.html"
          />
          <pre
            v-else-if="previewData.content"
            class="whitespace-pre-wrap rounded bg-gray-50 p-4 text-sm"
            style="line-height: 1.6"
          >{{ previewData.content }}</pre>
          <!-- PDF / HTML file -->
          <iframe
            v-else-if="previewData.url && (previewData.type === 'pdf' || previewData.type === 'html')"
            :src="previewData.url"
            style="width: 100%; height: 85vh; border: none; margin-bottom: -5px;"
          />
          <!-- Video -->
          <video
            v-else-if="previewData.url && ['mp4', 'avi', 'mov', 'mkv'].includes(previewData.type)"
            :src="previewData.url"
            controls
            autoplay
            style="width: 100%; max-height: 85vh; background: #000; outline: none; border-bottom-left-radius: 8px; border-bottom-right-radius: 8px;"
          />
          <!-- Image -->
          <div v-else-if="previewData.url && ['jpg', 'jpeg', 'png', 'gif'].includes(previewData.type)" class="text-center p-4">
             <Image :src="previewData.url" style="max-width: 100%" />
          </div>
          <div v-else class="py-12 text-center text-gray-500 bg-white">
            <h3 class="mb-4">该文件格式不支持在线预览</h3>
            <Button type="primary" :href="previewData.url" target="_blank">
              独立下载
            </Button>
          </div>
        </div>
        <div v-else-if="!previewLoading" class="py-12 text-center text-gray-400">
          未能加载预览内容
        </div>
      </Spin>
    </Modal>
  </div>
</template>

<script lang="ts">
import { h } from 'vue';
export { h };
</script>
