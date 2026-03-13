<script setup lang="ts">
import { onMounted, reactive, ref, h } from 'vue';
import { SyncOutlined, DatabaseOutlined, ToolOutlined } from '@ant-design/icons-vue';
import {
  Button,
  Card,
  Space,
  Table,
  Popconfirm,
  message,
  Tag,
  TypographyText,
} from 'ant-design-vue';
import type { TableColumnsType } from 'ant-design-vue';
import dayjs from 'dayjs';

import {
  getAiKnowledgeIndexesApi,
  rebuildAiKnowledgeIndexApi,
} from '#/api/ai';

defineOptions({ name: 'AiKnowledgeBaseConfig' });

const loading = ref(false);
const tableData = ref<any[]>([]);
const pagination = reactive({
  current: 1,
  pageSize: 20,
  total: 0,
});

const selectedRowKeys = ref<number[]>([]);
const rebuilding = ref(false);

const columns: TableColumnsType = [
  { title: '指导书编号/ID', dataIndex: 'guidebook', width: 100 },
  { title: '来源指导书标题', dataIndex: 'guidebook_title', width: 220 },
  { title: '涉及实验项目', dataIndex: 'experiment_title', width: 200 },
  {
    title: '生成分段库容量(Chunks)',
    dataIndex: 'chunk_num',
    sorter: true,
    width: 150,
  },
  {
    title: '向量编译状态',
    dataIndex: 'status',
    width: 140,
    customRender: ({ text }) => {
      const colorMap: Record<string, string> = {
        pending: 'default',
        processing: 'processing',
        completed: 'success',
        failed: 'error'
      };
      const labelMap: Record<string, string> = {
        pending: '列队等待调度',
        processing: '切片编码抽特征中...',
        completed: 'RAG落库就绪',
        failed: '编译中断打回'
      };
      return h(Tag, { color: colorMap[text] || 'default' }, () => labelMap[text] || text);
    },
  },
  {
    title: '流水线反馈 / 异常日志',
    dataIndex: 'remark',
    width: 250,
    customRender: ({ text }) => {
       return h(TypographyText, { ellipsis: { tooltip: text } }, () => text);
    }
  },
  {
    title: '触发同步时间',
    dataIndex: 'updated_at',
    width: 180,
    customRender: ({ text }) => {
      return text ? dayjs(text).format('YYYY-MM-DD HH:mm:ss') : '-';
    },
  },
  { title: '强制控制', key: 'action', width: 120, fixed: 'right' },
];

const fetchData = async () => {
  loading.value = true;
  try {
    const res: any = await getAiKnowledgeIndexesApi({
      page: pagination.current,
      page_size: pagination.pageSize,
    });
    console.log('AI Knowledge Response:', res);
    
    // Robust extraction logic
    if (res && res.results) {
      tableData.value = res.results;
      pagination.total = res.count || res.results.length;
    } else if (res?.data?.results) {
      tableData.value = res.data.results;
      pagination.total = res.data.count || res.data.results.length;
    } else if (res?.data?.data?.results) {
      tableData.value = res.data.data.results;
      pagination.total = res.data.data.count || res.data.data.results.length;
    } else if (Array.isArray(res)) {
      tableData.value = res;
      pagination.total = res.length;
    } else if (Array.isArray(res?.data)) {
      tableData.value = res.data;
      pagination.total = res.data.length;
    } else if (Array.isArray(res?.data?.data)) {
      tableData.value = res.data.data;
      pagination.total = res.data.data.length;
    } else if (res?.data?.items) {
      tableData.value = res.data.items;
      pagination.total = res.data.total || res.data.items.length;
    } else if (res?.data?.list) {
      tableData.value = res.data.list;
      pagination.total = res.data.total || res.data.list.length;
    } else {
      console.warn('Unexpected response structure', res);
      tableData.value = [];
      pagination.total = 0;
    }
  } catch (error) {
    console.error('Fetch error:', error);
    message.error('获取列表受阻');
  } finally {
    loading.value = false;
  }
};

const handleSelectionChange = (selectedKeys: any[]) => {
  selectedRowKeys.value = selectedKeys as number[];
};

const triggerRebuild = async (guidebookIds: number[]) => {
  if (guidebookIds.length === 0) {
    message.warning('请勾选异常或需要重构特征索引的知识图谱文件行');
    return;
  }
  
  try {
    rebuilding.value = true;
    await rebuildAiKnowledgeIndexApi({
      guidebook_ids: guidebookIds,
      force: true,
      clear_existing: true,
    });
    message.success(`异步排队完成！已将 ${guidebookIds.length} 份数据推入 Celery GPU集群重试池`);
    selectedRowKeys.value = [];
    fetchData(); // 状态可能变为 pending，立即刷新显示
  } catch {
    message.error('向消息队列发起指令失败');
  } finally {
    rebuilding.value = false;
  }
};

const handleSingleRebuild = (record: any) => {
  triggerRebuild([record.guidebook]);
};

const handleBatchRebuild = () => {
  // mapped field from row ID isn't enough, we need guidebook ID specifically
  const ids = selectedRowKeys.value.map(id => {
    const row = tableData.value.find((r: any) => r.id === id);
    return row ? (row as any).guidebook : id;
  });
  triggerRebuild(ids);
};

const handleTableChange = (pag: any) => {
  pagination.current = pag.current;
  pagination.pageSize = pag.pageSize;
  fetchData();
};

onMounted(() => {
  fetchData();
});
</script>

<template>
  <div class="p-4">
    <Card title="知识库大盘治理 (RAG Chroma Vector)">
      <div class="mb-4 flex gap-4 w-full">
        <Space>
          <Button @click="fetchData">
            <template #icon><SyncOutlined /></template>
            全量更新探针
          </Button>
        </Space>
        
        <div class="flex-grow flex justify-end">
          <Popconfirm title="此操作将会清空之前 ChromaDB 切片并下发高开支构建命令，确认进行？" @confirm="handleBatchRebuild">
            <Button type="primary" danger :loading="rebuilding">
              <template #icon><DatabaseOutlined /></template>
              清空并强制重新解析勾选文档
            </Button>
          </Popconfirm>
        </div>
      </div>

      <Table
        :columns="columns"
        :data-source="tableData"
        :loading="loading"
        :pagination="pagination"
        :row-selection="{ selectedRowKeys: selectedRowKeys, onChange: handleSelectionChange }"
        @change="handleTableChange"
        row-key="id"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'action'">
             <Popconfirm title="确认为这份文档抛出重试流水?" @confirm="handleSingleRebuild(record)">
                <Button type="link" size="small" :disabled="record.status === 'processing'">
                  <template #icon><ToolOutlined /></template>
                  手动修补
                </Button>
              </Popconfirm>
          </template>
        </template>
      </Table>
    </Card>
  </div>
</template>
