<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue';

import { useUserStore } from '@vben/stores';

import {
  Avatar,
  Button,
  Card,
  Col,
  Form,
  Input,
  InputPassword,
  message,
  Row,
  TabPane,
  Tabs,
  Upload,
} from 'ant-design-vue';

import { getUserInfoApi } from '#/api/core/user';
import { changePasswordApi, updateUserInfoApi, uploadAvatarApi } from '#/api/user';

defineOptions({ name: 'SystemProfile' });

const userStore = useUserStore();

// Basic Settings Form State
const basicFormState = reactive({
  id: 0,
  username: '',
  email: '',
  first_name: '',
  last_name: '',
  biography: '', 
  avatar: '', 
});

// Security Settings Form State
const passwordFormState = reactive({
  old_password: '',
  new_password: '',
  confirm_password: '',
});

const activeTab = ref('basic');
const basicLoading = ref(false);
const passwordLoading = ref(false);

const basicFormRef = ref();
const passwordFormRef = ref();

// Fetch User Info
const fetchUserInfo = async () => {
  try {
    const res: any = await getUserInfoApi();
    const data = res.data || res;

    Object.assign(basicFormState, {
      id: data.id,
      username: data.username || '',
      email: data.email || '',
      first_name: data.first_name || '',
      last_name: data.last_name || '',
      biography: data.biography || '', 
      avatar: data.avatar || '',
    });
  } catch (error) {
    console.error(error);
    message.error('获取用户信息失败');
  }
};

// Handle Basic Info Update
const handleUpdateBasicInfo = async () => {
  try {
    await basicFormRef.value.validate();
    basicLoading.value = true;
    
    const updateData = {
      email: basicFormState.email,
      first_name: basicFormState.first_name,
      last_name: basicFormState.last_name,
      biography: basicFormState.biography,
    };

    await updateUserInfoApi(updateData);
    
    // Update store to reflect changes globally
    const userInfo = await getUserInfoApi();
    userStore.setUserInfo(userInfo);
    
    message.success('基本信息更新成功');
    // Refresh local form state
    await fetchUserInfo();
  } catch (error: any) {
    if (error.errorFields) return;
    message.error(`更新失败: ${error.response?.data?.detail || error.message}`);
  } finally {
    basicLoading.value = false;
  }
};

// Handle Password Change
const handleChangePassword = async () => {
  try {
    await passwordFormRef.value.validate();
    if (passwordFormState.new_password !== passwordFormState.confirm_password) {
      message.error('两次输入的密码不一致！');
      return;
    }

    passwordLoading.value = true;
    await changePasswordApi({
      old_password: passwordFormState.old_password,
      new_password: passwordFormState.new_password,
    });
    
    message.success('密码修改成功，请重新登录');
    // Reset form
    passwordFormRef.value.resetFields();
  } catch (error: any) {
    if (error.errorFields) return;
    message.error(`修改失败: ${error.response?.data?.detail || error.message}`);
  } finally {
    passwordLoading.value = false;
  }
};

// Avatar Upload
const uploadLoading = ref(false);

const customUpload = async ({ file, onSuccess, onError }: any) => {
    try {
        uploadLoading.value = true;
        const res: any = await uploadAvatarApi(file);
        const data = res.data || res; 
        
        if (data.user && data.user.avatar) {
             basicFormState.avatar = data.user.avatar;
             // Update store user info avatar
             const currentUser = userStore.userInfo;
             if (currentUser) {
                 userStore.setUserInfo({
                     ...currentUser,
                     avatar: data.user.avatar
                 });
             }
             message.success('头像上传成功');
             onSuccess();
        } else {
             message.warning('头像上传成功，但未返回最新头像地址');
             onSuccess();
             await fetchUserInfo();
        }
    } catch (e: any) {
        message.error('头像上传失败');
        onError(e);
    } finally {
        uploadLoading.value = false;
    }
};

onMounted(() => {
  fetchUserInfo();
});
</script>

