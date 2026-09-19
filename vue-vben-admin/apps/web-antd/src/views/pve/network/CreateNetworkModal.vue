<script setup lang="ts">
import type { RuleObject } from 'ant-design-vue/es/form';

import type {
  CreateNetworkParams,
  PveNetworkInterface,
  PveNetworkType,
} from '#/api/pve/types';

import { computed, ref, watch } from 'vue';

import {
  Alert,
  Checkbox,
  Col,
  Divider,
  Form,
  FormItem,
  Input,
  InputNumber,
  message,
  Modal,
  Row,
  Select,
} from 'ant-design-vue';

import { createNodeNetworkApi, updateNodeNetworkApi } from '#/api/pve/node';

const props = defineProps({
  open: { type: Boolean, default: false },
  /** create：新建；edit：修改已有接口 */
  mode: { type: String as () => 'create' | 'edit', default: 'create' },
  type: { type: String as () => PveNetworkType, default: 'bridge' },
  /** mode 为 edit 时必传，用于回填 */
  record: {
    type: Object as () => PveNetworkInterface | undefined,
    default: undefined,
  },
  serverId: { type: Number, default: undefined },
  node: { type: String, default: undefined },
});

const emit = defineEmits(['update:open', 'success']);

const TYPE_LABEL: Record<PveNetworkType, string> = {
  bridge: 'Linux Bridge',
  bond: 'Linux Bond',
  vlan: 'Linux VLAN',
};

// PVE Linux Bond 支持的模式（balance-slb / lacp-* 仅 OVS Bond 可用，故不列出）
const BOND_MODES = [
  'balance-rr',
  'active-backup',
  'balance-xor',
  'broadcast',
  '802.3ad',
  'balance-tlb',
  'balance-alb',
].map((v) => ({ label: v, value: v }));

const HASH_POLICIES = ['layer2', 'layer2+3', 'layer3+4'].map((v) => ({
  label: v,
  value: v,
}));

/** 可被清空的字段。PVE 不会因为字段缺省就清值，必须显式放进 delete */
const CLEARABLE_FIELDS = [
  'cidr',
  'gateway',
  'cidr6',
  'gateway6',
  'comments',
  'mtu',
  'bridge_ports',
  'bridge_vids',
  'slaves',
  'bond_xmit_hash_policy',
  'bond-primary',
  'vlan-raw-device',
  'vlan-id',
] as const;

const isEdit = computed(() => props.mode === 'edit');
const formRef = ref();
const confirmLoading = ref(false);

const emptyState = (): CreateNetworkParams => ({
  iface: '',
  type: props.type,
  autostart: true,
  cidr: '',
  gateway: '',
  cidr6: '',
  gateway6: '',
  comments: '',
  mtu: undefined,
  bridge_ports: '',
  bridge_vlan_aware: false,
  bridge_vids: '',
  slaves: '',
  bond_mode: 'balance-rr',
  bond_xmit_hash_policy: undefined,
  'bond-primary': '',
  'vlan-raw-device': '',
  'vlan-id': undefined,
});

const str = (v: unknown) => (v === undefined || v === null ? '' : String(v).trim());
const num = (v: unknown) =>
  v === undefined || v === null || v === '' ? undefined : Number(v);

/** 把 PVE 返回的接口记录回填成表单状态 */
const stateFromRecord = (r: PveNetworkInterface): CreateNetworkParams => ({
  ...emptyState(),
  iface: r.iface,
  type: (r.type as PveNetworkType) ?? props.type,
  autostart: Boolean(r.autostart),
  cidr: str(r.cidr ?? r.address),
  gateway: str(r.gateway),
  cidr6: str(r.cidr6 ?? r.address6),
  gateway6: str(r.gateway6),
  comments: str(r.comments),
  mtu: num(r.mtu),
  bridge_ports: str(r.bridge_ports),
  bridge_vlan_aware: Boolean(r.bridge_vlan_aware),
  bridge_vids: str(r.bridge_vids),
  slaves: str(r.slaves),
  bond_mode: r.bond_mode ?? 'balance-rr',
  bond_xmit_hash_policy: r.bond_xmit_hash_policy ?? undefined,
  'bond-primary': str(r['bond-primary']),
  'vlan-raw-device': str(r['vlan-raw-device']),
  'vlan-id': num(r['vlan-id']),
});

