<script setup lang="ts">
import type {
  PveNetworkInterface,
  PVEServerModel,
  PveStorage,
} from '#/api/pve/types';

import { computed, reactive, ref, watch } from 'vue';

import {
  Card,
  Form,
  Input,
  InputNumber,
  message,
  Modal,
  Select,
  Switch,
  Tabs,
} from 'ant-design-vue';

import {
  getIsoListApi,
  getNextVmidApi,
  getNodeListApi,
  getNodeNetworkApi,
  getPveNodesApi,
  getServerNodeStoragesApi,
} from '#/api/pve/node';
import { createVmApi } from '#/api/pve/vm';

const props = defineProps({
  serverId: { type: Number },
});

const emit = defineEmits(['success', 'register']);

const isModalOpen = ref(false);
const submitting = ref(false);
const activeTab = ref('general');

// Options
const serverOptions = ref<PVEServerModel[]>([]);
const nodeOptions = ref<{ label: string; value: string }[]>([]);
const storageOptions = ref<PveStorage[]>([]);
const isoStorageOptions = ref<PveStorage[]>([]);
const diskStorageOptions = ref<PveStorage[]>([]);
const isoOptions = ref<{ label: string; value: string }[]>([]);
const networkOptions = ref<PveNetworkInterface[]>([]);

// Form State
const formRef = ref();
const formState = reactive({
  // General
  server_id: undefined as number | undefined,
  node: undefined as string | undefined,
  vmid: undefined as number | undefined,
  name: '',
  description: '',

  // OS
  ostype: 'l26', // Linux 2.6 - 5.x Kernel
  iso_storage: undefined as string | undefined,
  iso: undefined as string | undefined,

  // System / CPU / Memory
  sockets: 1,
  cores: 1,
  cpu: 'x86-64-v2-AES',
  memory: 2048, // 2GB
  numa: false,

  // Disk
  disk_storage: undefined as string | undefined,
  disk_size: 32, // GB
  scsihw: 'virtio-scsi-single',

  // Network
  network_bridge: 'vmbr0',
  network_firewall: true,
});

const rules: any = {
  server_id: [
    {
      required: true,
      message: '请选择服务器',
      trigger: 'change',
      type: 'number',
    },
  ],
  node: [{ required: true, message: '请选择节点', trigger: 'change' }],
  vmid: [
    { required: true, message: '请输入VMID', trigger: 'blur', type: 'number' },
  ],
  name: [{ required: true, message: '请输入虚拟机名称', trigger: 'blur' }],
  disk_storage: [
    { required: true, message: '请选择磁盘存储', trigger: 'change' },
  ],
  network_bridge: [
    { required: true, message: '请选择网络桥接', trigger: 'change' },
  ],
};

const osTypeOptions = [
  { label: 'Linux 2.6 - 6.x Kernel', value: 'l26' },
  { label: 'Microsoft Windows 11/2022', value: 'win11' },
  { label: 'Microsoft Windows 10/2016/2019', value: 'win10' },
  { label: 'Other', value: 'other' },
];

const cpuTypeOptions = [
  { label: 'x86-64-v2-AES (Default)', value: 'x86-64-v2-AES' },
  { label: 'Host', value: 'host' },
  { label: 'kvm64', value: 'kvm64' },
  { label: 'qemu64', value: 'qemu64' },
];

const scsiHwOptions = [
  { label: 'VirtIO SCSI Single', value: 'virtio-scsi-single' },
  { label: 'VirtIO SCSI', value: 'virtio-scsi-pci' },
  { label: 'LSI 53C895A', value: 'lsi' },
  { label: 'LSI 53C810', value: 'lsi53c810' },
  { label: 'MegaRAID SAS 8708EM2', value: 'megasas' },
];

// Computed
const modalTitle = computed(() => '创建虚拟机');

// Watchers
watch(
  () => formState.server_id,
  async (newVal) => {
    if (newVal) {
      formState.node = undefined;
      nodeOptions.value = [];
      await fetchNodes(newVal);
    }
  },
);

