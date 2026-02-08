<script setup lang="ts">
import type { PVEServerModel, PveStorage } from '#/api/pve/types';

import { onMounted, ref, watch } from 'vue';

import {
  CloudUploadOutlined,
  DeleteOutlined,
  FileOutlined,
  FolderOpenOutlined,
  HddOutlined,
  InboxOutlined,
  ReloadOutlined,
} from '@ant-design/icons-vue';
import {
  Button,
  Card,
  Drawer,
  message,
  Popconfirm,
  Select,
  Space,
  Table,
  Tag,
  UploadDragger,
} from 'ant-design-vue';

import { getNodeListApi, getPveNodesApi } from '#/api/pve/node';
import {
  deleteStorageContentApi,
  getStorageContentApi,
  getStorageListApi,
  uploadToStorageApi,
} from '#/api/pve/storage';

defineOptions({
  name: 'PVEStorage',
});

// State
const loading = ref(false);
const contentLoading = ref(false);
const servers = ref<PVEServerModel[]>([]);
const nodes = ref<any[]>([]);
const storageList = ref<PveStorage[]>([]);
const storageContent = ref<any[]>([]);

const selectedServerId = ref<number | undefined>();
const selectedNode = ref<string | undefined>();
const selectedStorage = ref<string | undefined>();

const contentDrawerVisible = ref(false);
const uploadVisible = ref(false);
const fileList = ref([]);
const uploadContentType = ref('iso');

// Columns
const columns = [
  { title: 'ID', dataIndex: 'storage', key: 'storage', width: 150 },
  { title: '类型', dataIndex: 'type', key: 'type', width: 100 },
  { title: '内容类型', dataIndex: 'content', key: 'content' },
  { title: '状态', key: 'status', width: 100 },
  { title: '总容量', key: 'total', width: 120 },
  { title: '已用', key: 'used', width: 120 },
  { title: '可用', key: 'avail', width: 120 },
  { title: '使用率', key: 'percent', width: 200 },
  { title: '操作', key: 'action', width: 120 },
];

const contentColumns = [
  { title: '名称', dataIndex: 'volid', key: 'volid' },
  { title: '格式', dataIndex: 'format', key: 'format', width: 100 },
  { title: '大小', key: 'size', width: 120 },
  { title: '备注', dataIndex: 'notes', key: 'notes' },
  { title: '操作', key: 'action', width: 150 },
];

