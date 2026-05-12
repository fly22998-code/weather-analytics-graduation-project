<template>
  <div class="auth-container">
    <div class="bg-decoration top-left"></div>
    <div class="bg-decoration bottom-right"></div>
    
    <el-card class="auth-card">
      <div slot="header" class="auth-header">
        <h2>用户注册</h2>
      </div>
      
      <el-form 
        :model="registerForm" 
        :rules="registerRules as any"
        ref="registerFormRef"  
        class="auth-form"
        label-width="0" 
        @submit.prevent
      >
        <el-form-item 
          prop="email" 
          class="form-item"
          :error="emailError"
        >
          <el-input 
            v-model="registerForm.email" 
            type="email" 
            placeholder="请输入邮箱"
            class="full-width-input"
            :disabled="isEmailRegistered || isDisabledEmail" 
            @blur="handleEmailBlur"
            @input="handleEmailInput"
            @change="handleEmailChange"
            @clear="handleEmailClear"
            clearable
            ref="emailInputRef"
          >
            <template #suffix>
              <el-icon v-if="emailStatus === EmailStatus.VALIDATING" class="is-loading status-icon">
                <Loading />
              </el-icon>
              
              <el-icon 
                v-else-if="(emailStatus === EmailStatus.VALID || emailStatus === EmailStatus.UNREGISTERED) && hasCheckedDuplicate" 
                class="status-icon success-icon"
              >
                <CircleCheckFilled />
              </el-icon>
              
              <el-icon 
                v-else-if="(emailStatus === EmailStatus.INVALID || emailStatus === EmailStatus.REGISTERED) && hasCheckedDuplicate" 
                class="status-icon error-icon"
              >
                <CircleCloseFilled />
              </el-icon>
            </template>
          </el-input>
        </el-form-item>
        
        <el-form-item 
          prop="code" 
          class="form-item" 
          ref="codeFormItemRef"
        >
          <el-row :gutter="12">
            <el-col :span="14">
              <el-input 
                v-model="registerForm.code" 
                placeholder="请输入6位验证码"
                class="full-width-input"
                :disabled="isDisabledCodeInput || state.isEmailRegistered"  
                maxlength="6"
                @input="handleCodeInput"
                @change="handleCodeChange"
                ref="codeInputRef"
              >
              </el-input>
            </el-col>
            <el-col :span="10">
              <el-button 
                type="default" 
                class="full-width-btn send-code-btn"
                @click="handleSendCode"
                :loading="state.isSendingCode"  
                :disabled="isDisabledSendCode || !canSendCode || state.isEmailRegistered"  
              >
                {{ state.isCounting ? `${state.count}秒后重发` : '发送验证码' }}
              </el-button>
            </el-col>
          </el-row>
        </el-form-item>
        
        <el-form-item 
          prop="password" 
          class="form-item" 
          :error="state.serverErrors.password"
        >
          <el-input 
            v-model="registerForm.password" 
            :type="state.showPwd ? 'text' : 'password'" 
            placeholder="至少8位，包含至少一个字母和数字"
            class="full-width-input"
            :disabled="isDisabledAction || state.isEmailRegistered"  
            @input="handlePasswordInput"
            autocomplete="new-password"
          >
            <template #suffix>
              <el-icon class="pwd-toggle" @click="state.showPwd = !state.showPwd">
                <View v-if="state.showPwd" />
                <Hide v-else />
              </el-icon>
            </template>
          </el-input>
        </el-form-item>
        
        <el-form-item 
          prop="confirmPassword" 
          class="form-item" 
        >
          <el-input 
            v-model="registerForm.confirmPassword" 
            :type="state.showConfirmPwd ? 'text' : 'password'" 
            placeholder="请再次输入密码"
            class="full-width-input"
            :disabled="isDisabledAction || state.isEmailRegistered"  
            @input="handleConfirmInput"
          >
            <template #suffix>
              <el-icon class="pwd-toggle" @click="state.showConfirmPwd = !state.showConfirmPwd">
                <View v-if="state.showConfirmPwd" />
                <Hide v-else />
              </el-icon>
            </template>
          </el-input>
        </el-form-item>
        
        <el-form-item class="form-actions">
          <el-button 
            type="primary" 
            class="full-width-btn register-btn"
            @click="handleRegister"
            :loading="state.isLoading"
            :disabled="isDisabledAction || state.isEmailRegistered"  
          >
            完成注册
          </el-button>
          <div class="login-link">
            已有账号？<router-link to="/userlogin" class="interactive-link">立即登录</router-link>
          </div>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
