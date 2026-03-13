<script lang="ts" setup>
import type { MenuItem } from '#/api/menu/types';

import { computed, ref, watch } from 'vue';

import {
  Button,
  Drawer,
  Form,
  Input,
  InputNumber,
  message,
  Space,
  Switch,
  TreeSelect,
} from 'ant-design-vue';

import { createMenu, getMenuTreeApi, updateMenu } from '#/api/menu';

import DraggableIconPicker from './components/DraggableIconPicker.vue';

const props = defineProps<{
  open: boolean;
  record?: MenuItem | null;
}>();

const emit = defineEmits(['update:open', 'success']);

const formRef = ref();
const loading = ref(false);
const menuTree = ref<MenuItem[]>([]);

const formData = ref<Partial<MenuItem>>({
  title: '',
  path: '',
  component: '',
  icon: '',
  parent: undefined,
  order: 0,
  is_hidden: false,
});

const isUpdate = computed(() => !!props.record?.id);
const title = computed(() => (isUpdate.value ? '编辑菜单' : '新增菜单'));

// Fetch menu tree for parent selection
const fetchMenuTree = async () => {
  try {
    const res = await getMenuTreeApi();
    let data: MenuItem[] = [];
    if (Array.isArray(res)) {
      data = res;
    } else if (res && Array.isArray((res as any).data)) {
      data = (res as any).data;
    }
    menuTree.value = data;
  } catch (error) {
    console.error('Fetch menu tree error:', error);
  }
};

const handleOpen = async () => {
  formData.value = {
    title: '',
    path: '',
    component: '',
    icon: '',
    parent: undefined,
    order: 0,
    is_hidden: false,
  };

  if (isUpdate.value && props.record) {
    const r = props.record;
    formData.value = {
      ...r,
      is_hidden:
        (r as any).hidden === undefined ? r.is_hidden : (r as any).hidden,
    };
  }

  await fetchMenuTree();
};

watch(
  () => props.open,
  (val) => {
    if (val) {
      handleOpen();
    }
  },
);

const handleOk = async () => {
  try {
    loading.value = true;
    await formRef.value.validate();

    const submitData = {
      ...formData.value,
      title: formData.value.title,
      path: formData.value.path,
    };

    // 先更新当前菜单
    if (isUpdate.value && props.record?.id) {
      await updateMenu(props.record.id, submitData);
      message.success('更新成功');
    } else {
      await createMenu(submitData);
      message.success('创建成功');
    }

    // 如果是更新操作，处理级联更新
    if (isUpdate.value && props.record?.id) {
      const currentId = props.record.id;
      const isHidden = formData.value.is_hidden;

      // 获取所有菜单列表（用于查找子菜单和父菜单）
      const { getMenuList } = await import('#/api/menu');
      const menuRes: any = await getMenuList({ page_size: 1000 });
      let allMenus: any[] = [];

      if (Array.isArray(menuRes)) {
        allMenus = menuRes;
      } else if (menuRes?.results) {
        allMenus = menuRes.results;
      } else if (menuRes?.data) {
        allMenus = Array.isArray(menuRes.data)
          ? menuRes.data
          : menuRes.data?.results || [];
      }

      console.log('所有菜单:', allMenus);

      // 情况1: 如果隐藏父菜单，递归隐藏所有子菜单
      if (isHidden) {
        const findAllChildren = (parentId: number): number[] => {
          const children = allMenus.filter((m) => m.parent === parentId);
          let result = children.map((c) => c.id);

          children.forEach((child) => {
            result = result.concat(findAllChildren(child.id));
          });

          return result;
        };

        const childrenIds = findAllChildren(currentId);
        console.log('需要隐藏的子菜单IDs:', childrenIds);

        // 批量更新子菜单为隐藏
        for (const childId of childrenIds) {
          const child = allMenus.find((m) => m.id === childId);
          if (child && !child.is_hidden && !child.hidden) {
            try {
              await updateMenu(childId, { ...child, is_hidden: true });
              console.log(`隐藏子菜单: ${child.title} (ID: ${childId})`);
            } catch (error) {
              console.error(`隐藏子菜单失败 (ID: ${childId}):`, error);
            }
          }
        }

        message.success('已自动隐藏所有子菜单');
      }
      // 情况2: 如果显示子菜单，递归显示所有父菜单
      else {
        const findAllParents = (menuId: number): number[] => {
          const menu = allMenus.find((m) => m.id === menuId);
          if (!menu || !menu.parent) return [];

          const parentId = menu.parent;
          return [parentId, ...findAllParents(parentId)];
        };

        const parentIds = findAllParents(currentId);
        console.log('需要显示的父菜单IDs:', parentIds);

        // 批量更新父菜单为显示
        for (const parentId of parentIds) {
          const parent = allMenus.find((m) => m.id === parentId);
          if (parent && (parent.is_hidden || parent.hidden)) {
            try {
              await updateMenu(parentId, { ...parent, is_hidden: false });
              console.log(`显示父菜单: ${parent.title} (ID: ${parentId})`);
            } catch (error) {
              console.error(`显示父菜单失败 (ID: ${parentId}):`, error);
            }
          }
        }

        if (parentIds.length > 0) {
          message.success('已自动显示所有父菜单');
        }
      }
    }

    emit('success');
    handleCancel();
  } catch (error) {
    console.error(error);
  } finally {
    loading.value = false;
  }
};

const handleCancel = () => {
  emit('update:open', false);
};
</script>

<template>
  <Drawer :open="open" :title="title" :width="600" @close="handleCancel">
    <template #footer>
      <div style="text-align: right">
        <Space>
          <Button @click="handleCancel">取消</Button>
          <Button :loading="loading" type="primary" @click="handleOk">
            确定
          </Button>
        </Space>
      </div>
    </template>

    <Form
      ref="formRef"
      :label-col="{ span: 5 }"
      :model="formData"
      :wrapper-col="{ span: 19 }"
    >
      <Form.Item
        label="菜单名称"
        name="title"
        :rules="[{ required: true, message: '请输入菜单名称' }]"
      >
        <Input v-model:value="formData.title" placeholder="请输入菜单名称" />
      </Form.Item>

      <Form.Item
        label="路由路径"
        name="path"
        :rules="[{ required: true, message: '请输入路由路径' }]"
      >
        <Input v-model:value="formData.path" placeholder="请输入路由路径" />
      </Form.Item>

      <Form.Item label="组件路径" name="component">
        <Input
          v-model:value="formData.component"
          placeholder="请输入组件路径, 如: system/user/index"
        />
      </Form.Item>

      <Form.Item label="图标" name="icon">
        <DraggableIconPicker v-model="formData.icon" prefix="ant-design" />
      </Form.Item>

      <Form.Item label="父菜单" name="parent">
        <TreeSelect
          v-model:value="formData.parent"
          :tree-data="menuTree"
          :field-names="{ children: 'children', label: 'title', value: 'id' }"
          style="width: 100%"
          placeholder="请选择父菜单 (可选)"
          allow-clear
          tree-default-expand-all
        />
      </Form.Item>

      <Form.Item label="排序" name="order">
        <InputNumber
          v-model:value="formData.order"
          :min="0"
          style="width: 100%"
        />
      </Form.Item>

      <Form.Item label="状态" name="is_hidden">
        <Space>
          <Switch v-model:checked="formData.is_hidden" />
          <span>{{ formData.is_hidden ? '隐藏' : '显示' }}</span>
        </Space>
      </Form.Item>
    </Form>
  </Drawer>
</template>