watch(
  () => formState.node,
  async (newVal) => {
    if (newVal && formState.server_id) {
      await Promise.all([
        fetchStorages(formState.server_id, newVal),
        fetchNetworks(formState.server_id, newVal),
        fetchNextVmid(formState.server_id),
      ]);
    }
  },
);

watch(
  () => formState.iso_storage,
  async (newVal) => {
    if (newVal && formState.server_id && formState.node) {
      formState.iso = undefined;
      await fetchIsos(formState.server_id, formState.node, newVal);
    }
  },
);

// Methods
const open = async () => {
  isModalOpen.value = true;
  activeTab.value = 'general';
  resetForm();
  await fetchServers();

  if (props.serverId) {
    formState.server_id = props.serverId;
  }
};

const close = () => {
  isModalOpen.value = false;
};

const resetForm = () => {
  formState.server_id = props.serverId;
  formState.node = undefined;
  formState.vmid = undefined;
  formState.name = '';
  formState.description = '';
  formState.ostype = 'l26';
  formState.iso_storage = undefined;
  formState.iso = undefined;
  formState.sockets = 1;
  formState.cores = 1;
  formState.memory = 2048;
  formState.disk_storage = undefined;
  formState.disk_size = 32;
  formState.network_bridge = 'vmbr0';
};

const fetchServers = async () => {
  try {
    const res = await getNodeListApi();

    let rawList: PVEServerModel[] = [];

    if (Array.isArray(res)) {
      rawList = res;
    } else if ((res as any).results && Array.isArray((res as any).results)) {
      rawList = (res as any).results;
    } else if ((res as any).data && Array.isArray((res as any).data.results)) {
      rawList = (res as any).data.results;
    } else if ((res as any).data && Array.isArray((res as any).data)) {
      rawList = (res as any).data;
    }

    serverOptions.value = rawList.filter((s) => s.is_active);

  } catch (error) {
    console.error('fetchServers error:', error);
    message.error('获取服务器列表失败');
  }
};

const fetchNodes = async (serverId: number) => {
  try {
    const res = await getPveNodesApi(serverId);

    let nodes: any[] = [];
    if (Array.isArray(res)) {
      nodes = res;
    } else if ((res as any).data && Array.isArray((res as any).data)) {
      nodes = (res as any).data;
    }

    if (nodes.length > 0) {
      nodeOptions.value = nodes.map((node: any) => ({
        label: node.node,
        value: node.node,
      }));
      // Auto select if only one node
      if (nodeOptions.value.length === 1) {
        formState.node = nodeOptions.value[0]?.value;
      }
    }
  } catch (error) {
    console.error('fetchNodes error:', error);
    message.error('获取节点列表失败');
  }
};

const fetchStorages = async (serverId: number, node: string) => {
  try {
    const res = await getServerNodeStoragesApi(serverId, node);

    let storages: PveStorage[] = [];
    if (Array.isArray(res)) {
      storages = res;
    } else if ((res as any).data && Array.isArray((res as any).data)) {
      storages = (res as any).data;
    }

    if (storages.length > 0) {
      storageOptions.value = storages;
      // Filter for ISO (must support 'iso')
      isoStorageOptions.value = storages.filter((s) =>
        s.content.includes('iso'),
      );
      // Filter for Disk (usually 'images' or 'rootdir')
      diskStorageOptions.value = storages.filter((s) =>
        s.content.includes('images'),
      );

      // Auto select defaults
      if (diskStorageOptions.value.length > 0) {
        // Prefer local-lvm or a storage with space
        const preferred =
          diskStorageOptions.value.find((s) => s.storage === 'local-lvm') ||
          diskStorageOptions.value[0];
        if (preferred) {
          formState.disk_storage = preferred.storage;
        }
      }
      if (isoStorageOptions.value.length > 0) {
        const preferred =
          isoStorageOptions.value.find((s) => s.storage === 'local') ||
          isoStorageOptions.value[0];
        if (preferred) {
          formState.iso_storage = preferred.storage;
        }
      }
    }
  } catch {
    message.error('获取存储列表失败');
  }
};