// @ts-nocheck
import { ref, reactive, computed, onUnmounted, watch, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import axios, { AxiosError, CancelTokenSource, InternalAxiosRequestConfig } from 'axios';
import type { AxiosResponse, AxiosRequestHeaders } from 'axios';
import { ElMessage, ElMessageBox, ElForm, ElFormItem, ElInput, ElButton, ElCard, ElRow, ElCol, ElIcon } from 'element-plus';
import type { FormInstance } from 'element-plus';
// 引入图标
import { 
  CircleCheckFilled, 
  CircleCloseFilled, 
  Loading,
  View, 
  Hide 
} from '@element-plus/icons-vue';

import { BASE_URL } from '@/store/config';
import { generateSignedHeaders } from '@/utils/signature';

// ========== 枚举定义 ==========
const EmailStatus = {
  INIT: 'init',
  VALIDATING: 'validating',
  VALID: 'valid',
  INVALID: 'invalid',
  REGISTERED: 'registered',
  UNREGISTERED: 'unregistered'
} as const;

// ========== 响应式状态 ==========
const isEmailRegistered = ref(false);
const emailError = ref('');
const emailStatus = ref(EmailStatus.INIT);
const hasCheckedDuplicate = ref(false);
let currentRequestId = '';

const registerForm = ref({
  email: '',
  code: '',
  password: '',
  confirmPassword: '',
  verify_token: ''
});

const state = reactive({
  lastCheckedEmail: '',
  lastCheckedResult: null,
  lastCheckTime: 0,
  checkCount: 0,
  isEmailRegistered: false,
  isSendingCode: false,
  isCounting: false,
  count: 60,
  isLoading: false,
  showPwd: false,
  showConfirmPwd: false,
  isCheckingEmail: false,
  emailCheckRequestId: null,
  countdownTimer: null,
  emailCheckCancelSource: null,
  serverErrors: {
    email: '',
    code: '',
    password: ''
  },
  debounceTimer: null
});

// ========== 常量定义 ==========
const REGISTERED_MESSAGE = '该邮箱已注册，请直接登录';
const UNREGISTERED_MESSAGE = '';
// 正则表达式
const emailReg = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
const tempMailRegex = /tempmail|disposable|mailinator|10minutemail|guerrillamail|fakeinbox|throwaway/;
const codeRegex = /^\d+$/;
const passwordRegex = /^(?=.*[A-Za-z])(?=.*\d).+$/;

// ========== 工具函数 ==========
const getRequestKey = (config) => {
  let dataStr = '';
  if (config.method?.toUpperCase() === 'POST' && config.data) {
    const sortedData = Object.keys(config.data).sort().reduce((obj, key) => {
      obj[key] = config.data[key];
      return obj;
    }, {});
    dataStr = JSON.stringify(sortedData);
  } else if (config.params) {
    dataStr = JSON.stringify(config.params);
  }
  return `${config.method}-${config.url}-${dataStr}`;
};

// ========== 配置初始化 ==========
const router = useRouter();
const isUnmounted = ref(false);
const registerFormRef = ref(null);
const emailInputRef = ref(null);
const codeFormItemRef = ref(null);
const codeInputRef = ref(null);

// ========== Axios实例配置 ==========
const axiosInstance = axios.create({
  baseURL: BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
});

// 请求拦截器
const pendingRequests = new Map();
axiosInstance.interceptors.request.use((config) => {
  const requestKey = getRequestKey(config);
  
  if (pendingRequests.has(requestKey)) {
    pendingRequests.get(requestKey)('重复请求已取消');
    pendingRequests.delete(requestKey);
  }
  
  const source = axios.CancelToken.source();
  config.cancelToken = source.token;
  pendingRequests.set(requestKey, source.cancel);
  
  if (!config.headers) {
    config.headers = new axios.AxiosHeaders();
  }
  
  return config;
}, (error) => Promise.reject(error));

// 响应拦截器
axiosInstance.interceptors.response.use(
  (response) => {
    const requestKey = getRequestKey(response.config);
    pendingRequests.delete(requestKey);
    return response;
  },
  (error) => {
    if (error.config) {
      const requestKey = getRequestKey(error.config);
      pendingRequests.delete(requestKey);
    }
    return Promise.reject(error);
  }
);

// ========== 计算属性 ==========
const isDisabledEmail = computed(() => {
  return state.isSendingCode || state.isLoading || state.isCounting;
});

const isDisabledCodeInput = computed(() => {
  return state.isSendingCode || state.isLoading || state.isEmailRegistered;
});

const isEmailValid = computed(() => {
  const email = registerForm.value.email.trim();
  if (!email || !emailReg.test(email)) return false;
  
  const [, domain] = email.split('@');
  if (!domain || !domain.includes('.')) return false;
  
  if (tempMailRegex.test(domain)) return false;
  
  return true;
});

const canSendCode = computed(() => {
  return isEmailValid.value && 
         !state.isEmailRegistered && 
         !state.serverErrors.email && 
         (emailStatus.value === EmailStatus.VALID || 
          emailStatus.value === EmailStatus.UNREGISTERED);
});

const isDisabledSendCode = computed(() => {
  return state.isSendingCode || state.isLoading || state.isCounting;
});

const isDisabledAction = computed(() => {
  return state.isLoading || state.isEmailRegistered;
});

// ========== 表单验证规则 ==========
const registerRules = reactive({
  email: [
    { required: true, message: '请输入邮箱', trigger: ['blur', 'input'] },
    { 
      validator: (rule, value, callback) => {
        const trimmedValue = value.trim();
        hasCheckedDuplicate.value = false;

        if (!trimmedValue) {
          emailError.value = '请输入邮箱';
          emailStatus.value = EmailStatus.INIT;
          return callback(new Error(emailError.value));
        }

        if (!emailReg.test(trimmedValue)) {
          emailError.value = '请输入正确的邮箱格式（如xxx@qq.com）';
          emailStatus.value = EmailStatus.INIT;
          return callback(new Error(emailError.value));
        }

        const [, domain] = trimmedValue.split('@');
        if (!domain || !domain.includes('.')) {
          emailError.value = '邮箱域名格式不正确';
          emailStatus.value = EmailStatus.INIT;
          return callback(new Error(emailError.value));
        }

        if (tempMailRegex.test(domain)) {
          emailError.value = '不支持临时邮箱注册，请使用常用邮箱';
          emailStatus.value = EmailStatus.INIT;
          return callback(new Error(emailError.value));
        }

        emailError.value = '';
        emailStatus.value = EmailStatus.VALID;
        callback();
      },
      trigger: ['input', 'blur']
    },
    { 
      validator: async (rule, value, callback) => {
        try {
          const trimmedValue = value.trim();
          if (!trimmedValue || !isEmailValid.value) {
            return callback();
          }

          state.checkCount++;
          // console.log(`第${state.checkCount}次验证邮箱: ${trimmedValue}`);

          const now = Date.now();
          const isSameEmail = trimmedValue === state.lastCheckedEmail;
          const isRecentCheck = now - state.lastCheckTime < 30000;

          if (isSameEmail && isRecentCheck && state.lastCheckedResult !== null) {
            state.isEmailRegistered = state.lastCheckedResult;
            
            if (state.lastCheckedResult) {
              emailError.value = REGISTERED_MESSAGE;
              emailStatus.value = EmailStatus.REGISTERED;
              callback(new Error(emailError.value));
            } else {
              emailError.value = UNREGISTERED_MESSAGE;
              emailStatus.value = EmailStatus.UNREGISTERED;
              callback();
            }
            hasCheckedDuplicate.value = true;
            return;
          }

          emailStatus.value = EmailStatus.VALIDATING;
          hasCheckedDuplicate.value = true;
          state.isCheckingEmail = true;
          currentRequestId = Date.now();
          state.emailCheckRequestId = currentRequestId;
          
          if (state.emailCheckCancelSource) {
            state.emailCheckCancelSource.cancel('新请求已发起');
          }
          state.emailCheckCancelSource = axios.CancelToken.source();

          await new Promise(resolve => setTimeout(resolve, 300));

          if (state.emailCheckRequestId !== currentRequestId || isUnmounted.value) {
            return callback();
          }

          const res = await axiosInstance.get(`${BASE_URL}/weather/user/check-email/`, {
            params: { email: trimmedValue },
            cancelToken: state.emailCheckCancelSource.token
          });

          if (state.emailCheckRequestId !== currentRequestId || isUnmounted.value) {
            return callback();
          }

          state.lastCheckedEmail = trimmedValue;
          state.lastCheckTime = now;
          const { code, message } = res.data;
          
          switch (code) {
            case 200:
              state.lastCheckedResult = false;
              state.isEmailRegistered = false;
              emailError.value = UNREGISTERED_MESSAGE;
              emailStatus.value = EmailStatus.UNREGISTERED;
              callback();
              break;
            case 1001:
              state.lastCheckedResult = true;
              state.isEmailRegistered = true;
              emailError.value = REGISTERED_MESSAGE;
              emailStatus.value = EmailStatus.REGISTERED;
              callback(new Error(emailError.value));
              break;
            default:
              state.lastCheckedResult = null;
              emailError.value = message || '邮箱校验失败，请稍后重试';
              emailStatus.value = EmailStatus.INVALID;
              callback(new Error(emailError.value));
          }
        } catch (error) {
          if (axios.isCancel(error)) {
            return callback();
          }
          
          if (isUnmounted.value) {
            return callback();
          }
          
          const isNetworkError = !error.response;
          emailError.value = isNetworkError 
            ? '网络连接异常，请检查网络' 
            : error.response?.data?.['message'] || '邮箱验证失败，请重试';
            
          emailStatus.value = EmailStatus.INVALID;
          hasCheckedDuplicate.value = true;
          callback(new Error(emailError.value));
        } finally {
          if (!isUnmounted.value && state.emailCheckRequestId === currentRequestId) {
            state.isCheckingEmail = false;
          }
        }
      },
      trigger: ['blur', 'change']
    }
  ],
  code: [
    { required: true, message: '请输入验证码', trigger: ['blur', 'change'] },
    { min: 6, max: 6, message: '验证码必须为6位', trigger: ['blur', 'change'] },
    { pattern: codeRegex, message: '验证码只能是数字', trigger: ['blur', 'change'] }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: ['blur', 'change'] },
    { min: 8, message: '密码长度至少8位', trigger: ['blur', 'change'] },
    { 
      pattern: passwordRegex, 
      message: '密码必须包含至少一个字母和一个数字', 
      trigger: ['blur', 'change'] 
    }
  ],
  confirmPassword: [
    { required: true, message: '请确认密码', trigger: ['blur', 'change'] },
    { 
      validator: (rule, value, callback) => {
        if (value !== registerForm.value.password) {
          callback(new Error('两次密码输入不一致'));
        } else {
          callback();
        }
      },
      trigger: ['blur', 'change']
    }
  ]
});

