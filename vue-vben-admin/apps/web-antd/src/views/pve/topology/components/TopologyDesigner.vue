<script setup lang="ts">
import type { ElementDefinition } from 'cytoscape';
import type { NetworkTopologyModel } from '#/api/pve/types';

import { computed, onMounted, reactive, ref } from 'vue';

import {
  ApiOutlined,
  DeleteOutlined,
  DownloadOutlined,
  FullscreenOutlined,
  PlusOutlined,
  ReloadOutlined,
  SaveOutlined,
} from '@ant-design/icons-vue';
import {
  Button,
  Form,
  Input,
  message,
  Modal,
  Popconfirm,
  Space,
  Switch,
  Tag,
  Textarea,
} from 'ant-design-vue';

import {
  createTopologyApi,
  deleteTopologyApi,
  getTopologyDetailApi,
  getTopologyListApi,
  updateTopologyApi,
} from '#/api/pve/topology-manage';

import { NODE_TYPES, type NodeType } from '../utils/cytoscape-style';
import { deserializeCytoscapeData, serializeCytoscapeData } from '../utils/pve-to-cytoscape';
import CytoscapeCanvas from './CytoscapeCanvas.vue';
import NodeEditor from './NodeEditor.vue';

const canvasRef = ref<InstanceType<typeof CytoscapeCanvas>>();
let cyInstance: any = null;

const isDrawMode = computed(() => canvasRef.value?.isDrawMode ?? false);

const toggleDrawMode = () => {
  if (!canvasRef.value) return;
  if (isDrawMode.value) {
    canvasRef.value.disableDrawMode();
  } else {
    canvasRef.value.enableDrawMode();
  }
};

// ── 拓扑列表 ──────────────────────────────────────────
const listLoading = ref(false);
const topologyList = ref<NetworkTopologyModel[]>([]);
const currentTopology = ref<NetworkTopologyModel | null>(null);
const saving = ref(false);

// ── 画布 elements ─────────────────────────────────────
const canvasElements = ref<ElementDefinition[]>([]);

// ── 节点编辑抽屉 ──────────────────────────────────────
const nodeEditorOpen = ref(false);
const editingNodeData = ref<Record<string, any> | null>(null);

// ── 新建拓扑弹窗 ──────────────────────────────────────
const createModalVisible = ref(false);
const createLoading = ref(false);
const createFormRef = ref();
const createForm = reactive({ name: '', description: '' });
const createRules: any = {
  name: [{ required: true, message: '请输入拓扑名称', trigger: 'blur' }],
};

// ── 拓扑信息编辑 ──────────────────────────────────────
const topologyForm = reactive({ name: '', description: '', is_active: true });

// ── 统计 ──────────────────────────────────────────────
const stats = reactive({ nodes: 0, edges: 0 });

const updateStats = () => {
  if (!cyInstance) return;
  stats.nodes = cyInstance.nodes().length;
  stats.edges = cyInstance.edges().length;
};

// ── API ───────────────────────────────────────────────
const normalizeList = (res: any): NetworkTopologyModel[] => {
  if (Array.isArray(res)) return res;
  if (res?.results) return res.results;
  if (Array.isArray(res?.data)) return res.data;
  if (res?.data?.results) return res.data.results;
  return [];
};

const loadList = async () => {
  listLoading.value = true;
  try {
    const res = await getTopologyListApi();
    topologyList.value = normalizeList(res);
    // 自动选中第一条
    if (!currentTopology.value && topologyList.value.length > 0) {
      await selectTopology(topologyList.value[0]!);
    }
  } catch (err: any) {
    message.error(`获取拓扑列表失败: ${err.message}`);
  } finally {
    listLoading.value = false;
  }
};

const selectTopology = async (item: NetworkTopologyModel) => {
  try {
    const res = await getTopologyDetailApi(item.id);
    const detail: NetworkTopologyModel = (res as any).data ?? res;
    currentTopology.value = detail;
    Object.assign(topologyForm, {
      name: detail.name,
      description: detail.description ?? '',
      is_active: detail.is_active,
    });
    const els = deserializeCytoscapeData(detail.diagram_data);
    canvasRef.value?.load(els);
    updateStats();
  } catch (err: any) {
    message.error(`加载拓扑失败: ${err.message}`);
  }
};

const handleCreateTopology = () => {
  createForm.name = '';
  createForm.description = '';
  createModalVisible.value = true;
};

const handleCreateConfirm = () => {
  createFormRef.value.validate().then(async () => {
    createLoading.value = true;
    try {
      const res = await createTopologyApi({
        name: createForm.name,
        description: createForm.description,
        is_active: true,
        diagram_data: { elements: { nodes: [], edges: [] } },
      });
      message.success('拓扑创建成功');
      createModalVisible.value = false;
      await loadList();
      // 选中新建的拓扑
      const created = (res as any).data ?? res;
      if (created?.id) {
        const item = topologyList.value.find((t) => t.id === created.id);
        if (item) await selectTopology(item);
      }
    } catch (err: any) {
      message.error(`创建失败: ${err.message}`);
    } finally {
      createLoading.value = false;
    }
  });
};

