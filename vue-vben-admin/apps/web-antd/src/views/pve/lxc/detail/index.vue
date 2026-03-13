<script setup lang="ts">
import type { LxcContainerModel } from '#/api/pve/types';

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

import { getLxcByIdApi } from '#/api/pve/lxc';

import Backup from './components/Backup.vue';
import Console from './components/Console.vue';
import Options from './components/Options.vue';
import Resources from './components/Resources.vue';
import Snapshots from './components/Snapshots.vue';
import Summary from './components/Summary.vue';

defineOptions({ name: 'LxcDetail' });

const route = useRoute();
const activeKey = ref('summary');

const lxcId = route.params.id as string;
const lxcData = ref<null | LxcContainerModel>(null);
const loading = ref(false);

const fetchLxcDetails = async () => {
  loading.value = true;
  try {
    const res: any = await getLxcByIdApi(lxcId);
    lxcData.value = res;
  } catch (error) {
    console.error(error);
  } finally {
    loading.value = false;
  }
};

onMounted(() => {
  fetchLxcDetails();
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
          class="lxc-detail-tabs h-full"
          destroy-inactive-tab-pane
        >
          <TabPane key="summary" tab="概要">
            <template #tab>
              <span>
                <DashboardOutlined />
                概要
              </span>
            </template>
            <Summary :lxc-id="lxcId" :lxc="lxcData" />
          </TabPane>

          <TabPane key="console" tab="控制台">
            <template #tab>
              <span>
                <CodeOutlined />
                控制台
              </span>
            </template>
            <Console
              :lxc-id="lxcId"
              :lxc="lxcData"
              :active="activeKey === 'console'"
            />
          </TabPane>

          <TabPane key="resources" tab="资源">
            <template #tab>
              <span>
                <HddOutlined />
                资源
              </span>
            </template>
            <Resources :lxc-id="lxcId" :lxc="lxcData" />
          </TabPane>

          <TabPane key="options" tab="选项">
            <template #tab>
              <span>
                <SettingOutlined />
                选项
              </span>
            </template>
            <Options :lxc-id="lxcId" :lxc="lxcData" />
          </TabPane>

          <TabPane key="backup" tab="备份">
            <template #tab>
              <span>
                <SaveOutlined />
                备份
              </span>
            </template>
            <Backup :lxc-id="lxcId" :lxc="lxcData" />
          </TabPane>

           <TabPane key="snapshots" tab="快照">
            <template #tab>
              <span>
                <CameraOutlined />
                快照
              </span>
            </template>
            <Snapshots :lxc-id="lxcId" :lxc="lxcData" />
          </TabPane>
        </Tabs>
      </Spin>
    </Card>
  </div>
</template>

<style scoped>
:deep(.ant-tabs-nav) {
  width: 160px;
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
