<script setup lang="ts">
import { onMounted, reactive, ref, h } from 'vue';
import { PlusOutlined, CodeOutlined, SyncOutlined } from '@ant-design/icons-vue';
import {
  Button,
  Card,
  Form,
  Input,
  Select,
  Space,
  Switch,
  Table,
  Modal,
  Popconfirm,
  message,
  TypographyParagraph,
  TreeSelect,
} from 'ant-design-vue';
import type { TableColumnsType } from 'ant-design-vue';
import {
  getAiAgentsApi,
  createAiAgentApi,
  updateAiAgentApi,
  deleteAiAgentApi,
} from '#/api/ai';
import { getOrganizationTree } from '#/api/organization';
import { getExperimentListApi } from '#/api/experiment';

defineOptions({ name: 'AiAgentConfig' });

const orgOptions = ref<any[]>([]);
const expOptions = ref<any[]>([]);

const loading = ref(false);
const tableData = ref<any[]>([]);
const pagination = reactive({
  current: 1,
  pageSize: 20,
  total: 0,
});

const formRef = ref();
const modalVisible = ref(false);
const submitting = ref(false);
const modalTitle = ref('配置智能体');

const formState = reactive({
  id: null as null | number,
  agent_key: 'experiment_helper',
  agent_name: '实验导师',
  context_type: 'experiment',
  system_prompt: '你是一个擅长辅导实验的技术导师。解答时尽可能给出步骤与解释，而非单纯提供代码。',
  welcome_message: '你好！我是你的专属实验助教，关于这份实验文档你有什么地方不清楚的可以尽管问我~',
  enable_rag: true,
  enable_memory: true,
  is_active: true,
  owner_organization: undefined as undefined | number,
  bounded_experiment: undefined as undefined | number,
  temperature: 0.7,
  max_tokens: 2000,
  rag_top_k: 3,
  memory_window: 20,
  language: 'zh-CN',
});

const columns: TableColumnsType = [
  { title: '角色标识', dataIndex: 'agent_key', width: 150 },
  { title: '角色名', dataIndex: 'agent_name', width: 120 },
  { title: '场景归队', dataIndex: 'context_type', width: 120 },
  { 
    title: '系统人设 Prompt', 
    dataIndex: 'system_prompt', 
    width: 250, 
    customRender: ({ text }) => {
      // 溢出打点的展示渲染组件结构
      return h(TypographyParagraph, { ellipsis: { tooltip: text }, content: text, style: { margin: 0, maxWidth: '220px' } });
    }
  },
  {
    title: '启用 RAG 知识检索',
    dataIndex: 'enable_rag',
    width: 130,
    customRender: ({ text }) => (text ? '是' : '否'),
  },
  {
    title: '上下文记忆追溯',
    dataIndex: 'enable_memory',
    width: 140,
    customRender: ({ text }) => (text ? '保持' : '剥离(单发)'),
  },
  {
    title: '状态',
    dataIndex: 'is_active',
    width: 80,
    customRender: ({ text }) => (text ? '在岗' : '休息'),
  },
  { title: '操作', key: 'action', width: 160, fixed: 'right' },
];

const fetchData = async () => {
  loading.value = true;
  try {
    const res: any = await getAiAgentsApi({
      page: pagination.current,
      page_size: pagination.pageSize,
    });
    console.log('AI Agents Response:', res);
    
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
    message.error('获取列表数据阻塞');
  } finally {
    loading.value = false;
  }
};

const handleCreate = () => {
  modalTitle.value = '新增场景特化智能体';
  Object.assign(formState, {
    id: null,
    agent_key: '',
    agent_name: '',
    context_type: 'general',
    system_prompt: '你是一个助手...',
    welcome_message: '您好，请问有什么可以帮助您的？',
    enable_rag: false,
    enable_memory: true,
    is_active: true,
    owner_organization: undefined,
    bounded_experiment: undefined,
    temperature: 0.7,
    max_tokens: 2000,
    rag_top_k: 3,
    memory_window: 20,
    language: 'zh-CN',
  });
  modalVisible.value = true;
};

const handleEdit = (record: any) => {
  modalTitle.value = '微调 Agent 人设与策略';
  const orgId = typeof record.owner_organization === 'object' && record.owner_organization ? record.owner_organization.id : record.owner_organization;
  const expId = typeof record.bounded_experiment === 'object' && record.bounded_experiment ? record.bounded_experiment.id : record.bounded_experiment;
  
  Object.assign(formState, {
    ...record,
    owner_organization: orgId,
    bounded_experiment: expId,
  });
  modalVisible.value = true;
};

const handleDelete = async (record: any) => {
  try {
    await deleteAiAgentApi(record.id);
    message.success('移除成功');
    fetchData();
  } catch {
    message.error('移除失败');
  }
};

const handleSubmit = async () => {
  try {
    await formRef.value.validate();
    submitting.value = true;

    if (formState.id) {
      await updateAiAgentApi(formState.id, formState);
      message.success('配置已保存并热加载应用');
    } else {
      await createAiAgentApi(formState);
      message.success('Agent 创建成功入列');
    }
    modalVisible.value = false;
    fetchData();
  } catch (error: any) {
    if (!error.errorFields) message.error('提交失败：请检查字段规范');
  } finally {
    submitting.value = false;
  }
};

const handleTableChange = (pag: any) => {
  pagination.current = pag.current;
  pagination.pageSize = pag.pageSize;
  fetchData();
};