const handleSaveTopology = async () => {
  if (!currentTopology.value) {
    message.warning('请先选择或新建一个拓扑');
    return;
  }
  saving.value = true;
  try {
    const elements = cyInstance ? serializeCytoscapeData(cyInstance) : {};
    await updateTopologyApi(currentTopology.value.id, {
      name: topologyForm.name,
      description: topologyForm.description,
      is_active: topologyForm.is_active,
      diagram_data: { elements },
    });
    message.success('保存成功');
    await loadList();
  } catch (err: any) {
    message.error(`保存失败: ${err.message}`);
  } finally {
    saving.value = false;
  }
};

const handleDeleteTopology = async (item: NetworkTopologyModel) => {
  try {
    await deleteTopologyApi(item.id);
    message.success('已删除');
    if (currentTopology.value?.id === item.id) {
      currentTopology.value = null;
      canvasElements.value = [];
    }
    await loadList();
  } catch (err: any) {
    message.error(`删除失败: ${err.message}`);
  }
};

const handleClearCanvas = () => {
  canvasRef.value?.load([]);
  updateStats();
};

const handleExport = () => {
  const png = canvasRef.value?.exportPng();
  if (!png) return;
  const link = document.createElement('a');
  link.download = `${topologyForm.name || 'topology'}.png`;
  link.href = png;
  link.click();
};

// ── 节点面板 ──────────────────────────────────────────
const palette = Object.entries(NODE_TYPES).map(([type, { label, color }]) => ({
  type: type as NodeType,
  label,
  color,
}));

const handleAddNode = (type: NodeType) => {
  if (!currentTopology.value) {
    message.warning('请先选择或新建一个拓扑');
    return;
  }
  canvasRef.value?.addNode({
    id: `${type}-${Date.now()}`,
    label: NODE_TYPES[type].label,
    type,
  });
  updateStats();
};

// ── 节点编辑 ──────────────────────────────────────────
const handleNodeClick = (data: Record<string, any>) => {
  if (!currentTopology.value) return;
  editingNodeData.value = data;
  nodeEditorOpen.value = true;
};

const handleNodeSave = (data: Record<string, any>) => {
  canvasRef.value?.updateNode(data.id, data);
  updateStats();
};

// ── 从实时拓扑导入 ────────────────────────────────────
const loadImportedElements = async (elements: ElementDefinition[]) => {
  if (!currentTopology.value) {
    // 自动创建一个新拓扑
    const res = await createTopologyApi({
      name: `导入-${new Date().toLocaleDateString('zh-CN')}`,
      description: '从实时拓扑导入',
      is_active: true,
      diagram_data: {},
    });
    const created = (res as any).data ?? res;
    await loadList();
    const item = topologyList.value.find((t) => t.id === created?.id) ?? topologyList.value[0];
    if (item) {
      await selectTopology(item);
    }
  }
  canvasRef.value?.load(elements);
  updateStats();
  message.success('已导入实时拓扑，可在此基础上编辑并保存');
};

const resizeCanvas = () => canvasRef.value?.fitView();

const selectTopologyById = async (id: number) => {
  // 等列表加载完再查找
  if (topologyList.value.length === 0) {
    await loadList();
  }
  const item = topologyList.value.find((t) => t.id === id);
  if (item) await selectTopology(item);
};

defineExpose({ loadImportedElements, resizeCanvas, selectTopologyById });

onMounted(() => loadList());
</script>

