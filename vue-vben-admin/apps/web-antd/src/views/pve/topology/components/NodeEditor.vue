<script setup lang="ts">
import { reactive, watch } from 'vue';

import { Drawer, Form, Input, Select } from 'ant-design-vue';

import { NODE_TYPES } from '../utils/cytoscape-style';

const props = defineProps<{
  open: boolean;
  nodeData: Record<string, any> | null;
}>();

const emit = defineEmits<{
  'update:open': [val: boolean];
  save: [data: Record<string, any>];
}>();

const form = reactive({
  label: '',
  type: 'pve-node' as string,
  ip: '',
  interface: '',
  description: '',
});

watch(
  () => props.nodeData,
  (data) => {
    if (!data) return;
    form.label = data.label ?? '';
    form.type = data.type ?? 'pve-node';
    form.ip = data.ip ?? '';
    form.interface = data.interface ?? '';
    form.description = data.description ?? '';
  },
  { immediate: true },
);

const typeOptions = Object.entries(NODE_TYPES).map(([value, { label }]) => ({
  value,
  label,
}));

const handleSave = () => {
  emit('save', {
    ...props.nodeData,
    ...form,
  });
  emit('update:open', false);
};
</script>

<template>
  <Drawer
    :open="open"
    title="编辑节点"
    width="360"
    @close="emit('update:open', false)"
  >
    <Form layout="vertical">
      <Form.Item label="节点名称">
        <Input v-model:value="form.label" placeholder="节点名称" />
      </Form.Item>
      <Form.Item label="节点类型">
        <Select v-model:value="form.type" :options="typeOptions" />
      </Form.Item>
      <Form.Item label="IP / 网段">
        <Input v-model:value="form.ip" placeholder="例如: 192.168.1.1/24" />
      </Form.Item>
      <Form.Item label="接口名">
        <Input v-model:value="form.interface" placeholder="例如: eth0、vmbr0" />
      </Form.Item>
      <Form.Item label="备注">
        <Input.TextArea v-model:value="form.description" :rows="3" placeholder="用途说明" />
      </Form.Item>
    </Form>

    <template #footer>
      <div class="flex justify-end gap-2">
        <button
          class="rounded border border-gray-300 px-3 py-1 text-sm hover:bg-gray-50"
          @click="emit('update:open', false)"
        >
          取消
        </button>
        <button
          class="rounded bg-blue-600 px-3 py-1 text-sm text-white hover:bg-blue-700"
          @click="handleSave"
        >
          保存
        </button>
      </div>
    </template>
  </Drawer>
</template>
