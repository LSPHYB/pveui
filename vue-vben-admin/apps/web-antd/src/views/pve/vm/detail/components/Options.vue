<script setup lang="ts">
import type { VirtualMachineModel } from '#/api/pve/types';

import { onMounted, reactive, ref, watch } from 'vue';

import {
  MenuOutlined,
  ReloadOutlined,
  SaveOutlined,
} from '@ant-design/icons-vue';
import {
  Button,
  Card,
  Checkbox,
  Col,
  Form,
  FormItem,
  Input,
  message,
  Modal,
  Row,
  Select,
  Space,
  Spin,
  Switch,
} from 'ant-design-vue';

import { getVmConfigByIdApi, updateVmConfigApi } from '#/api/pve/vm';

defineOptions({ name: 'VmOptions' });

const props = defineProps<{
  vm: null | VirtualMachineModel;
  vmId: string;
}>();

const loading = ref(false);
const saving = ref(false);
const originalConfig = ref<Record<string, any>>({});
const bootOrderModalVisible = ref(false);

const formState = reactive({
  name: '',
  description: '',
  onboot: false,
  boot: '',
  bootdisk: '',
  bios: '',
  agent: false,
  protection: false,
  tablet: false,
  kvm: true,
});

// 引导设备列表
interface BootDevice {
  key: string;
  enabled: boolean;
  type: string; // 'disk', 'cdrom', 'net', 'usb'
  description: string;
}

const bootDevices = ref<BootDevice[]>([]);
const draggedIndex = ref<null | number>(null);

const parseBool = (val: any) => {
  if (val === null || val === undefined) return false;
  if (typeof val === 'boolean') return val;
  const str = String(val).toLowerCase();
  return ['1', 'enabled', 'on', 'true', 'yes'].includes(str);
};

// 解析 boot 字符串为设备列表
const parseBootOrder = (bootString: string, config: Record<string, any>) => {
  const devices: BootDevice[] = [];

  // 获取所有可能的启动设备
  const allDevices = new Set<string>();
  Object.keys(config).forEach((key) => {
    if (/^(scsi|sata|ide|virtio|efidisk|net)\d+$/i.test(key)) {
      allDevices.add(key);
    }
  });

  // 解析 boot 字符串 (格式: "order=ide2;virtio0;ide0;net0")
  if (bootString && bootString.startsWith('order=')) {
    const orderPart = bootString.replace('order=', '');
    const enabledDevices = orderPart.split(';').filter(Boolean);

    enabledDevices.forEach((deviceKey) => {
      if (allDevices.has(deviceKey)) {
        devices.push({
          key: deviceKey,
          enabled: true,
          type: getDeviceType(deviceKey, config),
          description: getDeviceDescription(deviceKey, config),
        });
        allDevices.delete(deviceKey);
      }
    });
  }

  // 添加未启用的设备
  allDevices.forEach((deviceKey) => {
    devices.push({
      key: deviceKey,
      enabled: false,
      type: getDeviceType(deviceKey, config),
      description: getDeviceDescription(deviceKey, config),
    });
  });

  return devices;
};

// 获取设备类型
const getDeviceType = (key: string, config: Record<string, any>): string => {
  if (key.startsWith('net')) return 'net';
  const value = config[key] || '';
  if (value.includes('media=cdrom')) return 'cdrom';
  return 'disk';
};

// 获取设备描述
const getDeviceDescription = (
  key: string,
  config: Record<string, any>,
): string => {
  const value = config[key] || '';
  if (key.startsWith('net')) {
    const match = value.match(/bridge=([^,]+)/);
    return match ? `Bridge: ${match[1]}` : value.slice(0, 50);
  }

  // 提取存储和大小信息
  const parts = value.split(',');
  let storage = '';
  let size = '';
  let media = '';

  parts.forEach((part: string) => {
    if (part.includes(':')) {
      storage = part.split(':')[0] || '';
    }
    if (part.startsWith('size=')) {
      size = part.replace('size=', '');
    }
    if (part.startsWith('media=')) {
      media = part.replace('media=', '');
    }
  });

  if (media) {
    return `${storage} (${media})${size ? ` - ${size}` : ''}`;
  }
  return `${storage}${size ? ` - ${size}` : ''}`;
};

// 生成 boot 字符串
const generateBootString = (devices: BootDevice[]): string => {
  const enabledDevices = devices.filter((d) => d.enabled).map((d) => d.key);
  return enabledDevices.length > 0 ? `order=${enabledDevices.join(';')}` : '';
};

const assignConfigToForm = (config: Record<string, any> = {}) => {
  originalConfig.value = { ...config };

  const formData = {
    name: config.name || props.vm?.name || '',
    description: config.description || '',
    onboot: parseBool(config.onboot),
    boot: config.boot || '',
    bootdisk: config.bootdisk || '',
    bios: config.bios || '',
    agent: parseBool(config.agent),
    protection: parseBool(config.protection),
    tablet: parseBool(config.tablet ?? config.usb0),
    kvm: config.kvm === undefined ? true : parseBool(config.kvm),
  };

  Object.assign(formState, formData);

  // 解析引导顺序
  bootDevices.value = parseBootOrder(config.boot || '', config);
};