// ========== 事件处理函数 ==========
const handleEmailInput = () => {
  const currentEmail = registerForm.value.email.trim();
  hasCheckedDuplicate.value = false;
  emailStatus.value = EmailStatus.INIT;
  
  if (currentEmail !== state.lastCheckedEmail) {
    state.isEmailRegistered = false;
    state.lastCheckedResult = null;
    state.checkCount = 0;
  }

  if (state.debounceTimer) {
    clearTimeout(state.debounceTimer);
  }

  if (!currentEmail) {
    resetEmailState();
    return;
  }

  if (!isEmailValid.value) {
    state.debounceTimer = setTimeout(() => {
      if (isUnmounted.value) return;
      registerFormRef.value?.validateField('email').catch(() => {});
    }, 300);
  } else {
    emailError.value = '';
    emailStatus.value = EmailStatus.VALID;
  }
};

const handleEmailClear = () => {
  resetEmailState();
};

const resetEmailState = () => {
  if (isUnmounted.value) return;
  
  if (state.debounceTimer) {
    clearTimeout(state.debounceTimer);
  }
  
  state.lastCheckedEmail = '';
  state.lastCheckedResult = null;
  state.lastCheckTime = 0;
  state.isEmailRegistered = false;
  state.serverErrors.email = '';
  emailError.value = '';
  emailStatus.value = EmailStatus.INIT;
  hasCheckedDuplicate.value = false;
  state.checkCount = 0;
  
  if (registerFormRef.value) {
    registerFormRef.value.clearValidate(['email']);
  }
};

