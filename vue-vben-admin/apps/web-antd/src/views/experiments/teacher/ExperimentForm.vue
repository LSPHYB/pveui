<script setup lang="ts">
import type { FormInstance } from 'ant-design-vue';

import type { CreateExperimentPayload } from '#/api/experiment/types';

import { computed, onMounted, reactive, ref } from 'vue';

import {
  ArrowLeftOutlined,
  DeleteOutlined,
  MinusCircleOutlined,
  PlusOutlined,
  UploadOutlined,
} from '@ant-design/icons-vue';
import {
  Alert,
  Button,
  Card,
  Checkbox,
  Col,
  DatePicker,
  Descriptions,
  Divider,
  Form,
  Input,
  InputNumber,
  message,
  Modal,
  Row,
  Select,
  Space,
  Steps,
  Table,
  Tag,
  Textarea,
  Upload,
} from 'ant-design-vue';
import { useRoute, useRouter } from 'vue-router';

import {
  createExperimentApi,
  deleteGuidebookApi,
  getExperimentDetailApi,
  publishExperimentApi,
  updateExperimentApi,
  uploadGuidebookApi,
} from '#/api/experiment';
import { CATEGORY_LABEL, DIFFICULTY_LABEL, DOC_TYPE_LABEL, formatDateTime } from '../utils';

defineOptions({ name: 'ExperimentForm' });

const router = useRouter();
const route = useRoute();

const isEdit = computed(() => !!route.params.id);
const viewMode = computed(() => route.query.mode === 'view');
const experimentId = ref<number | string>(route.params.id as string || '');

const currentStep = ref(0);
const saving = ref(false);
const formRef = ref<FormInstance>();

// ─────────── 表单数据 ───────────
const form = reactive<CreateExperimentPayload & { objectives: string[] }>({
  title: '',
  course_code: '',
  description: '',
  objectives: [''],
  category: 'linux',
  difficulty: 'medium',
  estimated_hours: 2,
  start_time: '',
  end_time: '',
  late_submission_allowed: false,
  late_penalty_rate: 0.1,
  required_resources: {},
  pve_template_id: '',
  total_score: 100,
  scoring_criteria: { '基础操作': 40, '问题回答': 30, '操作截图': 30 },
  status: 'draft',
  is_active: true,
  remark: '',
});

// 评分标准（UI 用数组操作）
const scoringItems = ref<Array<{ name: string; score: number }>>([
  { name: '基础操作', score: 40 },
  { name: '问题回答', score: 30 },
  { name: '操作截图', score: 30 },
]);

const totalScoringScore = computed(() =>
  scoringItems.value.reduce((s, i) => s + (i.score || 0), 0),
);

// 指导书文件列表（step2 用于显示已创建实验的文档）
const guidebooks = ref<any[]>([]);
const uploadingGuide = ref(false);
const pendingUpload = ref<{
  file: File;
  title: string;
  doc_type: string;
  description: string;
  is_public: boolean;
} | null>(null);
const showUploadModal = ref(false);
const uploadForm = reactive({ title: '', doc_type: 'guide', description: '', is_public: true });

// 加载编辑数据
onMounted(async () => {
  if (isEdit.value && experimentId.value) {
    try {
      const detail = await getExperimentDetailApi(experimentId.value);
      form.title = detail.title;
      form.course_code = detail.course_code;
      form.description = detail.description;
      form.objectives = detail.objectives?.length ? detail.objectives : [''];
      form.category = detail.category;
      form.difficulty = detail.difficulty;
      form.estimated_hours = detail.estimated_hours;
      form.late_submission_allowed = detail.late_submission_allowed;
      form.late_penalty_rate = detail.late_penalty_rate;
      form.total_score = detail.total_score;
      form.scoring_criteria = detail.scoring_criteria ?? {};
      form.status = detail.status;
      form.is_active = detail.is_active;
      form.pve_template_id = detail.pve_template_id;

      if (detail.start_time) form.start_time = detail.start_time;
      if (detail.end_time) form.end_time = detail.end_time;

      // 转换评分标准为数组
      scoringItems.value = Object.entries(detail.scoring_criteria ?? {}).map(([name, score]) => ({
        name,
        score: score as number,
      }));

      guidebooks.value = detail.guidebooks ?? [];
    } catch (e) {
      message.error('加载实验信息失败');
    }
  }
  // 只读预览模式：直接跳到摘要步骤
  if (viewMode.value) {
    currentStep.value = 3;
  }
});

