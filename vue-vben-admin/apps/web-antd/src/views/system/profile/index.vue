<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue';

import {
  Button,
  Card,
  Col,
  Descriptions,
  Form,
  InputPassword,
  message,
  Row,
} from 'ant-design-vue';

import { getUserInfoApi } from '#/api/core/user';
import { changePasswordApi } from '#/api/user';

defineOptions({ name: 'SystemProfile' });

interface UserInfoState {
  username: string;
  email: string;
  is_superuser: boolean;
  [key: string]: any;
}

const user = reactive<UserInfoState>({
  username: '',
  email: '',
  is_superuser: false,
});

const pwdForm = reactive({
  old_password: '',
  new_password: '',
  confirm_password: '', // Front-end implementation didn't have confirm, but usually good to have.
  // But front-end implementation implies API only needs old and new. I'll stick to simple first.
});

// Front-end used { old_password, new_password }
// I'll stick to that.

const loading = ref(false);
const saving = ref(false);
const formRef = ref();

const fetchUserInfo = async () => {
  loading.value = true;
  try {
    const res: any = await getUserInfoApi();
    // Assuming res is UserInfo object directly or in data
    const data = res.data || res;
    Object.assign(user, {
      username: data.username || data.realName || '',
      email: data.email || '',
      is_superuser: !!data.is_superuser, // check if this field exists on UserInfo or needs casting
    });
  } catch {
    message.error('获取用户信息失败');
  } finally {
    loading.value = false;
  }
};

const handleUpdatePassword = async () => {
  try {
    await formRef.value.validate();
    saving.value = true;
    await changePasswordApi({
      old_password: pwdForm.old_password,
      new_password: pwdForm.new_password,
    });
    message.success('密码修改成功');
    // Reset form
    pwdForm.old_password = '';
    pwdForm.new_password = '';
    formRef.value.clearValidate();
  } catch (error: any) {
    if (error.errorFields) return;
    message.error(`修改失败: ${error.response?.data?.detail || error.message}`);
  } finally {
    saving.value = false;
  }
};

onMounted(() => {
  fetchUserInfo();
});
</script>

<template>
  <div class="p-4">
    <Row :gutter="[16, 16]">
      <Col :span="8" :xs="24" :md="8">
        <Card title="基本信息" :loading="loading">
          <Descriptions :column="1" bordered size="small">
            <Descriptions.Item label="用户名">
              {{ user.username }}
            </Descriptions.Item>
            <Descriptions.Item label="邮箱">
              {{ user.email || '-' }}
            </Descriptions.Item>
            <Descriptions.Item label="超级管理员">
              {{ user.is_superuser ? '是' : '否' }}
            </Descriptions.Item>
          </Descriptions>
        </Card>
      </Col>

      <Col :span="16" :xs="24" :md="16">
        <Card title="修改密码">
          <Form
            ref="formRef"
            :model="pwdForm"
            layout="vertical"
            style="max-width: 400px"
          >
            <Form.Item
              label="旧密码"
              name="old_password"
              :rules="[{ required: true, message: '请输入旧密码' }]"
            >
              <InputPassword
                v-model:value="pwdForm.old_password"
                placeholder="请输入旧密码"
              />
            </Form.Item>

            <Form.Item
              label="新密码"
              name="new_password"
              :rules="[
                { required: true, message: '请输入新密码' },
                { min: 6, message: '密码长度至少6位' },
              ]"
            >
              <InputPassword
                v-model:value="pwdForm.new_password"
                placeholder="请输入新密码"
              />
            </Form.Item>

            <Form.Item>
              <Button
                type="primary"
                :loading="saving"
                @click="handleUpdatePassword"
              >
                修改密码
              </Button>
            </Form.Item>
          </Form>
        </Card>
      </Col>
    </Row>
  </div>
</template>