<template>
  <div class="p-4">
    <Card :bordered="false" class="profile-container">
      <Tabs v-model:activeKey="activeTab" tab-position="left">
        <!-- Tab 1: Basic Settings -->
        <TabPane key="basic" tab="基本设置">
          <div class="settings-title">基本设置</div>
          <Row :gutter="24">
            <!-- Left Column: Form -->
            <Col :span="14" :xs="24" :md="14" :lg="12">
              <Form
                ref="basicFormRef"
                :model="basicFormState"
                layout="vertical"
                class="py-4"
              >
                <Form.Item label="用户名" >
                   <Input v-model:value="basicFormState.username" disabled />
                   <span class="text-secondary text-xs">用户名不可修改</span>
                </Form.Item>
                
                <Form.Item label="邮箱" name="email" :rules="[{ type: 'email', message: '请输入有效的邮箱地址' }]">
                  <Input v-model:value="basicFormState.email" placeholder="请输入邮箱" />
                </Form.Item>

                <Form.Item label="名 (First Name)" name="first_name">
                  <Input v-model:value="basicFormState.first_name" placeholder="请输入名" />
                </Form.Item>

                <Form.Item label="姓 (Last Name)" name="last_name">
                  <Input v-model:value="basicFormState.last_name" placeholder="请输入姓" />
                </Form.Item>

                <Form.Item label="个人简介">
                  <Input.TextArea 
                    v-model:value="basicFormState.biography" 
                    :rows="4" 
                    placeholder="个人简介..." 
                    :maxlength="200"
                  />
                </Form.Item>

                <Form.Item>
                  <Button type="primary" :loading="basicLoading" @click="handleUpdateBasicInfo">
                    更新基本信息
                  </Button>
                </Form.Item>
              </Form>
            </Col>

            <!-- Right Column: Avatar -->
            <Col :span="10" :xs="24" :md="10" :lg="12" class="avatar-col">
              <div class="avatar-wrapper">
                <Avatar :size="100" :src="basicFormState.avatar" class="mb-4">
                  <template #icon v-if="!basicFormState.avatar">
                     <span class="text-xl">{{ basicFormState.first_name?.[0]?.toUpperCase() || basicFormState.username?.[0]?.toUpperCase() }}</span>
                  </template>
                </Avatar>
                <Upload 
                    name="avatar"
                    list-type="picture-card"
                    class="avatar-uploader"
                    :show-upload-list="false"
                    :custom-request="customUpload"
                >
                    <Button :loading="uploadLoading">更换头像</Button>
                </Upload>
              </div>
            </Col>
          </Row>
        </TabPane>

        <!-- Tab 2: Security Settings -->
        <TabPane key="security" tab="安全设置">
          <div class="settings-title">安全设置</div>
          <div class="py-4 max-w-lg">
             <div class="mb-6">
                <h4 class="font-medium mb-2">修改密码</h4>
                <p class="text-secondary text-sm">修改当前账户的登录密码。建议使用由字母、数字和符号组成的强密码。</p>
             </div>
             
             <Form
                ref="passwordFormRef"
                :model="passwordFormState"
                layout="vertical"
              >
                <Form.Item
                  label="当前密码"
                  name="old_password"
                  :rules="[{ required: true, message: '请输入当前密码' }]"
                >
                  <InputPassword v-model:value="passwordFormState.old_password" placeholder="请输入当前密码" />
                </Form.Item>

                <Form.Item
                  label="新密码"
                  name="new_password"
                  :rules="[
                    { required: true, message: '请输入新密码' },
                    { min: 6, message: '密码长度至少6位' }
                  ]"
                >
                  <InputPassword v-model:value="passwordFormState.new_password" placeholder="请输入新密码" />
                </Form.Item>

                <Form.Item
                  label="确认新密码"
                  name="confirm_password"
                  :rules="[
                    { required: true, message: '请再次输入新密码' }
                  ]"
                >
                  <InputPassword v-model:value="passwordFormState.confirm_password" placeholder="请再次输入新密码" />
                </Form.Item>

                <Form.Item>
                  <Button type="primary" :loading="passwordLoading" @click="handleChangePassword">
                    修改密码
                  </Button>
                </Form.Item>
              </Form>
          </div>
        </TabPane>
      </Tabs>
    </Card>
  </div>
</template>

<style scoped>
.profile-container {
  min-height: 600px;
}

.settings-title {
  font-size: 1.25rem;
  font-weight: 500;
  line-height: 1.75rem;
  margin-bottom: 12px;
  color: rgba(0, 0, 0, 0.85);
}

.text-secondary {
  color: rgba(0, 0, 0, 0.45);
}

.avatar-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-top: 20px;
}

.avatar-col {
  display: flex;
  justify-content: center;
  align-items: flex-start;
}
</style>
