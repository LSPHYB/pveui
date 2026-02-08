<script setup lang="ts">
import type { VirtualMachineModel } from '#/api/pve/types';

import { onMounted, ref } from 'vue';
import { useRoute } from 'vue-router';

import {
  CameraOutlined,
  CodeOutlined,
  DashboardOutlined,
  HddOutlined,
  SaveOutlined,
  SettingOutlined,
} from '@ant-design/icons-vue';
import { Card, Spin, TabPane, Tabs } from 'ant-design-vue';

import { getVmByIdApi } from '#/api/pve/vm';

import Backup from './components/Backup.vue';
import Console from './components/Console.vue';
import Hardware from './components/Hardware.vue';
import Options from './components/Options.vue';
import Snapshots from './components/Snapshots.vue';
import Summary from './components/Summary.vue';

defineOptions({ name: 'VmDetail' });

const route = useRoute();
const activeKey = ref('summary');

const vmId = route.params.id as string;
const vmData = ref<null | VirtualMachineModel>(null);
const loading = ref(false);

const fetchVmDetails = async () => {
  loading.value = true;
  try {
    const res = await getVmByIdApi(vmId);
    vmData.value = res;
  } catch (error) {
    console.error(error);
  } finally {
    loading.value = false;
  }
};

onMounted(() => {
  fetchVmDetails();
});
</script>

<template>
  <div class="h-full bg-slate-50 p-4 dark:bg-neutral-900">
    <Card
      class="h-full shadow-sm"
      :body-style="{ padding: '0px', height: '100%' }"
    >
      <Spin :spinning="loading">
        <Tabs
          v-model:active-key="activeKey"
          tab-position="left"
          class="vm-detail-tabs h-full"
          destroy-inactive-tab-pane
        >
          <TabPane key="summary" tab="概要">
            <template #tab>
              <span>
                <DashboardOutlined />
                概要
              </span>
            </template>
            <Summary :vm-id="vmId" :vm="vmData" />
          </TabPane>

          <TabPane key="console" tab="控制台">
            <template #tab>
              <span>
                <CodeOutlined />
                控制台
              </span>
            </template>
            <Console
              :vm-id="vmId"
              :vm="vmData"
              :active="activeKey === 'console'"
            />
          </TabPane>

          <TabPane key="hardware" tab="硬件">
            <template #tab>
              <span>
                <HddOutlined />
                硬件
              </span>
            </template>
            <Hardware :vm-id="vmId" :vm="vmData" />
          </TabPane>

          <TabPane key="options" tab="选项">
            <template #tab>
              <span>
                <SettingOutlined />
                选项
              </span>
            </template>
            <Options :vm-id="vmId" :vm="vmData" />
          </TabPane>

          <TabPane key="backup" tab="备份">
            <template #tab>
              <span>
                <SaveOutlined />
                备份
              </span>
            </template>
            <Backup :vm-id="vmId" :vm="vmData" />
          </TabPane>

          <TabPane key="snapshots" tab="快照">
            <template #tab>
              <span>
                <CameraOutlined />
                快照
              </span>
            </template>
            <Snapshots :vm-id="vmId" :vm="vmData" />
          </TabPane>
        </Tabs>
      </Spin>
    </Card>
  </div>
</template>

<style scoped>
:deep(.ant-tabs-nav) {
  width: 160px; /* Force a width for the left sidebar to look like a menu */
}

:deep(.ant-tabs-content-holder) {
  height: 100%;
  border-left: 1px solid var(--border-color);
}

:deep(.ant-tabs-content) {
  height: 100%;
}

:deep(.ant-tabs-tabpane) {
  height: 100%;
  padding: 0;
}

:deep(.ant-spin-nested-loading),
:deep(.ant-spin-container) {
  height: 100%;
}

:deep(.ant-tabs-tab) {
  justify-content: flex-start;
  padding-left: 24px !important;
}
</style>