// ─────────── 步骤1：目标 ───────────
const addObjective = () => form.objectives.push('');
const removeObjective = (i: number) => form.objectives.splice(i, 1);

// ─────────── 步骤3：评分 ───────────
const addScoringItem = () => scoringItems.value.push({ name: '', score: 0 });
const removeScoringItem = (i: number) => scoringItems.value.splice(i, 1);

const buildScoringCriteria = () => {
  const criteria: Record<string, number> = {};
  for (const item of scoringItems.value) {
    if (item.name) criteria[item.name] = item.score;
  }
  return criteria;
};

// ─────────── 保存/发布 ───────────
const buildPayload = (): CreateExperimentPayload => ({
  ...form,
  objectives: form.objectives.filter(Boolean),
  scoring_criteria: buildScoringCriteria(),
});

const saveOrCreate = async (status: 'draft' | 'published' = 'draft') => {
  saving.value = true;
  try {
    const payload = { ...buildPayload(), status };
    if (isEdit.value && experimentId.value) {
      await updateExperimentApi(experimentId.value, payload);
      message.success('更新成功');
    } else {
      const result = await createExperimentApi(payload);
      experimentId.value = result.id;
      message.success('创建成功');
    }
    return true;
  } catch (e: any) {
    // RequestClient 抛出的是 response.data（{code, message}），直接取 e.message
    message.error(e?.message ?? '保存失败');
    return false;
  } finally {
    saving.value = false;
  }
};

const handleSaveDraft = async () => {
  if (await saveOrCreate('draft')) {
    router.push('/experiments/teacher');
  }
};

const handlePublish = async () => {
  // 发布前先保存一次，确保最新的评分标准、表单数据已入库
  const saved = await saveOrCreate('draft');
  if (!saved) return;

  saving.value = true;
  try {
    await publishExperimentApi(experimentId.value);
    message.success('实验已发布！');
    router.push('/experiments/teacher');
  } catch (e: any) {
    message.error(e?.message ?? '发布失败，请检查是否已上传指导书');
  } finally {
    saving.value = false;
  }
};

const nextStep = async () => {
  if (currentStep.value === 0) {
    // 步骤0：校验表单后保存（获取 experimentId）
    try {
      await formRef.value?.validate();
    } catch {
      return;
    }
  }
  // 每步切换都保存，确保最新数据（尤其是评分标准）在发布前已入库
  const ok = await saveOrCreate('draft');
  if (!ok) return;
  currentStep.value++;
};

// ─────────── 指导书上传 ───────────
const beforeUpload = (file: File) => {
  pendingUpload.value = { file, title: file.name, doc_type: 'guide', description: '', is_public: true };
  uploadForm.title = file.name;
  uploadForm.doc_type = 'guide';
  uploadForm.description = '';
  uploadForm.is_public = true;
  showUploadModal.value = true;
  return false; // 阻止自动上传
};

const handleUploadConfirm = async () => {
  if (!pendingUpload.value || !experimentId.value) return;
  uploadingGuide.value = true;
  try {
    const fd = new FormData();
    fd.append('file', pendingUpload.value.file);
    fd.append('title', uploadForm.title || pendingUpload.value.file.name);
    fd.append('doc_type', uploadForm.doc_type);
    fd.append('description', uploadForm.description);
    fd.append('is_public', String(uploadForm.is_public));
    const result = await uploadGuidebookApi(experimentId.value, fd);
    guidebooks.value.push(result);
    showUploadModal.value = false;
    message.success('上传成功');
  } catch (e: any) {
    message.error(e?.message ?? '上传失败');
  } finally {
    uploadingGuide.value = false;
  }
};

const handleDeleteGuidebook = async (id: number, idx: number) => {
  try {
    await deleteGuidebookApi(id);
    guidebooks.value.splice(idx, 1);
    message.success('已删除');
  } catch {
    message.error('删除失败');
  }
};

