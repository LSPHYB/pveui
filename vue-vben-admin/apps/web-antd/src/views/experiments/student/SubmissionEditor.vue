<script setup lang="ts">
import type { AttachmentItem, GuidebookListItem, SubmissionDetail } from '#/api/experiment/types';

import {
  computed,
  onBeforeUnmount,
  onMounted,
  ref,
  watch,
} from 'vue';

import {
  ArrowLeftOutlined,
  DeleteOutlined,
  PaperClipOutlined,
  PlayCircleOutlined,
  SendOutlined,
  SaveOutlined,
  UploadOutlined,
} from '@ant-design/icons-vue';
import {
  Alert,
  Button,
  Col,
  Divider,
  Empty,
  Form,
  Image,
  Input,
  InputNumber,
  Layout,
  List,
  message,
  Modal,
  Radio,
  Row,
  Space,
  Spin,
  Tag,
  Textarea,
  Upload,
} from 'ant-design-vue';
import type { UploadRequestOption } from 'ant-design-vue/es/vc-upload/interface';
import { useRoute, useRouter } from 'vue-router';

import {
  deleteAttachmentApi,
  getGuidebookDownloadUrl,
  getSubmissionDetailApi,
  previewGuidebookApi,
  saveDraftApi,
  submitReportApi,
  uploadAttachmentApi,
} from '#/api/experiment';

import {
  DOC_TYPE_LABEL,
  formatFileSize,
} from '../utils';
import { marked } from 'marked';

defineOptions({ name: 'SubmissionEditor' });

const router = useRouter();
const route = useRoute();
const submissionId = route.params.id as string;

// ─── 数据状态 ───
const loading = ref(false);
const submission = ref<SubmissionDetail | null>(null);
const guidebooks = ref<GuidebookListItem[]>([]);
const attachments = ref<AttachmentItem[]>([]);

// ─── 预览 ───
const previewVisible = ref(false);
const previewLoading = ref(false);
const previewData = ref<{ type: string; content?: string; html?: string; url?: string } | null>(null);
const previewTitle = ref('');

// ─── 表单 ───
const form = ref({
  report_title: '',
  report_content: '',
  vm_info: {} as Record<string, any>,
});

// ─── 自动保存 ───
const lastSaveTime = ref<string | null>(null);
const saving = ref(false);
const isDirty = ref(false);
let autoSaveTimer: ReturnType<typeof setInterval> | null = null;

// ─── 提交状态 ───
const submitting = ref(false);
const uploadingAttachment = ref(false);
const guidebookCollapsed = ref(false);

