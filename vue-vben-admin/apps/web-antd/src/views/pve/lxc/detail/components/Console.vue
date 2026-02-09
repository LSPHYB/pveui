<script setup lang="ts">
import type { LxcContainerModel } from '#/api/pve/types';

import { computed, nextTick, onBeforeUnmount, ref, watch } from 'vue';

import { useAccessStore } from '@vben/stores';

import {
  AppstoreOutlined,
  ArrowDownOutlined,
  ArrowUpOutlined,
  CodeOutlined,
  CopyOutlined,
  DesktopOutlined,
  DownOutlined,
  FileTextOutlined,
  HddOutlined,
  PlayCircleOutlined,
  PoweroffOutlined,
  ReloadOutlined,
  StopOutlined,
} from '@ant-design/icons-vue';
import RFB from '@novnc/novnc/core/rfb';
import {
  Button,
  Dropdown,
  Menu,
  MenuDivider,
  MenuItem,
  message,
  Modal,
  Segmented,
  Space,
  Spin,
  Form,
  FormItem,
  Input,
  InputNumber,
  Checkbox,
} from 'ant-design-vue';

import {
  getLxcConsoleApi,
  getLxcStatusByIdApi,
  operateLxcApi,
  cloneLxcApi,
  convertLxcToTemplateApi,
} from '#/api/pve/lxc';

import WebSshConsole from './WebSshConsole.vue';

defineOptions({ name: 'LxcConsole' });

const props = defineProps<{
  active: boolean;
  lxc: null | LxcContainerModel;
  lxcId: string;
}>();

// Console type: 'novnc' or 'ssh'
const consoleType = ref<'novnc' | 'ssh'>('ssh'); // Default to SSH for better LXC experience

const novncContainer = ref<HTMLElement | null>(null);
const consoleLoading = ref(false);
const consoleError = ref('');
const rfb = ref<null | RFB>(null);
const connected = ref(false);
const isManualReconnect = ref(false);

const lxcStatus = ref<any>({});
const statusTimer = ref<any>(null);
const actionLoading = ref(false);

const API_BASE = (import.meta.env.VITE_GLOB_API_URL || '').replace(/\/$/, '');

const buildBackendUrl = (path: string) => {
  if (!path) return '';
  if (path.startsWith('http://') || path.startsWith('https://')) {
    return path;
  }
  const base = API_BASE || window.location.origin;
  if (path.startsWith('/')) {
    return `${base}${path}`;
  }
  return `${base}/${path}`;
};

// --- Status polling ---

const fetchStatus = async () => {
  if (!props.lxcId) return;
  try {
    const res = await getLxcStatusByIdApi(props.lxcId);
    lxcStatus.value = (res as any)?.data || res || {};
  } catch (error) {
    console.warn('获取LXC状态失败:', error);
  }
};

const startPolling = () => {
  stopPolling();
  fetchStatus();
  statusTimer.value = setInterval(fetchStatus, 3000);
};

const stopPolling = () => {
  if (statusTimer.value) {
    clearInterval(statusTimer.value);
    statusTimer.value = null;
  }
};

// --- Power Actions ---

