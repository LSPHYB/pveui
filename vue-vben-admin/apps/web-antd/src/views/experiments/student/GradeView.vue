<script setup lang="ts">
import type { SubmissionDetail } from '#/api/experiment/types';

import { computed, onMounted, ref } from 'vue';

import { ArrowLeftOutlined, TrophyOutlined } from '@ant-design/icons-vue';
import {
  Alert,
  Button,
  Card,
  Col,
  Descriptions,
  Image,
  Progress,
  Row,
  Spin,
  Tag,
  message,
} from 'ant-design-vue';
import { useRoute, useRouter } from 'vue-router';

import { getExperimentDetailApi, getMySubmissionApi } from '#/api/experiment';
import { formatDateTime } from '../utils';

defineOptions({ name: 'StudentGradeView' });

const router = useRouter();
const route = useRoute();
const experimentId = route.params.id as string;

const loading = ref(false);
const submission = ref<SubmissionDetail | null>(null);
const experimentTitle = ref('');
const totalScore = ref(100);

const score = computed(() => submission.value?.score ?? 0);

const gradeLabel = computed(() => {
  const s = score.value;
  if (s >= 90) return { label: '优秀', color: '#52c41a' };
  if (s >= 80) return { label: '良好', color: '#1677ff' };
  if (s >= 70) return { label: '中等', color: '#faad14' };
  if (s >= 60) return { label: '及格', color: '#fa8c16' };
  return { label: '不及格', color: '#ff4d4f' };
});

const scorePercent = computed(() => {
  if (!totalScore.value) return 0;
  return Math.round((score.value / totalScore.value) * 100);
});

const loadData = async () => {
  loading.value = true;
  try {
    // 加载实验信息
    const exp = await getExperimentDetailApi(experimentId);
    experimentTitle.value = exp.title;
    totalScore.value = exp.total_score;

    // 加载我的提交
    const sub = await getMySubmissionApi(experimentId);
    submission.value = sub;
  } catch (e: any) {
    message.error('加载成绩信息失败');
  } finally {
    loading.value = false;
  }
};

onMounted(loadData);
</script>

