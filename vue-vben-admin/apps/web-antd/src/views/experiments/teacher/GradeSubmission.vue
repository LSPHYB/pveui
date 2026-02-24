<script setup lang="ts">
import type { SubmissionDetail } from '#/api/experiment/types';

import { computed, onMounted, reactive, ref } from 'vue';

import {
  ArrowLeftOutlined,
  LeftOutlined,
  RightOutlined,
  PaperClipOutlined,
  PlayCircleOutlined,
} from '@ant-design/icons-vue';
import {
  Avatar,
  Button,
  Card,
  Col,
  Descriptions,
  Divider,
  Form,
  Image,
  Input,
  InputNumber,
  Layout,
  message,
  Modal,
  Radio,
  Row,
  Space,
  Spin,
  Statistic,
  Tag,
  Textarea,
} from 'ant-design-vue';
import { useRoute, useRouter } from 'vue-router';

import {
  getExperimentDetailApi,
  getSubmissionDetailApi,
  getSubmissionListApi,
  gradeSubmissionApi,
  returnSubmissionApi,
} from '#/api/experiment';
import { formatDateTime, SUBMISSION_STATUS_COLOR } from '../utils';
import { marked } from 'marked';

defineOptions({ name: 'SubmissionGrading' });

const router = useRouter();
const route = useRoute();

const loading = ref(false);
const submitting = ref(false);
const submission = ref<SubmissionDetail | null>(null);

// 提交列表（用于上一份/下一份导航）
const submissionList = ref<number[]>([]);
const currentIndex = ref(0);

const submissionId = computed(() => Number(route.params.id));

// 报告查看模式
const reportViewMode = ref<'preview' | 'source'>('preview');

// 渲染 Markdown 解析的 HTML
const renderedReport = computed(() => {
  if (!submission.value?.report_content) return '';
  return marked.parse(submission.value.report_content);
});

const gradeForm = reactive<{
  scoring_details: Record<string, { score: number; total: number; comment: string }>;
  feedback: string;
}>({
  scoring_details: {},
  feedback: '',
});

const totalScore = computed(() => {
  return Object.values(gradeForm.scoring_details).reduce(
    (sum, item) => sum + (item.score ?? 0),
    0,
  );
});

const quickComments = ['步骤完整', '截图清晰', '格式规范', '思路清晰', '有创新', '需改进', '命令错误', '缺少截图'];

const addQuickComment = (tag: string) => {
  gradeForm.feedback = gradeForm.feedback ? `${gradeForm.feedback}，${tag}` : tag;
};

const initScoringDetails = (exp: SubmissionDetail, experimentScoringCriteria?: Record<string, number>) => {
  gradeForm.scoring_details = {};
  gradeForm.feedback = exp.feedback ?? '';

  // 优先用单独加载的实验评分标准，其次尝试嵌套对象（experiment 为对象时）
  const criteria: Record<string, number> =
    experimentScoringCriteria ??
    (exp as any).experiment?.scoring_criteria ??
    {};

  for (const [key, total] of Object.entries(criteria)) {
    const existing = exp.scoring_details?.[key];
    gradeForm.scoring_details[key] = {
      score: existing?.score ?? 0,
      total: total as number,
      comment: existing?.comment ?? '',
    };
  }
  // 无评分模板但有已有批改记录，直接回填
  if (Object.keys(gradeForm.scoring_details).length === 0 && exp.scoring_details) {
    for (const [key, val] of Object.entries(exp.scoring_details)) {
      gradeForm.scoring_details[key] = {
        score: val.score ?? 0,
        total: val.total ?? 0,
        comment: val.comment ?? '',
      };
    }
  }
  // 兜底：仍为空时提供一个"总分"分项让教师能打分
  if (Object.keys(gradeForm.scoring_details).length === 0) {
    gradeForm.scoring_details['总分'] = { score: 0, total: 100, comment: '' };
  }
};

