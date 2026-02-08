<script setup lang="ts">
import type { PVEServerModel } from '#/api/pve/types';

import { onMounted, reactive, ref } from 'vue';

import {
  CloudUploadOutlined,
  InboxOutlined,
  ReloadOutlined,
} from '@ant-design/icons-vue';
import {
  Button,
  Card,
  Descriptions,
  Form,
  Input,
  message,
  Modal,
  Popconfirm,
  Select,
  Space,
  Table,
  Tag,
  Upload,
} from 'ant-design-vue';

import { getNodeListApi, getPveNodesApi } from '#/api/pve/node';
import {
  deleteStorageContentApi,
  getStorageContentApi,
  getStorageListApi,
  uploadToStorageApi,
} from '#/api/pve/storage';

defineOptions({
  name: 'PVETemplates',
});

// Types
interface TemplateItem {
  volid: string;
  content: string;
  format: string;
  size: number;
  ctime: number;
  notes?: string;
  server_id: number;
  server_name: string;
  server_host: string;
  node: string;
  storage: string;
  verification?: any;
}

// State
const loading = ref(false);
const servers = ref<PVEServerModel[]>([]);
const tableData = ref<TemplateItem[]>([]);
const uploadModalVisible = ref(false);
const detailModalVisible = ref(false);
const currentTemplate = ref<null | TemplateItem>(null);

// Upload State
const uploadLoading = ref(false);
const uploadNodesLoading = ref(false);
const uploadStoragesLoading = ref(false);
const uploadNodes = ref<any[]>([]);
const uploadStorages = ref<any[]>([]);
const uploadFileList = ref<any[]>([]);

const filters = reactive({
  server_id: undefined as number | undefined,
  node: '',
  storage: '',
  content_type: 'all',
});

const uploadForm = reactive({
  server_id: undefined as number | undefined,
  node: undefined as string | undefined,
  storage: undefined as string | undefined,
  content_type: 'iso',
});

// Pagination
const pagination = reactive({
  current: 1,
  pageSize: 20,
  total: 0,
  showTotal: (total: number) => `共 ${total} 条`,
  onChange: (page: number, pageSize: number) => {
    pagination.current = page;
    pagination.pageSize = pageSize;
    // Client-side pagination logic if needed, but we regenerate tableData usually
  },
});

// Columns
const columns = [
  { title: '服务器', dataIndex: 'server_name', key: 'server_name', width: 150 },
  { title: '节点', dataIndex: 'node', key: 'node', width: 120 },
  { title: '存储', dataIndex: 'storage', key: 'storage', width: 150 },
  { title: '文件名', dataIndex: 'volid', key: 'volid', ellipsis: true },
  { title: '类型', dataIndex: 'content', key: 'content', width: 120 },
  { title: '大小', dataIndex: 'size', key: 'size', width: 120 },
  { title: '创建时间', dataIndex: 'ctime', key: 'ctime', width: 180 },
  { title: '操作', key: 'action', width: 150, fixed: 'right' },
];

// Helpers
const formatContentType = (content: string) => {
  const typeMap: Record<string, string> = {
    iso: 'ISO镜像',
    vztmpl: '容器模板',
    backup: '备份文件',
  };
  return typeMap[content] || content || '未知';
};

const getContentTypeColor = (content: string) => {
  const colorMap: Record<string, string> = {
    iso: 'blue',
    vztmpl: 'green',
    backup: 'orange',
  };
  return colorMap[content] || 'default';
};

