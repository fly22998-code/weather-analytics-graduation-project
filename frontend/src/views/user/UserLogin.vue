<template>
  <div class="auth-container">
    <div class="bg-decoration top-left"></div>
    <div class="bg-decoration bottom-right"></div>
    
    <el-card class="auth-card">
      <div slot="header" class="auth-header">
        <el-icon class="header-icon"><i class="el-icon-key"></i></el-icon>
        <h2>用户登录</h2>
      </div>
      
      <el-form 
        :model="loginForm" 
        :rules="loginRules" 
        ref="loginFormRef" 
        class="auth-form"
        label-width="0"  
        @submit.native.prevent
      >
        <el-form-item prop="email" class="form-item">
          <el-input 
            v-model="loginForm.email" 
            type="email" 
            placeholder="请输入邮箱"
            class="full-width-input"
            :autofocus="true"
            @keydown.enter="handleEnterKey"
            name="weather-login-page-email"
            autocomplete="new-password"
            :disabled="isLoading"
          >
          </el-input>
        </el-form-item>
        
        <el-form-item prop="password" class="form-item">
          <el-input 
            v-model="loginForm.password" 
            type="password"
            placeholder="请输入密码"
            class="full-width-input"
            show-password
            @keydown.enter="handleEnterKey"
            name="weather-login-page-password"
            autocomplete="new-password"
            :disabled="isLoading"
          >
          </el-input>
        </el-form-item>
        
        <el-form-item class="form-actions">
          <el-button 
            type="primary" 
            class="full-width-btn" 
            @click="handleLogin"
            :loading="isLoading"
            :disabled="isLoading"
          >
            <span v-if="!isLoading">登录</span>
            <span v-else>登录中...</span>
          </el-button>
          <div class="register-link">
            还没有账号？
            <router-link to="/register" class="interactive-link">立即注册</router-link>
            <span style="margin: 0 8px;">|</span>
            <router-link to="/password-reset" class="interactive-link">忘记密码？</router-link>
          </div>
        </el-form-item>
      </el-form>
    </el-card>

    <div class="beian-info">
      <a href="https://beian.miit.gov.cn" target="_blank" rel="noopener noreferrer">
        浙ICP备2025209216号-1
      </a>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, watch, onUnmounted, nextTick } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import axios, { AxiosError } from 'axios';
import type { AxiosRequestConfig, CancelTokenSource } from 'axios';
import { ElMessage, ElMessageBox, ElForm } from 'element-plus';

import { BASE_URL } from '@/store/config';
import { isLoggedIn, notifyAuthChanged } from '@/utils/auth';
import { setSessionSignKey } from '@/utils/signature';
import { clearAccessToken, setAccessToken } from '@/utils/tokenStorage';

const axiosInstance = axios.create({
  baseURL: BASE_URL,
  timeout: 8000,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json'
  }
});

interface LoginResponse {
  code: number;
  message: string;
  data: {
    token: string;
    access_token?: string;
    sign_key?: string;
    email: string;
    expire_text: string;
  };
}

interface ErrorResponseData {
  code?: number;
  message: string;
  data?: any;
}

let cancelSource: CancelTokenSource | null = null;
// 移除 showLoginPwd，因为 show-password 属性会自动处理
const isLoading = ref(false);
const router = useRouter();
const route = useRoute();
const loginFormRef = ref<InstanceType<typeof ElForm> | null>(null);
const loginRequestId = ref<number | null>(null);
const lastErrorTime = ref(0);
const remainingAttempts = ref<number | null>(null);

const loginForm = reactive({
  email: '',
  password: ''
});

const emailReg = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;

const loginRules = reactive({
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { 
      pattern: emailReg, 
      message: '请输入正确的邮箱格式（如xxx@example.com）', 
      trigger: ['blur', 'change']
    }
  ] as any[],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 8, message: '密码长度至少8位', trigger: 'blur' },
    { max: 128, message: '密码长度不能超过128位', trigger: 'blur' },
    { 
      validator: (rule: any, value: string, callback: any) => {
        if (value && (/^\d+$/.test(value) || /^[a-zA-Z]+$/.test(value))) {
          callback(new Error('密码不能全为数字或全为字母'));
          return;
        }
        callback();
      },
      trigger: 'blur'
    }
  ] as any[]
});

