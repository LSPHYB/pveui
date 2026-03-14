<script setup lang="ts">
import type { ElementDefinition } from 'cytoscape';

import { nextTick, onMounted, ref, watch } from 'vue';

import { useRoute } from 'vue-router';

import { Tabs } from 'ant-design-vue';

import LiveTopology from './components/LiveTopology.vue';
import TopologyDesigner from './components/TopologyDesigner.vue';

defineOptions({ name: 'PVETopology' });

const route = useRoute();
const activeTab = ref<'live' | 'designer'>('live');
const designerRef = ref<InstanceType<typeof TopologyDesigner>>();

// Tab 切换到设计器时，等 DOM 显示后触发 cy.resize()
watch(activeTab, async (val) => {
  if (val === 'designer') {
    await nextTick();
    designerRef.value?.resizeCanvas();
  }
});

const handleImportToDesigner = async (elements: ElementDefinition[]) => {
  activeTab.value = 'designer';
  await nextTick();
  designerRef.value?.loadImportedElements(elements);
};

// 从拓扑管理点击预览跳转时，自动切换到设计器 tab 并定位到对应拓扑
onMounted(async () => {
  const id = route.query.id;
  if (id) {
    activeTab.value = 'designer';
    await nextTick();
    designerRef.value?.resizeCanvas();
    designerRef.value?.selectTopologyById(Number(id));
  }
});
</script>

<template>
  <div class="flex h-full flex-col p-5">
    <Tabs
      v-model:activeKey="activeTab"
      class="flex h-full flex-col"
      :tabBarStyle="{ marginBottom: '12px' }"
    >
      <Tabs.TabPane key="live" tab="实时拓扑" force-render>
        <LiveTopology @import-to-designer="handleImportToDesigner" />
      </Tabs.TabPane>

      <Tabs.TabPane key="designer" tab="拓扑设计" force-render>
        <TopologyDesigner ref="designerRef" />
      </Tabs.TabPane>
    </Tabs>
  </div>
</template>

<style scoped>
:deep(.ant-tabs) {
  display: flex;
  flex-direction: column;
  height: 100%;
}
:deep(.ant-tabs-content-holder) {
  flex: 1;
  overflow: hidden;
}
:deep(.ant-tabs-content) {
  height: 100%;
}
:deep(.ant-tabs-tabpane) {
  height: 100%;
}
</style>
