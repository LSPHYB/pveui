<script setup lang="ts">
import type { LxcContainerModel } from '#/api/pve/types';

import { onMounted, reactive, ref, watch } from 'vue';

import {
  ReloadOutlined,
  SaveOutlined,
} from '@ant-design/icons-vue';
import {
  Button,
  Card,
  Col,
  Form,
  FormItem,
  Input,
  message,
  Row,
  Space,
  Spin,
  Switch,
} from 'ant-design-vue';

import { getLxcConfigApi, updateLxcConfigApi } from '#/api/pve/lxc';

defineOptions({ name: 'LxcOptions' });

const props = defineProps<{
  lxc: null | LxcContainerModel;
  lxcId: string;
}>();

const loading = ref(false);
const saving = ref(false);
const originalConfig = ref<Record<string, any>>({});
const formState = reactive({
  hostname: '',
  description: '',
  onboot: false,
  protection: false,
  unprivileged: false,
  // Features
  nesting: false,
  nfs: false,
  fuse: false,
  keyctl: false,
});

const parseBool = (val: any) => {
  if (val === null || val === undefined) return false;
  if (typeof val === 'boolean') return val;
  const str = String(val).toLowerCase();
  return ['1', 'enabled', 'on', 'true', 'yes'].includes(str);
};

const parseFeatures = (featuresStr: string) => {
  const f: Record<string, boolean> = { nesting: false, nfs: false, fuse: false, keyctl: false };
  if (!featuresStr) return f;
  featuresStr.split(',').forEach(part => {
    const [key, val] = part.split('=');
    if (key && Object.prototype.hasOwnProperty.call(f, key)) {
        f[key] = val === '1';
    } else if (key === 'nesting' || key === 'nfs' || key === 'fuse' || key === 'keyctl') {
         // handle cases where parsing might be simpler (e.g. just key presence?)
         // usually features are key=1
         if (key) f[key] = true;
    }
  });
  return f;
}

const assignConfigToForm = (config: Record<string, any> = {}) => {
  originalConfig.value = { ...config };

  const features = parseFeatures(config.features || '');

  const formData = {
    hostname: config.hostname || props.lxc?.name || '',
    description: config.description || '',
    onboot: parseBool(config.onboot),
    protection: parseBool(config.protection),
    unprivileged: parseBool(config.unprivileged),
    nesting: features.nesting,
    nfs: features.nfs,
    fuse: features.fuse,
    keyctl: features.keyctl,
  };

  Object.assign(formState, formData);
};

const loadOptions = async () => {
  if (!props.lxcId) return;

  loading.value = true;
  try {
    const res: any = await getLxcConfigApi(props.lxcId);
    const config = res?.data?.config || res?.data || {};

    assignConfigToForm(config);
  } catch (error: any) {
    message.error(error.message || '获取配置失败');
  } finally {
    loading.value = false;
  }
};

const handleSave = async () => {
  if (!props.lxcId) return;

  const params: Record<string, any> = {};
  const orig = originalConfig.value;
  const origFeatures = parseFeatures(orig.features || '');

  if (formState.hostname !== (orig.hostname || props.lxc?.name || ''))
    params.hostname = formState.hostname;
  if (formState.description !== (orig.description || ''))
    params.description = formState.description;
  if (formState.onboot !== parseBool(orig.onboot))
    params.onboot = formState.onboot ? 1 : 0;
  if (formState.protection !== parseBool(orig.protection))
    params.protection = formState.protection ? 1 : 0;
  
  // Features reconstruction
  const newFeaturesParts = [];
  if (formState.nesting) newFeaturesParts.push('nesting=1');
  if (formState.nfs) newFeaturesParts.push('nfs=1');
  if (formState.fuse) newFeaturesParts.push('fuse=1');
  if (formState.keyctl) newFeaturesParts.push('keyctl=1');
  
  const newFeaturesStr = newFeaturesParts.join(',');
  // Logic to only update if changed is tricky because default is empty.
  // We can compare against reconstructed original string or just update if any flag changed.
  
  const isFeaturesChanged = 
      formState.nesting !== origFeatures.nesting ||
      formState.nfs !== origFeatures.nfs ||
      formState.fuse !== origFeatures.fuse ||
      formState.keyctl !== origFeatures.keyctl;

  if (isFeaturesChanged) {
      params.features = newFeaturesStr;
  }

  if (Object.keys(params).length === 0) {
    message.info('无更改');
    return;
  }

  saving.value = true;
  try {
    await updateLxcConfigApi(props.lxcId, params);
    message.success('保存成功');
    loadOptions();
  } catch (error: any) {
    message.error(error.message || '保存失败');
  } finally {
    saving.value = false;
  }
};