const handleEnterKey = () => {
  if (!isLoading.value) {
    handleLogin();
  }
};

const showError = (message: string, field?: 'email' | 'password') => {
  const now = Date.now();
  if (now - lastErrorTime.value < 1000) return;
  
  lastErrorTime.value = now;
  ElMessage.error(message);
  
  if (field) {
    nextTick(() => {
      const input = document.querySelector<HTMLInputElement>(
        field === 'email' ? 'input[type="email"]' : 'input[type="password"], input[type="text"]'
      );
      input?.focus();
    });
  }
};

const handleLogin = async (forceLogin = false) => {
  const shouldForceLogin = forceLogin === true;
  if (!loginFormRef.value || isLoading.value) return;

  if (cancelSource) {
    cancelSource.cancel('新请求已发起，取消之前的请求');
  }
  cancelSource = axios.CancelToken.source();

  try {
    await loginFormRef.value.validate();
  } catch (error) {
    return showError('请完善登录信息');
  }

  isLoading.value = true;
  const currentRequestId = Date.now();
  loginRequestId.value = currentRequestId;

  try {
    const config: AxiosRequestConfig = {
      url: '/weather/user/login/',
      method: 'post',
      data: {
        email: loginForm.email.trim().toLowerCase(),
        password: loginForm.password,
        force_login: shouldForceLogin
      },
      cancelToken: cancelSource.token
    };

    const response = await axiosInstance.post<LoginResponse>(
      config.url, 
      config.data, 
      { cancelToken: config.cancelToken }
    );

    if (loginRequestId.value !== currentRequestId) return;

    if (response.data.code === 200) {
      const { token, access_token, sign_key, email, expire_text } = response.data.data;
      setAccessToken(access_token || token);
      setSessionSignKey(sign_key);
      localStorage.removeItem('last_login_email');
      notifyAuthChanged();
      
      ElMessage({
        message: `登录成功，即将跳转（有效期${expire_text}）`,
        type: 'success',
        duration: 630
      });
      
      const redirectPath = router.currentRoute.value.query.redirect as string || '/weather';
      router.push(redirectPath).catch(err => {
        console.error('跳转失败:', err);
        ElMessage.error('跳转失败，请手动刷新页面');
      });
    } else {
      showError(response.data.message || '登录失败，请重试');
    }

  } catch (error) {
    if (axios.isCancel(error)) {
      console.log('请求已取消:', error.message);
      return;
    }

    const err = error as AxiosError<ErrorResponseData>;
    const resData = err.response?.data;
    const backendMsg = resData?.message;

    if (err.message.includes('timeout')) {
      ElMessageBox.confirm(
        '登录超时，是否重试？',
        '网络提示',
        {
          confirmButtonText: '重试',
          cancelButtonText: '取消',
          type: 'warning',
          autofocus: false,
          customClass: 'minimal-alert-box'
        }
      ).then(() => {
        if (loginRequestId.value === currentRequestId) {
          handleLogin();
        }
      }).catch(() => {});
    } 
    else if (err.response?.status === 429) {
      showError(backendMsg || '请求过于频繁，请稍后再试');
    } 
    else if (err.response?.status === 409 && resData?.code === 4091 && !shouldForceLogin) {
      try {
        await ElMessageBox.confirm(
          backendMsg || '该账号已在其他设备登录，继续登录会使其他设备退出。是否继续？',
          '登录确认',
          {
            confirmButtonText: '继续登录',
            cancelButtonText: '取消',
            type: 'warning',
            autofocus: false,
            customClass: 'minimal-alert-box'
          }
        );
        isLoading.value = false;
        return handleLogin(true);
      } catch {
        return;
      }
    }
    else if (err.response?.status === 403) {
      clearAccessToken();
      showError(backendMsg || '账号状态异常，无法登录');
      loginForm.password = ''; 
    } 
    else if (err.response?.status === 401) {
      showError(backendMsg || '邮箱或密码错误', 'password');
      const match = backendMsg?.match(/还剩(\d+)次/);
      if (match && match[1]) {
        remainingAttempts.value = parseInt(match[1]);
      }
      loginForm.password = ''; 
    } 
    else if (err.response?.status === 400) {
      showError(backendMsg || '请求数据错误，请检查输入');
    } 
    else if (err.response?.status === 500) {
      showError('服务器繁忙，请稍后重试');
    } 
    else {
      showError('网络错误，请检查连接');
    }
  } finally {
    if (loginRequestId.value === currentRequestId) {
      isLoading.value = false;
    }
  }
};