const formState = ref<CreateNetworkParams>(emptyState());
/** 打开编辑时的原始值，用于对比出需要 delete 的字段 */
const originalState = ref<CreateNetworkParams | undefined>();

watch(
  () => props.open,
  (isOpen) => {
    if (!isOpen) return;
    if (props.mode === 'edit' && props.record) {
      const s = stateFromRecord(props.record);
      formState.value = s;
      originalState.value = { ...s };
    } else {
      formState.value = emptyState();
      originalState.value = undefined;
    }
    formRef.value?.clearValidate?.();
  },
);

/** 编辑时类型固定取记录的类型，新建时取父组件选择的类型 */
const effectiveType = computed<PveNetworkType>(() =>
  isEdit.value
    ? ((props.record?.type as PveNetworkType) ?? props.type)
    : props.type,
);

const title = computed(
  () =>
    `${isEdit.value ? '编辑' : '创建'}: ${TYPE_LABEL[effectiveType.value] ?? effectiveType.value}`,
);

// --- Bond 联动：哈希策略仅 balance-xor / 802.3ad 可用，primary 仅 active-backup 可用 ---
const hashPolicyEnabled = computed(() =>
  ['802.3ad', 'balance-xor'].includes(formState.value.bond_mode ?? ''),
);
const bondPrimaryEnabled = computed(
  () => formState.value.bond_mode === 'active-backup',
);

// --- VLAN 联动 ---
// eno1.100 形式：原始设备与标签都由名称推导
// vlan100 形式：标签由名称推导，需另填原始设备
// 其余自定义名称（ifupdown2）：两者都需手工指定
const vlanNameEncodesDevice = computed(() =>
  /^.+\.\d+$/.test(formState.value.iface ?? ''),
);
const vlanNameEncodesTag = computed(
  () =>
    vlanNameEncodesDevice.value || /^vlan\d+$/.test(formState.value.iface ?? ''),
);

const rules = computed<Record<string, RuleObject[]>>(() => {
  const cidrRule: RuleObject = {
    pattern: /^$|^[\da-f.:]+\/\d{1,3}$/i,
    message: '格式应为 IP/掩码位数，如 192.168.1.10/24',
  };
  const base: Record<string, RuleObject[]> = {
    iface: [
      { required: true, message: '请输入接口名称' },
      {
        pattern: /^[\w.-]+$/,
        message: '只能包含字母、数字、下划线、点和连字符',
      },
    ],
    cidr: [cidrRule],
    cidr6: [cidrRule],
  };
  if (effectiveType.value === 'bond') {
    base.slaves = [{ required: true, message: '请填写从属设备' }];
  }
  if (effectiveType.value === 'vlan' && !vlanNameEncodesDevice.value) {
    base['vlan-raw-device'] = [
      { required: true, message: '请填写 VLAN 原始设备' },
    ];
  }
  return base;
});

/** 只提交与当前类型相关的字段，避免把无关参数发给 PVE */
const collectFields = (): Record<string, any> => {
  const s = formState.value;
  const payload: Record<string, any> = {
    type: effectiveType.value,
    autostart: s.autostart,
    cidr: s.cidr,
    gateway: s.gateway,
    cidr6: s.cidr6,
    gateway6: s.gateway6,
    comments: s.comments,
    mtu: s.mtu,
  };

  switch (effectiveType.value) {
    case 'bond': {
      payload.slaves = s.slaves;
      payload.bond_mode = s.bond_mode;
      if (hashPolicyEnabled.value) {
        payload.bond_xmit_hash_policy = s.bond_xmit_hash_policy;
      }
      if (bondPrimaryEnabled.value) {
        payload['bond-primary'] = s['bond-primary'];
      }
      break;
    }
    case 'bridge': {
      payload.bridge_ports = s.bridge_ports;
      payload.bridge_vlan_aware = s.bridge_vlan_aware;
      if (s.bridge_vlan_aware) {
        payload.bridge_vids = s.bridge_vids;
      }
      break;
    }
    case 'vlan': {
      if (!vlanNameEncodesDevice.value) {
        payload['vlan-raw-device'] = s['vlan-raw-device'];
      }
      if (!vlanNameEncodesTag.value) {
        payload['vlan-id'] = s['vlan-id'];
      }
      break;
    }
  }
  return payload;
};