const formatBytes = (bytes?: number) => {
  if (!bytes && bytes !== 0) return '-';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${Number.parseFloat((bytes / k ** i).toFixed(2))} ${sizes[i]}`;
};

const formatTime = (timestamp?: number) => {
  if (!timestamp) return '-';
  try {
    const date = new Date(timestamp * 1000);
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  } catch {
    return timestamp;
  }
};

// Logic
const fetchServers = async () => {
  try {
    const res = await getNodeListApi();
    let data: any[] = [];
    if (Array.isArray(res)) {
      data = res;
    } else if (res && (res as any).results) {
      data = (res as any).results;
    } else if (res && (res as any).data) {
      // Handle wrapped data
      data = Array.isArray((res as any).data)
        ? (res as any).data
        : (res as any).data.results || [];
    }
    servers.value = data.filter((s) => s.is_active);
  } catch {
    message.error('获取服务器列表失败');
  }
};

const loadTemplates = async () => {
  loading.value = true;
  const allTemplates: TemplateItem[] = [];

  const targetServers = filters.server_id
    ? servers.value.filter((s) => s.id === filters.server_id)
    : servers.value;

  try {
    for (const server of targetServers) {
      try {
        // Get Nodes
        const nodesRes = await getPveNodesApi(server.id);
        let nodesData: any[] = [];
        // Handle varied node response
        if (Array.isArray(nodesRes)) nodesData = nodesRes;
        else if ((nodesRes as any).results)
          nodesData = (nodesRes as any).results;
        else if ((nodesRes as any).data)
          nodesData = Array.isArray((nodesRes as any).data)
            ? (nodesRes as any).data
            : (nodesRes as any).data.results || [];

        for (const nodeInfo of nodesData) {
          const nodeName = nodeInfo.node || nodeInfo.name;
          if (filters.node && !nodeName.includes(filters.node)) {
            continue;
          }

          try {
            // Get Storages
            const storagesRes = await getStorageListApi(server.id, nodeName);
            let storagesData: any[] = [];
            if (Array.isArray(storagesRes)) storagesData = storagesRes;
            else if ((storagesRes as any).results)
              storagesData = (storagesRes as any).results;
            else if ((storagesRes as any).data)
              storagesData = Array.isArray((storagesRes as any).data)
                ? (storagesRes as any).data
                : (storagesRes as any).data.results || [];

            for (const storage of storagesData) {
              if (
                filters.storage &&
                !storage.storage.includes(filters.storage)
              ) {
                continue;
              }

              const contentTypes = storage.content?.split(',') || [];
              const hasIso = contentTypes.includes('iso');
              const hasVztmpl = contentTypes.includes('vztmpl');

              if (!hasIso && !hasVztmpl) continue;

              try {
                // Fetch ISOs
                if (
                  hasIso &&
                  (filters.content_type === 'all' ||
                    filters.content_type === 'iso')
                ) {
                  const isoRes = await getStorageContentApi(
                    server.id,
                    nodeName,
                    storage.storage,
                    'iso',
                  );
                  let isoList: any[] = [];
                  if (Array.isArray(isoRes)) isoList = isoRes;
                  else if ((isoRes as any).data)
                    isoList = Array.isArray((isoRes as any).data)
                      ? (isoRes as any).data
                      : [];

                  isoList.forEach((item) => {
                    allTemplates.push({
                      ...item,
                      server_id: server.id,
                      server_name: server.name,
                      server_host: server.host,
                      node: nodeName,
                      storage: storage.storage,
                      content: 'iso',
                    });
                  });
                }

                // Fetch Vztmpls
                if (
                  hasVztmpl &&
                  (filters.content_type === 'all' ||
                    filters.content_type === 'vztmpl')
                ) {
                  const vztmplRes = await getStorageContentApi(
                    server.id,
                    nodeName,
                    storage.storage,
                    'vztmpl',
                  );
                  let vztmplList: any[] = [];
                  if (Array.isArray(vztmplRes)) vztmplList = vztmplRes;
                  else if ((vztmplRes as any).data)
                    vztmplList = Array.isArray((vztmplRes as any).data)
                      ? (vztmplRes as any).data
                      : [];

                  vztmplList.forEach((item) => {
                    allTemplates.push({
                      ...item,
                      server_id: server.id,
                      server_name: server.name,
                      server_host: server.host,
                      node: nodeName,
                      storage: storage.storage,
                      content: 'vztmpl',
                    });
                  });
                }
              } catch {
                console.warn(
                  `Failed to fetch content for storage ${storage.storage}`,
                );
              }
            }
          } catch {
            console.warn(`Failed to fetch storages for node ${nodeName}`);
          }
        }
      } catch {
        console.warn(`Failed to fetch nodes for server ${server.name}`);
      }
    }
  } finally {
    tableData.value = allTemplates;
    pagination.total = allTemplates.length;
    loading.value = false;
  }
};

const handleViewDetails = (record: TemplateItem) => {
  currentTemplate.value = record;
  detailModalVisible.value = true;
};

const handleDelete = async (record: TemplateItem) => {
  try {
    loading.value = true;
    await deleteStorageContentApi(
      record.server_id,
      record.node,
      record.storage,
      record.volid,
    );
    message.success('删除成功');
    loadTemplates();
  } catch (error: any) {
    message.error(`删除失败: ${error.message}`);
  } finally {
    loading.value = false;
  }
};

// Upload Logic
const handleUploadServerChange = async () => {
  uploadForm.node = undefined;
  uploadForm.storage = undefined;
  uploadNodes.value = [];
  uploadStorages.value = [];

  if (!uploadForm.server_id) return;

  uploadNodesLoading.value = true;
  try {
    const res = await getPveNodesApi(uploadForm.server_id);
    let data: any[] = [];
    if (Array.isArray(res)) data = res;
    else if ((res as any).data)
      data = Array.isArray((res as any).data)
        ? (res as any).data
        : (res as any).data.results || [];

    uploadNodes.value = data.map((item) => ({
      label: item.node || item.name,
      value: item.node || item.name,
    }));
  } catch {
    message.error('获取节点列表失败');
  } finally {
    uploadNodesLoading.value = false;
  }
};

const handleUploadNodeChange = async () => {
  uploadForm.storage = undefined;
  uploadStorages.value = [];

  if (!uploadForm.server_id || !uploadForm.node) return;

  uploadStoragesLoading.value = true;
  try {
    const res = await getStorageListApi(uploadForm.server_id, uploadForm.node);
    let data: any[] = [];
    if (Array.isArray(res)) data = res;
    else if ((res as any).data)
      data = Array.isArray((res as any).data)
        ? (res as any).data
        : (res as any).data.results || [];

    // Filter for ISO/Vztmpl support
    uploadStorages.value = data.filter((s: any) => {
      const ctypes = s.content?.split(',') || [];
      return ctypes.includes('iso') || ctypes.includes('vztmpl');
    });
  } catch {
    message.error('获取存储列表失败');
  } finally {
    uploadStoragesLoading.value = false;
  }
};

const handleUpload = async () => {
  if (uploadFileList.value.length === 0) {
    message.warning('请选择要上传的文件');
    return;
  }
  const file = uploadFileList.value[0].originFileObj;
  if (!file) return;

  if (!uploadForm.server_id || !uploadForm.node || !uploadForm.storage) {
    message.warning('请完整填写上传信息');
    return;
  }

  uploadLoading.value = true;
  const formData = new FormData();
  formData.append('file', file);
  formData.append('content', uploadForm.content_type);
  formData.append('filename', file.name);

  try {
    await uploadToStorageApi(
      uploadForm.server_id,
      uploadForm.node,
      uploadForm.storage,
      formData,
    );
    message.success('上传成功');
    uploadModalVisible.value = false;
    loadTemplates();
    // Reset form
    uploadForm.server_id = undefined;
    uploadForm.node = undefined;
    uploadForm.storage = undefined;
    uploadFileList.value = [];
  } catch (error: any) {
    message.error(`上传失败: ${error.message}`);
  } finally {
    uploadLoading.value = false;
  }
};

onMounted(async () => {
  await fetchServers();
  loadTemplates();
});
</script>

<template>
  <div class="p-5">
    <Card title="模板管理">
      <template #extra>
        <Space wrap>
          <div class="flex flex-col gap-1">
            <span class="text-xs text-gray-500">服务器</span>
            <Select
              v-model:value="filters.server_id"
              placeholder="全部服务器"
              allow-clear
              style="width: 200px"
              :options="servers.map((s) => ({ label: s.name, value: s.id }))"
              @change="loadTemplates"
            />
          </div>

          <div class="flex flex-col gap-1">
            <span class="text-xs text-gray-500">节点</span>
            <Input
              v-model:value="filters.node"
              placeholder="节点名称"
              style="width: 150px"
              allow-clear
              @press-enter="loadTemplates"
            />
          </div>

          <div class="flex flex-col gap-1">
            <span class="text-xs text-gray-500">存储</span>
            <Input
              v-model:value="filters.storage"
              placeholder="存储名称"
              style="width: 150px"
              allow-clear
              @press-enter="loadTemplates"
            />
          </div>

          <div class="flex flex-col gap-1">
            <span class="text-xs text-gray-500">类型</span>
            <Select
              v-model:value="filters.content_type"
              placeholder="全部类型"
              style="width: 150px"
              @change="loadTemplates"
            >
              <Select.Option value="all">全部类型</Select.Option>
              <Select.Option value="iso">ISO镜像</Select.Option>
              <Select.Option value="vztmpl">容器模板</Select.Option>
            </Select>
          </div>

          <div class="flex items-end pb-0.5">
            <Button
              type="primary"
              @click="loadTemplates"
              :loading="loading"
              class="mr-2"
            >
              <template #icon><ReloadOutlined /></template>
              刷新
            </Button>
            <Button type="primary" @click="uploadModalVisible = true">
              <template #icon><CloudUploadOutlined /></template>
              上传模板
            </Button>
          </div>
        </Space>
      </template>

      <Table
        :columns="columns"
        :data-source="tableData"
        :loading="loading"
        :pagination="pagination"
        row-key="volid"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'server_name'">
            <div>
              <div class="font-medium">{{ record.server_name }}</div>
              <div class="text-xs text-gray-400">{{ record.server_host }}</div>
            </div>
          </template>

          <template v-else-if="column.key === 'content'">
            <Tag :color="getContentTypeColor(record.content)">
              {{ formatContentType(record.content) }}
            </Tag>
          </template>

          <template v-else-if="column.key === 'size'">
            {{ formatBytes(record.size) }}
          </template>

          <template v-else-if="column.key === 'ctime'">
            {{ formatTime(record.ctime) }}
          </template>

          <template v-else-if="column.key === 'action'">
            <Space>
              <Button
                size="small"
                type="link"
                @click="handleViewDetails(record)"
              >
                详情
              </Button>
              <Popconfirm
                title="确定要删除此模板吗？"
                ok-text="确定"
                cancel-text="取消"
                @confirm="handleDelete(record)"
              >
                <Button size="small" type="link" danger> 删除 </Button>
              </Popconfirm>
            </Space>
          </template>
        </template>
      </Table>
    </Card>

    <!-- Upload Modal -->
    <Modal
      v-model:open="uploadModalVisible"
      title="上传模板"
      width="600px"
      @ok="handleUpload"
      :confirm-loading="uploadLoading"
    >
      <Form layout="vertical">
        <Form.Item label="服务器" required>
          <Select
            v-model:value="uploadForm.server_id"
            placeholder="请选择服务器"
            :options="servers.map((s) => ({ label: s.name, value: s.id }))"
            @change="handleUploadServerChange"
          />
        </Form.Item>
        <Form.Item label="节点" required>
          <Select
            v-model:value="uploadForm.node"
            placeholder="请选择节点"
            :loading="uploadNodesLoading"
            :disabled="!uploadForm.server_id"
            :options="uploadNodes"
            @change="handleUploadNodeChange"
          />
        </Form.Item>
        <Form.Item label="存储" required>
          <Select
            v-model:value="uploadForm.storage"
            placeholder="请选择存储"
            :loading="uploadStoragesLoading"
            :disabled="!uploadForm.node"
          >
            <Select.Option
              v-for="s in uploadStorages"
              :key="s.storage"
              :value="s.storage"
            >
              {{ s.storage }} ({{ s.type }})
            </Select.Option>
          </Select>
        </Form.Item>
        <Form.Item label="模板类型" required>
          <Select v-model:value="uploadForm.content_type">
            <Select.Option value="iso">ISO镜像</Select.Option>
            <Select.Option value="vztmpl">容器模板</Select.Option>
          </Select>
        </Form.Item>
        <Form.Item label="文件" required>
          <Upload.Dragger
            v-model:file-list="uploadFileList"
            :max-count="1"
            :before-upload="() => false"
            accept=".iso,.img,.tar.gz"
          >
            <p class="ant-upload-drag-icon">
              <InboxOutlined />
            </p>
            <p class="ant-upload-text">点击或拖拽文件到此区域</p>
          </Upload.Dragger>
        </Form.Item>
      </Form>
    </Modal>

    <!-- Detail Modal -->
    <Modal
      v-model:open="detailModalVisible"
      :title="`模板详情 - ${currentTemplate?.volid?.split('/').pop() || ''}`"
      width="700px"
      :footer="null"
    >
      <Descriptions bordered :column="2" v-if="currentTemplate">
        <Descriptions.Item label="服务器">
          {{ currentTemplate.server_name }}
        </Descriptions.Item>
        <Descriptions.Item label="节点">
          {{ currentTemplate.node }}
        </Descriptions.Item>
        <Descriptions.Item label="存储">
          {{ currentTemplate.storage }}
        </Descriptions.Item>
        <Descriptions.Item label="类型">
          <Tag :color="getContentTypeColor(currentTemplate.content)">
            {{ formatContentType(currentTemplate.content) }}
          </Tag>
        </Descriptions.Item>
        <Descriptions.Item label="文件大小">
          {{ formatBytes(currentTemplate.size) }}
        </Descriptions.Item>
        <Descriptions.Item label="创建时间">
          {{ formatTime(currentTemplate.ctime) }}
        </Descriptions.Item>
        <Descriptions.Item label="完整路径" :span="2">
          {{ currentTemplate.volid }}
        </Descriptions.Item>
        <Descriptions.Item label="备注" :span="2">
          {{ currentTemplate.notes || '-' }}
        </Descriptions.Item>
      </Descriptions>
    </Modal>
  </div>
</template>

<style scoped>
/* Add any specific styles here if needed */
</style>