onMounted(() => {
  if (route.query.expired === '1') {
    ElMessageBox.alert('登录已过期，请重新登录', '会话已失效', {
      confirmButtonText: '重新登录',
      type: 'warning',
      showClose: false,
      closeOnClickModal: false,
      closeOnPressEscape: false,
      autofocus: false,
      customClass: 'minimal-alert-box'
    });
  }

  if (isLoggedIn()) {
    const redirectPath = router.currentRoute.value.query.redirect as string || '/weather';
    router.push(redirectPath).catch(() => {});
  }
  
  localStorage.removeItem('last_login_email');
});

watch(
  () => router.currentRoute.value.query.email,
  (newEmail) => {
    if (newEmail && typeof newEmail === 'string' && !isLoading.value) {
      setTimeout(() => {
        loginForm.email = newEmail;
      }, 100);
    }
  },
  { immediate: true }
);

onUnmounted(() => {
  if (cancelSource) {
    cancelSource.cancel('组件卸载，取消请求');
  }
  loginForm.password = '';
});
</script>

<style scoped>
/* 1. 深度选择器优化 - 加载动画 */
:deep(.el-button.is-loading .el-loading-spinner) {
  margin-right: 5px;
  width: 14px;  /* 16px 的 85% */
  height: 14px;
}

:deep(.el-input__wrapper) {
  transition: all 0.2s ease-out !important;
  height: 100% !important;
}

:deep(.el-form-item.is-error .el-input__wrapper) {
  border-color: #F56C6C !important;
}

:deep(.el-input__wrapper input:-webkit-autofill),
:deep(.el-input__wrapper input:-webkit-autofill:hover),
:deep(.el-input__wrapper input:-webkit-autofill:focus),
:deep(.el-input__wrapper input:-webkit-autofill:active) {
  -webkit-box-shadow: 0 0 0 1000px white inset !important;
  -webkit-text-fill-color: #606266 !important;
  transition: background-color 5000s ease-in-out 0s;
}

:global(html.dark) :deep(.el-input__wrapper input:-webkit-autofill),
:global(html.dark) :deep(.el-input__wrapper input:-webkit-autofill:hover),
:global(html.dark) :deep(.el-input__wrapper input:-webkit-autofill:focus),
:global(html.dark) :deep(.el-input__wrapper input:-webkit-autofill:active),
:global(body.site-dark-mode) :deep(.el-input__wrapper input:-webkit-autofill),
:global(body.site-dark-mode) :deep(.el-input__wrapper input:-webkit-autofill:hover),
:global(body.site-dark-mode) :deep(.el-input__wrapper input:-webkit-autofill:focus),
:global(body.site-dark-mode) :deep(.el-input__wrapper input:-webkit-autofill:active) {
  color: #f8fafc !important;
  caret-color: #f8fafc !important;
  -webkit-text-fill-color: #f8fafc !important;
  -webkit-box-shadow: 0 0 0 1000px #111827 inset !important;
  box-shadow: 0 0 0 1000px #111827 inset !important;
  transition: background-color 5000s ease-in-out 0s;
}

/* --- 页面整体容器 --- */
.auth-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 17px; /* 20px 的 85% */
  background-color: #f0f2f5;
  position: relative;
  /* 【关键保留】你要求的隐藏侧边栏滚动条代码 */
  overflow: hidden; 
  box-sizing: border-box;
  border: none !important;
}