const handleEmailChange = () => {
  const currentEmail = registerForm.value.email.trim();
  hasCheckedDuplicate.value = false;
  
  if (currentEmail) {
    registerFormRef.value?.validateField('email').then(() => {
      if (!state.isEmailRegistered) {
        emailError.value = '';
        emailStatus.value = EmailStatus.VALID;
      }
    }).catch(() => {});
  }
};

const handleEmailBlur = () => {
  const currentEmail = registerForm.value.email.trim();
  if (!currentEmail) {
    emailError.value = '请输入邮箱';
    emailStatus.value = EmailStatus.INIT;
    return;
  }

  registerFormRef.value?.validateField('email').then(() => {
    if (emailStatus.value === EmailStatus.UNREGISTERED) {
      // console.log('邮箱未注册，验证通过');
    }
  }).catch(err => {
    // console.log('验证失败:', err);
  });
};

const handleCodeInput = (value) => {
  if (isUnmounted.value) return;
  if (state.serverErrors.code) {
    state.serverErrors.code = '';
    if (codeFormItemRef.value) {
      codeFormItemRef.value.validateState = '';
      codeFormItemRef.value.validateMessage = '';
    }
  }
  registerForm.value.code = value.replace(/[^0-9]/g, '').slice(0, 6);
};

const handleCodeChange = () => {
  if (registerForm.value.code && registerFormRef.value) {
    registerFormRef.value.validateField('code').catch(() => {});
  }
};

