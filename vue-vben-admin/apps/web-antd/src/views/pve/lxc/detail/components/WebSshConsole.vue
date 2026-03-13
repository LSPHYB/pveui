<script setup lang="ts">
import type { LxcContainerModel } from '#/api/pve/types';

import { computed, nextTick, onBeforeUnmount, ref, watch } from 'vue';

import { useAccessStore } from '@vben/stores';

import {
  BgColorsOutlined,
  MinusOutlined,
  PlusOutlined,
  ReloadOutlined,
  SettingOutlined,
} from '@ant-design/icons-vue';
import { Terminal } from '@xterm/xterm';
import { FitAddon } from '@xterm/addon-fit';
import { WebLinksAddon } from '@xterm/addon-web-links';
import '@xterm/xterm/css/xterm.css';
import { Button, Dropdown, Menu, MenuItem, Space, Spin, Switch, InputNumber } from 'ant-design-vue';

import { getLxcSshConsoleApi } from '#/api/pve/lxc';

defineOptions({ name: 'WebSshConsole' });

const props = defineProps<{
  active: boolean;
  lxc: null | LxcContainerModel;
  lxcId: string;
}>();

// Terminal state
const terminalContainer = ref<HTMLElement | null>(null);
const terminalLoading = ref(false);
const terminalError = ref('');
const terminal = ref<null | Terminal>(null);
const fitAddon = ref<null | FitAddon>(null);
const websocket = ref<null | WebSocket>(null);
const connected = ref(false);

// Customization options
const fontSize = ref(14);
const currentTheme = ref('vscode-dark');
const cursorStyle = ref<'block' | 'underline' | 'bar'>('block');
const cursorBlink = ref(true);
const opacity = ref(100);

// Theme presets
const themes = {
  'vscode-dark': {
    name: 'VS Code Dark',
    background: '#1e1e1e',
    foreground: '#d4d4d4',
    cursor: '#ffffff',
    cursorAccent: '#000000',
    selectionBackground: '#264f78',
    black: '#000000',
    red: '#cd3131',
    green: '#0dbc79',
    yellow: '#e5e510',
    blue: '#2472c8',
    magenta: '#bc3fbc',
    cyan: '#11a8cd',
    white: '#e5e5e5',
    brightBlack: '#666666',
    brightRed: '#f14c4c',
    brightGreen: '#23d18b',
    brightYellow: '#f5f543',
    brightBlue: '#3b8eea',
    brightMagenta: '#d670d6',
    brightCyan: '#29b8db',
    brightWhite: '#ffffff',
  },
  'dracula': {
    name: 'Dracula',
    background: '#282a36',
    foreground: '#f8f8f2',
    cursor: '#f8f8f2',
    cursorAccent: '#282a36',
    selectionBackground: '#44475a',
    black: '#21222c',
    red: '#ff5555',
    green: '#50fa7b',
    yellow: '#f1fa8c',
    blue: '#bd93f9',
    magenta: '#ff79c6',
    cyan: '#8be9fd',
    white: '#f8f8f2',
    brightBlack: '#6272a4',
    brightRed: '#ff6e6e',
    brightGreen: '#69ff94',
    brightYellow: '#ffffa5',
    brightBlue: '#d6acff',
    brightMagenta: '#ff92df',
    brightCyan: '#a4ffff',
    brightWhite: '#ffffff',
  },
  'monokai': {
    name: 'Monokai',
    background: '#272822',
    foreground: '#f8f8f2',
    cursor: '#f8f8f0',
    cursorAccent: '#272822',
    selectionBackground: '#49483e',
    black: '#272822',
    red: '#f92672',
    green: '#a6e22e',
    yellow: '#f4bf75',
    blue: '#66d9ef',
    magenta: '#ae81ff',
    cyan: '#a1efe4',
    white: '#f8f8f2',
    brightBlack: '#75715e',
    brightRed: '#f92672',
    brightGreen: '#a6e22e',
    brightYellow: '#f4bf75',
    brightBlue: '#66d9ef',
    brightMagenta: '#ae81ff',
    brightCyan: '#a1efe4',
    brightWhite: '#f9f8f5',
  },
  'solarized-dark': {
    name: 'Solarized Dark',
    background: '#002b36',
    foreground: '#839496',
    cursor: '#839496',
    cursorAccent: '#073642',
    selectionBackground: '#073642',
    black: '#073642',
    red: '#dc322f',
    green: '#859900',
    yellow: '#b58900',
    blue: '#268bd2',
    magenta: '#d33682',
    cyan: '#2aa198',
    white: '#eee8d5',
    brightBlack: '#002b36',
    brightRed: '#cb4b16',
    brightGreen: '#586e75',
    brightYellow: '#657b83',
    brightBlue: '#839496',
    brightMagenta: '#6c71c4',
    brightCyan: '#93a1a1',
    brightWhite: '#fdf6e3',
  },
  'github': {
    name: 'GitHub',
    background: '#ffffff',
    foreground: '#24292e',
    cursor: '#044289',
    cursorAccent: '#ffffff',
    selectionBackground: '#0366d625',
    black: '#24292e',
    red: '#d73a49',
    green: '#22863a',
    yellow: '#b08800',
    blue: '#005cc5',
    magenta: '#5a32a3',
    cyan: '#3192aa',
    white: '#6a737d',
    brightBlack: '#959da5',
    brightRed: '#d73a49',
    brightGreen: '#22863a',
    brightYellow: '#dbab09',
    brightBlue: '#005cc5',
    brightMagenta: '#5a32a3',
    brightCyan: '#3192aa',
    brightWhite: '#d1d5da',
  },
  'nord': {
    name: 'Nord',
    background: '#2e3440',
    foreground: '#d8dee9',
    cursor: '#d8dee9',
    cursorAccent: '#2e3440',
    selectionBackground: '#434c5e',
    black: '#3b4252',
    red: '#bf616a',
    green: '#a3be8c',
    yellow: '#ebcb8b',
    blue: '#81a1c1',
    magenta: '#b48ead',
    cyan: '#88c0d0',
    white: '#e5e9f0',
    brightBlack: '#4c566a',
    brightRed: '#bf616a',
    brightGreen: '#a3be8c',
    brightYellow: '#ebcb8b',
    brightBlue: '#81a1c1',
    brightMagenta: '#b48ead',
    brightCyan: '#8fbcbb',
    brightWhite: '#eceff4',
  },
};

