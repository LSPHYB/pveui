<script setup lang="ts">
import type { Core, ElementDefinition, LayoutOptions } from 'cytoscape';

import { nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue';

import { useResizeObserver } from '@vueuse/core';

import Cytoscape from 'cytoscape';
import CxtMenu from 'cytoscape-cxtmenu';
import EdgeHandles from 'cytoscape-edgehandles';

import { getStylesheet } from '../utils/cytoscape-style';

// 防止重复注册
if (!(Cytoscape as any)._edgehandlesRegistered) {
  Cytoscape.use(EdgeHandles as any);
  (Cytoscape as any)._edgehandlesRegistered = true;
}
if (!(Cytoscape as any)._cxtmenuRegistered) {
  Cytoscape.use(CxtMenu as any);
  (Cytoscape as any)._cxtmenuRegistered = true;
}

const props = withDefaults(
  defineProps<{
    elements?: ElementDefinition[];
    readonly?: boolean;
    layout?: LayoutOptions;
  }>(),
  {
    elements: () => [],
    readonly: false,
    layout: () => ({
      name: 'cose',
      animate: true,
      animationDuration: 600,
      nodeRepulsion: () => 8000,
      idealEdgeLength: () => 120,
      gravity: 0.3,
    }),
  },
);

const emit = defineEmits<{
  ready: [cy: Core];
  nodeClick: [nodeData: any];
  edgeClick: [edgeData: any];
  graphChanged: [];
}>();

const containerRef = ref<HTMLDivElement>();
let cy: Core | null = null;
let eh: any = null;

// 连线模式状态，暴露给父组件
const isDrawMode = ref(false);

const initCytoscape = () => {
  if (!containerRef.value) return;

  cy = Cytoscape({
    container: containerRef.value,
    elements: props.elements,
    style: getStylesheet(),
    layout: props.layout,
    wheelSensitivity: 0.3,
    minZoom: 0.1,
    maxZoom: 3,
    boxSelectionEnabled: !props.readonly,
    userPanningEnabled: true,
    userZoomingEnabled: true,
  });

  // 节点/边点击（连线模式下不触发编辑）
  cy.on('tap', 'node', (evt) => {
    if (isDrawMode.value) return;
    // 过滤 edgehandles 内部节点
    if (evt.target.hasClass('eh-handle')) return;
    emit('nodeClick', evt.target.data());
  });

  cy.on('tap', 'edge', (evt) => {
    if (isDrawMode.value) return;
    emit('edgeClick', evt.target.data());
  });

  if (!props.readonly) {
    // ── edgehandles v4 ────────────────────────────────
    eh = (cy as any).edgehandles({
      preview: true,
      hoverDelay: 150,
      snap: false,
      noEdgeEventsInDraw: true,
      disableBrowserGestures: true,
    });

    // 禁止自环
    cy.on('ehpreviewon', (_e: any, src: any, tgt: any) => {
      if (src.id() === tgt.id()) eh.stop();
    });

    cy.on('ehcomplete', (_e: any, _src: any, _tgt: any, added: any) => {
      added.data('label', '');
      emit('graphChanged');
    });

    // ── 右键菜单 ──────────────────────────────────────
    (cy as any).cxtmenu({
      selector: 'node:not(.eh-handle)',
      commands: [
        {
          content: '编辑',
          select: (ele: any) => emit('nodeClick', ele.data()),
        },
        {
          content: '删除节点',
          select: (ele: any) => { ele.remove(); emit('graphChanged'); },
        },
      ],
    });

    (cy as any).cxtmenu({
      selector: 'edge',
      commands: [
        {
          content: '删除连线',
          select: (ele: any) => { ele.remove(); emit('graphChanged'); },
        },
      ],
    });
  }

  emit('ready', cy);
};

/** 进入连线模式：所有节点同时显示连接句柄，拖拽即可连线 */
const enableDrawMode = () => {
  if (!eh) return;
  eh.enableDrawMode();
  isDrawMode.value = true;
};

/** 退出连线模式 */
const disableDrawMode = () => {
  if (!eh) return;
  eh.disableDrawMode();
  isDrawMode.value = false;
};

/** 重新加载 elements 并重新布局 */
const load = async (elements: ElementDefinition[], layoutOpts?: LayoutOptions) => {
  if (!cy) return;
  cy.elements().remove();
  cy.add(elements);
  await nextTick();
  cy.resize();
  cy.layout(layoutOpts ?? props.layout).run();
};

/** 添加节点 */
const addNode = (data: Record<string, any>) => {
  if (!cy) return;
  cy.resize();
  const w = cy.width() || containerRef.value?.offsetWidth || 600;
  const h = cy.height() || containerRef.value?.offsetHeight || 400;
  const pos = {
    x: w / 2 + (Math.random() * 140 - 70),
    y: h / 2 + (Math.random() * 140 - 70),
  };
  const added = cy.add({ group: 'nodes', data, position: pos });
  cy.animate({ center: { eles: added }, duration: 150, easing: 'ease-out' });
  emit('graphChanged');
};

/** 更新节点数据 */
const updateNode = (id: string, data: Record<string, any>) => {
  if (!cy) return;
  const node = cy.getElementById(id);
  if (node.length) {
    node.data(data);
    emit('graphChanged');
  }
};

/** 导出 PNG */
const exportPng = (): string =>
  cy?.png({ full: true, scale: 2, bg: '#fff' }) ?? '';

/** 自适应视图 */
const fitView = () => {
  if (!cy) return;
  cy.resize();
  cy.fit(undefined, 60);
  if (cy.zoom() > 1.2) {
    cy.zoom(1.2);
    cy.center();
  }
};

const getJson = () => cy?.json();
const getElements = () => cy?.elements().jsons() ?? [];

defineExpose({
  load, addNode, updateNode, exportPng, fitView,
  getJson, getElements, enableDrawMode, disableDrawMode,
  isDrawMode,
});

// 只读模式下监听 elements prop 变化
watch(
  () => props.elements,
  async (newEls) => {
    if (props.readonly && cy) {
      cy.elements().remove();
      cy.add(newEls);
      await nextTick();
      cy.resize();
      cy.layout(props.layout).run();
    }
  },
  { deep: true },
);

useResizeObserver(containerRef, () => { cy?.resize(); });

onMounted(() => initCytoscape());

onBeforeUnmount(() => {
  eh?.disableDrawMode?.();
  eh?.destroy?.();
  cy?.destroy();
  cy = null;
});
</script>

<template>
  <div
    ref="containerRef"
    class="cytoscape-canvas"
    :class="{ 'draw-mode': isDrawMode }"
  />
</template>

<style scoped>
.cytoscape-canvas {
  width: 100%;
  height: 100%;
  background: #fafafa;
  border-radius: 8px;
}
/* 连线模式时改变鼠标样式，提示用户 */
.cytoscape-canvas.draw-mode {
  cursor: crosshair;
  background: #f0f5ff;
  outline: 2px solid #165dff;
  outline-offset: -2px;
}
</style>
