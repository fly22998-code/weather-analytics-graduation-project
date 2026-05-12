<template>
  <div class="auth-container">
    <div class="bg-decoration top-left"></div>
    <div class="bg-decoration bottom-right"></div>

    <el-card class="auth-card">
      <div slot="header" class="auth-header">
        <h2>{{ currentStep === 1 ? '找回密码' : '设置新密码' }}</h2>
      </div>

      <el-form
        :model="form"
        :rules="currentStep === 1 ? emailRules : pwdRules"
        ref="formRef"
        class="auth-form"
        label-width="0"
      >
        <div v-if="currentStep === 1" class="verify-step">
          <div class="input-item-gap">
            <el-form-item prop="email" class="form-item">
              <el-input
                v-model="form.email"
                type="email"
                placeholder="请输入注册时的邮箱"
                class="full-width-input"
                :disabled="isSendingCode || isCounting"
              />
            </el-form-item>
          </div>

          <div class="input-item-gap">
            <el-form-item prop="code" class="form-item">
              <el-row :gutter="12">
                <el-col :span="14">
                  <el-input
                    v-model="form.code"
                    placeholder="请输入6位验证码"
                    class="full-width-input"
                    :disabled="isSendingCode"
                    maxlength="6"
                    @input="form.code = form.code.replace(/[^0-9]/g, '')"
                  />
                </el-col>
                <el-col :span="10">
                  <el-button
                    type="default"
                    class="full-width-btn send-code-btn"
                    @click="sendCode"
                    :loading="isSendingCode"
                  >
                    {{ isCounting ? `${count}秒后重发` : '发送验证码' }}
                  </el-button>
                </el-col>
              </el-row>
            </el-form-item>
          </div>

          <el-form-item class="form-actions">
            <el-button
              type="primary"
              class="full-width-btn"
              @click="goToNextStep"
              :loading="isVerifying"
            >
              <span v-if="!isVerifying">验证并下一步</span>
              <span v-else>验证中...</span>
            </el-button>
            <div class="login-link">
              记得密码了？<router-link to="/userlogin" class="interactive-link">立即登录</router-link>
            </div>
          </el-form-item>
        </div>

        <div v-else class="reset-step">
          <div class="input-item-gap">
            <el-form-item prop="newPwd" class="form-item">
              <el-input
                v-model="form.newPwd"
                :type="showNewPwd ? 'text' : 'password'"
                placeholder="请输入新密码（至少8位，含字母和数字）"
                class="full-width-input"
                @blur="checkPasswordMatch"
              >
                <template #suffix>
                  <el-icon
                    @click="showNewPwd = !showNewPwd"
                    style="cursor: pointer;"
                    :disabled="false"
                  >
                    <Eye v-if="!showNewPwd" />
                    <EyeClosed v-if="showNewPwd" />
                  </el-icon>
                </template>
              </el-input>
            </el-form-item>
          </div>

          <div class="input-item-gap">
            <el-form-item prop="confirmNewPwd" class="form-item">
              <el-input
                v-model="form.confirmNewPwd"
                :type="showConfirmNewPwd ? 'text' : 'password'"
                placeholder="请再次输入新密码"
                class="full-width-input"
                @blur="checkPasswordMatch"
              >
                <template #suffix>
                  <el-icon
                    @click="showConfirmNewPwd = !showConfirmNewPwd"
                    style="cursor: pointer;"
                    :disabled="false"
                  >
                    <Eye v-if="!showConfirmNewPwd" />
                    <EyeClosed v-if="showConfirmNewPwd" />
                  </el-icon>
                </template>
              </el-input>
            </el-form-item>
          </div>

          <el-form-item class="form-actions">
            <el-button
              type="primary"
              class="full-width-btn"
              @click="resetPassword"
              :loading="isResetting"
            >
              <span v-if="!isResetting">确认重置密码</span>
              <span v-else>重置中...</span>
            </el-button>
            <div class="login-link">
              <router-link to="/userlogin" class="interactive-link">返回登录</router-link>
            </div>
          </el-form-item>
        </div>
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
import { ref, reactive, onMounted, onUnmounted } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import axios from 'axios';
import { BASE_URL } from '@/store/config';
import { generateSignedHeaders } from '@/utils/signature';

