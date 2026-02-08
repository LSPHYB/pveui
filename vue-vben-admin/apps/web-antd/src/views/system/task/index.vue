<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue';

import { PlusOutlined } from '@ant-design/icons-vue';
import {
  Button,
  Card,
  Form,
  Input,
  message,
  Modal,
  Popconfirm,
  Radio,
  Space,
  Table,
  Tag,
} from 'ant-design-vue';

import {
  createTaskApi,
  deleteTaskApi,
  listTasksApi,
  runTaskNowApi,
  updateTaskApi,
} from '#/api/task';

defineOptions({ name: 'SystemTask' });

interface TaskItem {
  jobId: string;
  jobName: string;
  invokeTarget: string;
  cronExpression: string;
  jobParams: any[];
  status: number; // 1: enabled, 0: disabled
  nextValidTime?: string;
}

const loading = ref(false);
const tableData = ref<TaskItem[]>([]);
const query = reactive({ job_name: '' });
const pagination = reactive({
  current: 1,
  pageSize: 10,
  total: 0,
  showSizeChanger: true,
  showTotal: (total: number) => `共 ${total} 条`,
});

// Modal
const modalVisible = ref(false);
const modalTitle = ref('新增任务');
const confirmLoading = ref(false);
const formRef = ref();

const formState = reactive({
  jobId: undefined as string | undefined,
  jobName: '',
  invokeTarget: '',
  cronExpression: '* * * * *',
  jobParams: [] as any[],
  status: 1,
});

const paramsStr = ref('[]');

const columns = [
  { title: '任务名称', dataIndex: 'jobName', width: 150 },
  { title: '调用目标', dataIndex: 'invokeTarget' },
  { title: 'Cron表达式', dataIndex: 'cronExpression', width: 150 },
  { title: '下次执行', dataIndex: 'nextValidTime', width: 180 },
  { title: '状态', dataIndex: 'status', width: 80 },
  { title: '操作', key: 'action', width: 220, fixed: 'right' as const },
];

// Helper
const formatDate = (dateStr: string) => {
  if (!dateStr) return '-';
  return new Date(dateStr).toLocaleString('zh-CN');
};

// Actions
const fetchData = async () => {
  loading.value = true;
  try {
    const params = {
      job_name: query.job_name || undefined,
      page: pagination.current,
      page_size: pagination.pageSize,
    };
    const res: any = await listTasksApi(params);
    if (res.results) {
      tableData.value = res.results;
      pagination.total = res.count;
    } else if (res.data?.rows) {
      tableData.value = res.data.rows;
      pagination.total = res.data.total;
    } else {
      tableData.value = [];
      pagination.total = 0;
    }
  } catch {
    message.error('获取任务列表失败');
  } finally {
    loading.value = false;
  }
};

const handleSearch = () => {
  pagination.current = 1;
  fetchData();
};

const handleTableChange = (pag: any) => {
  pagination.current = pag.current;
  pagination.pageSize = pag.pageSize;
  fetchData();
};

const handleCreate = () => {
  modalTitle.value = '新增任务';
  Object.assign(formState, {
    jobId: undefined,
    jobName: '',
    invokeTarget: '',
    cronExpression: '* * * * *',
    jobParams: [],
    status: 1,
  });
  paramsStr.value = '[]';
  modalVisible.value = true;
};

const handleEdit = (record: TaskItem) => {
  modalTitle.value = '编辑任务';
  Object.assign(formState, {
    jobId: record.jobId,
    jobName: record.jobName,
    invokeTarget: record.invokeTarget,
    cronExpression: record.cronExpression,
    jobParams: record.jobParams || [],
    status: record.status,
  });
  paramsStr.value = JSON.stringify(record.jobParams || []);
  modalVisible.value = true;
};

const handleDelete = async (id: string) => {
  try {
    await deleteTaskApi(id);
    message.success('删除成功');
    fetchData();
  } catch {
    message.error('删除失败');
  }
};

const handleRun = async (id: string) => {
  try {
    await runTaskNowApi(id);
    message.success('已触发执行');
  } catch (error: any) {
    message.error(error.response?.data?.detail || '执行失败');
  }
};

