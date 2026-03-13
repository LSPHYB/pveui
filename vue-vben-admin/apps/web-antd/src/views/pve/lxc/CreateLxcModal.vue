<script setup lang="ts">
import {
  createLxcApi,
  getNextVmidApi,
  getPveListApi,
  getPveNodesApi,
  getPveStorageApi,
  getPveStorageContentApi,
} from '#/api/pve/lxc';
import { getNodeNetworkApi } from '#/api/pve/node';
import {
  Form,
  Input,
  InputNumber,
  message,
  Modal,
  Radio,
  Select,
  Switch,
  Tabs,
} from 'ant-design-vue';
import { type RuleObject } from 'ant-design-vue/es/form';
import { ref, watch } from 'vue';


const props = defineProps({
  open: { type: Boolean, default: false },
});

const emit = defineEmits(['update:open', 'success']);

const activeKey = ref('1');
const confirmLoading = ref(false);

const formRef = ref();

const formState = ref({
  server_id: undefined as number | undefined,
  node: undefined as string | undefined,
  vmid: undefined as number | undefined,
  hostname: '',
  password: '',
  confirm_password: '', // New Field
  
  template_storage: undefined as string | undefined,
  template_file: undefined as string | undefined,
  
  storage: undefined as string | undefined, // RootFS
  disk_size: 8,
  
  cores: 1,
  memory: 512,
  swap: 512,
  
  network_bridge: 'vmbr0',
  ip_address: 'dhcp', // 'dhcp' or CIDR
  gateway: '',
  ipv6: 'dhcp', // Default PVE often sets 'auto' or 'dhcp'
  
  dns_domain: '',
  dns_server: '',
  
  ssh_public_key: '',
  unprivileged: true,
  features: { nesting: true }, // Default usually nesting=1 keyctl=1

  start_after_create: true,
  description: '',
});

// Options Lists
const pveList = ref<any[]>([]);
const nodeList = ref<any[]>([]);
const rootStorageList = ref<any[]>([]);
const tmplStorageList = ref<any[]>([]);
const templateList = ref<any[]>([]);
const networkList = ref<any[]>([]);

// Rules
const rules: any = {
  server_id: [{ required: true, message: '请选择服务器' }],
  node: [{ required: true, message: '请选择节点' }],
  hostname: [{ required: true, message: '请输入主机名' }],
  password: [{ required: true, message: '请输入密码' }],
  confirm_password: [
    { required: true, message: '请确认密码' },
    {
      validator: async (_rule: RuleObject, value: string) => {
        if (value && value !== formState.value.password) {
          return Promise.reject('两次输入的密码不一致');
        }
        return Promise.resolve();
      },
      trigger: 'change',
    },
  ],
  template_storage: [{ required: true, message: '请选择模板存储' }],
  template_file: [{ required: true, message: '请选择模板文件' }],
  storage: [{ required: true, message: '请选择根磁盘存储' }],
  disk_size: [{ required: true, message: '请输入磁盘大小' }],
  cores: [{ required: true, message: '请输入核心数' }],
  memory: [{ required: true, message: '请输入内存大小' }],
  network_bridge: [{ required: true, message: '请输入网桥' }],
};



// Watch open to fetch lists
watch(
  () => props.open,
  async (val) => {
    if (val) {
      activeKey.value = '1';
      // Reset form if needed, but keeping selections might be nice. 
      // Reset sensitive fields
      formState.value.password = '';
      formState.value.confirm_password = '';
      
      try {
        const res = await getPveListApi();
        let rawList: any[] = [];
        if (Array.isArray(res)) {
          rawList = res;
        } else if ((res as any).results && Array.isArray((res as any).results)) {
          rawList = (res as any).results;
        } else if ((res as any).data && Array.isArray((res as any).data.results)) {
          rawList = (res as any).data.results;
        } else if ((res as any).data && Array.isArray((res as any).data)) {
          rawList = (res as any).data;
        }
        pveList.value = rawList;
      } catch (error) {
        message.error('获取服务器列表失败');
      }
    }
  },
);

// Handlers
const handleServerChange = async (val: any) => {
  nodeList.value = [];
  formState.value.node = undefined;
  rootStorageList.value = [];
  tmplStorageList.value = [];
  
  if (!val) return;
  
  try {
    const res = await getPveNodesApi(val);
    let nodes: any[] = [];
    if (Array.isArray(res)) {
      nodes = res;
    } else if ((res as any).data && Array.isArray((res as any).data)) {
      nodes = (res as any).data;
    }
    nodeList.value = nodes;
    
    // Auto select if only one node
    if (nodes.length === 1) {
        formState.value.node = nodes[0].node;
        handleNodeChange(nodes[0].node);
    }
    
    // Auto populate next vmid
    if (formState.value.server_id) {
       const vmidRes: any = await getNextVmidApi(formState.value.server_id);
       if (vmidRes && vmidRes.vmid) {
         formState.value.vmid = vmidRes.vmid;
       } else if (vmidRes && vmidRes.data && vmidRes.data.vmid) {
         formState.value.vmid = vmidRes.data.vmid;
       }
    }
  } catch (error) {
    console.error(error);
    message.error('获取节点失败');
  }
};

