<script setup lang="ts">
import type { PVEServerModel } from '#/api/pve/types';

import { computed, nextTick, onBeforeUnmount, ref, watch } from 'vue';

import { FitAddon } from '@xterm/addon-fit';
import { Terminal } from '@xterm/xterm';
import '@xterm/xterm/css/xterm.css';
import {
  Alert,
  Button,
  Form,
  FormItem,
  Input,
  InputPassword,
  message,
  Modal,
  Select,
  Space,
  Spin,
} from 'ant-design-vue';

import { createNodeShellSessionApi, getPveNodesApi } from '#/api/pve/node';

defineOptions({ name: 'NodeShellModal' });

const props = defineProps({
  open: { type: Boolean, default: false },
  server: {
    type: Object as () => PVEServerModel | undefined,
    default: undefined,
  },
});

const emit = defineEmits(['update:open']);

type Stage = 'auth' | 'terminal';

const stage = ref<Stage>('auth');
const connecting = ref(false);
const connected = ref(false);
const errorText = ref('');

const nodes = ref<any[]>([]);
const formRef = ref();
const formState = ref({ node: undefined as string | undefined, username: '', password: '' });

const terminalContainer = ref<HTMLElement | null>(null);
let terminal: null | Terminal = null;
let websocket: null | WebSocket = null;
let resizeObserver: null | ResizeObserver = null;

const title = computed(() =>
  props.server ? `Shell: ${props.server.name} (${props.server.host})` : 'PVE Shell',
);

/** token_id 形如 root@pam!one，取 ! 之前作为用户名默认值 */
const defaultUsername = (tokenId?: string) =>
  tokenId ? (tokenId.split('!')[0] ?? '') : '';

const fetchNodes = async (serverId: number) => {
  try {
    const res: any = await getPveNodesApi(serverId);
    const data = Array.isArray(res) ? res : (res?.results ?? res?.data ?? []);
    nodes.value = Array.isArray(data) ? data : [];
    if (!formState.value.node && nodes.value.length > 0) {
      formState.value.node = nodes.value[0]?.node;
    }
  } catch {
    message.error('获取节点列表失败');
  }
};

const teardown = () => {
  resizeObserver?.disconnect();
  resizeObserver = null;
  websocket?.close();
  websocket = null;
  terminal?.dispose();
  terminal = null;
  connected.value = false;
};

const buildWsUrl = (proxyUrl?: string, proxyPath?: string) => {
  if (proxyUrl?.startsWith('ws')) return proxyUrl;
  if (!proxyPath?.startsWith('/')) {
    // 宁可明确报错，也不要拼出 ws://host/undefined 这种地址
    throw new Error('后端未返回有效的 WebSocket 地址（proxy_url / proxy_path）');
  }
  const scheme = globalThis.location.protocol === 'https:' ? 'wss' : 'ws';
  return `${scheme}://${globalThis.location.host}${proxyPath}`;
};

/**
 * 等待终端容器挂载。Modal 的内容通过 teleport 渲染，单次 nextTick
 * 不保证拿得到 ref，之前这里直接 `return` 导致连接被静默跳过。
 */
const waitForContainer = async (): Promise<HTMLElement | null> => {
  for (let i = 0; i < 20; i++) {
    if (terminalContainer.value) return terminalContainer.value;
    await new Promise((resolve) => {
      globalThis.requestAnimationFrame(() => resolve(null));
    });
  }
  return null;
};

const openTerminal = async (wsUrl: string) => {
  stage.value = 'terminal';
  await nextTick();

  const term = new Terminal({
    cursorBlink: true,
    fontSize: 14,
    fontFamily: 'Menlo, Monaco, Consolas, "Courier New", monospace',
    theme: { background: '#1e1e1e', foreground: '#d4d4d4' },
    scrollback: 5000,
  });
  const fit = new FitAddon();
  term.loadAddon(fit);
  terminal = term;

  // 先建连，再渲染终端：终端尺寸/挂载出问题不能连累 WebSocket。
  const ws = new WebSocket(wsUrl);
  websocket = ws;

  const container = await waitForContainer();
  if (container) {
    try {
      term.open(container);
      fit.fit();
    } catch (error: any) {
      errorText.value = `终端渲染失败: ${error?.message || error}`;
    }
  } else {
    errorText.value = '终端容器未就绪，输出无法显示';
  }

  ws.addEventListener('open', () => {
    connected.value = true;
    connecting.value = false;
    ws.send(JSON.stringify({ type: 'resize', cols: term.cols, rows: term.rows }));
    term.focus();
  });

  // 后端已完成 termproxy 握手与分帧，这里收到的就是终端输出
  ws.addEventListener('message', (event) => {
    if (typeof event.data === 'string') term.write(event.data);
  });

  ws.addEventListener('error', () => {
    errorText.value = `WebSocket 连接失败: ${wsUrl}`;
    connecting.value = false;
  });

  ws.addEventListener('close', (event) => {
    connected.value = false;
    connecting.value = false;
    // 1006 = 握手未完成就断开，通常是 /ws/ 没被反代转发，或后端拒绝了会话令牌
    if (!event.wasClean && event.code === 1006 && !errorText.value) {
      errorText.value =
        '连接被中断（1006）：请检查 /ws/ 反向代理是否生效、会话令牌是否已过期';
    }
    term.write('\r\n\u001B[33m连接已断开\u001B[0m\r\n');
  });

  term.onData((data) => {
    if (ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: 'input', data }));
    }
  });

  term.onResize(({ cols, rows }) => {
    if (ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: 'resize', cols, rows }));
    }
  });

  if (container) {
    resizeObserver = new ResizeObserver(() => {
      try {
        fit.fit();
      } catch {
        // 容器隐藏时 fit 会抛错，忽略
      }
    });
    resizeObserver.observe(container);
  }
};