const formatBytes = (bytes: number) => {
  if (!bytes) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${Number.parseFloat((bytes / k ** i).toFixed(1))} ${sizes[i]}`;
};

const formatNetRate = (bytes: number) => {
  return `${formatBytes(bytes)}/s`;
};

const statusDisplay = computed(() => {
  const s = lxcStatus.value || {};
  const cpu = s.cpu ? (s.cpu * 100).toFixed(1) : '0';
  const memTotal = s.maxmem || 1;
  const memUsed = s.mem || 0;
  const memPercent = ((memUsed / memTotal) * 100).toFixed(1);
  const netIn = s.netin || 0;
  const netOut = s.netout || 0;

  const status = s.status || 'unknown';

  return {
    cpu: `${cpu}%`,
    mem: `${memPercent}%`,
    status,
    netIn,
    netOut,
  };
});

const lastNetStats = ref({ in: 0, out: 0, time: 0 });
const netRates = ref({ in: 0, out: 0 });

watch(
  () => lxcStatus.value,
  (newVal) => {
    if (!newVal) return;
    const now = Date.now();
    const currentIn = newVal.netin || 0;
    const currentOut = newVal.netout || 0;

    if (lastNetStats.value.time > 0) {
      const timeDiff = (now - lastNetStats.value.time) / 1000;
      if (timeDiff > 0) {
        netRates.value = {
          in: Math.max(0, (currentIn - lastNetStats.value.in) / timeDiff),
          out: Math.max(0, (currentOut - lastNetStats.value.out) / timeDiff),
        };
      }
    }
    lastNetStats.value = { in: currentIn, out: currentOut, time: now };
  },
);

const handlePowerAction = async (action: string) => {
  if (!props.lxcId) return;
  if (['shutdown', 'stop'].includes(action)) {
    Modal.confirm({
      title: '确认操作',
      content: `确定要执行 ${getActionLabel(action)} 操作吗？`,
      async onOk() {
        await executePowerAction(action);
      },
    });
  } else {
    await executePowerAction(action);
  }
};

const executePowerAction = async (action: string) => {
  actionLoading.value = true;
  try {
    await operateLxcApi(props.lxcId, action);
    message.success(`已发送 ${getActionLabel(action)} 命令`);
    setTimeout(fetchStatus, 1000);
  } catch (error: any) {
    message.error(error.message || '操作失败');
  } finally {
    actionLoading.value = false;
  }
};

const getActionLabel = (action: string) => {
  const map: Record<string, string> = {
    start: '启动',
    stop: '停止',
    shutdown: '关机',
    reboot: '重启',
  };
  return map[action] || action;
};


// Clone and Template Logic
const cloneModalVisible = ref(false);
const cloneForm = ref({
  newid: undefined as number | undefined,
  hostname: '',
  description: '',
  full: true,
  storage: '',
  target: '',
});


const handleCloneClick = () => {
  if (!props.lxc) return;
  
  // 检查容器状态并给出提示
  const status = lxcStatus.value?.status || props.lxc.status;
  if (status === 'running') {
    Modal.warning({
      title: '克隆运行中的容器',
      content: `容器正在运行。Proxmox VE 对运行中容器的克隆有以下限制：\n\n1. 完整克隆：需要先创建快照\n2. 链接克隆：可以直接克隆，但依赖源容器\n\n建议：\n• 如需完整克隆，请先停止容器或创建快照\n• 如需快速克隆，可选择"链接克隆"模式`,
      okText: '继续克隆',
      onOk: () => {
        openCloneModal();
      },
    });
  } else {
    openCloneModal();
  }
};

const openCloneModal = () => {
  if (!props.lxc) return;
  const status = lxcStatus.value?.status || props.lxc.status;
  
  cloneForm.value = {
    newid: undefined,
    hostname: `${props.lxc.name}-clone`,
    description: `克隆自 ${props.lxc.name}`,
    full: status === 'stopped', // 运行中默认链接克隆，停止时默认完整克隆
    storage: '',
    target: '',
  };
  cloneModalVisible.value = true;
};

const performClone = async () => {
  if (!props.lxcId) return;
  
  // 再次检查状态和克隆模式
  const status = lxcStatus.value?.status || props.lxc?.status;
  if (status === 'running' && cloneForm.value.full) {
    Modal.error({
      title: '无法执行完整克隆',
      content: '容器正在运行，无法进行完整克隆。\n\n请选择以下方案之一：\n1. 停止容器后再进行完整克隆\n2. 先创建快照，然后基于快照克隆\n3. 使用"链接克隆"模式（取消勾选"完整克隆"）',
    });
    return;
  }
  
  try {
    actionLoading.value = true;
    const res: any = await cloneLxcApi(props.lxcId, cloneForm.value);
    message.success(`克隆任务已提交，新容器ID: ${res.newid || '自动分配'}`);
    cloneModalVisible.value = false;
  } catch (error: any) {
    const errorMsg = error.message || error.response?.data?.detail || '未知错误';
    
    // 特殊处理常见错误
    if (errorMsg.includes('without snapshots')) {
      Modal.error({
        title: '克隆失败',
        content: '无法对运行中的容器进行完整克隆（需要快照）。\n\n解决方案：\n1. 停止容器后再克隆\n2. 先创建快照，然后基于快照克隆\n3. 使用"链接克隆"模式',
      });
    } else {
      message.error(`克隆失败: ${errorMsg}`);
    }
  } finally {
    actionLoading.value = false;
  }
};

const handleTemplateClick = () => {
  if (!props.lxc) return;
  
  Modal.confirm({
    title: '确认转换为模板',
    content: `确定要将容器 "${props.lxc.name}" (VMID: ${props.lxc.vmid}) 转换为模板吗？\n\n注意：\n1. 容器必须处于停止状态\n2. 转换后将无法直接启动，只能用于克隆\n3. 此操作不可逆`,
    okText: '确认转换',
    okType: 'primary',
    cancelText: '取消',
    onOk: async () => {
      try {
        actionLoading.value = true;
        await convertLxcToTemplateApi(props.lxcId);
        message.success('容器已成功转换为模板');
        setTimeout(fetchStatus, 1000);
      } catch (error: any) {
        message.error(`转换失败: ${error.message || '未知错误'}`);
      } finally {
        actionLoading.value = false;
      }
    },
  });
};
const handleReloadConsole = () => {
  if (consoleType.value === 'novnc') {
    initConsole();
  }
  // SSH console has its own reload button
};

const consoleTypeOptions = [
  {
    label: 'SSH 终端',
    value: 'ssh',
    icon: CodeOutlined,
  },
  {
    label: 'noVNC',
    value: 'novnc',
    icon: DesktopOutlined,
  },
];

// --- Console Logic ---

const initConsole = async () => {
  if (!props.lxcId) return;
  cleanupConsole();
  consoleLoading.value = true;
  consoleError.value = '';
  connected.value = false;

  try {
    const response: any = await getLxcConsoleApi(props.lxcId);
    const session = response?.data || response;
    const hasProxyUrl = session?.proxy_url || session?.proxy_path;
    const hasWebsocketUrl = session?.websocket_url;

    if (!hasProxyUrl && !hasWebsocketUrl) {
      throw new Error('未获取到控制台会话信息：缺少 WebSocket URL');
    }

    let wsUrl = '';
    let connectionMode = '';

    if (session.proxy_url) {
      wsUrl = session.proxy_url;
      connectionMode = 'proxy';
      if (!wsUrl.startsWith('ws://') && !wsUrl.startsWith('wss://')) {
        const baseUrl = buildBackendUrl('');
        const wsProtocol = baseUrl.startsWith('https') ? 'wss' : 'ws';
        const wsHost = baseUrl.replace(/^https?:\/\//, '').replace(/\/$/, '');
        wsUrl = `${wsProtocol}://${wsHost}${wsUrl.startsWith('/') ? wsUrl : `/${wsUrl}`}`;
      }
    } else if (session.proxy_path) {
      const baseUrl = buildBackendUrl('');
      const wsProtocol = baseUrl.startsWith('https') ? 'wss' : 'ws';
      const wsHost = baseUrl.replace(/^https?:\/\//, '').replace(/\/$/, '');
      wsUrl = `${wsProtocol}://${wsHost}${session.proxy_path.startsWith('/') ? session.proxy_path : `/${session.proxy_path}`}`;
      connectionMode = 'proxy';
    } else if (session.websocket_url) {
      wsUrl = session.websocket_url;
      connectionMode = 'direct';
    }

    if (connectionMode === 'proxy') {
      const accessStore = useAccessStore();
      const jwtToken = accessStore.accessToken;
      if (jwtToken) {
        const separator = wsUrl.includes('?') ? '&' : '?';
        wsUrl = `${wsUrl}${separator}jwt_token=${encodeURIComponent(jwtToken)}`;
      }
    }

    // LXC noVNC usually doesn't require password, or password check fails if sent as null.
    // We force empty string if password is null/undefined to avoid "password check failed" error.
    let effectivePassword = '';
    
    // 修复：优先使用ticket作为密码（PVE LXC控制台需要）
    if (session.ticket) {
      effectivePassword = session.ticket;
      console.log('Using ticket as password');
    } else if (session.password) {
      effectivePassword = session.password;
      console.log('Using session password');
    } else {
      try {
        const urlObj = new URL(wsUrl);
        const vncticketFromUrl = urlObj.searchParams.get('vncticket');
        if (vncticketFromUrl) {
          effectivePassword = vncticketFromUrl;  // Use ticket as password
          console.log('Using vncticket from URL as password');
        }
      } catch (e) {
        console.warn('Failed to parse vncticket from wsUrl', e);
      }
    }
    
    console.log('Connecting with password:', effectivePassword ? '***' : '(empty)');
    
    await nextTick();
    const container = novncContainer.value;
    if (!container) throw new Error('找不到 noVNC 容器元素');

    const client = new RFB(container, wsUrl, {
      credentials: { password: effectivePassword },
      shared: true,
      repeaterID: '',
    });

    rfb.value = client;
    
    // LXC控制台缩放配置
    client.scaleViewport = true;   // 初始化时先关闭
    client.resizeSession = false;   // 服务器不支持
    client.clipViewport = false;    // 不裁剪
    client.dragViewport = false;    // 禁用拖拽，因为我们要缩放

    client.background = '#000000';
    client.qualityLevel = 8;
    client.compressionLevel = 2;

    // 监听安全失败
    client.addEventListener('securityfailure', (e: any) => {
      console.error('Security failure:', e.detail.status, e.detail.reason);
      consoleError.value = `认证失败: ${e.detail.reason || '密码验证失败'}`;
      consoleLoading.value = false;
    });

    client.addEventListener('connect', () => {
      connected.value = true;
      consoleLoading.value = false;
      consoleError.value = '';
      
      // 连接成功后设置缩放以填满容器
      setTimeout(() => {
        if (rfb.value && container) {
          const canvas = container.querySelector('canvas');
          
          if (canvas) {
            rfb.value.scaleViewport = true;
            
            const containerWidth = container.clientWidth;
            const containerHeight = container.clientHeight;
            const canvasWidth = canvas.width;
            const canvasHeight = canvas.height;
            
            // 计算填满容器的缩放比例
            const scaleX = containerWidth / canvasWidth;
            const scaleY = containerHeight / canvasHeight;
            const scale = Math.max(scaleX, scaleY); // 用max填满，不留黑边
            
            const canvasElement = canvas as HTMLCanvasElement;
            canvasElement.style.width = `${canvasWidth * scale}px`;
            canvasElement.style.height = `${canvasHeight * scale}px`;
            canvasElement.style.maxWidth = 'none';
            canvasElement.style.maxHeight = 'none';
            
            console.log(`Applied scale: ${scale.toFixed(2)}`);
          }
          
          container.dispatchEvent(new Event('resize', { bubbles: true }));
        }
      }, 500);
    });

    client.addEventListener('disconnect', (e: any) => {
      consoleLoading.value = false;
      if (isManualReconnect.value) return;

      const reason =
        e?.detail?.clean === false && e?.detail?.reason
          ? e.detail.reason
          : '连接已断开';
      consoleError.value = reason;
    });

    client.addEventListener('credentialsrequired', () => {
      consoleError.value = '需要密码验证';
      consoleLoading.value = false;
    });
  } catch (error: any) {
    consoleError.value = error.message || '初始化失败';
    consoleLoading.value = false;
  }
};