// ─── 步骤大纲（从报告内容中提取 ## 标题） ───
const outlineItems = computed<string[]>(() => {
  const content = form.value.report_content ?? '';
  const lines = content.split('\n');
  return lines
    .filter((l) => l.startsWith('## ') || l.startsWith('# '))
    .map((l) => l.replace(/^#+\s+/, ''));
});

// ─── 字数统计 ───
const wordCount = computed(() => (form.value.report_content ?? '').length);

// ─── 加载数据 ───
const loadData = async () => {
  loading.value = true;
  try {
    const sub = await getSubmissionDetailApi(submissionId);
    submission.value = sub;
    form.value.report_title = sub.report_title ?? '';
    form.value.report_content = sub.report_content ?? '';
    form.value.vm_info = sub.vm_info ?? {};
    attachments.value = sub.attachments ?? [];

    // 若有关联实验的指导书
    const expId = (sub as any).experiment ?? (sub as any).experiment_info?.id;
    if (expId) {
      const { getExperimentDetailApi } = await import('#/api/experiment');
      const expDetail = await getExperimentDetailApi(expId);
      guidebooks.value = expDetail.guidebooks ?? [];
    }
  } catch (e: any) {
    message.error('加载报告失败');
  } finally {
    loading.value = false;
  }
};

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

const getFileIcon = (gb: GuidebookListItem) => {
  const t = gb.file_type?.toLowerCase();
  if (t === 'pdf') return '📄';
  if (['mp4', 'avi', 'mkv', 'mov'].includes(t)) return '🎬';
  if (t === 'md') return '📝';
  return '📎';
};

// ─── 保存草稿 ───
const doSave = async (showSuccess = true) => {
  if (!isDirty.value && showSuccess) return;
  saving.value = true;
  try {
    await saveDraftApi(submissionId, {
      report_title: form.value.report_title,
      report_content: form.value.report_content,
      vm_info: form.value.vm_info,
    });
    lastSaveTime.value = new Date().toLocaleTimeString('zh-CN');
    isDirty.value = false;
    if (showSuccess) message.success('草稿已保存');
  } catch {
    if (showSuccess) message.error('保存失败，请检查网络连接');
  } finally {
    saving.value = false;
  }
};

// 表单变化标记 dirty
watch(form, () => { isDirty.value = true; }, { deep: true });

// ─── 提交报告 ───
const handleSubmit = () => {
  if (!form.value.report_content?.trim()) {
    message.warning('报告内容不能为空');
    return;
  }
  Modal.confirm({
    title: '确认提交',
    content: '提交后报告将进入批改队列，提交前请先保存草稿。是否确认提交？',
    okText: '确认提交',
    okType: 'primary',
    cancelText: '取消',
    onOk: async () => {
      // 先保存再提交
      await doSave(false);
      submitting.value = true;
      try {
        await submitReportApi(submissionId);
        message.success('报告已成功提交！');
        const expId = submission.value?.experiment;
        router.push(expId ? `/experiments/student/${expId}` : '/experiments/student');
      } catch (e: any) {
        message.error(e?.response?.data?.message ?? '提交失败，请重试');
      } finally {
        submitting.value = false;
      }
    },
  });
};

// ─── 附件上传 ───
const customUpload = async (options: UploadRequestOption) => {
  uploadingAttachment.value = true;
  const hideMsg = message.loading(`正在上传附件 "${(options.file as File).name}"，请稍候...`, 0);
  try {
    const fd = new FormData();
    fd.append('file', options.file as File);
    const result = await uploadAttachmentApi(submissionId, fd);
    attachments.value.push(result);
    message.success('上传成功');
    (options.onSuccess as any)?.(result);
  } catch (e: any) {
    message.error('上传失败，文件可能过大或网络异常');
    (options.onError as any)?.(e);
  } finally {
    hideMsg();
    uploadingAttachment.value = false;
  }
};

const handleDeleteAttachment = async (att: AttachmentItem, idx: number) => {
  try {
    await deleteAttachmentApi(att.id);
    attachments.value.splice(idx, 1);
    message.success('已删除');
  } catch {
    message.error('删除失败');
  }
};

// ─── 粘贴图片处理 ───
const handlePaste = async (e: ClipboardEvent) => {
  if (isReadonly.value) return;
  const items = e.clipboardData?.items;
  if (!items) return;

  for (let i = 0; i < items.length; i++) {
    const item = items[i]!;
    if (item.type.includes('image')) {
      const file = item.getAsFile();
      if (!file) continue;

      e.preventDefault(); // 只在一确认是图片时才阻止默认的粘贴行为
      const el = e.target as HTMLTextAreaElement;
      const start = el.selectionStart ?? form.value.report_content.length;
      const end = el.selectionEnd ?? start;

      // 插入占位符
      const placeholder = `\n![上传中...]()\n`;
      const currentContent = form.value.report_content ?? '';
      form.value.report_content =
        currentContent.substring(0, start) +
        placeholder +
        currentContent.substring(end);

      // 调整光标
      setTimeout(() => {
        el.selectionStart = el.selectionEnd = start + placeholder.length;
      }, 0);

      try {
        const fd = new FormData();
        fd.append('file', file, `pasted_image_${Date.now()}.png`);
        const result = await uploadAttachmentApi(submissionId, fd);
        attachments.value.push(result);
        message.success('图片粘贴上传成功');

        // 替换占位符
        const imgUrl = toAbsUrl(result.file_url);
        const mdImage = `\n![粘贴的图片](${imgUrl})\n`;
        form.value.report_content = form.value.report_content.replace(placeholder, mdImage);
      } catch (err: any) {
        message.error('图片粘贴上传失败');
        form.value.report_content = form.value.report_content.replace(placeholder, '');
      }
      break; // 每次粘贴只处理一张图
    }
  }
};

// ─── 生命周期 ───
onMounted(async () => {
  await loadData();
  // 自动保存，每 30 秒
  autoSaveTimer = setInterval(() => doSave(false), 30_000);
});

onBeforeUnmount(() => {
  if (autoSaveTimer) clearInterval(autoSaveTimer);
  // 离开前尝试保存
  if (isDirty.value) doSave(false);
});

// ─── 帮助 ───
const submissionStatus = computed(() => submission.value?.submission_status ?? 'draft');
const isReadonly = computed(() => submissionStatus.value === 'submitted' || submissionStatus.value === 'graded');

// 报告查看模式
const reportViewMode = ref<'preview' | 'source'>('source');

watch(isReadonly, (val) => {
  if (val) reportViewMode.value = 'preview';
}, { immediate: true });

// 渲染 Markdown 解析的 HTML
const renderedReport = computed(() => {
  if (!form.value?.report_content) return '';
  return marked.parse(form.value.report_content);
});

// 返回后状态（后端退回后 status 设回 'draft'，需显示退回原因提示）
const returnedFeedback = computed(() => {
  const fb = submission.value?.feedback ?? '';
  return fb.startsWith('[\u9000\u56de\u539f\u56e0]') ? fb.replace('[\u9000\u56de\u539f\u56e0]', '').trim() : null;
});

// 展示显示状态标签
const statusLabel = computed(() => {
  if (returnedFeedback.value) return '已退回';
  if (isReadonly.value) return '已提交';
  return '草稿';
});

// 附件 URL 辅助
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
  <div class="submission-editor" style="height: 100%; display: flex; flex-direction: column;">
    <!-- 顶部工具栏 -->
    <div
      class="flex shrink-0 items-center justify-between border-b bg-white px-5 py-2"
      style="border-color: #f0f0f0"
    >
      <Space>
        <Button
          size="small"
          :icon="h(ArrowLeftOutlined)"
          @click="router.back()"
        >
          返回
        </Button>
        <span class="font-semibold text-sm">
          实验报告
          <template v-if="submission">
            — {{ submission.experiment_info?.title ?? '' }}
          </template>
        </span>
        <Tag
          :color="isReadonly ? 'success' : returnedFeedback ? 'warning' : 'orange'"
          size="small"
        >
          {{ statusLabel }}
        </Tag>
      </Space>
      <Space>
        <span v-if="lastSaveTime" class="text-gray-400 text-xs">
          上次保存：{{ lastSaveTime }}
        </span>
        <Button
          v-if="!isReadonly"
          size="small"
          :icon="h(SaveOutlined)"
          :loading="saving"
          @click="doSave(true)"
        >
          保存草稿
        </Button>
        <Button
          v-if="!isReadonly"
          type="primary"
          size="small"
          :icon="h(SendOutlined)"
          :loading="submitting"
          @click="handleSubmit"
        >
          提交报告
        </Button>
      </Space>
    </div>

    <Spin :spinning="loading" style="flex: 1; overflow: hidden">
      <Layout style="height: 100%; background: #f5f5f5">
        <!-- ════ 左侧：指导书面板 ════ -->
        <Layout.Sider
          :width="340"
          v-model:collapsed="guidebookCollapsed"
          collapsible
          :collapsedWidth="40"
          :trigger="null"
          style="background: #fff; border-right: 1px solid #f0f0f0; overflow: hidden; display: flex; flex-direction: column"
        >
          <div style="display: flex; flex-direction: column; height: 100%; overflow: hidden">
            <!-- 展开时的完整面板 -->
            <template v-if="!guidebookCollapsed">
              <!-- Guidebook Tabs Header -->
              <div class="border-b px-3 py-3 shrink-0 flex items-center justify-between text-sm font-semibold text-gray-700 bg-gray-50/50" style="border-color: #f0f0f0">
                <span>实验指导书</span>
                <Button size="small" type="text" @click="guidebookCollapsed = true">
                  <span class="text-xs text-gray-500 hover:text-blue-500">收起 &lt;&lt;</span>
                </Button>
              </div>

              <!-- Directory Content -->
              <div class="flex-1 overflow-y-auto w-full">
                <div v-if="guidebooks.length === 0" class="py-12 text-center">
                  <Empty description="暂无指导书数据" />
                </div>
                <!-- 目录列表 -->
                <List v-else :data-source="guidebooks" :bordered="false" class="bg-white">
                  <template #renderItem="{ item: gb }">
                    <List.Item class="hover:bg-blue-50/50 px-4 transition-colors cursor-pointer border-b border-gray-100 last:border-0" style="padding-top: 12px; padding-bottom: 12px;" @click="handlePreview(gb)">
                      <div class="flex flex-col w-full">
                        <div class="flex items-start gap-2 mb-1">
                          <span class="text-base leading-none translate-y-0.5">{{ getFileIcon(gb) }}</span>
                          <span class="font-medium text-gray-800 leading-snug line-clamp-2">{{ gb.title }}</span>
                        </div>
                        <div class="flex items-center gap-2 pl-7 mt-0.5">
                          <Tag size="small" :bordered="false" class="text-[10px] m-0">{{ DOC_TYPE_LABEL[gb.doc_type] ?? gb.doc_type }}</Tag>
                          <span class="text-xs text-gray-400">{{ formatFileSize(gb.file_size) }}</span>
                          <Button size="small" type="link" class="ml-auto p-0 h-auto text-xs flex items-center gap-1" @click.stop="" :href="getGuidebookDownloadUrl(gb.id)" target="_blank">下载</Button>
                        </div>
                      </div>
                    </List.Item>
                  </template>
                </List>
              </div>
            </template>

            <!-- 收起时的极简侧边栏显示 -->
            <template v-else>
              <div 
                class="flex h-full w-full cursor-pointer flex-col items-center pt-4 hover:bg-gray-100" 
                @click="guidebookCollapsed = false"
                title="展开指导书"
              >
                <div style="writing-mode: vertical-lr; letter-spacing: 4px;" class="text-sm font-semibold text-gray-500">
                  展开指导书 >>
                </div>
              </div>
            </template>
          </div>
        </Layout.Sider>

        <!-- ════ 中间：报告编辑器 ════ -->
        <Layout.Content style="overflow-y: auto; padding: 16px">
          <div v-if="returnedFeedback">
            <Alert
              type="warning"
              :message="`教师退回修改，请参考以下原因后重新提交：${returnedFeedback}`"
              show-icon
              class="mb-4"
            />
          </div>
          <div v-else-if="isReadonly">
            <Alert
              type="info"
              message="报告已提交，无法继续编辑"
              show-icon
              class="mb-4"
            />
          </div>

          <Form layout="vertical">
            <!-- 报告标题 -->
            <Form.Item label="报告标题">
              <Input
                v-model:value="form.report_title"
                :disabled="isReadonly"
                placeholder="如：Linux 用户权限管理实验报告"
                size="large"
              />
            </Form.Item>

            <!-- 实验环境 -->
            <Form.Item label="实验环境（虚拟机信息）">
              <Row :gutter="12">
                <Col :span="8">
                  <Input
                    v-model:value="form.vm_info.vm_name"
                    :disabled="isReadonly"
                    placeholder="虚拟机名称"
                    addon-before="名称"
                  />
                </Col>
                <Col :span="8">
                  <Input
                    v-model:value="form.vm_info.vmid"
                    :disabled="isReadonly"
                    placeholder="VMID"
                    addon-before="VMID"
                  />
                </Col>
                <Col :span="8">
                  <Input
                    v-model:value="form.vm_info.ip"
                    :disabled="isReadonly"
                    placeholder="IP 地址"
                    addon-before="IP"
                  />
                </Col>
              </Row>
            </Form.Item>

            <!-- 报告正文 -->
            <Form.Item>
              <template #label>
                <div class="flex items-center justify-between w-full pb-1">
                  <span>报告正文（支持 Markdown 语法）</span>
                  <Radio.Group v-model:value="reportViewMode" size="small" button-style="solid">
                    <Radio.Button value="preview">渲染视图</Radio.Button>
                    <Radio.Button value="source">源码视图</Radio.Button>
                  </Radio.Group>
                </div>
              </template>

              <!-- 渲染模式 -->
              <div
                v-if="reportViewMode === 'preview'"
                class="report-content min-h-[500px] overflow-x-auto rounded-md bg-white border p-4 prose prose-sm max-w-none"
                style="border-color: #d9d9d9"
                v-html="renderedReport || `<p class='text-gray-400'>（无内容）</p>`"
              ></div>

              <!-- 源码模式 -->
              <div v-else>
                <Textarea
                  v-model:value="form.report_content"
                  :disabled="isReadonly"
                  :rows="22"
                  placeholder="# 实验环境\n\n## 一、实验过程\n\n1. 第一步：创建用户\n```bash\nuseradd tom\n```\n\n## 二、实验结果\n\n## 三、思考题\n"
                  style="font-family: 'Consolas', monospace; font-size: 13px; line-height: 1.8"
                  @paste="handlePaste"
                />
                <div class="mt-1 flex justify-between text-xs text-gray-400">
                  <span>支持 Markdown 语法（# 标题, ```代码块```, **加粗** 等）</span>
                  <span>{{ wordCount }} 字符</span>
                </div>
              </div>
            </Form.Item>

            <!-- 操作截图上传 -->
            <Form.Item label="操作截图 / 录屏附件">
              <Upload
                v-if="!isReadonly"
                :custom-request="customUpload"
                :show-upload-list="false"
                accept="image/*,video/*"
                :multiple="true"
              >
                <Button
                  :icon="h(UploadOutlined)"
                  :loading="uploadingAttachment"
                  size="small"
                >
                  上传截图/录屏
                </Button>
                <span class="ml-2 text-xs text-gray-400">支持 JPG、PNG、MP4 等</span>
              </Upload>

              <!-- 附件列表 -->
              <div
                v-if="attachments.length > 0"
                class="mt-3 grid gap-3"
                style="grid-template-columns: repeat(auto-fill, minmax(180px, 1fr))"
              >
                <div
                  v-for="(att, idx) in attachments"
                  :key="att.id"
                  class="relative rounded-md border bg-white p-2"
                  style="border-color: #e8e8e8"
                >
                  <!-- 缩略图 -->
                  <div class="mb-2 overflow-hidden rounded" style="height: 100px; background: #f5f5f5; display: flex; align-items: center; justify-content: center">
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

                  <!-- 附件信息 -->
                  <div class="space-y-1">
                    <p class="truncate text-xs font-medium" :title="att.file_name">
                      {{ att.file_name }}
                    </p>
                    <Input
                      v-if="!isReadonly"
                      v-model:value="att.description"
                      placeholder="图片说明（可选）"
                      size="small"
                    />
                    <p v-else class="text-xs text-gray-500">{{ att.description || '—' }}</p>
                    <div class="flex items-center justify-between">
                      <div class="flex items-center gap-1">
                        <span class="text-xs text-gray-400">步骤：</span>
                        <InputNumber
                          v-if="!isReadonly"
                        v-model:value="(att.step_number as number | undefined)"
                          :min="1"
                          size="small"
                          style="width: 60px"
                        />
                        <Tag v-else-if="att.step_number" size="small">{{ att.step_number }}</Tag>
                      </div>
                      <Popconfirm
                        v-if="!isReadonly"
                        title="确认删除？"
                        ok-text="删除"
                        ok-type="danger"
                        cancel-text="取消"
                        @confirm="handleDeleteAttachment(att, idx)"
                      >
                        <Button
                          type="text"
                          danger
                          size="small"
                          :icon="h(DeleteOutlined)"
                        />
                      </Popconfirm>
                    </div>
                  </div>
                </div>
              </div>
              <div v-else class="mt-2 text-xs text-gray-400">
                暂无附件，请上传操作截图作为证明
              </div>
            </Form.Item>
          </Form>
        </Layout.Content>

        <!-- ════ 右侧：大纲 ════ -->
        <Layout.Sider
          :width="220"
          style="background: #fafafa; border-left: 1px solid #f0f0f0; overflow-y: auto; padding: 16px"
        >
          <div class="mb-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">
            报告大纲
          </div>
          <div v-if="outlineItems.length === 0" class="text-xs text-gray-400">
            使用 # 或 ## 标题自动生成大纲
          </div>
          <div v-else class="space-y-1">
            <div
              v-for="(item, idx) in outlineItems"
              :key="idx"
              class="cursor-pointer rounded px-2 py-1 text-xs text-gray-600 hover:bg-blue-50 hover:text-blue-500"
            >
              {{ idx + 1 }}. {{ item }}
            </div>
          </div>

          <Divider />

          <!-- 附件数量 -->
          <div class="text-xs text-gray-500">
            <div class="mb-1 font-semibold">附件</div>
            <div>{{ attachments.length }} 个文件</div>
          </div>

          <Divider />

          <!-- 字数 -->
          <div class="text-xs text-gray-500">
            <div class="mb-1 font-semibold">字数统计</div>
            <div>{{ wordCount }} 字符</div>
          </div>
        </Layout.Sider>
      </Layout>
    </Spin>

    <!-- 视频预览弹窗 -->
    <Modal
      v-model:open="videoPreviewVisible"
      :title="videoPreviewTitle"
      :footer="null"
      width="1280px"
      style="top: 20px"
      :destroy-on-close="true"
      :body-style="{ padding: 0 }"
    >
      <video
        v-if="videoPreviewUrl"
        :src="videoPreviewUrl"
        controls
        autoplay
        style="width: 100%; max-height: 85vh; background: #000; outline: none; border-bottom-left-radius: 8px; border-bottom-right-radius: 8px;"
      />
    </Modal>

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

<style scoped>
.submission-editor {
  height: 100%;
  min-height: 0;
}
:deep(.ant-layout) {
  background: transparent;
}
:deep(.ant-form-item) {
  margin-bottom: 16px;
}
.submission-editor :deep(.ant-spin-nested-loading) {
  display: flex;
  flex: 1;  
  flex-direction: column;
  height: 100%;
  min-height: 0;
}
.submission-editor :deep(.ant-spin-container) {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
  overflow: hidden;
}
</style>