const fetchIsos = async (serverId: number, node: string, storage: string) => {
  try {
    const res: any = await getIsoListApi(serverId, node, storage);

    let isos: any[] = [];
    if (Array.isArray(res)) {
      isos = res;
    } else if (res.data && Array.isArray(res.data)) {
      isos = res.data;
    }

    if (isos.length > 0) {
      isoOptions.value = isos.map((item: any) => ({
        label: item.volid.split('/').pop(), // Display filename
        value: item.volid, // Use full volid like local:iso/proxmox.iso
      }));
    } else {
      isoOptions.value = [];
    }
  } catch (error) {
    console.error(error);
    message.warning('获取ISO列表失败');
  }
};

const fetchNetworks = async (serverId: number, node: string) => {
  try {
    const res: any = await getNodeNetworkApi(serverId, node);

    let networks: any[] = [];
    if (Array.isArray(res)) {
      networks = res;
    } else if (res.data && Array.isArray(res.data)) {
      networks = res.data;
    }

    if (networks.length > 0) {
      // Filter for bridges (type = bridge)
      networkOptions.value = networks.filter(
        (net: any) => net.type === 'bridge',
      );
      if (networkOptions.value.length > 0) {
        // Prefer vmbr0
        const vmbr0 = networkOptions.value.find((n) => n.iface === 'vmbr0');
        formState.network_bridge = vmbr0
          ? vmbr0.iface
          : networkOptions.value[0]?.iface || 'vmbr0';
      }
    }
  } catch (error) {
    console.error(error);
  }
};

const fetchNextVmid = async (serverId: number) => {
  try {
    const res: any = await getNextVmidApi(serverId);
    if (res && res.vmid) {
      formState.vmid = res.vmid;
    } else if (res && res.data && res.data.vmid) {
      formState.vmid = res.data.vmid;
    }
  } catch (error) {
    console.error(error);
  }
};

const handleSubmit = async () => {
  try {
    await formRef.value.validate();
    submitting.value = true;

    // Prepare data format for backend
    // Backend expects 'iso' to be filename or volid.
    // And 'iso_storage' if iso is just filename.
    // Our isoOptions.value uses volid.

    // Backend:
    // if ':' in iso_value: params['ide2'] = f'{iso_value},media=cdrom'
    // else: uses iso_storage

    // So we can just pass the volid as 'iso'.

    const payload = {
      ...formState,
      // Ensure specific types if needed, though form does it
    };

    await createVmApi(payload);
    message.success('虚拟机创建任务已提交');
    emit('success');
    close();
  } catch (error: any) {
    console.error(error);
    message.error(`创建失败: ${error.message || '未知错误'}`);
  } finally {
    submitting.value = false;
  }
};

defineExpose({
  open,
});
</script>