const cleanupConsole = () => {
  if (rfb.value) {
    try {
      isManualReconnect.value = true;
      const currentRfb = rfb.value;
      rfb.value = null; // Prevent repeated calls
      
      // Use setTimeout to delay disconnect ensuring RFB object stability
      setTimeout(() => {
        try {
          if (currentRfb && typeof currentRfb.disconnect === 'function') {
            currentRfb.disconnect();
          }
        } catch (e) {
          console.warn('Disconnect failed:', e);
        }
        isManualReconnect.value = false;
      }, 100);
    } catch {
      isManualReconnect.value = false;
    }
  }
};

watch(
  () => props.active,
  (active) => {
    if (active) {
      startPolling();
      nextTick(() => setTimeout(initConsole, 50));
    } else {
      stopPolling();
      cleanupConsole();
    }
  },
  { immediate: true },
);

onBeforeUnmount(() => {
  stopPolling();
  cleanupConsole();
});
</script>

<template>
  <div class="console-layout">
    <div class="console-toolbar">
      <!-- Left: Resources Status & Console Type Switcher -->
      <div class="resources-info">
        <Space size="large">
          <!-- Console Type Switcher -->
          <Segmented
            v-model:value="consoleType"
            :options="consoleTypeOptions"
            size="small"
          >
            <template #label="{ payload }">
              <div class="console-type-option">
                <component :is="payload.icon" class="icon" />
                <span>{{ payload.label }}</span>
              </div>
            </template>
          </Segmented>

          <div class="info-item">
            <AppstoreOutlined class="icon" />
            <span class="value">{{ statusDisplay.cpu }}</span>
          </div>
          <div class="info-item">
            <HddOutlined class="icon" />
            <span class="value">{{ statusDisplay.mem }}</span>
          </div>
          <div class="info-item">
            <Space size="small">
              <span
                ><ArrowUpOutlined class="icon-up" />
                {{ formatNetRate(netRates.out) }}</span
              >
              <span
                ><ArrowDownOutlined class="icon-down" />
                {{ formatNetRate(netRates.in) }}</span
              >
            </Space>
          </div>
        </Space>
      </div>

      <!-- Right: Actions -->
      <div class="actions-group">
        <Space>
          <!-- Power Actions -->
          <template v-if="statusDisplay.status === 'stopped'">
            <Button
              :loading="actionLoading"
              type="primary"
              @click="handlePowerAction('start')"
            >
              <template #icon><PlayCircleOutlined /></template>
              启动
            </Button>
          </template>

          <template v-else>
            <Dropdown.Button
              :loading="actionLoading"
              @click="handlePowerAction('shutdown')"
              type="default"
              danger
            >
              <template #icon><DownOutlined /></template>
              <PoweroffOutlined />
              关机
              <template #overlay>
                <Menu @click="(e) => handlePowerAction(e.key as string)">
                  <MenuItem key="reboot">
                    <Space><ReloadOutlined /> 重启</Space>
                  </MenuItem>
                  <MenuDivider />
                  <MenuItem key="stop">
                    <Space><StopOutlined /> 强制停止</Space>
                  </MenuItem>
                </Menu>
              </template>
            </Dropdown.Button>
          </template>

          <!-- More Actions -->
          <Dropdown>
            <template #overlay>
              <Menu>
                <MenuItem key="clone" @click="handleCloneClick">
                  <Space><CopyOutlined /> 克隆</Space>
                </MenuItem>
                <MenuItem key="template" @click="handleTemplateClick">
                  <Space><FileTextOutlined /> 转换为模板</Space>
                </MenuItem>
              </Menu>
            </template>
            <Button> 更多 <DownOutlined /> </Button>
          </Dropdown>

          <Button
            v-if="consoleType === 'novnc'"
            type="text"
            @click="handleReloadConsole"
          >
            <template #icon><ReloadOutlined /></template>
          </Button>
        </Space>
      </div>
    </div>

    <!-- Console Area -->
    <div class="console-viewport">
      <!-- SSH Console -->
      <WebSshConsole
        v-if="consoleType === 'ssh'"
        :lxc-id="lxcId"
        :lxc="lxc"
        :active="active"
      />

      <!-- noVNC Console -->
      <div v-else class="pve-console-wrapper">
        <div v-if="consoleLoading" class="console-overlay">
          <Spin size="large" />
          <p class="mt-4 text-gray-400">正在建立连接...</p>
        </div>
        <div v-else-if="consoleError" class="console-overlay">
          <p class="mb-4 text-red-500">{{ consoleError }}</p>
          <Button type="primary" @click="initConsole">重试</Button>
        </div>
        <div
          ref="novncContainer"
          class="novnc-container"
          :style="{ opacity: consoleLoading || consoleError ? 0 : 1 }"
        ></div>
      </div>
    </div>

    <!-- Clone Modal -->
    <Modal
      v-model:open="cloneModalVisible"
      title="克隆容器"
      :confirm-loading="actionLoading"
      ok-text="开始克隆"
      cancel-text="取消"
      @ok="performClone"
      width="600px"
    >
      <div v-if="lxc">
        <div class="mb-4 rounded border border-blue-200 bg-blue-50 p-3 text-blue-700">
          <div class="mb-1 font-bold">源容器信息</div>
          名称: <b>{{ lxc.name }}</b> (VMID: {{ lxc.vmid }})
        </div>

        <Form layout="vertical">
          <FormItem label="新容器ID">
            <InputNumber
              v-model:value="cloneForm.newid"
              placeholder="留空自动分配"
              class="w-full"
              :min="100"
            />
            <div class="mt-1 text-xs text-gray-400">
              留空将自动分配下一个可用的 VMID
            </div>
          </FormItem>

          <FormItem label="主机名">
            <Input
              v-model:value="cloneForm.hostname"
              placeholder="新容器的主机名"
            />
          </FormItem>

          <FormItem label="描述">
            <Input
              v-model:value="cloneForm.description"
              placeholder="新容器的描述信息"
            />
          </FormItem>

          <FormItem label="克隆模式">
            <Checkbox v-model:checked="cloneForm.full">
              完整克隆
            </Checkbox>
            <div class="ml-6 mt-1 text-xs text-gray-400">
              <div class="mb-1">
                <b>完整克隆：</b>复制所有数据，新容器完全独立（推荐用于生产环境）
              </div>
              <div class="mb-1">
                <b>链接克隆：</b>创建引用，速度快但依赖源容器（适合测试环境）
              </div>
              <div 
                v-if="lxcStatus?.status === 'running'" 
                class="mt-2 rounded bg-yellow-50 p-2 text-yellow-700"
              >
                ⚠️ 容器正在运行，完整克隆需要先创建快照或停止容器
              </div>
            </div>
          </FormItem>

          <FormItem label="目标存储（可选）">
            <Input
              v-model:value="cloneForm.storage"
              placeholder="留空使用默认存储"
            />
          </FormItem>

          <FormItem label="目标节点（可选）">
            <Input
              v-model:value="cloneForm.target"
              placeholder="留空克隆到同一节点"
            />
            <div class="mt-1 text-xs text-gray-400">
              跨节点克隆需要共享存储或完整克隆模式
            </div>
          </FormItem>
        </Form>
      </div>
    </Modal>
  </div>
