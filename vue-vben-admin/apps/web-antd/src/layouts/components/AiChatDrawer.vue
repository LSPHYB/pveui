<script setup lang="ts">
import { ref, nextTick, onMounted, computed, watch } from 'vue';
import { useDraggable } from '@vueuse/core';
import { useRoute } from 'vue-router';
import {
  RobotOutlined,
  SendOutlined,
  PlusOutlined,
  DeleteOutlined,
  ThunderboltOutlined,
} from '@ant-design/icons-vue';
import {
  Button,
  Drawer,
  Input,
  Select,
  Progress,
  Tooltip,
  message as antMessage,
} from 'ant-design-vue';
import { useUserStore, useAccessStore } from '@vben/stores';
import {
  getAvailableModelsApi,
  getMyQuotaApi,
  getMyConversationsApi,
  createConversationApi,
  deleteConversationApi,
} from '#/api/ai';

// ── 状态 ──────────────────────────────────────────────────────────────
const drawerVisible = ref(false);
const isPulsing = ref(true);
const unreadCount = ref(0);

const isLoading = ref(false);
const inputMessage = ref('');
const messages = ref<any[]>([]);
const messageListRef = ref<HTMLElement | null>(null);

const floatingBtnRef = ref<HTMLElement | null>(null);

const { x, y, style: floatingStyle } = useDraggable(floatingBtnRef, {
  initialValue: { x: 1000, y: 800 },
});

const availableModels = ref<any[]>([]);
const selectedModel = ref<string | undefined>(undefined);

// 会话管理
const conversations = ref<any[]>([]);
const currentConversationId = ref<number | null>(null);
const showConvList = ref(false);

// 配额
const quota = ref<{ daily?: any; monthly?: any }>({});

// 实验上下文感知：从当前路由提取实验ID，定向 RAG 检索
const route = useRoute();
const currentExperimentId = ref<string | null>(null);

const resolveExperimentContext = async () => {
  // 路由形如: /experiments/student/submission/:id
  const submissionId = route.params.id as string;
  if (!submissionId || !route.path.includes('/submission/')) {
    currentExperimentId.value = null;
    return;
  }
  try {
    const { getSubmissionDetailApi } = await import('#/api/experiment');
    const sub: any = await getSubmissionDetailApi(submissionId);
    const expId = sub?.experiment ?? sub?.experiment_info?.id;
    currentExperimentId.value = expId ? String(expId) : null;
  } catch {
    currentExperimentId.value = null;
  }
};

watch(() => route.fullPath, () => resolveExperimentContext(), { immediate: true });

// ── 计算属性 ────────────────────────────────────────────────────────────
const dailyPercent = computed(() => {
  const d = quota.value.daily;
  if (!d || !d.limit) return 0;
  return Math.min(100, Math.round((d.used / d.limit) * 100));
});

const userStore = useUserStore();
const username = computed(() => userStore.userInfo?.username || 'Me');

// ── 工具方法 ────────────────────────────────────────────────────────────
const scrollToBottom = () => {
  nextTick(() => {
    if (messageListRef.value) {
      messageListRef.value.scrollTop = messageListRef.value.scrollHeight;
    }
  });
};

const toggleDrawer = () => {
  drawerVisible.value = !drawerVisible.value;
  if (drawerVisible.value) {
    unreadCount.value = 0;
    isPulsing.value = false;
  }
};

// ── 初始化 ──────────────────────────────────────────────────────────────
const loadModels = async () => {
  try {
    const res: any = await getAvailableModelsApi();
    const list = res?.results || res?.data?.results || res?.data?.data?.results || res?.data?.items || res?.data?.list || (Array.isArray(res) ? res : (Array.isArray(res?.data) ? res.data : []));
    availableModels.value = list;
    const def = list.find((m: any) => m.is_default) ?? list[0];
    if (def) selectedModel.value = def.model_key;
  } catch (err) {
    console.error('Failed to load available models:', err);
  }
};

const loadQuota = async () => {
  try {
    const res: any = await getMyQuotaApi();
    quota.value = res?.data ?? res ?? {};
  } catch {
    // 配额不可用时静默
  }
};

const loadConversations = async () => {
  try {
    const res: any = await getMyConversationsApi({ page_size: 30 });
    let items = [];
    if (res && res.results) {
      items = res.results;
    } else if (res?.data?.results) {
      items = res.data.results;
    } else if (res?.data?.data?.results) {
      items = res.data.data.results;
    } else if (Array.isArray(res)) {
      items = res;
    } else if (Array.isArray(res?.data)) {
      items = res.data;
    } else if (Array.isArray(res?.data?.data)) {
      items = res.data.data;
    } else if (res?.data?.items) {
      items = res.data.items;
    } else if (res?.data?.list) {
      items = res.data.list;
    }
    conversations.value = items || [];
  } catch (err) {
    console.warn('Failed to load conversations:', err);
    conversations.value = [];
  }
};