const handlePasswordInput = () => {
  if (state.serverErrors.password) {
    state.serverErrors.password = '';
    registerFormRef.value?.clearValidate(['password']);
  }
};

const handleConfirmInput = () => {
  registerFormRef.value?.validateField('confirmPassword').catch(() => {});
};

const handleSendCode = async () => {
  if (state.isSendingCode || state.isCounting || !canSendCode.value) {
    return;
  }
  
  state.isSendingCode = true;
  const email = registerForm.value.email.trim();
  
  try {
    const res = await axiosInstance.post(`${BASE_URL}/weather/user/send-register-code/`, {
      email: email
    }, {
      headers: {
        'Content-Type': 'application/json',
        ...generateSignedHeaders({ email })
      }
    });

    const { code, message } = res.data;
    
    if (code === 200) {
      ElMessage.success('验证码已发送，请查收邮箱');
      startCountdown();
      setTimeout(() => {
        codeInputRef.value?.focus();
      }, 300);
    } else {
      ElMessage.error(message || '验证码发送失败');
    }
  } catch (error) {
    console.error('发送验证码错误:', error);
    ElMessage.error(error.response?.data?.message || '发送失败，请重试');
  } finally {
    state.isSendingCode = false;
  }
};

const startCountdown = () => {
  if (state.countdownTimer) {
    clearInterval(state.countdownTimer);
  }
  
  state.isCounting = true;
  state.count = 60;
  
  state.countdownTimer = setInterval(() => {
    if (isUnmounted.value) {
      clearInterval(state.countdownTimer);
      return;
    }
    
    state.count--;
    
    if (state.count <= 0) {
      clearInterval(state.countdownTimer);
      state.isCounting = false;
      state.count = 60;
      registerForm.value.code = '';
    }
  }, 1000);
};

const handleRegister = async () => {
  if (!registerFormRef.value || isDisabledAction.value) return;

  state.serverErrors = { email: '', code: '', password: '' };
  if (codeFormItemRef.value) {
    codeFormItemRef.value.validateState = '';
    codeFormItemRef.value.validateMessage = '';
  }

  try {
    await registerFormRef.value.validate();
  } catch (error) {
    ElMessage.warning('请完善登录信息');
    return;
  }

  state.isLoading = true;

  try {
    const verifyRes = await axiosInstance.post(`${BASE_URL}/weather/user/verify-code/`, {
      email: registerForm.value.email,
      code: registerForm.value.code
    });

    if (verifyRes.data.code !== 200) {
      ElMessage.error(verifyRes.data.message || '验证码错误');
      codeInputRef.value?.focus();
      return;
    }

    const { verify_token } = verifyRes.data.data || {};
    if (!verify_token) {
      ElMessage.error('验证失败，请重新获取验证码');
      return;
    }

    const regRes = await axiosInstance.post(`${BASE_URL}/weather/user/register/`, {
      email: registerForm.value.email,
      password: registerForm.value.password,
      verify_token: verify_token
    });

    if (regRes.data.code === 200) {
      ElMessage.success('注册成功，即将跳转登录页');
      setTimeout(() => {
        router.push({ path: '/userlogin', query: { email: registerForm.value.email } });
      }, 800);
    } else {
      ElMessage.error(regRes.data.message || '注册失败');
    }
  } catch (error) {
    console.error('注册错误:', error);
    ElMessage.error(error.response?.data?.message || '网络错误，请重试');
  } finally {
    state.isLoading = false;
  }
};