const handleNodeChange = async (val: any) => {
  if (!val || !formState.value.server_id) return;
  
  try {
    const res = await getPveStorageApi(formState.value.server_id, val);
    let storages: any[] = [];
    if (Array.isArray(res)) {
      storages = res;
    } else if ((res as any).data && Array.isArray((res as any).data)) {
      storages = (res as any).data;
    } else if ((res as any).results && Array.isArray((res as any).results)) {
      storages = (res as any).results;
    }
    
    rootStorageList.value = storages.filter((item: any) => 
      item.content && item.content.includes('rootdir')
    );
    tmplStorageList.value = storages.filter((item: any) => 
      item.content && item.content.includes('vztmpl')
    );
    
    // Auto select preferred storage
    if (rootStorageList.value.length > 0) {
      const preferred = rootStorageList.value.find((s: any) => s.storage === 'local-lvm') || rootStorageList.value[0];
      formState.value.storage = preferred.storage;
    }
    if (tmplStorageList.value.length > 0) {
       const local = tmplStorageList.value.find((s: any) => s.storage === 'local');
       if (local) {
           formState.value.template_storage = local.storage;
           handleTemplateStorageChange(local.storage);
       }
    }
    
    // Fetch Networks
    fetchNetworks(val);

  } catch (error) {
    message.error('获取存储列表失败');
  }
};

const fetchNetworks = async (node: string) => {
    if (!formState.value.server_id) return;
    try {
        const res: any = await getNodeNetworkApi(formState.value.server_id, node);
        let nets: any[] = [];
        if (Array.isArray(res)) {
            nets = res;
        } else if (res.data && Array.isArray(res.data)) {
            nets = res.data;
        }
        // Filter for bridge
        networkList.value = nets.filter((n: any) => n.type === 'bridge');
        
        // Auto select vmbr0
        if (networkList.value.some(n => n.iface === 'vmbr0')) {
            formState.value.network_bridge = 'vmbr0';
        } else if (networkList.value.length > 0) {
            formState.value.network_bridge = networkList.value[0].iface;
        }
    } catch (e) {
        console.error(e);
    }
};

const handleTemplateStorageChange = async (val: any) => {
  templateList.value = [];
  formState.value.template_file = undefined;
  
  if (!val || !formState.value.server_id || !formState.value.node) return;
  
  try {
    const res = await getPveStorageContentApi(formState.value.server_id, formState.value.node, val, 'vztmpl');
    console.log('Template Storage Content Response:', res);
    
    let list: any[] = [];
    if (Array.isArray(res)) {
      list = res;
    } else if ((res as any).data && Array.isArray((res as any).data)) {
      list = (res as any).data;
    } else if ((res as any).results && Array.isArray((res as any).results)) {
       list = (res as any).results;
    }
    
    // Log the first item to see structure
    if (list.length > 0) {
        console.log('First template item:', list[0]);
    } else {
        console.log('Template list is empty');
    }
    
    templateList.value = list;
  } catch (error) {
    console.error('Fetch template error:', error);
    message.error('获取模板列表失败');
  }
};

const formatDisk = (gb?: number) => gb ? `${gb} GB` : '-';




const ipv4Mode = ref('dhcp');

const handleOk = async () => {
  try {
    await formRef.value.validate();
    confirmLoading.value = true;
    
    // Check mode
    if (ipv4Mode.value === 'dhcp') {
        formState.value.ip_address = 'dhcp';
    }
    
    const payload = {
      ...formState.value,
      ostemplate: formState.value.template_file,
    };
    
    const res: any = await createLxcApi(payload);
    message.success(`创建任务已提交 (UPID: ${res.upid})`);
    emit('update:open', false);
    emit('success');
  } catch (error: any) {
    if (error && error.errorFields) {
        // Find the tab of the first error and switch to it? 
        // Or just let user find it. 
        // Ideally we validate per step.For now full validation.
        message.error('表单验证失败，请检查填写内容');
        return;
    }
    message.error(`创建失败: ${error.message || '未知错误'}`);
  } finally {
    confirmLoading.value = false;
  }
};

const handleCancel = () => {
  emit('update:open', false);
};
</script>