const loadSubmission = async (id: number | string) => {
  loading.value = true;
  try {
    const data = await getSubmissionDetailApi(id);
    submission.value = data;

    // 单独加载实验详情获取完整 scoring_criteria（experiment 字段可能只是 ID）
    const expId = (data as any).experiment ?? (data as any).experiment_info?.id;
    let scoringCriteria: Record<string, number> | undefined;
    if (expId && typeof expId === 'number') {
      try {
        const expDetail = await getExperimentDetailApi(expId);
        scoringCriteria = expDetail.scoring_criteria as Record<string, number>;
      } catch {
        // 加载失败时使用原有逻辑兜底
      }
    }

    initScoringDetails(data, scoringCriteria);
  } catch (e: any) {
    message.error('加载提交记录失败');
  } finally {
    loading.value = false;
  }
};

onMounted(async () => {
  // 加载当前
  await loadSubmission(submissionId.value);

  // 尝试加载同实验的提交列表，用于导航
  const expId = (submission.value as any)?.experiment;
  if (expId) {
    const listRes = await getSubmissionListApi({ experiment: expId, page_size: 200 });
    const list = listRes?.results ?? (Array.isArray(listRes) ? listRes : []);
    submissionList.value = list.filter((s: any) => s.submission_status !== 'draft').map((s: any) => s.id);
    currentIndex.value = submissionList.value.indexOf(submissionId.value);
  }
});

const goToSubmission = async (id: number) => {
  router.push(`/experiments/teacher/grade/${id}`);
  await loadSubmission(id);
};

const handlePrev = () => {
  if (currentIndex.value > 0) {
    currentIndex.value--;
    goToSubmission(submissionList.value[currentIndex.value]!);
  }
};

const handleNext = () => {
  if (currentIndex.value < submissionList.value.length - 1) {
    currentIndex.value++;
    goToSubmission(submissionList.value[currentIndex.value]!);
  }
};

const handleGrade = async () => {
  if (totalScore.value < 0) {
    message.warning('总分不能为负');
    return;
  }
  submitting.value = true;
  try {
    await gradeSubmissionApi(submissionId.value, {
      score: totalScore.value,
      feedback: gradeForm.feedback,
      scoring_details: gradeForm.scoring_details,
    });
    message.success('批改成功！');
    // 自动跳下一份
    if (currentIndex.value < submissionList.value.length - 1) {
      handleNext();
    } else {
      router.back();
    }
  } catch (e: any) {
    message.error(e?.message ?? '批改失败');
  } finally {
    submitting.value = false;
  }
};

// 退回修改：使用正规 Modal + ref，不依赖 document.getElementById
const showReturnModal = ref(false);
const returnReason = ref('');
const returning = ref(false);

const handleReturn = () => {
  returnReason.value = '';
  showReturnModal.value = true;
};

const confirmReturn = async () => {
  if (!returnReason.value.trim()) {
    message.warning('请填写退回原因');
    return;
  }
  returning.value = true;
  try {
    await returnSubmissionApi(submissionId.value, returnReason.value.trim());
    message.success('已退回，等待学生修改');
    showReturnModal.value = false;
    router.back();
  } catch (e: any) {
    message.error(e?.message ?? '退回失败');
  } finally {
    returning.value = false;
  }
};

// 附件 URL 辅助：处理后端可能返回的相对路径
function toAbsUrl(url: string | null | undefined): string {
  if (!url) return '';
  if (url.startsWith('http')) return url;
  const base = (import.meta.env.VITE_GLOB_API_URL as string ?? 'http://127.0.0.1:8000/api').replace(/\/api\/?$/, '');
  return `${base}${url.startsWith('/') ? '' : '/'}${url}`;
}

// 视频预览相关
const videoPreviewVisible = ref(false);
const videoPreviewUrl = ref('');
const videoPreviewTitle = ref('');

const handlePreviewVideo = (att: any) => {
  videoPreviewUrl.value = toAbsUrl(att.file_url) || '';
  videoPreviewTitle.value = att.file_name || '视频预览';
  videoPreviewVisible.value = true;
};
</script>