// Helpers
const formatBytes = (bytes?: number) => {
  if (!bytes) return '-';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${Number.parseFloat((bytes / k ** i).toFixed(2))} ${sizes[i]}`;
};

const getUsagePercent = (used: number, total: number) => {
  if (!total) return 0;
  return Math.round((used / total) * 100);
};

const getUsageColor = (percent: number) => {
  if (percent >= 90) return 'red';
  if (percent >= 75) return 'orange';
  return 'blue';
};

// Actions
const fetchServers = async () => {
  try {
    const res = await getNodeListApi();
    let data: any[] = [];

    if (Array.isArray(res)) {
      data = res;
    } else if (res && Array.isArray((res as any).results)) {
      data = (res as any).results;
    } else if (
      res &&
      (res as any).data &&
      Array.isArray((res as any).data.results)
    ) {
      data = (res as any).data.results;
    } else if (res && Array.isArray((res as any).data)) {
      data = (res as any).data;
    }

    // @ts-ignore
    servers.value = data.filter((s) => s.is_active);

    // Auto select first
    if (!selectedServerId.value && servers.value.length > 0) {
      selectedServerId.value = servers.value[0].id;
    }
  } catch {
    message.error('获取服务器列表失败');
  }
};

const fetchNodes = async (serverId: number) => {
  try {
    const res = await getPveNodesApi(serverId);
    let data: any[] = [];

    if (Array.isArray(res)) {
      data = res;
    } else if (res && Array.isArray((res as any).results)) {
      data = (res as any).results;
    } else if (
      res &&
      (res as any).data &&
      Array.isArray((res as any).data.results)
    ) {
      data = (res as any).data.results;
    } else if (res && Array.isArray((res as any).data)) {
      data = (res as any).data;
    }

    nodes.value = data;
    if (data.length > 0) {
      selectedNode.value = data[0].node;
    } else {
      selectedNode.value = undefined;
      storageList.value = [];
    }
  } catch {
    message.error('获取节点列表失败');
    nodes.value = [];
  }
};

const fetchStorage = async () => {
  if (!selectedServerId.value || !selectedNode.value) return;

  loading.value = true;
  try {
    const res = await getStorageListApi(
      selectedServerId.value,
      selectedNode.value,
    );
    let data: any[] = [];
    if (Array.isArray(res)) {
      data = res;
    } else if (res && Array.isArray((res as any).results)) {
      data = (res as any).results;
    } else if (
      res &&
      (res as any).data &&
      Array.isArray((res as any).data.results)
    ) {
      data = (res as any).data.results;
    } else if (res && Array.isArray((res as any).data)) {
      data = (res as any).data;
    }
    storageList.value = data;
  } catch (error: any) {
    message.error(`获取存储列表失败: ${error.message}`);
  } finally {
    loading.value = false;
  }
};

const showContent = async (record: PveStorage) => {
  selectedStorage.value = record.storage;
  contentDrawerVisible.value = true;
  // Reset upload content type
  uploadContentType.value = 'iso';
  fetchContent(record.storage);
};

const fetchContent = async (storage: string) => {
  if (!selectedServerId.value || !selectedNode.value) return;

  contentLoading.value = true;
  try {
    const res = await getStorageContentApi(
      selectedServerId.value,
      selectedNode.value,
      storage,
    );
    let data: any[] = [];
    if (Array.isArray(res)) {
      data = res;
    } else if (res && Array.isArray((res as any).results)) {
      data = (res as any).results;
    } else if (
      res &&
      (res as any).data &&
      Array.isArray((res as any).data.results)
    ) {
      data = (res as any).data.results;
    } else if (res && Array.isArray((res as any).data)) {
      data = (res as any).data;
    }
    storageContent.value = data;
  } catch (error: any) {
    message.error(`获取存储内容失败: ${error.message}`);
  } finally {
    contentLoading.value = false;
  }
};

const handleUpload = async (options: any) => {
  const { file, onSuccess, onError } = options;

  if (
    !selectedServerId.value ||
    !selectedNode.value ||
    !selectedStorage.value
  ) {
    message.error('未选择存储位置');
    return;
  }

  const formData = new FormData();
  formData.append('file', file);
  formData.append('content', uploadContentType.value);

  try {
    await uploadToStorageApi(
      selectedServerId.value,
      selectedNode.value,
      selectedStorage.value,
      formData,
    );
    message.success(`${file.name} 上传成功`);
    onSuccess('ok');
    fetchContent(selectedStorage.value);
  } catch (error: any) {
    // message.error(`${file.name} 上传失败`);
    onError(error);
  }
};

const handleDeleteContent = async (record: any) => {
  if (!selectedServerId.value || !selectedNode.value || !selectedStorage.value)
    return;
  try {
    contentLoading.value = true;
    await deleteStorageContentApi(
      selectedServerId.value,
      selectedNode.value,
      selectedStorage.value,
      record.volid,
    );
    message.success('删除成功');
    fetchContent(selectedStorage.value);
  } catch (error: any) {
    message.error(`删除失败: ${error.message}`);
  } finally {
    contentLoading.value = false;
  }
};

// Lifecycle & Watch
onMounted(() => {
  fetchServers();
});

watch(selectedServerId, (newVal) => {
  if (newVal) {
    fetchNodes(newVal);
  }
});

watch(selectedNode, (newVal) => {
  if (newVal) {
    fetchStorage();
  }
});
</script>

<template>
  <div class="p-5">
    <Card title="存储管理">
      <template #extra>
        <Space>
          <span class="text-gray-500">服务器:</span>
          <Select
            v-model:value="selectedServerId"
            style="width: 200px"
            placeholder="选择服务器"
            :options="servers.map((s) => ({ label: s.name, value: s.id }))"
          />

          <span class="ml-4 text-gray-500">节点:</span>
          <Select
            v-model:value="selectedNode"
            style="width: 150px"
            placeholder="选择节点"
            :options="nodes.map((n) => ({ label: n.node, value: n.node }))"
            :disabled="!selectedServerId"
          />

          <Button
            @click="fetchStorage"
            :disabled="!selectedNode"
            :loading="loading"
          >
            <template #icon><ReloadOutlined /></template>
            刷新
          </Button>
        </Space>
      </template>

      <Table
        :columns="columns"
        :data-source="storageList"
        :loading="loading"
        :pagination="false"
        row-key="storage"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'storage'">
            <Space>
              <HddOutlined />
              <span class="font-medium">{{ record.storage }}</span>
            </Space>
          </template>

          <template v-else-if="column.key === 'status'">
            <Tag :color="record.active ? 'success' : 'default'">
              {{ record.active ? '在线' : '离线' }}
            </Tag>
          </template>

          <template v-else-if="column.key === 'total'">
            {{ formatBytes(record.total) }}
          </template>

          <template v-else-if="column.key === 'used'">
            {{ formatBytes(record.used) }}
          </template>

          <template v-else-if="column.key === 'avail'">
            {{ formatBytes(record.avail) }}
          </template>

          <template v-else-if="column.key === 'percent'">
            <div class="h-2.5 w-full rounded-full bg-gray-200 dark:bg-gray-700">
              <div
                class="h-2.5 rounded-full"
                :class="`bg-${getUsageColor(getUsagePercent(record.used, record.total))}-500`"
                :style="{
                  width: `${getUsagePercent(record.used, record.total)}%`,
                }"
              ></div>
            </div>
            <span class="text-xs text-gray-500"
              >{{ getUsagePercent(record.used, record.total) }}%</span
            >
          </template>

          <template v-else-if="column.key === 'action'">
            <Button size="small" type="link" @click="showContent(record)">
              <template #icon><FolderOpenOutlined /></template>
              查看内容
            </Button>
          </template>
        </template>
      </Table>
    </Card>

    <Drawer
      v-model:open="contentDrawerVisible"
      :title="`存储内容: ${selectedStorage}`"
      width="800"
    >
      <div class="mb-4 text-right">
        <Button @click="uploadVisible = !uploadVisible">
          <template #icon><CloudUploadOutlined /></template>
          上传文件
        </Button>
      </div>

      <div v-if="uploadVisible" class="mb-6 rounded border bg-gray-50 p-4">
        <UploadDragger
          name="file"
          :custom-request="handleUpload"
          :file-list="fileList"
          @update:file-list="fileList = $event"
        >
          <p class="ant-upload-drag-icon">
            <InboxOutlined />
          </p>
          <p class="ant-upload-text">点击或拖拽文件到此区域上传</p>
          <p class="ant-upload-hint">支持上传 ISO 镜像模版等文件.</p>
        </UploadDragger>
      </div>

      <Table
        :columns="contentColumns"
        :data-source="storageContent"
        :loading="contentLoading"
        row-key="volid"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'volid'">
            <Space>
              <FileOutlined />
              <span>{{ record.volid }}</span>
            </Space>
          </template>

          <template v-else-if="column.key === 'size'">
            {{ formatBytes(record.size) }}
          </template>

          <template v-else-if="column.key === 'action'">
            <Space>
              <!-- <Button size="small" type="link" @click="handleDownload(record)">
                 <template #icon><DownloadOutlined /></template>
                 下载
               </Button> -->
              <Popconfirm
                title="确定要删除此文件吗？"
                ok-text="确定"
                cancel-text="取消"
                @confirm="handleDeleteContent(record)"
              >
                <Button size="small" type="link" danger>
                  <template #icon><DeleteOutlined /></template>
                  删除
                </Button>
              </Popconfirm>
            </Space>
          </template>
        </template>
      </Table>
    </Drawer>
  </div>
</template>