onMounted(() => {
  loadOptions();
});

watch(
  () => props.lxcId,
  (val, oldVal) => {
    if (val && val !== oldVal) {
      loadOptions();
    }
  },
);
</script>

<template>
  <div class="flex h-full flex-col bg-gray-50 p-4 dark:bg-neutral-900">
    <Card :bordered="false" class="options-card h-full shadow-sm">
      <template #title>
        <div class="flex items-center justify-between py-2">
          <div class="flex items-center gap-2">
            <h3 class="m-0 text-lg font-semibold">容器选项</h3>
            <span class="text-sm font-normal text-gray-400"
              >VMID: {{ lxc?.vmid }}</span
            >
          </div>
          <Space>
            <Button @click="loadOptions" :loading="loading">
              <template #icon><ReloadOutlined /></template>
              刷新
            </Button>
            <Button type="primary" @click="handleSave" :loading="saving">
              <template #icon><SaveOutlined /></template>
              保存
            </Button>
          </Space>
        </div>
      </template>

      <div class="options-content" v-if="!loading">
        <Form layout="vertical" class="mx-auto max-w-4xl py-4">
          <!-- 基础信息 -->
          <div class="section-title">基础配置</div>
          <Row :gutter="24">
            <Col :span="12">
              <FormItem label="主机名 (Hostname)">
                <Input v-model:value="formState.hostname" />
              </FormItem>
            </Col>
            <Col :span="12">
              <FormItem label="描述" help="容器的备注信息">
                <Input v-model:value="formState.description" />
              </FormItem>
            </Col>
          </Row>

          <Row :gutter="24">
            <Col :span="12">
               <FormItem label="无特权容器">
                  <Switch v-model:checked="formState.unprivileged" disabled />
                  <span class="ml-2 text-gray-400">{{ formState.unprivileged ? '是' : '否' }} (创建后不可更改)</span>
               </FormItem>
            </Col>
          </Row>

          <!-- 功能开关 -->
          <div class="section-title mt-4">功能特性</div>
          <div class="switches-grid">
            <div class="switch-item">
              <div class="switch-label">
                <span>开机自启动</span>
                <small>PVE启动时自动跟随启动</small>
              </div>
              <Switch v-model:checked="formState.onboot" />
            </div>

            <div class="switch-item">
              <div class="switch-label">
                <span>防删除保护</span>
                <small>防止误删容器</small>
              </div>
              <Switch v-model:checked="formState.protection" />
            </div>

            <div class="switch-item">
               <div class="switch-label">
                  <span>Nesting</span>
                  <small>允许嵌套虚拟化 (Docker 等需要)</small>
               </div>
               <Switch v-model:checked="formState.nesting" />
            </div>

            <div class="switch-item">
               <div class="switch-label">
                  <span>NFS</span>
                  <small>允许挂载 NFS</small>
               </div>
               <Switch v-model:checked="formState.nfs" />
            </div>
            
            <div class="switch-item">
               <div class="switch-label">
                  <span>FUSE</span>
                  <small>允许 FUSE 文件系统</small>
               </div>
               <Switch v-model:checked="formState.fuse" />
            </div>

             <div class="switch-item">
               <div class="switch-label">
                  <span>Keyctl</span>
                  <small>允许 Keyctl 操作</small>
               </div>
               <Switch v-model:checked="formState.keyctl" />
            </div>
          </div>
        </Form>
      </div>
      <div v-else class="flex h-full items-center justify-center">
        <Spin size="large" tip="正在加载配置..." />
      </div>
    </Card>
  </div>
</template>

<style scoped>
.options-card :deep(.ant-card-body) {
  height: calc(100% - 65px);
  padding: 0 24px 24px;
  overflow-y: auto;
}

.options-content {
  height: 100%;
}

.section-title {
  display: flex;
  align-items: center;
  padding-bottom: 8px;
  margin-bottom: 16px;
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-1);
  border-bottom: 1px dashed var(--border-color);
}

/* Feature Switches Grid */
.switches-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
  margin-top: 16px;
}

.switch-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: var(--color-fill-1);
  border: 1px solid transparent;
  border-radius: 6px;
  transition: all 0.2s;
}

.switch-item:hover {
  background: var(--color-fill-2);
  border-color: var(--color-primary-light-4);
}

.switch-label {
  display: flex;
  flex-direction: column;
}

.switch-label span {
  font-weight: 500;
  color: var(--color-text-1);
}

.switch-label small {
  font-size: 12px;
  color: var(--color-text-3);
}
</style>