// ── 会话管理 ───────────────────────────────────────────────────────────
const createNewConversation = async () => {
  try {
    // 在实验报告页时，携带实验ID让后端做定向 RAG 检索
    const isExpPage = !!currentExperimentId.value;
    const res: any = await createConversationApi({
      context_type: isExpPage ? 'experiment' : 'general',
      context_id: isExpPage ? currentExperimentId.value! : undefined,
      model_key: selectedModel.value,
    });
    const conv = res?.data?.data || res?.data || res;
    currentConversationId.value = conv?.id || res?.data?.id || res?.id;
    if (!currentConversationId.value) {
      console.error('Failed to parse conversation ID from response:', res);
      throw new Error('Invalid conversation response');
    }
    messages.value = [];
    showConvList.value = false;
    await loadConversations();
  } catch {
    antMessage.error('创建会话失败，请稍后重试');
  }
};

const switchConversation = async (conv: any) => {
  currentConversationId.value = conv.id;
  showConvList.value = false;
  // 加载会话详情（确保拿到所有历史消息）
  try {
    isLoading.value = true;
    const accessStore = useAccessStore();
    const token = accessStore.accessToken;
    const apiBase = (import.meta.env.VITE_GLOB_API_URL || '/api').replace(/\/$/, '');
    
    const response = await fetch(`${apiBase}/chat/conversations/${conv.id}/`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
    });
    if (response.ok) {
        const detail = await response.json();
        const actualDetail = detail?.data?.data || detail?.data || detail;
        messages.value = actualDetail.messages || [];
    } else {
       messages.value = conv.messages ?? [];
    }
  } catch (err) {
     console.error('Failed to load conversation details:', err);
     messages.value = conv.messages ?? [];
  } finally {
    isLoading.value = false;
    scrollToBottom();
  }
};

const handleDeleteConversation = async (e: Event, convId: number) => {
  e.stopPropagation(); // 阻止触发外层 onClick 切换会话
  try {
    await deleteConversationApi(convId);
    antMessage.success('会话已删除');
    if (currentConversationId.value === convId) {
      clearChat();
    }
    await loadConversations();
  } catch (err) {
    antMessage.error('删除会话失败');
  }
};

// ── 发送消息（真实 SSE） ────────────────────────────────────────────────
const handleSend = async () => {
  const content = inputMessage.value.trim();
  if (!content || isLoading.value) return;
  inputMessage.value = '';

  // 若还没有会话，先创建一个
  if (!currentConversationId.value) {
    await createNewConversation();
    if (!currentConversationId.value) return;
  }

  // 乐观插入用户消息（临时ID）
  const tempId = Date.now();
  messages.value.push({ id: tempId, role: 'human', content });
  scrollToBottom();

  isLoading.value = true;

  const accessStore = useAccessStore();
  const token = accessStore.accessToken;

  const apiBase = (import.meta.env.VITE_GLOB_API_URL || '/api').replace(/\/$/, '');
  
  try {
    const response = await fetch(
      `${apiBase}/chat/conversations/${currentConversationId.value}/messages/`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ content }),
      },
    );

    if (!response.ok) {
      if (response.status === 429) throw new Error('请求过于频繁，请稍后再试');
      if (response.status === 402)
        throw new Error('使用配额已满，请联系管理员');
      if (response.status === 401) throw new Error('登录已过期，请重新登录');
      throw new Error(`请求失败 (${response.status})`);
    }

    const reader = response.body!.getReader();
    const decoder = new TextDecoder();
    let aiMsg: any = null;
    let buffer = '';

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const blocks = buffer.split('\n\n');
      buffer = blocks.pop() ?? '';

      for (const block of blocks) {
        const lines = block.split('\n');
        let eventType = '';
        for (const line of lines) {
          if (line.startsWith('event: ')) {
            eventType = line.slice(7).trim();
          } else if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              if (eventType === 'user_message') {
                // 将临时消息替换为服务端真实ID
                const idx = messages.value.findIndex((m) => m.id === tempId);
                if (idx !== -1) messages.value[idx] = data;
              } else if (eventType === 'content_chunk') {
                if (!aiMsg) {
                  aiMsg = { id: Date.now() + 1, role: 'ai', content: '' };
                  messages.value.push(aiMsg);
                }
                aiMsg.content += data.chunk ?? '';
                scrollToBottom();
              } else if (eventType === 'assistant_message') {
                if (aiMsg) {
                  const idx = messages.value.findIndex(
                    (m) => m.id === aiMsg.id,
                  );
                  if (idx !== -1) messages.value[idx] = data;
                } else {
                  messages.value.push(data);
                }
                scrollToBottom();
                // 刷新配额显示
                loadQuota();
              }
            } catch {
              // 忽略解析错误的块
            }
          }
        }
      }
    }
  } catch (err: any) {
    antMessage.error(err.message || '发送失败，请检查网络');
    messages.value.push({
      id: Date.now() + 99,
      role: 'ai',
      content: `【错误】${err.message || '发送失败'}`,
      isError: true,
    });
    scrollToBottom();
  } finally {
    isLoading.value = false;
    if (!drawerVisible.value) {
      unreadCount.value++;
      isPulsing.value = true;
    }
  }
};