const loadOptions = async () => {
  try {
    const orgRes: any = await getOrganizationTree();
    const orgs = orgRes?.results || orgRes?.data?.results || orgRes?.data?.items || orgRes?.data || orgRes || [];
    orgOptions.value = Array.isArray(orgs) ? orgs : [];
    
    // Fetch all experiments (large page size to get options)
    const expRes: any = await getExperimentListApi({ page: 1, page_size: 1000 });
    const exps = expRes?.results || expRes?.data?.results || expRes?.data?.items || expRes?.data || [];
    expOptions.value = Array.isArray(exps) ? exps : [];
  } catch (err) {
    console.error('Failed to load options', err);
  }
};

onMounted(() => {
  fetchData();
  loadOptions();
});
</script>

<template>
  <div class="p-4">
    <Card title="智能体调配工作台 (Prompt Studio)">
      <div class="mb-4 flex gap-4">
        <Space>
           <Button @click="fetchData">
              <template #icon><SyncOutlined /></template>
              刷新编排清单
           </Button>
        </Space>
        <div class="flex-grow flex justify-end">
          <Button type="primary" @click="handleCreate">
            <template #icon><PlusOutlined /></template>
            构筑新 Agent (场景预制体)
          </Button>
        </div>
      </div>

      <Table
        :columns="columns"
        :data-source="tableData"
        :loading="loading"
        :pagination="pagination"
        @change="handleTableChange"
        row-key="id"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'action'">
            <Space>
              <Button type="link" size="small" @click="handleEdit(record)">
                <template #icon><CodeOutlined /></template>
                参数编辑
              </Button>
              <Popconfirm title="剥除此配置后将退回总线默认状态，确认删除？" @confirm="handleDelete(record)">
                <Button type="link" danger size="small">解雇挂载</Button>
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
      width="700px"
      :confirm-loading="submitting"
    >
      <Form ref="formRef" :model="formState" layout="vertical">
        <div class="grid grid-cols-2 gap-4">
          <Form.Item label="系统键值映射 Key" name="agent_key" :rules="[{ required: true }]">
            <Input v-model:value="formState.agent_key" placeholder="如 experiment_helper_v1" />
          </Form.Item>
          <Form.Item label="拟人化角色名称" name="agent_name" :rules="[{ required: true }]">
            <Input v-model:value="formState.agent_name" placeholder="如 运维小能手" />
          </Form.Item>
        </div>
        <div class="grid grid-cols-2 gap-4">
          <Form.Item label="绑定所属组织 (留空则全局通用)" name="owner_organization">
            <TreeSelect
              v-model:value="formState.owner_organization"
              allowClear
              placeholder="请选择专属组织/班级"
              :tree-data="orgOptions"
              :field-names="{ children: 'children', label: 'name', value: 'id' }"
              tree-default-expand-all
            />
          </Form.Item>
          
          <Form.Item label="绑定特定实验 (留空则不限实验)" name="bounded_experiment">
            <Select v-model:value="formState.bounded_experiment" allowClear placeholder="请选择专属实验任务">
              <Select.Option v-for="exp in expOptions" :key="exp.id" :value="exp.id">
                {{ exp.title }}
              </Select.Option>
            </Select>
          </Form.Item>
        </div>
        
        <Form.Item label="绑定路由触发场景" name="context_type">
          <Select v-model:value="formState.context_type">
            <Select.Option value="general">全局兜底(闲聊模式)</Select.Option>
            <Select.Option value="experiment">指导书辅导(带 RAG 侧入)</Select.Option>
            <Select.Option value="code_review">环境内报错拦截器(报错诊断答疑)</Select.Option>
          </Select>
        </Form.Item>

        <Form.Item label="大脑提示词：你希望它如何工作 (System Prompt)" name="system_prompt" :rules="[{ required: true }]">
          <Input.TextArea v-model:value="formState.system_prompt" :rows="3" placeholder="在此框中预输入提示词，规范它的语气、解决思路方向，例如：你是一个精通 Kubernetes 部署的...不回答跟系统无关闲聊话题。" />
        </Form.Item>

        <Form.Item label="初次挂载时的主动打招呼语" name="welcome_message">
          <Input.TextArea v-model:value="formState.welcome_message" :rows="1" placeholder="打开聊天窗的第一句话" />
        </Form.Item>

        <div class="grid grid-cols-4 gap-4 mt-2 mb-2 p-3 bg-gray-50 dark:bg-gray-800 rounded-md">
          <Form.Item label="回复温度 (Temperature)" name="temperature">
            <Input v-model:value="formState.temperature" type="number" step="0.1" min="0" max="2" />
          </Form.Item>
          <Form.Item label="最大回复Tokens" name="max_tokens">
            <Input v-model:value="formState.max_tokens" type="number" step="100" />
          </Form.Item>
          <Form.Item label="偏好语言" name="language">
            <Select v-model:value="formState.language">
              <Select.Option value="zh-CN">中文 (zh-CN)</Select.Option>
              <Select.Option value="en-US">英文 (en-US)</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item label="记忆窗口(条)" name="memory_window">
            <Input v-model:value="formState.memory_window" type="number" />
          </Form.Item>
        </div>

        <div class="grid grid-cols-3 gap-4 mt-2">
          <Form.Item label="是否挂载 RAG 背景知识" name="enable_rag" class="mt-4">
            <Switch v-model:checked="formState.enable_rag" />
          </Form.Item>
          <Form.Item label="是否保留会话历史">
            <Switch v-model:checked="formState.enable_memory" />
          </Form.Item>
          <Form.Item label="立即生效（排班状态）">
            <Switch v-model:checked="formState.is_active" />
          </Form.Item>
        </div>
      </Form>
    </Modal>
  </div>
</template>