const currentStep = ref(1);

const form = reactive({
  email: '',
  code: '',
  newPwd: '',
  confirmNewPwd: '',
  verify_token: ''
});

const formRef = ref<InstanceType<typeof import('element-plus').ElForm> | null>(null);
const isSendingCode = ref(false);
const isCounting = ref(false);
const count = ref(60);
const isVerifying = ref(false);
const isResetting = ref(false);
const showNewPwd = ref(false);
const showConfirmNewPwd = ref(false);
let countdownTimer: NodeJS.Timeout | null = null;
let sessionTimer: NodeJS.Timeout | null = null;

const router = useRouter();
const route = useRoute();

const emailRules = reactive({
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: ['blur', 'change'] }
  ],
  code: [
    { required: true, message: '请输入6位验证码', trigger: 'blur' },
    { min: 6, max: 6, message: '验证码必须为6位', trigger: 'blur' },
    { pattern: /^\d{6}$/, message: '验证码仅支持数字', trigger: 'blur' }
  ]
});

const pwdRules = reactive({
  newPwd: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 8, message: '密码长度至少8位', trigger: 'blur' },
    { pattern: /^(?=.*[A-Za-z])(?=.*\d).+$/, message: '密码必须包含字母和数字', trigger: 'blur' }
  ],
  confirmNewPwd: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    { validator: (r: any, v: string, c: any) => v === form.newPwd ? c() : c(new Error('两次密码不一致')), trigger: 'blur' }
  ]
});

onMounted(() => {
  const isRefresh = checkIfPageRefresh();

  if (isRefresh) {
    restoreStateOnRefresh();
  } else {
    const savedState = localStorage.getItem('passwordResetState');
    if (savedState) {
      try {
        const { expireTime } = JSON.parse(savedState);
        if (expireTime && Date.now() >= expireTime) {
          resetToFirstStep();
          import('element-plus').then((el) => {
            el.ElMessage.info('验证已过期，请重新验证');
          });
        }
      } catch (error) {
        resetToFirstStep();
      }
    } else {
      resetToFirstStep();
    }
  }

  const removeRouteGuard = router.beforeEach((to, from) => {
    if (from.path === route.path && to.path !== route.path) {
      clearResetState();
      clearSessionTimer();
    }
  });

  onUnmounted(() => {
    removeRouteGuard();
    if (countdownTimer) clearInterval(countdownTimer);
    clearSessionTimer();
  });
});

const checkIfPageRefresh = () => {
  const perfData = window.performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
  return perfData?.type === 'reload';
};

const restoreStateOnRefresh = () => {
  const savedState = localStorage.getItem('passwordResetState');
  if (savedState) {
    try {
      const { step, email, expireTime, verify_token } = JSON.parse(savedState);
      const now = Date.now();

      if (step === 2 && email && expireTime && now < expireTime) {
        currentStep.value = 2;
        form.email = email;
        form.verify_token = verify_token || '';

        const remainingTime = expireTime - now;
        startSessionTimer(remainingTime);
      } else {
        resetToFirstStep();
        if (expireTime && now >= expireTime) {
          import('element-plus').then((el) => {
            el.ElMessage.info('验证已过期，请重新验证');
          });
        }
      }
    } catch (error) {
      console.error('状态解析失败', error);
      resetToFirstStep();
    }
  } else {
    resetToFirstStep();
  }
};

const startSessionTimer = (remainingTime: number) => {
  clearSessionTimer();

  sessionTimer = setTimeout(() => {
    resetToFirstStep();
    import('element-plus').then((el) => {
      el.ElMessage.info('验证已过期，请重新验证');
    });
  }, remainingTime);
};

const clearSessionTimer = () => {
  if (sessionTimer) {
    clearTimeout(sessionTimer);
    sessionTimer = null;
  }
};

const resetToFirstStep = () => {
  currentStep.value = 1;
  clearResetState();
  clearSessionTimer();
  form.email = '';
  form.code = '';
  form.newPwd = '';
  form.confirmNewPwd = '';
  form.verify_token = '';
};

const clearResetState = () => {
  localStorage.removeItem('passwordResetState');
};