const loadOptions = async () => {
  if (!props.vmId) return;

  loading.value = true;
  try {
    const res: any = await getVmConfigByIdApi(props.vmId);
    const config = res?.data?.config || res?.data || {};

    assignConfigToForm(config);
  } catch (error: any) {
    message.error(error.message || '获取配置失败');
  } finally {
    loading.value = false;
  }
};

const handleSave = async () => {
  if (!props.vmId) return;

  const params: Record<string, any> = {};
  const orig = originalConfig.value;

  if (formState.name !== (orig.name || props.vm?.name || ''))
    params.name = formState.name;
  if (formState.description !== (orig.description || ''))
    params.description = formState.description;
  if (formState.onboot !== parseBool(orig.onboot))
    params.onboot = formState.onboot ? 1 : 0;
  if (formState.agent !== parseBool(orig.agent))
    params.agent = formState.agent ? 1 : 0;
  if (formState.protection !== parseBool(orig.protection))
    params.protection = formState.protection ? 1 : 0;
  if (formState.tablet !== parseBool(orig.tablet ?? orig.usb0))
    params.tablet = formState.tablet ? 1 : 0;
  if (formState.kvm !== (orig.kvm === undefined ? true : parseBool(orig.kvm)))
    params.kvm = formState.kvm ? 1 : 0;
  if (formState.boot !== (orig.boot || '')) params.boot = formState.boot;
  if (formState.bootdisk !== (orig.bootdisk || ''))
    params.bootdisk = formState.bootdisk;
  if (formState.bios !== (orig.bios || '')) params.bios = formState.bios;

  if (Object.keys(params).length === 0) {
    message.info('无更改');
    return;
  }

  saving.value = true;
  try {
    await updateVmConfigApi(props.vmId, { params });
    message.success('保存成功');
    loadOptions();
  } catch (error: any) {
    message.error(error.message || '保存失败');
  } finally {
    saving.value = false;
  }
};

// 打开引导顺序编辑弹窗
const openBootOrderModal = () => {
  bootDevices.value = parseBootOrder(formState.boot, originalConfig.value);
  bootOrderModalVisible.value = true;
};

// 保存引导顺序
const saveBootOrder = () => {
  formState.boot = generateBootString(bootDevices.value);
  bootOrderModalVisible.value = false;
  message.success('引导顺序已更新 (请点击"保存"按钮应用更改)');
};

// 拖拽相关
const handleDragStart = (index: number) => {
  draggedIndex.value = index;
};

const handleDragOver = (e: DragEvent, index: number) => {
  e.preventDefault();
  if (draggedIndex.value === null || draggedIndex.value === index) return;

  const items = [...bootDevices.value];
  const draggedItem = items[draggedIndex.value];
  if (!draggedItem) return;
  items.splice(draggedIndex.value, 1);
  items.splice(index, 0, draggedItem);
  bootDevices.value = items;
  draggedIndex.value = index;
};

const handleDragEnd = () => {
  draggedIndex.value = null;
};

// 获取设备图标
const getDeviceIcon = (type: string) => {
  switch (type) {
    case 'cdrom': {
      return '💿';
    }
    case 'disk': {
      return '💾';
    }
    case 'net': {
      return '🌐';
    }
    default: {
      return '📦';
    }
  }
};

onMounted(() => {
  loadOptions();
});

watch(
  () => props.vm,
  (val) => {
    if (val && !originalConfig.value.name) {
      loadOptions();
    }
  },
);