<template>
  <div class="p-5">
    <!-- 返回 -->
    <div class="mb-5 flex items-center gap-3">
      <Button
        :icon="h(ArrowLeftOutlined)"
        @click="router.push(`/experiments/student/${experimentId}`)"
      />
      <h2 class="m-0 text-xl font-semibold">成绩单</h2>
    </div>

    <Spin :spinning="loading">
      <template v-if="submission">
        <!-- ─── 总分展示 ─── -->
        <Card class="mb-5 text-center" :body-style="{ padding: '32px 24px' }">
          <div class="mb-2 text-base text-gray-500">{{ experimentTitle }}</div>
          <div class="mb-4 flex items-center justify-center gap-4">
            <TrophyOutlined
              :style="{ fontSize: '48px', color: gradeLabel.color }"
            />
            <div>
              <div :style="{ fontSize: '52px', fontWeight: 700, color: gradeLabel.color, lineHeight: 1 }">
                {{ score }}
              </div>
              <div class="text-gray-400 text-sm">/ {{ totalScore }}</div>
            </div>
          </div>

          <Tag
            :color="gradeLabel.color"
            style="font-size: 16px; padding: 4px 16px; border-radius: 99px"
          >
            {{ gradeLabel.label }}
          </Tag>

          <div class="mx-auto mt-5 max-w-sm">
            <Progress
              :percent="scorePercent"
              :stroke-color="gradeLabel.color"
              :trail-color="'#f0f0f0'"
              stroke-linecap="round"
              :format="(p?: number) => `${p ?? 0}%`"
            />
          </div>

          <Descriptions :column="3" class="mt-5" size="small">
            <Descriptions.Item label="提交时间">
              {{ formatDateTime(submission.submit_time) }}
            </Descriptions.Item>
            <Descriptions.Item label="批改时间">
              {{ formatDateTime(submission.graded_at) }}
            </Descriptions.Item>
            <Descriptions.Item label="迟交">
              <Tag v-if="submission.is_late" color="orange">是</Tag>
              <span v-else class="text-gray-400">否</span>
            </Descriptions.Item>
          </Descriptions>
        </Card>

        <!-- ─── 分项明细 ─── -->
        <Card
          v-if="Object.keys(submission.scoring_details ?? {}).length > 0"
          title="📊 分项明细"
          class="mb-5"
        >
          <Row :gutter="[16, 16]">
            <Col
              v-for="(detail, name) in submission.scoring_details"
              :key="name"
              :xs="24"
              :sm="12"
              :md="8"
            >
              <Card size="small" :body-style="{ padding: '14px 16px' }">
                <div class="mb-2 flex items-center justify-between">
                  <span class="font-medium text-sm">{{ name }}</span>
                  <span
                    class="font-bold text-base"
                    :style="{ color: detail.score >= detail.total * 0.6 ? '#52c41a' : '#ff4d4f' }"
                  >
                    {{ detail.score }} / {{ detail.total }}
                  </span>
                </div>
                <Progress
                  :percent="detail.total ? Math.round((detail.score / detail.total) * 100) : 0"
                  :stroke-color="detail.score >= detail.total * 0.6 ? '#52c41a' : '#ff4d4f'"
                  size="small"
                  :show-info="false"
                />
                <p v-if="detail.comment" class="mt-2 text-xs text-gray-500 italic">
                  「{{ detail.comment }}」
                </p>
              </Card>
            </Col>
          </Row>
        </Card>

        <!-- ─── 教师总评 ─── -->
        <Card v-if="submission.feedback" title="💬 教师总评" class="mb-5">
          <div
            class="rounded-md bg-blue-50 p-4 text-sm leading-relaxed text-gray-700"
            style="white-space: pre-wrap; border-left: 4px solid #1677ff"
          >
            {{ submission.feedback }}
          </div>
          <div class="mt-3 text-right text-xs text-gray-400">
            — {{ submission.graded_by?.name ?? '教师' }}，{{ formatDateTime(submission.graded_at) }}
          </div>
        </Card>

        <!-- ─── 我的报告附件概览 ─── -->
        <Card
          v-if="submission.attachments?.length > 0"
          title="📎 我的截图附件"
          class="mb-5"
        >
          <Row :gutter="[12, 12]">
            <Col
              v-for="att in submission.attachments"
              :key="att.id"
              :xs="12"
              :sm="8"
              :md="6"
            >
              <div class="overflow-hidden rounded-md border" style="border-color: #e8e8e8">
                <Image
                  v-if="att.thumbnail_url"
                  :src="att.thumbnail_url"
                  :alt="att.file_name"
                  style="width: 100%; height: 100px; object-fit: cover"
                  :preview="{ src: att.file_url }"
                />
                <div v-else class="flex h-24 items-center justify-center bg-gray-100 text-gray-400 text-sm">
                  {{ att.file_type?.toUpperCase() }}
                </div>
                <div class="px-2 py-1 text-xs text-gray-500 truncate">
                  {{ att.description || att.file_name }}
                </div>
              </div>
            </Col>
          </Row>
        </Card>

        <!-- ─── 底部操作 ─── -->
        <div class="flex justify-center">
          <Button
            type="primary"
            @click="router.push(`/experiments/student/${experimentId}`)"
          >
            返回实验详情
          </Button>
        </div>
      </template>

      <!-- 未批改 -->
      <div v-else-if="!loading">
        <Alert
          type="info"
          message="成绩尚未发布，请耐心等待教师批改"
          show-icon
          class="mb-4"
        />
        <div class="text-center">
          <Button @click="router.push(`/experiments/student/${experimentId}`)">
            返回实验详情
          </Button>
        </div>
      </div>
    </Spin>
  </div>
</template>

<script lang="ts">
import { h } from 'vue';
export { h };
</script>