const isBlank = (v: any) => v === undefined || v === null || v === '';

/**
 * 编辑模式下算出需要清除的字段：原来有值、现在被清空的。
 * 不这样做的话 PVE 会保留原值，界面看起来"改了却没生效"。
 */
const collectDeletes = (payload: Record<string, any>): string[] => {
  const before = originalState.value;
  if (!before) return [];
  return CLEARABLE_FIELDS.filter((key) => {
    const had = !isBlank((before as Record<string, any>)[key]);
    // 字段可能因类型联动而没进 payload（如禁用的哈希策略），一并视为清空
    const now = isBlank(payload[key]);
    return had && now;
  });
};

const handleOk = async () => {
  if (!props.serverId || !props.node) {
    message.error('请先选择服务器与节点');
    return;
  }
  try {
    await formRef.value.validate();
  } catch {
    message.error('表单验证失败，请检查填写内容');
    return;
  }

  const fields = collectFields();
  const iface = formState.value.iface.trim();

  confirmLoading.value = true;
  try {
    if (isEdit.value) {
      const del = collectDeletes(fields);
      const body: Record<string, any> = Object.fromEntries(
        Object.entries(fields).filter(([, v]) => !isBlank(v)),
      );
      if (del.length > 0) body.delete = del;
      await updateNodeNetworkApi(props.serverId, props.node, iface, body as any);
      message.success(`${iface} 已修改，需点击「应用配置」后生效`);
    } else {
      const body = Object.fromEntries(
        Object.entries({ ...fields, iface }).filter(([, v]) => !isBlank(v)),
      );
      await createNodeNetworkApi(props.serverId, props.node, body as any);
      message.success(`${iface} 已创建，需点击「应用配置」后生效`);
    }
    emit('update:open', false);
    emit('success');
  } catch (error: any) {
    message.error(
      `${isEdit.value ? '修改' : '创建'}失败: ${error?.message || '未知错误'}`,
    );
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
    :title="title"
    width="900px"
    :confirm-loading="confirmLoading"
    :mask-closable="false"
    :ok-text="isEdit ? '保存' : '创建'"
    cancel-text="取消"
    @ok="handleOk"
    @cancel="handleCancel"
  >
    <Form
      ref="formRef"
      :model="formState"
      :rules="rules"
      :label-col="{ style: { width: '120px' } }"
      class="pt-2"
    >
      <Row :gutter="24">
        <!-- 左栏：名称与地址，三种类型完全一致 -->
        <Col :span="12">
          <FormItem label="名称" name="iface">
            <Input
              v-model:value="formState.iface"
              :disabled="isEdit"
              :placeholder="
                effectiveType === 'bridge'
                  ? 'vmbr2'
                  : effectiveType === 'bond'
                    ? 'bond0'
                    : 'vlan0'
              "
            />
          </FormItem>
          <FormItem label="IPv4/CIDR" name="cidr">
            <Input
              v-model:value="formState.cidr"
              placeholder="192.168.1.10/24"
            />
          </FormItem>
          <FormItem label="网关 (IPv4)" name="gateway">
            <Input v-model:value="formState.gateway" />
          </FormItem>
          <FormItem label="IPv6/CIDR" name="cidr6">
            <Input v-model:value="formState.cidr6" />
          </FormItem>
          <FormItem label="网关 (IPv6)" name="gateway6">
            <Input v-model:value="formState.gateway6" />
          </FormItem>
        </Col>

        <!-- 右栏：按类型变化 -->
        <Col :span="12">
          <FormItem label="自动启动" name="autostart">
            <Checkbox v-model:checked="formState.autostart" />
          </FormItem>

          <template v-if="effectiveType === 'bridge'">
            <FormItem label="VLAN 感知" name="bridge_vlan_aware">
              <Checkbox v-model:checked="formState.bridge_vlan_aware" />
            </FormItem>
            <FormItem label="网桥端口" name="bridge_ports">
              <Input
                v-model:value="formState.bridge_ports"
                placeholder="多个用空格分隔，如 eno1 eno2"
              />
            </FormItem>
          </template>

          <template v-else-if="effectiveType === 'bond'">
            <FormItem label="从属设备" name="slaves">
              <Input
                v-model:value="formState.slaves"
                placeholder="多个用空格分隔，如 eno1 eno2"
              />
            </FormItem>
            <FormItem label="模式" name="bond_mode">
              <Select
                v-model:value="formState.bond_mode"
                :options="BOND_MODES"
              />
            </FormItem>
            <FormItem label="哈希策略" name="bond_xmit_hash_policy">
              <Select
                v-model:value="formState.bond_xmit_hash_policy"
                :options="HASH_POLICIES"
                :disabled="!hashPolicyEnabled"
                :placeholder="
                  hashPolicyEnabled ? '请选择' : '仅 balance-xor / 802.3ad 可用'
                "
                allow-clear
              />
            </FormItem>
            <FormItem label="bond-primary" name="bond-primary">
              <Input
                v-model:value="formState['bond-primary']"
                :disabled="!bondPrimaryEnabled"
                :placeholder="
                  bondPrimaryEnabled ? '如 eno1' : '仅 active-backup 可用'
                "
              />
            </FormItem>
          </template>

          <template v-else>
            <FormItem label="VLAN 原始设备" name="vlan-raw-device">
              <Input
                v-model:value="formState['vlan-raw-device']"
                :disabled="vlanNameEncodesDevice"
                :placeholder="vlanNameEncodesDevice ? '已由名称推导' : '如 eno1'"
              />
            </FormItem>
            <FormItem label="VLAN 标签" name="vlan-id">
              <InputNumber
                v-model:value="formState['vlan-id']"
                class="w-full"
                :min="1"
                :max="4094"
                :disabled="vlanNameEncodesTag"
                :placeholder="vlanNameEncodesTag ? '已由名称推导' : '1-4094'"
              />
            </FormItem>
          </template>

          <FormItem label="备注" name="comments">
            <Input v-model:value="formState.comments" />
          </FormItem>
        </Col>
      </Row>

      <Divider class="my-2" />

      <Row :gutter="24">
        <Col :span="12">
          <FormItem label="MTU" name="mtu">
            <InputNumber
              v-model:value="formState.mtu"
              class="w-full"
              :min="1280"
              :max="65520"
              placeholder="1500"
            />
          </FormItem>
        </Col>
        <Col :span="12">
          <FormItem
            v-if="effectiveType === 'bridge'"
            label="VLAN ID"
            name="bridge_vids"
          >
            <Input
              v-model:value="formState.bridge_vids"
              :disabled="!formState.bridge_vlan_aware"
              :placeholder="
                formState.bridge_vlan_aware ? '2-4094' : '需先勾选 VLAN 感知'
              "
            />
          </FormItem>
        </Col>
      </Row>

      <Alert
        v-if="effectiveType === 'vlan'"
        type="info"
        show-icon
        class="mt-2"
        message="可以直接用「设备名.VLAN号」命名（如 eno1.100），原始设备与标签会自动推导；也可以自定义名称并指定 VLAN 原始设备（ifupdown1 仅支持 vlanXY 形式的命名）。"
      />
      <Alert
        type="warning"
        show-icon
        class="mt-2"
        :message="`${isEdit ? '修改' : '创建'}后配置写入待生效状态，需在列表页点击「应用配置」才会真正生效。`"
      />
    </Form>
  </Modal>
</template>