const handleSubmit = async () => {
  try {
    await formRef.value.validate();

    try {
      formState.jobParams = JSON.parse(paramsStr.value || '[]');
      if (!Array.isArray(formState.jobParams)) {
        throw new TypeError('Params must be array');
      }
    } catch {
      message.error('参数需为合法 JSON 数组');
      return;
    }

    confirmLoading.value = true;
    if (formState.jobId) {
      await updateTaskApi(formState.jobId, formState);
      message.success('更新成功');
    } else {
      await createTaskApi(formState);
      message.success('创建成功');
    }
    modalVisible.value = false;
    fetchData();
  } catch (error: any) {
    if (error.errorFields) return;
    message.error(`保存失败: ${error.response?.data?.detail || error.message}`);
  } finally {
    confirmLoading.value = false;
  }
};

onMounted(() => {
  fetchData();
});
</script>

<template>
  <div class="p-4">
    <Card title="任务管理">
      <template #extra>
        <Space>
          <Input
            v-model:value="query.job_name"
            placeholder="按名称搜索"
            style="width: 200px"
            allow-clear
            @press-enter="handleSearch"
          />
          <Button type="primary" @click="handleSearch">查询</Button>
          <Button type="primary" @click="handleCreate">
            <template #icon><PlusOutlined /></template>
            新增
          </Button>
        </Space>
      </template>

      <Table
        :columns="columns"
        :data-source="tableData"
        :loading="loading"
        :pagination="pagination"
        @change="handleTableChange"
        row-key="jobId"
        size="small"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.dataIndex === 'nextValidTime'">
            {{ formatDate(record.nextValidTime) }}
          </template>
          <template v-if="column.dataIndex === 'status'">
            <Tag :color="record.status === 1 ? 'green' : 'red'">
              {{ record.status === 1 ? '启用' : '停用' }}
            </Tag>
          </template>
          <template v-if="column.key === 'action'">
            <Space>
              <Button type="link" size="small" @click="handleEdit(record)">
                编辑
              </Button>
              <Popconfirm
                title="确定执行一次吗？"
                @confirm="handleRun(record.jobId)"
              >
                <Button type="link" size="small">执行</Button>
              </Popconfirm>
              <Popconfirm
                title="确定删除吗？"
                @confirm="handleDelete(record.jobId)"
              >
                <Button type="link" danger size="small">删除</Button>
              </Popconfirm>
            </Space>
          </template>
        </template>
      </Table>
    </Card>

    <Modal
      v-model:open="modalVisible"
      :title="modalTitle"
      @ok="handleSubmit"
      :confirm-loading="confirmLoading"
      width="600px"
    >
      <Form ref="formRef" :model="formState" layout="vertical">
        <Form.Item
          label="任务名称"
          name="jobName"
          :rules="[{ required: true, message: '请输入任务名称' }]"
        >
          <Input v-model:value="formState.jobName" />
        </Form.Item>
        <Form.Item
          label="调用目标"
          name="invokeTarget"
          :rules="[{ required: true, message: '请输入调用目标' }]"
        >
          <Input
            v-model:value="formState.invokeTarget"
            placeholder="如: myapp.tasks.some_func"
          />
        </Form.Item>
        <Form.Item
          label="Cron表达式"
          name="cronExpression"
          :rules="[{ required: true, message: '请输入Cron表达式' }]"
        >
          <Input
            v-model:value="formState.cronExpression"
            placeholder="* * * * *"
          />
          <div class="mt-1 text-xs text-gray-500">分 时 日 月 周</div>
        </Form.Item>
        <Form.Item label="参数(JSON数组)">
          <Input.TextArea
            v-model:value="paramsStr"
            placeholder='如 ["arg1", 123]'
          />
        </Form.Item>
        <Form.Item label="状态" name="status">
          <Radio.Group v-model:value="formState.status">
            <Radio :value="1">启用</Radio>
            <Radio :value="0">停用</Radio>
          </Radio.Group>
        </Form.Item>
      </Form>
    </Modal>
  </div>
</template>