<template>
  <Modal
    :open="open"
    title="创建: LXC 容器"
    width="800px"
    :confirm-loading="confirmLoading"
    :mask-closable="false"
    @ok="handleOk"
    @cancel="handleCancel"
  >
    <Form
      ref="formRef"
      :model="formState"
      :rules="rules"
      layout="vertical"
    >
      <Tabs v-model:activeKey="activeKey">
        <!-- 1. General (常规) -->
        <Tabs.TabPane key="1" tab="常规">
          <div class="grid grid-cols-2 gap-4">
             <Form.Item label="PVE服务器" name="server_id" extra="选择PVE所在服务器">
                <Select
                  v-model:value="formState.server_id"
                  placeholder="选择服务器"
                  @change="handleServerChange"
                >
                  <Select.Option v-for="item in pveList" :key="item.id" :value="item.id">
                    {{ item.name }} ({{ item.host }})
                  </Select.Option>
                </Select>
             </Form.Item>
             <Form.Item label="节点" name="node">
                <Select
                  v-model:value="formState.node"
                  placeholder="选择节点"
                  :disabled="!formState.server_id"
                  @change="handleNodeChange"
                >
                  <Select.Option v-for="item in nodeList" :key="item.node" :value="item.node">
                    {{ item.node }}
                  </Select.Option>
                </Select>
             </Form.Item>
          </div>
             
          <div class="grid grid-cols-2 gap-4">
             <Form.Item label="CT ID" name="vmid" extra="LXC 容器的唯一ID">
                <InputNumber v-model:value="formState.vmid" :min="100" class="w-full" placeholder="自动分配" />
             </Form.Item>
             <Form.Item label="主机名" name="hostname">
                <Input v-model:value="formState.hostname" placeholder="例如: my-container" />
             </Form.Item>
          </div>
             
          <div class="grid grid-cols-2 gap-4">
             <Form.Item label="密码" name="password">
                <Input.Password v-model:value="formState.password" placeholder="Root 密码" />
             </Form.Item>
             <Form.Item label="确认密码" name="confirm_password">
                <Input.Password v-model:value="formState.confirm_password" placeholder="确认密码" />
             </Form.Item>
          </div>
             
             <Form.Item label="SSH 公钥" name="ssh_public_key">
                <Input.TextArea v-model:value="formState.ssh_public_key" :rows="3" placeholder="可选: 粘贴 SSH 公钥" />
             </Form.Item>
             
             <Form.Item name="unprivileged">
                <div class="flex items-center space-x-2">
                    <Switch v-model:checked="formState.unprivileged" disabled />
                    <span>无特权的容器 (目前默认开启)</span>
                </div>
             </Form.Item>

        </Tabs.TabPane>
        
        <!-- 2. Template (模板) -->
        <Tabs.TabPane key="2" tab="模板">
           <div class="mb-4 rounded border bg-gray-50 p-4">
              <Form.Item label="存储" name="template_storage">
                 <Select
                  v-model:value="formState.template_storage"
                  placeholder="选择模板存储"
                  @change="handleTemplateStorageChange"
                 >
                    <Select.Option v-for="item in tmplStorageList" :key="item.storage" :value="item.storage">
                       {{ item.storage }} ({{ formatDisk(Math.floor(item.avail / 1024 / 1024 / 1024)) }} GB free)
                    </Select.Option>
                 </Select>
              </Form.Item>
              <Form.Item label="模板" name="template_file">
                 <Select
                  v-model:value="formState.template_file"
                  placeholder="选择系统模板"
                  show-search
                  option-filter-prop="children"
                 >
                    <Select.Option v-for="item in templateList" :key="item.volid" :value="item.volid">
                       {{ item.volid.split('/').pop() }}
                    </Select.Option>
                 </Select>
              </Form.Item>
           </div>
        </Tabs.TabPane>
        
        <!-- 3. Disks (磁盘) -->
        <Tabs.TabPane key="3" tab="磁盘">
           <div class="grid grid-cols-1 gap-y-4">
              <Form.Item label="存储" name="storage">
                 <Select v-model:value="formState.storage">
                    <Select.Option v-for="item in rootStorageList" :key="item.storage" :value="item.storage">
                       {{ item.storage }} ({{ formatDisk(Math.floor(item.avail / 1024 / 1024 / 1024)) }} GB free)
                    </Select.Option>
                 </Select>
              </Form.Item>
              <Form.Item label="磁盘大小 (GB)" name="disk_size">
                 <InputNumber v-model:value="formState.disk_size" :min="1" class="w-full" />
              </Form.Item>
           </div>
        </Tabs.TabPane>
        
        <!-- 4. CPU (CPU) -->
        <Tabs.TabPane key="4" tab="CPU">
           <div class="grid grid-cols-1 gap-y-4">
              <Form.Item label="核心数 (Cores)" name="cores">
                 <InputNumber v-model:value="formState.cores" :min="1" class="w-full" />
              </Form.Item>
           </div>
        </Tabs.TabPane>
        
        <!-- 5. Memory (内存) -->
        <Tabs.TabPane key="5" tab="内存">
           <div class="grid grid-cols-2 gap-x-8">
              <Form.Item label="内存 (MB)" name="memory">
                 <InputNumber v-model:value="formState.memory" :min="64" :step="128" class="w-full" />
              </Form.Item>
              <Form.Item label="交换分区 (MB)" name="swap">
                 <InputNumber v-model:value="formState.swap" :min="0" :step="128" class="w-full" />
              </Form.Item>
           </div>
           <div class="mt-2 text-gray-500">
             = {{ (formState.memory / 1024).toFixed(2) }} GB
           </div>
        </Tabs.TabPane>
        
        <!-- 6. Network (网络) -->
        <Tabs.TabPane key="6" tab="网络">
           <div class="grid grid-cols-1 gap-4">
              <Form.Item label="网桥" name="network_bridge">
                 <Select v-model:value="formState.network_bridge">
                    <Select.Option v-for="net in networkList" :key="net.iface" :value="net.iface">
                        {{ net.iface }} {{ net.comments ? `(${net.comments})` : '' }}
                    </Select.Option>
                 </Select>
              </Form.Item>
              
              <div class="border p-4 rounded bg-gray-50 mb-4">
                  <div class="mb-2 font-bold">IPv4</div>
                   <div class="flex items-center space-x-4 mb-2">
                       <Radio.Group v-model:value="ipv4Mode" name="ipv4mode">
                           <Radio value="dhcp">DHCP</Radio>
                           <Radio value="manual">静态</Radio> 
                       </Radio.Group>
                   </div>
                   <div v-if="ipv4Mode === 'manual'" class="grid grid-cols-2 gap-4">
                       <Form.Item label="IPv4/CIDR" name="ip_address">
                           <Input v-model:value="formState.ip_address" placeholder="192.168.1.2/24" />
                       </Form.Item>
                       <Form.Item label="网关" name="gateway">
                           <Input v-model:value="formState.gateway" />
                       </Form.Item>
                   </div>
               </div>
               
               <div class="border p-4 rounded bg-gray-50">
                  <div class="mb-2 font-bold">IPv6</div>
                   <div class="flex items-center space-x-4 mb-2">
                       <Radio.Group v-model:value="formState.ipv6" name="ipv6mode">
                           <Radio value="auto">SLAAC</Radio>
                           <Radio value="dhcp">DHCP</Radio>
                           <Radio value="manual">静态</Radio>
                       </Radio.Group>
                   </div>
               </div>
               
           </div>
        </Tabs.TabPane>
        
        <!-- 7. DNS -->
        <Tabs.TabPane key="7" tab="DNS">
            <div class="grid grid-cols-1 gap-4">
                <Form.Item label="DNS 域" name="dns_domain" extra="搜索域">
                    <Input v-model:value="formState.dns_domain" placeholder="使用主机设置" />
                </Form.Item>
                <Form.Item label="DNS 服务器" name="dns_server" extra="使用主机设置">
                    <Input v-model:value="formState.dns_server" placeholder="使用主机设置" />
                </Form.Item>
            </div>
        </Tabs.TabPane>
        
        <!-- 8. Confirm (确认) -->
        <Tabs.TabPane key="8" tab="确认">
           <div class="pt-4">
              <div class="mb-4">
                  <div class="font-bold mb-2">确认配置：</div>
                  <div class="bg-gray-50 p-4 rounded text-sm grid grid-cols-2 gap-2">
                     <div>节点: {{ formState.node }}</div>
                     <div>CT ID: {{ formState.vmid || 'Auto' }}</div>
                     <div>主机名: {{ formState.hostname }}</div>
                     <div>模板: {{ formState.template_file?.split('/').pop() }}</div>
                     <div>存储: {{ formState.storage }} ({{ formState.disk_size }} GB)</div>
                     <div>CPU: {{ formState.cores }} Cores</div>
                     <div>内存: {{ formState.memory }} MB (Swap: {{ formState.swap }} MB)</div>
                     <div>网络: {{ formState.network_bridge }} / {{ formState.ip_address }}</div>
                     <div>DNS: {{ formState.dns_domain || 'Host' }} / {{ formState.dns_server || 'Host' }}</div>
                  </div>
              </div>
              
              <div class="mt-4 flex items-center space-x-2">
                 <Switch v-model:checked="formState.start_after_create" />
                 <span>创建后启动</span>
              </div>
           </div>
        </Tabs.TabPane>
      </Tabs>
    </Form>
  </Modal>
</template>