const currentThemeColors = computed(() => themes[currentTheme.value as keyof typeof themes]);

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

const initTerminal = async () => {
  if (!props.lxcId) return;
  cleanupTerminal();
  terminalLoading.value = true;
  terminalError.value = '';
  connected.value = false;

  try {
    // Get SSH console session from backend
    const response: any = await getLxcSshConsoleApi(props.lxcId);
    const session = response?.data || response;

    if (!session?.websocket_url && !session?.proxy_url) {
      throw new Error('未获取到SSH控制台会话信息：缺少 WebSocket URL');
    }

    let wsUrl = session.websocket_url || session.proxy_url || '';

    // Handle relative URLs
    if (!wsUrl.startsWith('ws://') && !wsUrl.startsWith('wss://')) {
      const baseUrl = buildBackendUrl('');
      const wsProtocol = baseUrl.startsWith('https') ? 'wss' : 'ws';
      const wsHost = baseUrl.replace(/^https?:\/\//, '').replace(/\/$/, '');
      wsUrl = `${wsProtocol}://${wsHost}${wsUrl.startsWith('/') ? wsUrl : `/${wsUrl}`}`;
    }

    // Add JWT token for proxy authentication
    const accessStore = useAccessStore();
    const jwtToken = accessStore.accessToken;
    if (jwtToken && wsUrl.includes('/proxy/')) {
      const separator = wsUrl.includes('?') ? '&' : '?';
      wsUrl = `${wsUrl}${separator}jwt_token=${encodeURIComponent(jwtToken)}`;
    }

    await nextTick();
    const container = terminalContainer.value;
    if (!container) throw new Error('找不到终端容器元素');

    // Create xterm.js terminal with current theme
    const term = new Terminal({
      fontSize: fontSize.value,
      fontFamily: 'Monaco, "Cascadia Code", Consolas, "Courier New", monospace',
      fontWeight: '400',
      fontWeightBold: '700',
      letterSpacing: 0,
      lineHeight: 1.2,
      theme: currentThemeColors.value,
      cursorBlink: cursorBlink.value,
      cursorStyle: cursorStyle.value,
      scrollback: 10000,
      tabStopWidth: 8,
      allowProposedApi: true,
      smoothScrollDuration: 100,
      fastScrollModifier: 'shift',
    });

    terminal.value = term;

    // Add fit addon for responsive sizing
    const fit = new FitAddon();
    fitAddon.value = fit;
    term.loadAddon(fit);

    // Add web links addon for clickable URLs
    const webLinksAddon = new WebLinksAddon();
    term.loadAddon(webLinksAddon);

    term.open(container);
    fit.fit();

    // Create WebSocket connection
    const ws = new WebSocket(wsUrl);
    websocket.value = ws;

    ws.onopen = () => {
      connected.value = true;
      terminalLoading.value = false;
      terminalError.value = '';
      console.log('WebSSH connected');

      // Send terminal size to server
      ws.send(
        JSON.stringify({
          type: 'resize',
          cols: term.cols,
          rows: term.rows,
        }),
      );
    };

    ws.onmessage = (event) => {
      if (typeof event.data === 'string') {
        term.write(event.data);
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      terminalError.value = 'WebSocket 连接错误';
      terminalLoading.value = false;
    };

    ws.onclose = () => {
      connected.value = false;
      terminalLoading.value = false;
      if (!terminalError.value) {
        terminalError.value = '连接已断开';
      }
      console.log('WebSSH disconnected');
    };

    // Send user input to backend
    term.onData((data: string) => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(
          JSON.stringify({
            type: 'input',
            data: data,
          }),
        );
      }
    });

    // Handle terminal resize
    term.onResize(({ cols, rows }: { cols: number; rows: number }) => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(
          JSON.stringify({
            type: 'resize',
            cols: cols,
            rows: rows,
          }),
        );
      }
    });

    // Auto-fit on window resize
    const resizeObserver = new ResizeObserver(() => {
      if (fitAddon.value && terminal.value) {
        try {
          fitAddon.value.fit();
        } catch (e) {
          console.warn('Fit failed:', e);
        }
      }
    });

    resizeObserver.observe(container);

    // Store resize observer for cleanup
    (term as any)._resizeObserver = resizeObserver;
  } catch (error: any) {
    terminalError.value = error.message || '初始化SSH终端失败';
    terminalLoading.value = false;
    console.error('SSH Terminal init error:', error);
  }
};