<template>
  <div class="p-5">
    <!-- 顶部导航 -->
    <div class="mb-4 flex items-center justify-between">
      <Space>
        <Button :icon="h(ArrowLeftOutlined)" @click="router.back()">返回</Button>
        <span class="text-gray-500">
          批改作业
          <template v-if="submission">/ {{ submission.student.name }}</template>
        </span>
      </Space>
      <Space v-if="submissionList.length > 0">
        <Button :icon="h(LeftOutlined)" :disabled="currentIndex <= 0" @click="handlePrev">上一份</Button>
        <span class="px-2 text-gray-500">{{ currentIndex + 1 }} / {{ submissionList.length }}</span>
        <Button
          :icon="h(RightOutlined)"
          :disabled="currentIndex >= submissionList.length - 1"
          @click="handleNext"
        >
          下一份
        </Button>
      </Space>
    </div>

    <Spin :spinning="loading">
      <Layout v-if="submission">
        <!-- 左侧：学生报告 -->
        <Layout.Content style="margin-right: 16px">
          <Card>
            <template #title>
              <Space>
                <Avatar style="background-color: #1677ff">
                  {{ submission.student.name?.[0] ?? 'S' }}
                </Avatar>
                <span>{{ submission.student.name }}的实验报告</span>
              </Space>
            </template>
            <template #extra>
              <Space>
                <Tag v-if="submission.is_late" color="error">迟交</Tag>
                <Tag :color="SUBMISSION_STATUS_COLOR[submission.submission_status]">
                  {{ submission.submission_status === 'submitted' ? '待批改' : '已批改' }}
                </Tag>
                <span class="text-gray-500 text-sm">
                  提交于 {{ formatDateTime(submission.submit_time) }}
                </span>
              </Space>
            </template>

            <!-- 实验环境 -->
            <Descriptions :column="3" size="small" bordered class="mb-4">
              <Descriptions.Item label="虚拟机">
                {{ submission.vm_info?.vm_name ?? '—' }}
              </Descriptions.Item>
              <Descriptions.Item label="VMID">
                {{ submission.vm_info?.vmid ?? '—' }}
              </Descriptions.Item>
              <Descriptions.Item label="IP 地址">
                {{ submission.vm_info?.ip ?? '—' }}
              </Descriptions.Item>
            </Descriptions>

            <!-- 报告正文 -->
            <div class="mb-2 flex items-center justify-between">
              <h3 class="m-0 text-base font-semibold">{{ submission.report_title || '（无标题）' }}</h3>
              <Radio.Group v-model:value="reportViewMode" size="small" button-style="solid">
                <Radio.Button value="preview">渲染视图</Radio.Button>
                <Radio.Button value="source">源码视图</Radio.Button>
              </Radio.Group>
            </div>
            <!-- 渲染模式 -->
            <div
              v-if="reportViewMode === 'preview'"
              class="report-content max-h-[500px] overflow-y-auto overflow-x-auto rounded-md bg-gray-50 p-4 min-h-[100px] prose prose-sm max-w-none"
              v-html="renderedReport || '（无内容）'"
            ></div>
            <!-- 源码模式 -->
            <div
              v-else
              class="report-content max-h-[500px] overflow-y-auto overflow-x-auto rounded-md bg-gray-50 p-4 text-sm whitespace-pre-wrap leading-relaxed"
            >
              {{ submission.report_content || '（无内容）' }}
            </div>

            <!-- 附件 -->
            <Divider>操作截图 / 录屏（{{ submission.attachments?.length ?? 0 }} 个）</Divider>
            <Row :gutter="[12, 12]">
              <Col
                v-for="att in submission.attachments"
                :key="att.id"
                :xs="12"
                :sm="8"
                :md="6"
              >
                <Card size="small" hoverable>
                  <div class="mb-2 overflow-hidden rounded" style="height: 120px; background: #f5f5f5; display: flex; align-items: center; justify-content: center">
                    <!-- 有略缩图或直接是图片 -->
                    <Image
                      v-if="att.thumbnail_url || (att.file_type && att.file_type.startsWith('image/')) || /\.(jpg|jpeg|png|gif|webp)$/i.test(att.file_name)"
                      :src="toAbsUrl(att.thumbnail_url || att.file_url)"
                      :alt="att.file_name"
                      style="width: 100%; height: 100%; object-fit: cover"
                      :preview="{ src: toAbsUrl(att.file_url) }"
                    />
                    <!-- 视频类型 fallback -->
                    <a
                      v-else-if="(att.file_type && att.file_type.startsWith('video/')) || /\.(mp4|avi|mov|mkv)$/i.test(att.file_name)"
                      href="javascript:;"
                      @click="handlePreviewVideo(att)"
                      class="flex h-full w-full flex-col items-center justify-center text-blue-500 hover:bg-black/5"
                    >
                      <PlayCircleOutlined style="font-size: 28px" />
                      <span class="mt-1 text-xs text-gray-400 truncate w-full text-center px-2">播放视频</span>
                    </a>
                    <!-- 普通文件 fallback -->
                    <a
                      v-else
                      :href="toAbsUrl(att.file_url)"
                      target="_blank"
                      class="flex h-full w-full flex-col items-center justify-center text-gray-500 hover:bg-black/5"
                    >
                      <PaperClipOutlined style="font-size: 24px" />
                      <span class="mt-1 text-xs truncate w-full text-center px-1">点击查看</span>
                    </a>
                  </div>
                  <p class="mt-1 truncate text-xs text-gray-500" :title="att.description">
                    {{ att.description || att.file_name }}
                  </p>
                  <Tag v-if="att.step_number" size="small">步骤 {{ att.step_number }}</Tag>
                </Card>
              </Col>
            </Row>
          </Card>
        </Layout.Content>

        <!-- 右侧：评分面板 -->
        <Layout.Sider :width="420" style="background: transparent">
          <!-- 分项评分 -->
          <Card title="分项评分" class="mb-4">
            <Form layout="vertical">
              <div
                v-for="(item, key) in gradeForm.scoring_details"
                :key="key"
                class="mb-4 rounded-md bg-gray-50 p-3"
              >
                <div class="mb-2 flex items-center justify-between">
                  <span class="font-medium">{{ key }}</span>
                  <span class="text-gray-400 text-sm">满分 {{ item.total }} 分</span>
                </div>
                <div class="flex gap-2">
                  <InputNumber
                    v-model:value="(gradeForm.scoring_details[key] as any).score"
                    :min="0"
                    :max="item.total"
                    :addon-after="'分'"
                    style="width: 130px"
                  />
                  <Input
                    v-model:value="(gradeForm.scoring_details[key] as any).comment"
                    placeholder="评语（可选）"
                  />
                </div>
              </div>

              <Divider />

              <Statistic
                title="总分"
                :value="totalScore"
                :suffix="`/ ${submission.experiment_info?.title ? 100 : '—'}`"
                :value-style="{ color: totalScore >= 60 ? '#52c41a' : '#ff4d4f', fontSize: '28px' }"
              />
            </Form>
          </Card>

          <!-- 总体评语 -->
          <Card title="总体评语" class="mb-4">
            <Textarea
              v-model:value="gradeForm.feedback"
              :rows="5"
              placeholder="请给出总体评价和建议..."
            />
            <div class="mt-2 flex flex-wrap gap-1">
              <Tag
                v-for="tag in quickComments"
                :key="tag"
                class="cursor-pointer"
                @click="addQuickComment(tag)"
              >
                {{ tag }}
              </Tag>
            </div>
          </Card>

          <!-- 操作按钮 -->
          <Space direction="vertical" style="width: 100%">
            <Button type="primary" block :loading="submitting" @click="handleGrade">
              提交批改
            </Button>
            <Button block @click="handleReturn">退回修改</Button>
          </Space>
        </Layout.Sider>
      </Layout>

      <div v-else-if="!loading" class="py-16 text-center text-gray-400">
        未找到提交记录
      </div>
    </Spin>

    <!-- 退回修改 Modal -->
    <Modal
      v-model:open="showReturnModal"
      title="退回修改"
      ok-text="确认退回"
      cancel-text="取消"
      :confirm-loading="returning"
      @ok="confirmReturn"
    >
      <p class="mb-2">请输入退回原因（将发送给学生）：</p>
      <Textarea
        v-model:value="returnReason"
        :rows="4"
        placeholder="如：报告内容不完整，请补充步骤3的截图"
      />
    </Modal>

    <!-- 视频预览弹窗 -->
    <Modal
      v-model:open="videoPreviewVisible"
      :title="videoPreviewTitle"
      :footer="null"
      width="1080px"
      style="top: 20px"
      :destroy-on-close="true"
      :body-style="{ padding: 0 }"
    >
      <video
        v-if="videoPreviewUrl"
        :src="videoPreviewUrl"
        controls
        autoplay
        style="width: 100%; max-height: 80vh; background: #000; outline: none; border-bottom-left-radius: 8px; border-bottom-right-radius: 8px;"
      />
    </Modal>
  </div>
</template>

<script lang="ts">
import { h } from 'vue';
export { h };
</script>