const saveResetState = (step: number, email: string, verify_token?: string) => {
  const expireTime = Date.now() + 5 * 60 * 1000;
  localStorage.setItem('passwordResetState', JSON.stringify({
    step,
    email,
    expireTime,
    verify_token
  }));

  startSessionTimer(5 * 60 * 1000);
};

const checkPasswordMatch = () => {
  if (!form.newPwd && form.confirmNewPwd) {
    import('element-plus').then((el) => {
      el.ElMessage.warning('请先输入新密码');
    });
    return false;
  }

  if (form.newPwd && !form.confirmNewPwd) {
    import('element-plus').then((el) => {
      el.ElMessage.warning('请输入确认密码');
    });
    return false;
  }

  if (form.newPwd && form.confirmNewPwd && form.newPwd !== form.confirmNewPwd) {
    import('element-plus').then((el) => {
      el.ElMessage.error('两次输入的密码不一致，请重新输入');
    });
    return false;
  }

  return true;
};

const sendCode = async () => {
  const reg = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!reg.test(form.email)) {
    import('element-plus').then((el) => {
      el.ElMessage.warning('请输入正确的邮箱格式');
    });
    return;
  }
  if (isCounting.value) {
    import('element-plus').then((el) => {
      el.ElMessage.info(`验证码已发送，请等待${count.value}秒后再试`);
    });
    return;
  }
  if (isSendingCode.value) return;

  isSendingCode.value = true;
  try {
    const params = { email: form.email };

    const res = await axios.post(
      `${BASE_URL}/weather/user/send-reset-code/`,
      { email: form.email },
      {
        headers: {
          'Content-Type': 'application/json',
          ...generateSignedHeaders(params)
        }
      }
    );

    if (res.data.code === 200) {
      import('element-plus').then((el) => {
        el.ElMessage.success('验证码已发送（1分钟有效）');
      });
      startCountdown();
    } else {
      import('element-plus').then((el) => {
        el.ElMessage.error(res.data.message || '发送失败');
      });
    }
  } catch (e: any) {
    import('element-plus').then((el) => {
      el.ElMessage.error(e.response?.data?.message || '网络错误');
    });
  } finally {
    isSendingCode.value = false;
  }
};

const startCountdown = () => {
  isCounting.value = true;
  count.value = 60;

  if (countdownTimer) clearInterval(countdownTimer);

  countdownTimer = setInterval(() => {
    count.value--;
    if (count.value <= 0) {
      clearInterval(countdownTimer as NodeJS.Timeout);
      count.value = 60;
      isCounting.value = false;
      countdownTimer = null;
    }
  }, 1000);
};

const goToNextStep = async () => {
  if (!formRef.value) return;

  try {
    await formRef.value.validate();
    isVerifying.value = true;

    const res = await axios.post(
      `${BASE_URL}/weather/user/verify-code/`,
      { email: form.email, code: form.code, type: 'reset' },
      { headers: { 'Content-Type': 'application/json' } }
    );

    if (res.data.code === 200) {
      import('element-plus').then((el) => {
        el.ElMessage.success('验证通过');
      });
      currentStep.value = 2;
      form.verify_token = res.data.data?.verify_token || '';
      saveResetState(2, form.email, form.verify_token);
    } else {
      import('element-plus').then((el) => {
        el.ElMessage.error(res.data.message || '验证码错误');
      });
    }
  } catch (e: any) {
  } finally {
    isVerifying.value = false;
  }
};

const resetPassword = async () => {
  if (!formRef.value) return;

  if (!checkPasswordMatch()) return;

  try {
    await formRef.value.validate();
    isResetting.value = true;

    const requestData = {
      email: form.email,
      new_password: form.newPwd,
      verify_token: form.verify_token
    };

    const res = await axios.post(
      `${BASE_URL}/weather/user/reset-password/`,
      requestData,
      { headers: { 'Content-Type': 'application/json' } }
    );

    if (res.data.code === 200) {
      import('element-plus').then((el) => {
        el.ElMessage.success('重置成功，1.5秒后跳转登录');
      });
      clearResetState();
      clearSessionTimer();
      setTimeout(() => router.push('/userlogin'), 1500);
    } else {
      import('element-plus').then((el) => {
        el.ElMessage.error(res.data.message || '重置失败');
      });
    }
  } catch (e: any) {
    if (e?.message) {
      import('element-plus').then((el) => {
        el.ElMessage.error(e.message);
      });
    }
  } finally {
    isResetting.value = false;
  }
};
</script>