// ========== 监听逻辑 ==========
watch(() => emailStatus.value, (newStatus) => {
  const inputEl = emailInputRef.value?.$el?.querySelector('.el-input__wrapper');
  if (!inputEl) return;
  
  // 保留边框颜色逻辑
  inputEl.classList.remove('email-valid', 'email-invalid', 'email-checking', 'email-registered', 'email-unregistered');
  
  if (hasCheckedDuplicate.value) {
    switch (newStatus) {
      case EmailStatus.VALIDATING:
        inputEl.classList.add('email-checking');
        break;
      case EmailStatus.VALID:
      case EmailStatus.UNREGISTERED:
        inputEl.classList.add('email-valid');
        break;
      case EmailStatus.INVALID:
        inputEl.classList.add('email-invalid');
        break;
      case EmailStatus.REGISTERED:
        inputEl.classList.add('email-registered');
        break;
    }
  }
}, { flush: 'post' });

watch(
  () => registerForm.value.email,
  (newEmail, oldEmail) => {
    if (newEmail.trim() !== oldEmail.trim()) {
      state.isEmailRegistered = false;
      state.lastCheckedResult = null;
    }
  }
);

watch(() => state.isCounting, (newVal) => {
  try {
    if (!emailInputRef.value) return;
    const input = emailInputRef.value.$el?.querySelector('input');
    if (input) input.disabled = newVal || state.isEmailRegistered;
  } catch (err) {
    console.error('倒计时状态监听错误:', err);
  }
});

watch(() => state.isEmailRegistered, (isRegistered) => {
  try {
    if (isRegistered) {
      emailError.value = REGISTERED_MESSAGE;
      emailStatus.value = EmailStatus.REGISTERED;
      hasCheckedDuplicate.value = true;
      registerForm.value.code = '';
      registerForm.value.password = '';
      registerForm.value.confirmPassword = '';
      registerForm.value.verify_token = '';
      registerFormRef.value?.clearValidate(['code', 'password', 'confirmPassword']);
    }
  } catch (err) {
    console.error('邮箱注册状态监听错误:', err);
  }
});

// ========== 生命周期 ==========
onMounted(() => {
  setTimeout(() => {
    emailInputRef.value?.focus();
  }, 300);
});

onUnmounted(() => {
  isUnmounted.value = true;
  
  if (state.countdownTimer) clearInterval(state.countdownTimer);
  if (state.debounceTimer) clearTimeout(state.debounceTimer);
  
  pendingRequests.forEach(cancel => cancel('组件已卸载'));
  pendingRequests.clear();
  
  state.emailCheckCancelSource?.cancel('Component unmounted');
});
</script>

<style scoped>
/* 错误提示样式 (85% 缩放) */
:deep(.el-form-item__error) {
  display: block !important;
  padding-top: 3px; 
  color: #F56C6C !important;
  font-size: 10px !important; 
}

