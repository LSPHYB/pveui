<script lang="ts" setup>
import { computed, ref, watch } from 'vue';

import { usePagination } from '@vben/hooks';
import { IconifyIcon, listIcons } from '@vben/icons';

import { SearchOutlined } from '@ant-design/icons-vue';
import { useDraggable } from '@vueuse/core';
import { Empty, Input, Modal, Pagination } from 'ant-design-vue';

import { fetchIconsData } from './icons';

interface Props {
  modelValue?: string;
  prefix?: string;
  pageSize?: number;
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: '',
  prefix: 'ant-design',
  pageSize: 36,
});

const emit = defineEmits(['update:modelValue', 'change']);

const visible = ref(false);
const currentSelect = ref('');
const keyword = ref('');
const innerIcons = ref<string[]>([]);
const modalTitleRef = ref<HTMLElement | null>(null);

// Initialize fetch
watch(
  () => props.prefix,
  async (prefix) => {
    if (prefix) {
      // Auto fetch if generic prefix
      // Actually fetchIconsData logic handles caching
      innerIcons.value = await fetchIconsData(prefix);
    }
  },
  { immediate: true },
);

// Filter icons
const displayIcons = computed(() => {
  let source = props.prefix ? innerIcons.value : [];
  // Fallback to local listIcons if innerIcons is empty (e.g. svg icons)
  if (source.length === 0) {
    source = listIcons('', props.prefix);
  }

  if (!keyword.value) return source;
  return source.filter((item) =>
    item.toLowerCase().includes(keyword.value.toLowerCase()),
  );
});

// Pagination
const { paginationList, total, setCurrentPage, currentPage } = usePagination(
  displayIcons,
  props.pageSize,
);

const handlePageChange = (page: number) => {
  setCurrentPage(page);
};

const handleOpen = () => {
  visible.value = true;
  currentSelect.value = props.modelValue;
  keyword.value = '';
};

const handleSelect = (icon: string) => {
  currentSelect.value = icon;
  emit('update:modelValue', icon);
  emit('change', icon);
  visible.value = false;
};

// Draggable Logic
const { x, y, isDragging } = useDraggable(modalTitleRef);

// Implementation taken from Ant Design Vue simplified draggable demo logic
const startX = ref(0);
const startY = ref(0);
const startedDrag = ref(false);
const transformX = ref(0);
const transformY = ref(0);
const preTransformX = ref(0);
const preTransformY = ref(0);

const dragRect = ref({ left: 0, right: 0, top: 0, bottom: 0 });

watch([x, y], () => {
  if (!startedDrag.value) {
    startX.value = x.value;
    startY.value = y.value;
    const bodyRect = document.body.getBoundingClientRect();
    if (modalTitleRef.value) {
      const titleRect = modalTitleRef.value.getBoundingClientRect();
      dragRect.value.right = bodyRect.width - titleRect.width;
      dragRect.value.bottom = bodyRect.height - titleRect.height;
    }
    preTransformX.value = transformX.value;
    preTransformY.value = transformY.value;
  }
  startedDrag.value = true;
});

watch(isDragging, () => {
  if (!isDragging.value) {
    startedDrag.value = false;
  }
});

const transformStyles = computed(() => {
  if (!startedDrag.value && transformX.value === 0 && transformY.value === 0)
    return {};
  return {
    transform: `translate(${transformX.value}px, ${transformY.value}px)`,
  };
});

watch([x, y], () => {
  if (!startedDrag.value || !isDragging.value) return;

  const newX = preTransformX.value + x.value - startX.value;
  const newY = preTransformY.value + y.value - startY.value;

  // Optional: boundaries
  // transformX.value = Math.min(Math.max(dragRect.value.left, newX), dragRect.value.right);
  // transformY.value = Math.min(Math.max(dragRect.value.top, newY), dragRect.value.bottom);

  transformX.value = newX;
  transformY.value = newY;
});
</script>

<template>
  <div class="draggable-icon-picker">
    <!-- Trigger -->
    <div
      class="trigger-input flex h-[32px] cursor-pointer items-center justify-between rounded border bg-white px-3 py-1 transition-colors hover:border-primary"
      @click="handleOpen"
    >
      <div class="flex flex-1 items-center overflow-hidden">
        <IconifyIcon
          v-if="props.modelValue"
          :icon="props.modelValue"
          class="mr-2 size-4 flex-shrink-0"
        />
        <span v-if="props.modelValue" class="truncate text-sm">{{
          props.modelValue
        }}</span>
        <span v-else class="text-sm text-gray-400">请选择图标</span>
      </div>
      <SearchOutlined class="ml-2 text-xs text-gray-400" />
    </div>

    <!-- Modal -->
    <Modal
      v-model:open="visible"
      :mask-closable="false"
      :width="600"
      :footer="null"
      wrap-class-name="drag-modal"
    >
      <template #title>
        <div
          ref="modalTitleRef"
          class="-my-2 w-full cursor-move py-2"
          style="cursor: move"
        >
          选择图标
        </div>
      </template>

      <template #modalRender="{ originVNode }">
        <div :style="transformStyles">
          <component :is="originVNode" />
        </div>
      </template>

      <div class="pt-2">
        <!-- Search -->
        <Input
          v-model:value="keyword"
          placeholder="搜索图标"
          allow-clear
          class="mb-4"
        >
          <template #prefix>
            <SearchOutlined />
          </template>
        </Input>

        <!-- Icons Grid -->
        <div v-if="paginationList.length > 0" class="min-h-[300px]">
          <div class="grid grid-cols-6 gap-2">
            <div
              v-for="icon in paginationList"
              :key="icon"
              class="flex aspect-square cursor-pointer flex-col items-center justify-center rounded border border-transparent p-2 transition-all hover:border-primary hover:bg-gray-100"
              :class="{
                'border-primary bg-primary/10': currentSelect === icon,
              }"
              @click="handleSelect(icon)"
            >
              <IconifyIcon :icon="icon" class="mb-2 size-6 text-gray-700" />
              <span
                class="w-full truncate text-center text-xs text-gray-500"
                :title="icon"
                >{{ icon.split(':').pop() }}</span
              >
            </div>
          </div>
        </div>
        <div
          v-else
          class="flex min-h-[300px] flex-col items-center justify-center py-10 text-gray-400"
        >
          <Empty description="未找到相关图标" />
        </div>

        <!-- Pagination -->
        <div class="mt-4 flex justify-end border-t pt-2">
          <Pagination
            v-if="total > 0"
            size="small"
            :current="currentPage"
            :total="total"
            :page-size="pageSize"
            show-less-items
            @change="handlePageChange"
          />
        </div>
      </div>
    </Modal>
  </div>
</template>

<style scoped>
/* Ensure modal doesn't reset position on re-render oddly */
</style>