const cleanupTerminal = () => {
  if (websocket.value) {
    try {
      websocket.value.close();
    } catch (e) {
      console.warn('WebSocket close failed:', e);
    }
    websocket.value = null;
  }

  if (terminal.value) {
    try {
      const resizeObserver = (terminal.value as any)._resizeObserver;
      if (resizeObserver) {
        resizeObserver.disconnect();
      }
      terminal.value.dispose();
    } catch (e) {
      console.warn('Terminal dispose failed:', e);
    }
    terminal.value = null;
  }

  fitAddon.value = null;
  connected.value = false;
};

const handleReload = () => {
  initTerminal();
};

const increaseFontSize = () => {
  if (fontSize.value < 32) {
    fontSize.value += 2;
    updateTerminalOptions();
  }
};

const decreaseFontSize = () => {
  if (fontSize.value > 10) {
    fontSize.value -= 2;
    updateTerminalOptions();
  }
};

const changeTheme = (themeKey: string) => {
  currentTheme.value = themeKey;
  updateTerminalOptions();
};

const updateTerminalOptions = () => {
  if (terminal.value) {
    terminal.value.options.fontSize = fontSize.value;
    terminal.value.options.theme = currentThemeColors.value;
    terminal.value.options.cursorStyle = cursorStyle.value;
    terminal.value.options.cursorBlink = cursorBlink.value;
    fitAddon.value?.fit();
  }
};

watch(
  () => props.active,
  (active) => {
    if (active) {
      nextTick(() => setTimeout(initTerminal, 50));
    } else {
      cleanupTerminal();
    }
  },
  { immediate: true },
);

watch([cursorStyle, cursorBlink, opacity], () => {
  updateTerminalOptions();
});

onBeforeUnmount(() => {
  cleanupTerminal();
});
</script>