const handleConnect = async () => {
  if (!props.server) return;
  try {
    await formRef.value.validate();
  } catch {
    return;
  }

  connecting.value = true;
  errorText.value = '';
  try {
    const res = await createNodeShellSessionApi(props.server.id, {
      node: formState.value.node!,
      username: formState.value.username.trim(),
      password: formState.value.password,
    });
    // 密码用完即弃，不留在内存里
    formState.value.password = '';
    await openTerminal(buildWsUrl(res.proxy_url, res.proxy_path));
  } catch (error: any) {
    connecting.value = false;
    errorText.value = error?.message || '创建 Shell 会话失败';
  }
};

const handleClose = () => {
  teardown();
  emit('update:open', false);
};

watch(
  () => props.open,
  (isOpen) => {
    if (isOpen) {
      stage.value = 'auth';
      errorText.value = '';
      connecting.value = false;
      nodes.value = [];
      formState.value = {
        node: undefined,
        username: defaultUsername(props.server?.token_id),
        password: '',
      };
      if (props.server) fetchNodes(props.server.id);
    } else {
      teardown();
    }
  },
);

onBeforeUnmount(teardown);
</script>

<template>
  <Modal
    :open="open"
    :title="title"
    :width="stage === 'terminal' ? 1000 : 560"
    :mask-closable="false"
    :footer="null"
    destroy-on-close
    @cancel="handleClose"
  >
    <!-- 第一步：填凭据 -->
    <template v-if="stage === 'auth'">
      <Alert
        type="info"
        show-icon
        class="mb-4"
        message="PVE 的 Shell 不接受 API Token，需要用 PVE 用户名和密码登录。凭据仅用于换取一次性 ticket，不会被保存。"
      />

      <Form
        ref="formRef"
        :model="formState"
        :label-col="{ style: { width: '90px' } }"
      >
        <FormItem
          label="节点"
          name="node"
          :rules="[{ required: true, message: '请选择节点' }]"
        >
          <Select
            v-model:value="formState.node"
            placeholder="选择节点"
            :options="nodes.map((n) => ({ label: n.node, value: n.node }))"
          />
        </FormItem>
        <FormItem
          label="用户名"
          name="username"
          :rules="[
            { required: true, message: '请输入用户名' },
            {
              pattern: /@/,
              message: '需带 realm，如 root@pam',
            },
          ]"
        >
          <Input v-model:value="formState.username" placeholder="root@pam" />
        </FormItem>
        <FormItem
          label="密码"
          name="password"
          :rules="[{ required: true, message: '请输入密码' }]"
        >
          <InputPassword
            v-model:value="formState.password"
            placeholder="PVE 登录密码"
            @press-enter="handleConnect"
          />
        </FormItem>
      </Form>

      <Alert v-if="errorText" type="error" show-icon :message="errorText" />

      <div class="mt-4 text-right">
        <Space>
          <Button @click="handleClose">取消</Button>
          <Button type="primary" :loading="connecting" @click="handleConnect">
            连接
          </Button>
        </Space>
      </div>
    </template>

    <!-- 第二步：终端 -->
    <template v-else>
      <Spin :spinning="connecting" tip="正在连接...">
        <div
          ref="terminalContainer"
          class="h-[520px] w-full rounded bg-[#1e1e1e] p-2"
        ></div>
      </Spin>

      <!-- 终端阶段同样要显示错误，否则失败时只剩一块黑屏 -->
      <Alert
        v-if="errorText"
        type="error"
        show-icon
        class="mt-3"
        :message="errorText"
      />

      <div class="mt-3 flex items-center justify-between">
        <span class="text-xs text-gray-500">
          {{ connected ? '● 已连接' : '○ 未连接' }} · 节点 {{ formState.node }}
        </span>
        <Button @click="handleClose">关闭</Button>
      </div>
    </template>
  </Modal>
</template>