/* 背景光晕等比缩小 */
.bg-decoration {
  position: absolute;
  width: 425px; /* 500px 的 85% */
  height: 425px;
  border-radius: 50%;
  z-index: 0;
  filter: blur(85px);
  opacity: 0.3;
}
.top-left {
  top: -212px; /* 250px 的 85% */
  left: -212px;
  background: linear-gradient(135deg, #409EFF, #66B1CD);
}
.bottom-right {
  bottom: -212px;
  right: -212px;
  background: linear-gradient(135deg, #722ED1, #F5222D);
}

/* --- 核心登录卡片：整体 85% 缩放 --- */
.auth-card {
  width: 100%;
  max-width: 323px; /* 380px 的 85% */
  border-radius: 10px;
  box-shadow: 0 3px 14px rgba(0, 0, 0, 0.06);
  background-color: #fff;
  position: relative;
  z-index: 1;
  border: none !important;
  animation: fadeIn 0.3s ease-out forwards;
  margin-bottom: 34px; /* 40px 的 85% */
}

.auth-header {
  text-align: center;
  padding: 20px 0; /* 24px 的 85% */
  margin: 0;
  border: none !important;
}
.header-icon {
  font-size: 20px; /* 24px 的 85% */
  color: #409EFF;
  margin-bottom: 7px;
}
.auth-header h2 {
  color: #333;
  font-size: 17px; /* 20px 的 85% */
  font-weight: 500;
  margin: 0;
}

.auth-form {
  padding: 0 20px 20px; /* 24px 的 85% */
  border: none !important;
}

.form-item {
  margin-bottom: 6px;
  animation: fadeIn 0.3s ease-out forwards;
  opacity: 0;
  transform: translateY(5px);
  border: none !important;
}

:deep(.form-item:not(.form-actions) .el-form-item__content) {
  padding-bottom: 22px;
}

:deep(.form-item:not(.form-actions) .el-form-item__error) {
  top: auto;
  bottom: 2px;
  min-height: 16px;
  padding-top: 6px;
}

:deep(.form-item:nth-child(1)) { animation-delay: 0.05s; }
:deep(.form-item:nth-child(2)) { animation-delay: 0.1s; }
:deep(.form-item:nth-child(3)) { animation-delay: 0.15s; }

/* 按钮与输入框高度 */
.full-width-input {
  width: 100% !important;
  height: 38px; /* 44px 的 85% */
  border-radius: 7px !important;
}

:deep(.el-input__inner) {
  font-size: 12px !important;
}
:deep(.el-input__inner::placeholder) {
  font-size: 12px !important;
}

:deep(.el-input__suffix .el-icon) {
  color: #999;
  font-size: 14px;
  cursor: pointer;
  transition: color 0.2s;
}

:deep(.el-input__suffix .el-icon:hover) {
  color: #409EFF;
}

.full-width-btn {
  width: 100%;
  height: 38px; /* 44px 的 85% */
  font-size: 14px; /* 16px 的 85% */
  border-radius: 7px;
  transition: all 0.15s ease;
}

.form-actions {
  display: flex;
  flex-direction: column;
  gap: 14px; /* 16px 的 85% */
  margin-top: 7px;
  border: none !important;
}

.register-link {
  color: #666;
  font-size: 12px; /* 14px 的 85% */
  text-align: center;
  border: none !important;
}

.interactive-link {
  color: #409EFF;
  text-decoration: none;
  position: relative;
  padding: 2px 0;
}

.interactive-link::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  width: 0;
  height: 2px;
  background-color: #409EFF;
  transition: width 0.15s ease;
  border-radius: 1px;
}

.interactive-link:hover::after {
  width: 100%;
}

/* 底部备案信息同步缩小 */
.beian-info {
  position: absolute;
  bottom: 17px; /* 20px 的 85% */
  left: 0;
  right: 0;
  text-align: center;
  font-size: 12px; /* 14px 的 85% */
  color: #6b7280;
  z-index: 1;
  padding: 0 9px;
  margin: 0 !important;
  border: none !important;
  outline: none !important;
  box-shadow: none !important;
}

.beian-info a {
  color: #6b7280;
  text-decoration: none;
  transition: color 0.2s ease;
}

.beian-info a:hover {
  color: #409EFF;
  text-decoration: underline;
}

:deep(.el-card),
:deep(.el-form),
:deep(.el-form-item),
:deep(.el-input),
:deep(.el-button),
:deep(.el-icon) {
  border-top: none !important;
  box-shadow: none !important;
}

/* 移动端极限情况适配 */
@media (max-width: 480px) {
  .auth-card {
    max-width: 100%;
    margin: 0 10px 25px;
  }
  .full-width-input, .full-width-btn {
    height: 36px;
  }
  .beian-info {
    font-size: 11px;
    bottom: 12px;
  }
}

@keyframes fadeIn {
  from { 
    opacity: 0; 
    transform: translateY(5px);
  }
  to { 
    opacity: 1; 
    transform: translateY(0);
  }
}
</style>