<template>
  <div class="ssh-console-layout">
    <div class="ssh-toolbar">
      <div class="ssh-toolbar-left">
        <span class="connection-status" :class="{ connected }">
          <span class="status-dot"></span>
          {{ connected ? 'SSH 已连接' : 'SSH 未连接' }}
        </span>
      </div>
      <div class="ssh-toolbar-right">
        <Space>
          <!-- Theme Selector -->
          <Dropdown>
            <Button type="text" size="small">
              <template #icon><BgColorsOutlined /></template>
              {{ currentThemeColors.name }}
            </Button>
            <template #overlay>
              <Menu @click="({ key }) => changeTheme(String(key))">
                <MenuItem v-for="(theme, key) in themes" :key="key">
                  {{ theme.name }}
                </MenuItem>
              </Menu>
            </template>
          </Dropdown>

          <!-- Font Size Controls -->
          <Button
            type="text"
            size="small"
            :disabled="!connected || fontSize <= 10"
            @click="decreaseFontSize"
          >
            <template #icon><MinusOutlined /></template>
          </Button>
          <span class="font-size-display">{{ fontSize }}px</span>
          <Button
            type="text"
            size="small"
            :disabled="!connected || fontSize >= 32"
            @click="increaseFontSize"
          >
            <template #icon><PlusOutlined /></template>
          </Button>

          <!-- Cursor Settings -->
          <Dropdown>
            <Button type="text" size="small">
              <template #icon><SettingOutlined /></template>
              设置
            </Button>
            <template #overlay>
              <Menu selectable>
                <MenuItem key="cursor-blink">
                  <div class="setting-item">
                    <span>光标闪烁</span>
                    <Switch v-model:checked="cursorBlink" size="small" />
                  </div>
                </MenuItem>
                <MenuItem key="cursor-block" @click="cursorStyle = 'block'">
                  光标样式: Block {{ cursorStyle === 'block' ? '✓' : '' }}
                </MenuItem>
                <MenuItem key="cursor-underline" @click="cursorStyle = 'underline'">
                  光标样式: Underline {{ cursorStyle === 'underline' ? '✓' : '' }}
                </MenuItem>
                <MenuItem key="cursor-bar" @click="cursorStyle = 'bar'">
                  光标样式: Bar {{ cursorStyle === 'bar' ? '✓' : '' }}
                </MenuItem>
                <MenuItem key="opacity">
                  <div class="setting-item setting-item-vertical">
                    <span>透明度 ({{ opacity }}%)</span>
                    <InputNumber
                      v-model:value="opacity"
                      :min="50"
                      :max="100"
                      :step="10"
                      size="small"
                      style="width: 100%"
                    />
                  </div>
                </MenuItem>
              </Menu>
            </template>
          </Dropdown>

          <Button type="text" @click="handleReload">
            <template #icon><ReloadOutlined /></template>
            重连
          </Button>
        </Space>
      </div>
    </div>

    <div class="ssh-terminal-viewport" :style="{ opacity: opacity / 100 }">
      <div class="ssh-terminal-wrapper">
        <div v-if="terminalLoading" class="terminal-overlay">
          <Spin size="large" />
          <p class="mt-4 text-gray-400">正在建立SSH连接...</p>
        </div>
        <div v-else-if="terminalError" class="terminal-overlay">
          <p class="mb-4 text-red-500">{{ terminalError }}</p>
          <Button type="primary" @click="initTerminal">重试</Button>
        </div>
        <div
          ref="terminalContainer"
          class="xterm-container"
          :style="{ opacity: terminalLoading || terminalError ? 0 : 1 }"
        ></div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.ssh-console-layout {
  position: absolute;
  top: 0;
  left: 0;
  display: flex;
  flex-direction: column;
  width: 100%;
  height: 100%;
  overflow: hidden;
  background-color: #1e1e1e;
}

.ssh-toolbar {
  z-index: 10;
  display: flex;
  flex-shrink: 0;
  align-items: center;
  justify-content: space-between;
  height: 40px;
  padding: 0 16px;
  background-color: #2d2d30;
  border-bottom: 1px solid #3e3e42;
}

.ssh-toolbar-left {
  display: flex;
  align-items: center;
}

/* 强制覆盖 Ant Design 按钮在深色工具栏中的样式 */
.ssh-toolbar :deep(.ant-btn) {
  color: #e5e5e5;
}

.ssh-toolbar :deep(.ant-btn:hover) {
  color: #ffffff;
  background-color: rgba(255, 255, 255, 0.1);
}

.ssh-toolbar :deep(.ant-btn[disabled]) {
  color: #555555;
}

.connection-status {
  display: flex;
  gap: 8px;
  align-items: center;
  font-size: 13px;
  color: #cccccc;
}

.status-dot {
  width: 8px;
  height: 8px;
  background-color: #cd3131;
  border-radius: 50%;
}

.connection-status.connected .status-dot {
  background-color: #0dbc79;
}

.ssh-toolbar-right {
  display: flex;
  align-items: center;
}

.font-size-display {
  font-size: 12px;
  color: #cccccc;
}

.setting-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-width: 180px;
  padding: 0 8px;
}

.setting-item-vertical {
  flex-direction: column;
  align-items: flex-start;
  gap: 8px;
}

.ssh-terminal-viewport {
  position: relative;
  flex: 1;
  overflow: hidden;
  background: #1e1e1e;
  transition: opacity 0.2s ease;
}

.ssh-terminal-wrapper {
  display: flex;
  align-items: flex-start;
  justify-content: flex-start;
  width: 100%;
  height: 100%;
  padding: 8px;
  background: #1e1e1e;
}

.terminal-overlay {
  position: absolute;
  inset: 0;
  z-index: 5;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: rgb(0 0 0 / 80%);
}

.xterm-container {
  width: 100%;
  height: 100%;
}

/* Ensure xterm.js properly fills the container */
.xterm-container :deep(.xterm) {
  height: 100%;
 padding: 0;
}

.xterm-container :deep(.xterm-viewport) {
  overflow-y: auto;
}

.xterm-container :deep(.xterm-screen) {
  height: 100%;
}
</style>