</template>

<style scoped>
.console-layout {
  position: absolute;
  top: 0;
  left: 0;
  display: flex;
  flex-direction: column;
  width: 100%;
  height: 100%;
  overflow: hidden;
  background-color: var(--color-bg-2);
}

/* Toolbar Styling */
.console-toolbar {
  z-index: 10;
  display: flex;
  flex-shrink: 0;
  align-items: center;
  justify-content: space-between;
  height: 50px;
  padding: 0 16px;
  background-color: var(--color-bg-1);
  border-bottom: 1px solid var(--border-color);
}

.resources-info {
  font-family:
    -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue',
    Arial, sans-serif;
  font-size: 14px;
  color: var(--color-text-1);
}

.info-item {
  display: flex;
  gap: 6px;
  align-items: center;
}

.info-item .icon {
  font-size: 16px;
  color: var(--color-text-3);
}

.info-item .value {
  font-weight: 500;
}

.info-item .icon-up {
  color: #52c41a;
}

.info-item .icon-down {
  color: #1890ff;
}

/* Console Type Switcher */
.console-type-option {
  display: flex;
  gap: 6px;
  align-items: center;
}

.console-type-option .icon {
  font-size: 14px;
}

/* Text colors */
.text-error {
  color: #ff4d4f;
}

/* Console Viewport */
.console-viewport {
  position: relative;
  flex: 1;
  overflow: hidden;
  background: #000;
}

.pve-console-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  background: #000;
}

.console-overlay {
  position: absolute;
  inset: 0;
  z-index: 5;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: rgb(0 0 0 / 80%);
}

.novnc-container {
  display: block;
  width: 100%;
  height: 100%;
  position: relative;
  overflow: hidden;
}

.novnc-container :deep(div) {
  width: 100% !important;
  height: 100% !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
}

.novnc-container :deep(canvas) {
  outline: none !important;
  display: block !important;
  margin: 0 !important;
}
</style>