/* 邮箱状态样式 - 边框颜色 */
:deep(.email-checking .el-input__wrapper) { border-color: #409EFF !important; }
:deep(.email-valid .el-input__wrapper) { border-color: #67C23A !important; }
:deep(.email-invalid .el-input__wrapper) { border-color: #F56C6C !important; }
:deep(.email-registered .el-input__wrapper) { border-color: #F56C6C !important; }
:deep(.email-unregistered .el-input__wrapper) { border-color: #67C23A !important; }

/* 状态图标样式 (85% 缩放) */
.status-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  margin-left: 4px; 
  font-size: 15px; 
}
.success-icon { color: #67C23A; }
.error-icon { color: #F56C6C; }

/* 密码显示/隐藏按钮样式 (85% 缩放) */
.pwd-toggle {
  cursor: pointer;
  color: #909399; 
  font-size: 20px; 
  padding: 0 3px; 
  display: flex;
  align-items: center;
  height: 100%; 
}
.pwd-toggle:hover { color: #409EFF; }

/* 按钮加载样式 (85% 缩放) */
:deep(.el-button.is-loading) { pointer-events: none; }
:deep(.el-button.is-loading .el-loading-spinner) {
  display: inline-block !important;
  margin-right: 5px; 
  width: 14px; 
  height: 14px;
}
:deep(.el-button.is-loading .el-button__text) { display: inline-block !important; }

:deep(.el-input__wrapper) {
  transition: all 0.2s ease-out !important;
  height: 100% !important;
}

/* ⬇️ 新增：强制缩小输入框内部文字和占位符 (14px -> 12px) ⬇️ */
:deep(.el-input__inner) {
  font-size: 12px !important;
}
:deep(.el-input__inner::placeholder) {
  font-size: 12px !important;
}

/* 强制覆盖浏览器自动填充的蓝色背景 */
:deep(.el-input__wrapper input:-webkit-autofill),
:deep(.el-input__wrapper input:-webkit-autofill:hover),
:deep(.el-input__wrapper input:-webkit-autofill:focus),
:deep(.el-input__wrapper input:-webkit-autofill:active) {
  -webkit-box-shadow: 0 0 0 1000px white inset !important;
  -webkit-text-fill-color: #606266 !important;
  transition: background-color 5000s ease-in-out 0s;
}

:deep(.el-form-item.is-error .el-input__wrapper) {
  border-color: #F56C6C !important;
}

/* 布局样式 (85% 缩放) */
.auth-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 17px; 
  background-color: #f0f2f5;
  position: relative;
  overflow: hidden;
}

/* 背景光晕等比缩小 */
.bg-decoration {
  position: absolute;
  width: 425px; 
  height: 425px;
  border-radius: 50%;
  z-index: 0;
  filter: blur(85px); 
  opacity: 0.3;
}
.top-left { top: -212px; left: -212px; background: linear-gradient(135deg, #409EFF, #66B1CD); }
.bottom-right { bottom: -212px; right: -212px; background: linear-gradient(135deg, #722ED1, #ff000d); }

/* 卡片主体 (85% 缩放) */
.auth-card {
  width: 100%;
  max-width: 323px; 
  border-radius: 10px; 
  box-shadow: 0 3px 14px rgba(0, 0, 0, 0.06); 
  background-color: #fff;
  position: relative;
  z-index: 1;
  border: none;
  animation: fadeIn 0.3s ease-out forwards;
}

.auth-header { text-align: center; padding: 20px 0; margin: 0; } 
.auth-header h2 { color: #333; font-size: 17px; font-weight: 500; margin: 0; } 
.auth-form { padding: 0 20px 20px; } 

.form-item {
  margin-bottom: 14px; 
  animation: fadeIn 0.3s ease-out forwards;
  opacity: 0;
}
:deep(.form-item:nth-child(1)) { animation-delay: 0.05s; }
:deep(.form-item:nth-child(2)) { animation-delay: 0.1s; }
:deep(.form-item:nth-child(3)) { animation-delay: 0.15s; }
:deep(.form-item:nth-child(4)) { animation-delay: 0.2s; }

/* 按钮与输入框高度 (85% 缩放) */
.full-width-input { width: 100% !important; height: 38px; border-radius: 7px !important; } 

/* ⬇️ 修改：连带“发送验证码”按钮里的文字一起缩小 ⬇️ */
:deep(.el-col:nth-child(2) .el-button) { 
  height: 38px !important; 
  border-radius: 7px !important; 
  font-size: 12px !important; 
}

.full-width-btn { width: 100%; height: 38px; font-size: 14px; border-radius: 7px; }

.form-actions { display: flex; flex-direction: column; gap: 14px; margin-top: 7px; } 
.login-link { color: #666; font-size: 12px; text-align: center; } 
.interactive-link { color: #409EFF; text-decoration: none; position: relative; padding: 2px 0; }
.interactive-link::after {
  content: ''; position: absolute; bottom: 0; left: 0; width: 0; height: 2px;
  background-color: #409EFF; transition: width 0.15s ease;
}
.interactive-link:hover::after { width: 100%; }

@media (max-width: 480px) {
  .auth-card { max-width: 100%; margin: 0 10px; } 
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(4px); } 
  to { opacity: 1; transform: translateY(0); }
}
</style>