<template>
  <Modal
    v-model:open="isModalOpen"
    :title="modalTitle"
    width="800px"
    @ok="handleSubmit"
    @cancel="close"
    :confirm-loading="submitting"
  >
    <Form ref="formRef" :model="formState" :rules="rules" layout="vertical">
      <Tabs v-model:active-key="activeTab">
        <!-- GENERAL -->
        <Tabs.TabPane key="general" tab="常规">
          <div class="grid grid-cols-2 gap-4">
            <Form.Item label="PVE服务器" name="server_id">
              <Select
                v-model:value="formState.server_id"
                placeholder="选择服务器"
                :options="
                  serverOptions.map((s) => ({ label: s.name, value: s.id }))
                "
              />
            </Form.Item>

            <Form.Item label="节点" name="node">
              <Select
                v-model:value="formState.node"
                placeholder="选择节点"
                :options="nodeOptions"
                :disabled="!formState.server_id"
              />
            </Form.Item>
          </div>

          <div class="grid grid-cols-2 gap-4">
            <Form.Item label="VM ID" name="vmid" extra="通常自动生成，无需修改">
              <InputNumber
                v-model:value="formState.vmid"
                style="width: 100%"
                :min="100"
              />
            </Form.Item>

            <Form.Item label="名称" name="name">
              <Input v-model:value="formState.name" placeholder="虚拟机名称" />
            </Form.Item>
          </div>

          <Form.Item label="描述" name="description">
            <Input.TextArea v-model:value="formState.description" :rows="3" />
          </Form.Item>
        </Tabs.TabPane>

        <!-- OS -->
        <Tabs.TabPane key="os" tab="操作系统">
          <Form.Item label="操作系统类型" name="ostype">
            <Select v-model:value="formState.ostype" :options="osTypeOptions" />
          </Form.Item>

          <div class="mb-4 rounded border bg-gray-50 p-4">
            <Form.Item label="ISO存储" name="iso_storage">
              <Select
                v-model:value="formState.iso_storage"
                :options="
                  isoStorageOptions.map((s) => ({
                    label: `${s.storage} (可用: ${Math.round(s.avail / 1024 / 1024 / 1024)}GB)`,
                    value: s.storage,
                  }))
                "
                :disabled="!formState.node"
              />
            </Form.Item>

            <Form.Item label="ISO镜像" name="iso">
              <Select
                v-model:value="formState.iso"
                :options="isoOptions"
                :disabled="!formState.iso_storage"
                show-search
                placeholder="选择ISO文件"
              />
            </Form.Item>
          </div>
        </Tabs.TabPane>

        <!-- SYSTEM -->
        <Tabs.TabPane key="system" tab="系统配置">
          <div class="grid grid-cols-2 gap-4">
            <Form.Item label="SCSI控制器" name="scsihw">
              <Select
                v-model:value="formState.scsihw"
                :options="scsiHwOptions"
              />
            </Form.Item>
            <Form.Item label="Qemu Agent" name="qemu_agent">
              <Switch v-if="false" />
              <!-- Not implemented in backend yet -->
              <span class="text-xs text-gray-400">默认禁用 (后端暂不支持更改)</span>
            </Form.Item>
          </div>

          <div class="mt-4 grid grid-cols-2 gap-4">
            <Card size="small" title="CPU">
              <Form.Item label="Sockets" name="sockets">
                <InputNumber
                  v-model:value="formState.sockets"
                  :min="1"
                  :max="8"
                  class="w-full"
                />
              </Form.Item>
              <Form.Item label="Cores" name="cores">
                <InputNumber
                  v-model:value="formState.cores"
                  :min="1"
                  :max="128"
                  class="w-full"
                />
              </Form.Item>
              <Form.Item label="类别" name="cpu">
                <Select
                  v-model:value="formState.cpu"
                  :options="cpuTypeOptions"
                />
              </Form.Item>
              <Form.Item label="NUMA" name="numa">
                <Switch v-model:checked="formState.numa" />
              </Form.Item>
            </Card>

            <Card size="small" title="内存">
              <Form.Item label="内存 (MB)" name="memory">
                <InputNumber
                  v-model:value="formState.memory"
                  :min="16"
                  :step="512"
                  class="w-full"
                />
              </Form.Item>
              <div class="mt-2 text-gray-500">
                = {{ (formState.memory / 1024).toFixed(2) }} GB
              </div>
            </Card>
          </div>
        </Tabs.TabPane>

        <!-- DISK -->
        <Tabs.TabPane key="disk" tab="硬盘">
          <Form.Item label="磁盘存储" name="disk_storage">
            <Select
              v-model:value="formState.disk_storage"
              :options="
                diskStorageOptions.map((s) => ({
                  label: `${s.storage} (可用: ${Math.round(s.avail / 1024 / 1024 / 1024)}GB)`,
                  value: s.storage,
                }))
              "
            />
          </Form.Item>

          <Form.Item label="磁盘大小 (GB)" name="disk_size">
            <InputNumber
              v-model:value="formState.disk_size"
              :min="1"
              :max="100000"
              style="width: 200px"
            />
          </Form.Item>
        </Tabs.TabPane>

        <!-- NETWORK -->
        <Tabs.TabPane key="network" tab="网络">
          <Form.Item label="桥接网卡" name="network_bridge">
            <Select
              v-model:value="formState.network_bridge"
              :options="
                networkOptions.map((n) => ({
                  label: `${n.iface} ${n.comments ? `(${n.comments})` : ''}`,
                  value: n.iface,
                }))
              "
            />
          </Form.Item>

          <Form.Item label="防火墙" name="network_firewall">
            <Switch v-model:checked="formState.network_firewall" />
          </Form.Item>
        </Tabs.TabPane>
      </Tabs>
    </Form>
  </Modal>
</template>