watch(
  () => props.vmId,
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
            <h3 class="m-0 text-lg font-semibold">虚拟机选项</h3>
            <span class="text-sm font-normal text-gray-400"
              >VMID: {{ vmId }}</span
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
              <FormItem label="名称" help="虚拟机的显示名称">
                <Input v-model:value="formState.name" />
              </FormItem>
            </Col>
            <Col :span="12">
              <FormItem label="描述" help="虚拟机的备注信息">
                <Input v-model:value="formState.description" />
              </FormItem>
            </Col>
          </Row>

          <!-- 系统引导 -->
          <div class="section-title mt-4">系统引导</div>
          <Row :gutter="24">
            <Col :span="24">
              <FormItem label="引导顺序 (Boot Order)">
                <div
                  class="boot-order-input-wrapper"
                  @click="openBootOrderModal"
                >
                  <Input
                    v-model:value="formState.boot"
                    placeholder="order=ide2;virtio0;ide0;net0"
                    readonly
                    class="cursor-pointer"
                  >
                    <template #prefix>
                      <MenuOutlined class="text-gray-400" />
                    </template>
                  </Input>
                  <Button type="link" class="edit-btn">编辑</Button>
                </div>
                <div class="mt-1 text-xs text-gray-400">
                  拖拽调整设备启动优先级
                </div>
              </FormItem>
            </Col>
          </Row>
          <Row :gutter="24">
            <Col :span="12">
              <FormItem label="BIOS 类型">
                <Select v-model:value="formState.bios" allow-clear>
                  <Select.Option value="seabios">SeaBIOS (传统)</Select.Option>
                  <Select.Option value="ovmf">OVMF (UEFI)</Select.Option>
                </Select>
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
                <span>QEMU Guest Agent</span>
                <small>启用 QEMU 代理通信</small>
              </div>
              <Switch v-model:checked="formState.agent" />
            </div>

            <div class="switch-item">
              <div class="switch-label">
                <span>防删除保护</span>
                <small>防止误删虚拟机</small>
              </div>
              <Switch v-model:checked="formState.protection" />
            </div>

            <div class="switch-item">
              <div class="switch-label">
                <span>USB 平板 (Tablet)</span>
                <small>优化鼠标指针体验</small>
              </div>
              <Switch v-model:checked="formState.tablet" />
            </div>

            <div class="switch-item">
              <div class="switch-label">
                <span>KVM 硬件虚拟化</span>
                <small>提高虚拟化性能</small>
              </div>
              <Switch v-model:checked="formState.kvm" />
            </div>
          </div>
        </Form>
      </div>
      <div v-else class="flex h-full items-center justify-center">
        <Spin size="large" tip="正在加载配置..." />
      </div>
    </Card>

    <!-- 引导顺序编辑弹窗 -->
    <Modal
      v-model:open="bootOrderModalVisible"
      title="编辑引导顺序"
      :width="600"
      @ok="saveBootOrder"
      ok-text="确定"
      cancel-text="取消"
      class="boot-order-modal"
    >
      <div class="boot-order-editor">
        <div class="boot-order-table">
          <div class="table-header">
            <div class="col-drag"></div>
            <div class="col-enabled">启用</div>
            <div class="col-device">设备</div>
            <div class="col-desc">详细信息</div>
          </div>
          <div
            v-for="(device, index) in bootDevices"
            :key="device.key"
            class="table-row"
            :class="{
              dragging: draggedIndex === index,
              disabled: !device.enabled,
            }"
            draggable="true"
            @dragstart="handleDragStart(index)"
            @dragover="handleDragOver($event, index)"
            @dragend="handleDragEnd"
          >
            <div class="col-drag">
              <MenuOutlined class="drag-handle" />
            </div>
            <div class="col-enabled">
              <Checkbox v-model:checked="device.enabled" />
            </div>
            <div class="col-device">
              <div class="device-badge">
                <span class="device-icon">{{
                  getDeviceIcon(device.type)
                }}</span>
                <span class="device-key">{{ device.key }}</span>
              </div>
            </div>
            <div class="col-desc">
              {{ device.description }}
            </div>
          </div>
        </div>

        <div class="boot-order-tip">
          <p>💡 提示：拖动行以调整启动顺序，未勾选的设备将尝试跳过</p>
        </div>
      </div>
    </Modal>
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

.boot-order-input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.boot-order-input-wrapper .edit-btn {
  position: absolute;
  right: 8px;
  height: 22px;
  padding: 0 8px;
  line-height: 22px;
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

/* Boot Order Modal Styles */
.boot-order-editor {
  padding: 4px 0;
}

.boot-order-table {
  overflow: hidden;
  background: var(--color-bg-1);
  border: 1px solid var(--border-color);
  border-radius: 6px;
}

.table-header,
.table-row {
  display: flex;
  gap: 12px;
  align-items: center;
  padding: 10px 12px;
}

.table-header {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-2);
  background: var(--color-fill-2);
  border-bottom: 1px solid var(--border-color);
}

.table-row {
  background: var(--color-bg-1);
  border-bottom: 1px solid var(--border-color);
  transition: all 0.2s;
}

.table-row:last-child {
  border-bottom: none;
}

.table-row:hover {
  background: var(--color-fill-1);
}

.table-row.dragging {
  background: var(--color-fill-2);
  box-shadow: 0 2px 8px rgb(0 0 0 / 10%);
  opacity: 0.6;
}

.table-row.disabled {
  opacity: 0.6;
  filter: grayscale(1);
}

.table-row.disabled .col-device {
  opacity: 0.5;
}

.col-drag {
  display: flex;
  justify-content: center;
  width: 24px;
  color: var(--color-text-3);
  cursor: grab;
}

.col-enabled {
  display: flex;
  justify-content: center;
  width: 40px;
}

.col-device {
  width: 140px;
}

.device-badge {
  display: flex;
  gap: 8px;
  align-items: center;
  padding: 4px 8px;
  font-family: monospace;
  font-size: 13px;
  background: var(--color-fill-2);
  border-radius: 4px;
}

.col-desc {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  font-size: 13px;
  color: var(--color-text-2);
  white-space: nowrap;
}

.boot-order-tip {
  padding: 8px 12px;
  margin-top: 12px;
  font-size: 13px;
  color: var(--color-primary);
  background: var(--color-primary-light-1);
  border: 1px solid var(--color-primary-light-2);
  border-radius: 4px;
}

.boot-order-tip p {
  margin: 0;
}
</style>