const clearChat = () => {
  messages.value = [];
  currentConversationId.value = null;
};

// ── 生命周期 ────────────────────────────────────────────────────────────

onMounted(() => {
  if (typeof window !== 'undefined') {
    x.value = window.innerWidth - 80;
    y.value = window.innerHeight - 80;
  }
  loadModels();
  loadQuota();
  loadConversations();
});
</script>

<template>
  <div>
    <!-- 全局悬浮气泡 -->
    <div 
      ref="floatingBtnRef"
      class="fixed z-[999]" 
      :style="floatingStyle"
    >
      <div class="relative cursor-move">
        <!-- 脉冲环 -->
        <div
          v-show="isPulsing"
          class="absolute inset-0 rounded-full bg-blue-400 opacity-30 animate-ping"
        />
        <!-- AI 按钮 -->
        <Button
          type="primary"
          shape="circle"
          size="large"
          style="
            width: 56px;
            height: 56px;
            box-shadow: 0 4px 16px rgba(22, 93, 255, 0.4);
          "
          @click="toggleDrawer"
        >
          <template #icon>
            <RobotOutlined style="font-size: 22px" />
          </template>
        </Button>
        <!-- 未读角标 -->
        <div
          v-if="unreadCount > 0"
          class="absolute top-0 right-0 translate-x-1/2 -translate-y-1/2 bg-red-500 text-white min-w-[20px] h-5 rounded-full text-xs flex items-center justify-center font-bold shadow"
        >
          {{ unreadCount > 99 ? '99+' : unreadCount }}
        </div>
      </div>
    </div>

    <!-- AI 抽屉 -->
    <Drawer
      v-model:open="drawerVisible"
      title="AI 智能助手"
      placement="right"
      :width="420"
      :closable="true"
      :header-style="{ padding: '12px 16px' }"
      :body-style="{
        padding: 0,
        display: 'flex',
        flexDirection: 'column',
        background: '#f8fafc',
        overflow: 'hidden',
      }"
    >
      <!-- 抽屉右上角：模型选择 + 新对话 -->
      <template #extra>
        <div class="flex items-center gap-2">
          <Select
            v-model:value="selectedModel"
            :options="availableModels"
            :field-names="{ label: 'model_name', value: 'model_key' }"
            size="small"
            style="width: 130px"
            placeholder="选择模型"
          />
          <Tooltip title="新建对话">
            <Button size="small" @click="createNewConversation">
              <template #icon><PlusOutlined /></template>
            </Button>
          </Tooltip>
          <Tooltip title="历史会话">
            <Button size="small" @click="showConvList = !showConvList">
              <template #icon><ThunderboltOutlined /></template>
              历史会话
            </Button>
          </Tooltip>
        </div>
      </template>

      <!-- 历史会话列表（折叠面板） -->
      <div
        v-if="showConvList"
        class="border-b bg-white"
        style="max-height: 200px; overflow-y: auto"
      >
        <div
          v-if="conversations.length === 0"
          class="text-center text-gray-400 text-xs py-4"
        >
          暂无历史会话
        </div>
        <div
          v-for="conv in conversations"
          :key="conv.id"
          class="group flex items-center justify-between px-4 py-2 hover:bg-gray-50 cursor-pointer text-sm border-b"
          :class="
            conv.id === currentConversationId ? 'bg-blue-50 text-blue-600' : ''
          "
          @click="switchConversation(conv)"
        >
          <span class="truncate flex-1">{{ conv.title || '新对话' }}</span>
          
          <div class="flex items-center">
            <span class="text-gray-400 text-xs ml-2 shrink-0 group-hover:hidden">
              {{ conv.message_count }}条
            </span>
            <Button
              type="text"
              danger
              size="small"
              class="hidden group-hover:inline-flex items-center justify-center p-0 ml-2"
              @click="handleDeleteConversation($event, conv.id)"
              title="删除此会话"
            >
              <DeleteOutlined />
            </Button>
          </div>
        </div>
      </div>

      <!-- 消息列表 -->
      <div
        ref="messageListRef"
        class="flex-1 overflow-y-auto px-4 py-3 flex flex-col gap-3"
      >
        <div
          v-if="messages.length === 0"
          class="text-center text-gray-400 text-xs mt-8"
        >
          <RobotOutlined style="font-size: 32px; color: #93c5fd" />
          <p class="mt-2">你好！我是 AI 助手，有什么可以帮你的？</p>
        </div>

        <div
          v-for="msg in messages"
          :key="msg.id"
          class="flex items-start gap-2"
          :class="msg.role === 'human' ? 'flex-row-reverse' : ''"
        >
          <!-- 头像 -->
          <div
            class="shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-white text-xs font-bold"
            :class="
              msg.role === 'human' ? 'bg-blue-500' : 'bg-indigo-600'
            "
          >
            <RobotOutlined v-if="msg.role !== 'human'" />
            <span v-else>{{ username[0]?.toUpperCase() }}</span>
          </div>

          <!-- 气泡 -->
          <div
            class="max-w-[75%] rounded-2xl px-3 py-2 text-sm leading-relaxed break-words whitespace-pre-wrap"
            :class="
              msg.role === 'human'
                ? 'bg-blue-500 text-white rounded-tr-sm'
                : msg.isError
                  ? 'bg-red-50 text-red-600 border border-red-200 rounded-tl-sm'
                  : 'bg-white border border-gray-100 shadow-sm rounded-tl-sm'
            "
          >
            {{ msg.content }}

            <!-- RAG 引用来源 -->
            <div
              v-if="msg.sources && msg.sources.length"
              class="mt-2 pt-2 border-t border-gray-100 text-xs text-gray-500"
            >
              <span class="font-medium">参考来源：</span>
              <span
                v-for="(src, i) in msg.sources"
                :key="i"
                class="inline-block bg-gray-100 px-1 rounded mr-1"
              >
                {{ src.source ?? `来源${Number(i) + 1}` }}
              </span>
            </div>
          </div>
        </div>

        <!-- 思考中指示器 -->
        <div v-show="isLoading" class="flex items-center gap-2 text-xs text-gray-400">
          <div
            class="w-8 h-8 rounded-full bg-indigo-600 flex items-center justify-center text-white shrink-0"
          >
            <RobotOutlined />
          </div>
          <div class="bg-white border border-gray-100 rounded-2xl rounded-tl-sm px-3 py-2 shadow-sm">
            <span class="animate-pulse">AI 正在思考...</span>
          </div>
        </div>
      </div>

      <!-- 底部：配额 + 输入区 -->
      <div class="border-t bg-white p-3 flex flex-col gap-2 shrink-0">
        <!-- 配额进度条（有数据才显示） -->
        <div
          v-if="quota.daily"
          class="flex items-center gap-2 text-xs text-gray-500"
        >
          <span class="shrink-0">今日配额</span>
          <Progress
            :percent="dailyPercent"
            size="small"
            :show-info="false"
            class="flex-1"
            :stroke-color="dailyPercent >= 90 ? '#f5222d' : '#1677ff'"
          />
          <span class="shrink-0">
            {{ quota.daily.used ?? 0 }}/{{ quota.daily.limit ?? '∞' }}
          </span>
        </div>

        <!-- 输入框 -->
        <Input.TextArea
          v-model:value="inputMessage"
          placeholder="输入问题，按 Enter 发送，Shift+Enter 换行"
          :auto-size="{ minRows: 2, maxRows: 5 }"
          @press-enter="
            (e: KeyboardEvent) => {
              if (!e.shiftKey) {
                e.preventDefault();
                handleSend();
              }
            }
          "
        />

        <div class="flex justify-between items-center">
          <span class="text-xs text-gray-400">AI 生成内容仅供参考，请注意甄别</span>
          <div class="flex gap-2">
            <Tooltip title="清空当前对话">
              <Button size="small" @click="clearChat">
                <template #icon><DeleteOutlined /></template>
              </Button>
            </Tooltip>
            <Button
              type="primary"
              size="small"
              :disabled="!inputMessage.trim()"
              :loading="isLoading"
              @click="handleSend"
            >
              <template #icon><SendOutlined /></template>
              发送
            </Button>
          </div>
        </div>
      </div>
    </Drawer>
  </div>
</template>

<style scoped>
/* 确保抽屉 body 允许 flex 布局 */
:deep(.ant-drawer-body) {
  display: flex !important;
  flex-direction: column !important;
  overflow: hidden !important;
}
</style>