<style scoped>
:deep(.el-button.is-loading .el-loading-spinner) {
  margin-right: 5px;
  width: 14px;
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

.auth-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 17px;
  background-color: #f0f2f5;
  position: relative;
  overflow: hidden;
  box-sizing: border-box;
  border: none !important;
}

.bg-decoration {
  position: absolute;
  width: 425px;
  height: 425px;
  border-radius: 50%;
  z-index: 0;
  filter: blur(85px);
  opacity: 0.3;
}

.top-left {
  top: -212px;
  left: -212px;
  background: linear-gradient(135deg, #409EFF, #66B1CD);
}

.bottom-right {
  bottom: -212px;
  right: -212px;
  background: linear-gradient(135deg, #722ED1, #F5222D);
}

.auth-card {
  width: 100%;
  max-width: 323px;
  border-radius: 10px;
  box-shadow: 0 3px 14px rgba(0, 0, 0, 0.06);
  background-color: #fff;
  position: relative;
  z-index: 1;
  border: none !important;
  animation: fadeIn 0.3s ease-out forwards;
  margin-bottom: 34px;
}

.auth-header {
  text-align: center;
  padding: 20px 0;
  margin: 0;
  border: none !important;
}

.auth-header h2 {
  color: #333;
  font-size: 17px;
  font-weight: 500;
  margin: 0;
}

.auth-form {
  padding: 0 20px 20px;
}

.verify-step .input-item-gap,
.reset-step .input-item-gap {
  margin-bottom: 15px !important;
}

.form-item {
  margin-bottom: 0 !important;
  animation: fadeIn 0.3s ease-out forwards;
  opacity: 0;
  transform: translateY(5px);
}

.verify-step :deep(.form-item:nth-child(1)),
.reset-step :deep(.form-item:nth-child(1)) { animation-delay: 0.1s; }

.verify-step :deep(.form-item:nth-child(2)),
.reset-step :deep(.form-item:nth-child(2)) { animation-delay: 0.2s; }

.full-width-input {
  width: 100% !important;
  height: 38px;
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
  cursor: pointer;
  font-size: 14px;
  transition: color 0.2s;
}

:deep(.el-input__suffix .el-icon:hover) {
  color: #409EFF;
}

:deep(.el-input.is-disabled .el-input__wrapper) {
  background-color: #f5f5f5;
  cursor: not-allowed;
  --el-input-border-color: #e4e7ed !important;
}

:deep(.el-button.is-disabled) {
  background-color: #f5f5f5 !important;
  color: #c0c4cc !important;
  border-color: #e4e7ed !important;
  cursor: not-allowed !important;
}

.full-width-btn {
  width: 100%;
  height: 38px;
  font-size: 14px;
  border-radius: 7px;
}

:deep(.el-col:nth-child(2) .el-button) {
  height: 38px !important;
  border-radius: 7px !important;
  font-size: 12px !important;
}

:deep(.send-code-btn) {
  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;
  padding: 0 12px !important;
  box-sizing: border-box !important;
  line-height: 1 !important;
}

:deep(.send-code-btn .el-button__text) {
  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;
  line-height: 1 !important;
}

.form-actions {
  display: flex;
  flex-direction: column;
  gap: 14px;
  margin-top: 7px;
}

.login-link {
  color: #666;
  font-size: 12px;
  text-align: center;
}

.interactive-link {
  color: #409EFF;
  text-decoration: none;
  margin-left: 3px;
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

.interactive-link:hover::after { width: 100%; }

:deep(.el-form-item__error) {
  font-size: 10px;
  color: #F56C6C;
  padding-top: 3px;
  line-height: 1;
}

.beian-info {
  position: absolute;
  bottom: 17px;
  left: 0;
  right: 0;
  text-align: center;
  font-size: 12px;
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
:deep(.el-icon) {
  border-top: none !important;
  box-shadow: none !important;
}

@media (max-width: 480px) {
  .auth-card {
    max-width: 100%;
    margin: 0 10px 25px;
  }

  .auth-form {
    padding: 0 15px 15px;
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