const guidebookColumns = [
  { title: '标题', dataIndex: 'title' },
  { title: '类型', dataIndex: 'doc_type', width: 100 },
  { title: '文件名', dataIndex: 'file_name' },
  { title: '操作', key: 'action', width: 80 },
];
</script>

<template>
  <div class="p-5">
    <!-- 页头 -->
    <div class="mb-6 flex items-center gap-3">
      <Button :icon="h(ArrowLeftOutlined)" @click="router.push('/experiments/teacher')" />
      <h2 class="m-0 text-xl font-semibold">
        {{ viewMode ? '实验详情' : (isEdit ? '编辑实验' : '创建实验') }}
      </h2>
    </div>

    <!-- 步骤条（只读模式下隐藏） -->
    <Steps v-if="!viewMode" :current="currentStep" class="mb-6">
      <Steps.Step title="基本信息" />
      <Steps.Step title="上传指导书" />
      <Steps.Step title="评分设置" />
      <Steps.Step title="预览发布" />
    </Steps>

    <Card>
      <!-- ───── Step 0: 基本信息 ───── -->
      <div v-show="currentStep === 0">
        <Form ref="formRef" :model="form" layout="vertical">
          <Form.Item
            label="实验标题"
            name="title"
            :rules="[{ required: true, message: '请输入实验标题' }]"
          >
            <Input v-model:value="form.title" placeholder="如：Linux 用户和权限管理实验" />
          </Form.Item>

          <Row :gutter="16">
            <Col :span="12">
              <Form.Item label="课程代码">
                <Input v-model:value="form.course_code" placeholder="如：CS101-EXP02" />
              </Form.Item>
            </Col>
            <Col :span="12">
              <Form.Item
                label="分类"
                name="category"
                :rules="[{ required: true, message: '请选择分类' }]"
              >
                <Select v-model:value="form.category" style="width: 100%">
                  <Select.Option value="linux">Linux 系统</Select.Option>
                  <Select.Option value="network">网络技术</Select.Option>
                  <Select.Option value="virtualization">虚拟化</Select.Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Form.Item label="实验描述">
            <Textarea v-model:value="form.description" :rows="4" placeholder="实验背景和要求..." />
          </Form.Item>

          <Form.Item label="实验目标">
            <div
              v-for="(_, idx) in form.objectives"
              :key="idx"
              class="mb-2 flex items-center gap-2"
            >
              <Input v-model:value="form.objectives[idx]" placeholder="输入实验目标" />
              <Button
                type="text"
                danger
                :icon="h(MinusCircleOutlined)"
                @click="removeObjective(idx)"
              />
            </div>
            <Button type="dashed" :icon="h(PlusOutlined)" @click="addObjective">
              添加目标
            </Button>
          </Form.Item>

          <Row :gutter="16">
            <Col :span="8">
              <Form.Item label="难度">
                <Select v-model:value="form.difficulty" style="width: 100%">
                  <Select.Option value="easy">简单</Select.Option>
                  <Select.Option value="medium">中等</Select.Option>
                  <Select.Option value="hard">困难</Select.Option>
                </Select>
              </Form.Item>
            </Col>
            <Col :span="8">
              <Form.Item label="预计时长（小时）">
                <InputNumber
                  v-model:value="form.estimated_hours"
                  :min="0.5"
                  :step="0.5"
                  style="width: 100%"
                />
              </Form.Item>
            </Col>
            <Col :span="8">
              <Form.Item label="总分">
                <InputNumber v-model:value="form.total_score" :min="0" :max="200" style="width: 100%" />
              </Form.Item>
            </Col>
          </Row>

          <Row :gutter="16">
            <Col :span="12">
              <Form.Item
                label="开始时间"
                name="start_time"
                :rules="[{ required: true, message: '请选择开始时间' }]"
              >
                <DatePicker
                  v-model:value="form.start_time"
                  value-format="YYYY-MM-DDTHH:mm:ssZ"
                  show-time
                  style="width: 100%"
                  placeholder="选择开始时间"
                />
              </Form.Item>
            </Col>
            <Col :span="12">
              <Form.Item
                label="截止时间"
                name="end_time"
                :rules="[{ required: true, message: '请选择截止时间' }]"
              >
                <DatePicker
                  v-model:value="form.end_time"
                  value-format="YYYY-MM-DDTHH:mm:ssZ"
                  show-time
                  style="width: 100%"
                  placeholder="选择截止时间"
                />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item label="迟交设置">
            <Space align="center">
              <Checkbox v-model:checked="form.late_submission_allowed">允许迟交</Checkbox>
              <template v-if="form.late_submission_allowed">
                <span>扣分比例：</span>
                <InputNumber
                  v-model:value="form.late_penalty_rate"
                  :min="0"
                  :max="1"
                  :step="0.05"
                  :formatter="(v: number | string) => `${(Number(v) * 100).toFixed(0)}%`"
                  :parser="(v: string) => Number(v.replace('%', '')) / 100"
                  style="width: 100px"
                />
              </template>
            </Space>
          </Form.Item>

          <Form.Item label="PVE 推荐模板 ID（可选）">
            <Input v-model:value="form.pve_template_id" placeholder="如：ubuntu-22.04-template" />
          </Form.Item>
        </Form>
      </div>

      <!-- ───── Step 1: 上传指导书 ───── -->
      <div v-show="currentStep === 1">
        <Alert
          v-if="!experimentId"
          type="warning"
          class="mb-4"
          show-icon
        >
          <template #message>
            <span>请先完成基本信息并保存，才能上传指导书。</span>
            <Button
              type="link"
              size="small"
              :loading="saving"
              style="padding: 0 4px"
              @click="saveOrCreate('draft')"
            >
              点击重新保存
            </Button>
          </template>
        </Alert>

        <Upload
          v-if="experimentId"
          :before-upload="beforeUpload"
          :show-upload-list="false"
          accept=".pdf,.doc,.docx,.md,.mp4,.avi"
          class="mb-4 block"
        >
          <Button type="primary" :icon="h(UploadOutlined)" :loading="uploadingGuide">
            上传指导文档
          </Button>
          <span class="ml-2 text-gray-400 text-sm">支持 PDF、Word、Markdown、视频</span>
        </Upload>

        <Table
          :data-source="guidebooks"
          :columns="guidebookColumns"
          :pagination="false"
          size="small"
          row-key="id"
        >
          <template #bodyCell="{ column, record, index }">
            <template v-if="column.dataIndex === 'doc_type'">
              <Tag>{{ DOC_TYPE_LABEL[record.doc_type] ?? record.doc_type }}</Tag>
            </template>
            <template v-else-if="column.key === 'action'">
              <Button
                type="link"
                danger
                size="small"
                :icon="h(DeleteOutlined)"
                @click="handleDeleteGuidebook(record.id, index)"
              />
            </template>
          </template>
        </Table>

        <div v-if="guidebooks.length === 0" class="py-8 text-center text-gray-400">
          暂无指导书，请上传
        </div>
      </div>

      <!-- ───── Step 2: 评分设置 ───── -->
      <div v-show="currentStep === 2">
        <Alert
          type="info"
          message="设置各评分项目及分值，批改时教师可对每项给出评语"
          class="mb-4"
          show-icon
        />

        <div
          v-for="(item, idx) in scoringItems"
          :key="idx"
          class="mb-3 flex items-center gap-3"
        >
          <span class="w-6 shrink-0 text-gray-400">{{ idx + 1 }}.</span>
          <Input
            v-model:value="item.name"
            placeholder="评分项名称，如：基础操作"
            style="width: 220px"
          />
          <InputNumber
            v-model:value="item.score"
            :min="0"
            :max="form.total_score"
            :addon-after="'分'"
            style="width: 130px"
          />
          <Button
            type="text"
            danger
            :icon="h(MinusCircleOutlined)"
            @click="removeScoringItem(idx)"
          />
        </div>

        <Button type="dashed" :icon="h(PlusOutlined)" class="mb-4" @click="addScoringItem">
          添加评分项
        </Button>

        <Divider />
        <div class="text-base">
          总分预览：
          <span
            :class="[
              'font-bold',
              totalScoringScore === form.total_score ? 'text-green-500' : 'text-orange-500',
            ]"
          >
            {{ totalScoringScore }}
          </span>
          <span class="text-gray-400"> / {{ form.total_score }} 分</span>
          <span v-if="totalScoringScore !== form.total_score" class="ml-2 text-orange-400 text-sm">
            （建议与总分相同）
          </span>
        </div>
      </div>

      <!-- ───── Step 3: 预览发布 ───── -->
      <div v-show="currentStep === 3">
        <Descriptions :column="2" bordered>
          <Descriptions.Item label="实验标题">{{ form.title }}</Descriptions.Item>
          <Descriptions.Item label="课程代码">{{ form.course_code || '—' }}</Descriptions.Item>
          <Descriptions.Item label="分类">{{ CATEGORY_LABEL[form.category] ?? form.category }}</Descriptions.Item>
          <Descriptions.Item label="难度">{{ DIFFICULTY_LABEL[form.difficulty ?? 'medium'] }}</Descriptions.Item>
          <Descriptions.Item label="开始时间">{{ form.start_time ? formatDateTime(form.start_time) : '—' }}</Descriptions.Item>
          <Descriptions.Item label="截止时间">{{ form.end_time ? formatDateTime(form.end_time) : '—' }}</Descriptions.Item>
          <Descriptions.Item label="总分">{{ form.total_score }} 分</Descriptions.Item>
          <Descriptions.Item label="预计时长">{{ form.estimated_hours }} 小时</Descriptions.Item>
          <Descriptions.Item label="指导书数量">{{ guidebooks.length }} 个</Descriptions.Item>
          <Descriptions.Item label="允许迟交">
            {{ form.late_submission_allowed ? `是（扣 ${(form.late_penalty_rate ?? 0) * 100}%）` : '否' }}
          </Descriptions.Item>
          <Descriptions.Item label="评分标准" :span="2">
            <Space wrap>
              <Tag v-for="item in scoringItems" :key="item.name" color="blue">
                {{ item.name }}：{{ item.score }} 分
              </Tag>
            </Space>
          </Descriptions.Item>
        </Descriptions>
      </div>

      <!-- 底部按钮 -->
      <Divider />
      <div class="flex justify-between">
        <!-- 只读模式：只显示返回和去编辑 -->
        <template v-if="viewMode">
          <div />
          <Space>
            <Button @click="router.push('/experiments/teacher')">返回列表</Button>
            <Button
              type="primary"
              @click="router.push(`/experiments/teacher/edit/${experimentId}`)"
            >
              去编辑
            </Button>
          </Space>
        </template>
        <!-- 编辑/创建模式：正常步骤按钮 -->
        <template v-else>
          <Button v-if="currentStep > 0" @click="currentStep--">上一步</Button>
          <div v-else />
          <Space>
            <Button @click="router.push('/experiments/teacher')">取消</Button>
            <Button v-if="currentStep < 3" type="primary" :loading="saving" @click="nextStep">
              下一步
            </Button>
            <template v-else>
              <Button :loading="saving" @click="handleSaveDraft">保存草稿</Button>
              <Button type="primary" :loading="saving" @click="handlePublish">发布实验</Button>
            </template>
          </Space>
        </template>
      </div>
    </Card>

    <!-- 上传指导书 Modal -->
    <Modal
      v-model:open="showUploadModal"
      title="设置文档信息"
      ok-text="确认上传"
      cancel-text="取消"
      :confirm-loading="uploadingGuide"
      @ok="handleUploadConfirm"
    >
      <Form layout="vertical">
        <Form.Item label="文档标题">
          <Input v-model:value="uploadForm.title" />
        </Form.Item>
        <Form.Item label="文档类型">
          <Select v-model:value="uploadForm.doc_type" style="width: 100%">
            <Select.Option value="guide">指导书</Select.Option>
            <Select.Option value="reference">参考资料</Select.Option>
            <Select.Option value="video">视频教程</Select.Option>
          </Select>
        </Form.Item>
        <Form.Item label="描述（可选）">
          <Textarea v-model:value="uploadForm.description" :rows="2" />
        </Form.Item>
        <Form.Item label="对学生公开">
          <Checkbox v-model:checked="uploadForm.is_public" />
        </Form.Item>
      </Form>
    </Modal>
  </div>
</template>

<script lang="ts">
import { h } from 'vue';
export { h };
</script>