<template>
  <div class="flex h-full gap-3" style="min-height: 620px">
    <!-- 左侧面板 -->
    <div class="flex w-60 shrink-0 flex-col gap-3 overflow-y-auto">
      <!-- 拓扑列表 -->
      <div class="rounded-lg border border-gray-200 bg-white p-3 shadow-sm">
        <div class="mb-2 flex items-center justify-between">
          <span class="font-semibold text-sm">拓扑列表</span>
          <Space size="small">
            <Button size="small" type="text" :loading="listLoading" @click="loadList">
              <template #icon><ReloadOutlined /></template>
            </Button>
            <Button size="small" type="primary" @click="handleCreateTopology">
              <template #icon><PlusOutlined /></template>
              新建
            </Button>
          </Space>
        </div>
        <div v-if="!topologyList.length && !listLoading" class="py-4 text-center text-xs text-gray-400">
          暂无拓扑，点击「新建」创建
        </div>
        <div
          v-for="item in topologyList"
          :key="item.id"
          :class="[
            'group mb-1 flex cursor-pointer items-center justify-between rounded px-2 py-2 text-sm transition-colors',
            currentTopology?.id === item.id
              ? 'bg-blue-50 text-blue-700'
              : 'hover:bg-gray-50',
          ]"
          @click="selectTopology(item)"
        >
          <div class="min-w-0 flex-1">
            <div class="truncate font-medium">{{ item.name }}</div>
            <div class="flex items-center gap-1 mt-0.5">
              <Tag :color="item.is_active ? 'success' : 'default'" class="text-xs !m-0">
                {{ item.is_active ? '启用' : '禁用' }}
              </Tag>
            </div>
          </div>
          <Popconfirm
            title="确定删除该拓扑？"
            ok-text="删除"
            cancel-text="取消"
            @confirm.stop="handleDeleteTopology(item)"
          >
            <Button
              size="small"
              type="text"
              danger
              class="invisible group-hover:visible"
              @click.stop
            >
              <template #icon><DeleteOutlined /></template>
            </Button>
          </Popconfirm>
        </div>
      </div>

      <!-- 元素面板 -->
      <div class="rounded-lg border border-gray-200 bg-white p-3 shadow-sm">
        <div class="mb-2 font-semibold text-sm">元素面板</div>
        <div class="flex flex-wrap gap-1.5">
          <button
            v-for="item in palette"
            :key="item.type"
            class="flex items-center gap-1 rounded border px-2 py-1 text-xs transition-colors hover:opacity-80"
            :style="{ borderColor: item.color, color: item.color }"
            @click="handleAddNode(item.type)"
          >
            <span
              class="inline-block h-2 w-2 rounded-full"
              :style="{ background: item.color }"
            />
            {{ item.label }}
          </button>
        </div>
        <p class="mt-2 text-xs text-gray-400">
          点击按钮添加节点；点击工具栏「连线」进入连线模式后，从节点拖向另一节点即可连线
        </p>
      </div>

      <!-- 当前拓扑信息 -->
      <div v-if="currentTopology" class="rounded-lg border border-gray-200 bg-white p-3 shadow-sm">
        <div class="mb-2 font-semibold text-sm">拓扑信息</div>
        <Form layout="vertical" size="small">
          <Form.Item label="名称" class="mb-2">
            <Input v-model:value="topologyForm.name" />
          </Form.Item>
          <Form.Item label="描述" class="mb-2">
            <Textarea v-model:value="topologyForm.description" :rows="2" />
          </Form.Item>
          <Form.Item label="状态" class="mb-2">
            <Switch
              v-model:checked="topologyForm.is_active"
              checked-children="启用"
              un-checked-children="禁用"
            />
          </Form.Item>
        </Form>
        <div class="text-xs text-gray-400">
          节点: {{ stats.nodes }} / 连线: {{ stats.edges }}
        </div>
      </div>
    </div>

    <!-- 右侧画布区 -->
    <div class="flex flex-1 flex-col gap-2">
      <!-- 画布工具栏 -->
      <div class="flex items-center gap-2">
        <span class="font-medium text-sm text-gray-700">
          {{ currentTopology ? currentTopology.name : '请选择或新建拓扑' }}
        </span>
        <div class="flex-1" />
        <Space size="small">
          <Button size="small" @click="() => canvasRef?.fitView()">
            <template #icon><FullscreenOutlined /></template>
            自适应
          </Button>
          <Button
            size="small"
            :type="isDrawMode ? 'primary' : 'default'"
            :danger="isDrawMode"
            @click="toggleDrawMode"
          >
            <template #icon><ApiOutlined /></template>
            {{ isDrawMode ? '退出连线' : '连线' }}
          </Button>
          <Button size="small" @click="handleClearCanvas">清空画布</Button>
          <Button size="small" @click="handleExport">
            <template #icon><DownloadOutlined /></template>
            导出图片
          </Button>
          <Button
            size="small"
            type="primary"
            :loading="saving"
            :disabled="!currentTopology"
            @click="handleSaveTopology"
          >
            <template #icon><SaveOutlined /></template>
            保存
          </Button>
        </Space>
      </div>

      <!-- Cytoscape 画布 -->
      <div class="relative overflow-hidden rounded-lg border border-gray-200" style="height: 580px">
        <CytoscapeCanvas
          ref="canvasRef"
          :elements="canvasElements"
          :readonly="false"
          style="height: 580px; width: 100%"
          @ready="(cy) => { cyInstance = cy }"
          @node-click="handleNodeClick"
          @graph-changed="updateStats"
        />
        <div
          v-if="!currentTopology"
          class="pointer-events-none absolute inset-0 flex items-center justify-center"
        >
          <div class="rounded-full border border-dashed border-gray-300 bg-white/90 px-4 py-2 text-sm text-gray-400">
            请选择左侧拓扑或创建一个新拓扑开始绘制
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- 新建拓扑弹窗 -->
  <Modal
    v-model:open="createModalVisible"
    title="新建拓扑"
    :confirm-loading="createLoading"
    @ok="handleCreateConfirm"
    @cancel="createModalVisible = false"
  >
    <Form ref="createFormRef" :model="createForm" :rules="createRules" layout="vertical" class="mt-4">
      <Form.Item label="拓扑名称" name="name">
        <Input v-model:value="createForm.name" placeholder="例如: 生产集群网络拓扑" />
      </Form.Item>
      <Form.Item label="描述" name="description">
        <Textarea v-model:value="createForm.description" placeholder="补充拓扑用途、包含资源等信息" :rows="3" />
      </Form.Item>
    </Form>
  </Modal>

  <!-- 节点编辑抽屉 -->
  <NodeEditor
    v-model:open="nodeEditorOpen"
    :node-data="editingNodeData"
    @save="handleNodeSave"
  />
</template>
