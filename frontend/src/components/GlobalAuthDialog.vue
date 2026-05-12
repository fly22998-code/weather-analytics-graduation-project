<template>
  <el-dialog
    v-model="authModalState.open"
    width="440px"
    align-center
    destroy-on-close
    :show-close="!isSubmitting"
    :close-on-click-modal="!isSubmitting"
    :close-on-press-escape="!isSubmitting"
    class="global-auth-dialog"
    @closed="handleClosed"
  >
    <template #header>
      <div class="auth-dialog-header">
        <div class="auth-dialog-copy">
          <div class="auth-dialog-meta">{{ subtitleMap[authModalState.mode] }}</div>
          <h3>{{ titleMap[authModalState.mode] }}</h3>
          <p v-if="authModalState.reason" class="auth-dialog-reason">{{ authModalState.reason }}</p>
          <p v-else class="auth-dialog-subtitle">{{ helperMap[authModalState.mode] }}</p>
        </div>
      </div>
    </template>

    <div class="auth-mode-switcher">
      <button
        v-for="mode in modes"
        :key="mode.value"
        type="button"
        class="auth-mode-chip"
        :class="{ active: authModalState.mode === mode.value }"
        @click="switchAuthMode(mode.value)"
      >
        <span class="chip-dot"></span>
        {{ t(mode.labelKey) }}
      </button>
    </div>

    <el-form
      v-if="authModalState.mode === 'login'"
      ref="loginFormRef"
      :model="loginForm"
      :rules="loginRules"
      class="auth-form-shell"
      label-width="0"
      @submit.prevent
    >
      <el-form-item prop="email" class="auth-field">
        <div class="field-label">{{ t('auth.email') }}</div>
        <el-input
          v-model="loginForm.email"
          type="email"
          name="weather-login-email"
          autocomplete="new-password"
          :placeholder="t('auth.emailPlaceholder')"
          :disabled="isSubmitting"
        />
      </el-form-item>
      <el-form-item prop="password" class="auth-field">
        <div class="field-label">{{ t('auth.password') }}</div>
        <el-input
          v-model="loginForm.password"
          type="password"
          name="weather-login-password"
          autocomplete="new-password"
          show-password
          :placeholder="t('auth.passwordPlaceholder')"
          :disabled="isSubmitting"
        />
      </el-form-item>
      <div class="auth-inline-meta">
        <span class="auth-inline-tip">{{ t('auth.loginTip') }}</span>
      </div>
      <el-button class="auth-submit-btn" type="primary" :loading="isSubmitting" @click="handleLogin">{{ t('auth.login') }}</el-button>
    </el-form>

    <el-form
      v-else-if="authModalState.mode === 'register'"
      ref="registerFormRef"
      :model="registerForm"
      :rules="registerRules"
      class="auth-form-shell"
      label-width="0"
      @submit.prevent
    >
      <el-form-item prop="email" class="auth-field">
        <div class="field-label">{{ t('auth.email') }}</div>
        <el-input v-model="registerForm.email" :placeholder="t('auth.emailPlaceholder')" :disabled="isSubmitting || registerState.isCounting" />
      </el-form-item>
      <el-form-item prop="code" class="auth-field">
        <div class="field-label">{{ t('auth.code') }}</div>
        <div class="inline-action-row">
          <el-input v-model="registerForm.code" maxlength="6" :placeholder="t('auth.codePlaceholder')" :disabled="isSubmitting" />
          <el-button class="secondary-action-btn" :disabled="isSubmitting || registerState.isCounting" @click="handleSendRegisterCode">
            {{ registerState.isCounting ? formatCountdown(registerState.countdown) : t('auth.sendCode') }}
          </el-button>
        </div>
      </el-form-item>
      <el-form-item prop="password" class="auth-field">
        <div class="field-label">{{ t('auth.password') }}</div>
        <el-input v-model="registerForm.password" type="password" show-password :placeholder="t('auth.passwordHintPlaceholder')" :disabled="isSubmitting" />
      </el-form-item>
      <el-form-item prop="confirmPassword" class="auth-field">
        <div class="field-label">{{ t('auth.confirmPassword') }}</div>
        <el-input v-model="registerForm.confirmPassword" type="password" show-password :placeholder="t('auth.confirmPasswordPlaceholder')" :disabled="isSubmitting" />
      </el-form-item>
      <el-button class="auth-submit-btn" type="primary" :loading="isSubmitting" @click="handleRegister">{{ t('auth.completeRegister') }}</el-button>
    </el-form>

    <el-form
      v-else
      ref="resetFormRef"
      :model="resetForm"
      :rules="resetStep === 1 ? resetVerifyRules : resetPasswordRules"
      class="auth-form-shell"
      label-width="0"
      @submit.prevent
    >
      <template v-if="resetStep === 1">
        <el-form-item prop="email" class="auth-field">
          <div class="field-label">{{ t('auth.registerEmail') }}</div>
          <el-input v-model="resetForm.email" :placeholder="t('auth.registerEmailPlaceholder')" :disabled="isSubmitting || resetState.isCounting" />
        </el-form-item>
        <el-form-item prop="code" class="auth-field">
            <div class="field-label">{{ t('auth.code') }}</div>
          <div class="inline-action-row">
            <el-input v-model="resetForm.code" maxlength="6" :placeholder="t('auth.codePlaceholder')" :disabled="isSubmitting" />
            <el-button class="secondary-action-btn" :disabled="isSubmitting || resetState.isCounting" @click="handleSendResetCode">
              {{ resetState.isCounting ? formatCountdown(resetState.countdown) : t('auth.sendCode') }}
            </el-button>
          </div>
        </el-form-item>
        <el-button class="auth-submit-btn" type="primary" :loading="isSubmitting" @click="handleVerifyResetCode">{{ t('auth.verifyNext') }}</el-button>
      </template>

      <template v-else>
        <el-form-item prop="newPassword" class="auth-field">
          <div class="field-label">{{ t('auth.newPassword') }}</div>
          <el-input v-model="resetForm.newPassword" type="password" show-password :placeholder="t('auth.newPasswordPlaceholder')" :disabled="isSubmitting" />
        </el-form-item>
        <el-form-item prop="confirmNewPassword" class="auth-field">
          <div class="field-label">{{ t('auth.confirmNewPassword') }}</div>
          <el-input v-model="resetForm.confirmNewPassword" type="password" show-password :placeholder="t('auth.confirmNewPasswordPlaceholder')" :disabled="isSubmitting" />
        </el-form-item>
        <el-button class="auth-submit-btn" type="primary" :loading="isSubmitting" @click="handleResetPassword">{{ t('auth.confirmReset') }}</el-button>
      </template>
    </el-form>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue';
import axios from 'axios';
import type { FormInstance } from 'element-plus';
import { ElMessage, ElMessageBox } from 'element-plus';
import { BASE_URL } from '@/store/config';
import { authModalState, closeAuthModal, switchAuthMode, type AuthMode } from '@/utils/authModal';
import { checkTokenValid, notifyAuthChanged } from '@/utils/auth';
import { generateSignedHeaders, setSessionSignKey } from '@/utils/signature';
import { setAccessToken } from '@/utils/tokenStorage';
import { t } from '@/utils/i18n';

const titleMap = computed<Record<AuthMode, string>>(() => ({
  login: t('auth.login'),
  register: t('auth.register'),
  reset: t('auth.reset')
}));

const subtitleMap = computed<Record<AuthMode, string>>(() => ({
  login: t('auth.loginMeta'),
  register: t('auth.registerMeta'),
  reset: t('auth.resetMeta')
}));

const helperMap = computed<Record<AuthMode, string>>(() => ({
  login: t('auth.loginRequired'),
  register: t('auth.registerHelper'),
  reset: t('auth.resetHelper')
}));

const modes: Array<{ value: AuthMode; labelKey: 'auth.login' | 'auth.register' | 'auth.reset' }> = [
  { value: 'login', labelKey: 'auth.login' },
  { value: 'register', labelKey: 'auth.register' },
  { value: 'reset', labelKey: 'auth.reset' }
];

const isSubmitting = ref(false);

const loginFormRef = ref<FormInstance>();
const registerFormRef = ref<FormInstance>();
const resetFormRef = ref<FormInstance>();

const loginForm = reactive({
  email: '',
  password: ''
});

const registerForm = reactive({
  email: '',
  code: '',
  password: '',
  confirmPassword: ''
});

const resetForm = reactive({
  email: '',
  code: '',
  verifyToken: '',
  newPassword: '',
  confirmNewPassword: ''
});

const registerState = reactive({
  isCounting: false,
  countdown: 60,
  timer: null as ReturnType<typeof setInterval> | null
});

const resetState = reactive({
  isCounting: false,
  countdown: 60,
  timer: null as ReturnType<typeof setInterval> | null
});

const resetStep = ref(1);

const emailRules = computed(() => [
  { required: true, message: t('auth.emailRequired'), trigger: 'blur' },
  { type: 'email', message: t('auth.emailInvalid'), trigger: 'blur' }
]);

const loginRules = computed(() => ({
  email: emailRules.value,
  password: [
    { required: true, message: t('auth.passwordRequired'), trigger: 'blur' },
    { min: 8, message: t('auth.passwordMin'), trigger: 'blur' }
  ]
}));

const registerRules = computed(() => ({
  email: emailRules.value,
  code: [
    { required: true, message: t('auth.codeRequired'), trigger: 'blur' },
    { pattern: /^\d{6}$/, message: t('auth.codePattern'), trigger: 'blur' }
  ],
  password: [
    { required: true, message: t('auth.passwordRequired'), trigger: 'blur' },
    { min: 8, message: t('auth.passwordMin'), trigger: 'blur' },
    { pattern: /^(?=.*[A-Za-z])(?=.*\d).+$/, message: t('auth.passwordPattern'), trigger: 'blur' }
  ],
  confirmPassword: [
    {
      validator: (_rule: unknown, value: string, callback: (error?: Error) => void) => {
        if (value !== registerForm.password) {
          callback(new Error(t('auth.passwordMismatch')));
          return;
        }
        callback();
      },
      trigger: 'blur'
    }
  ]
}));

const resetVerifyRules = computed(() => ({
  email: emailRules.value,
  code: [
    { required: true, message: t('auth.codeRequired'), trigger: 'blur' },
    { pattern: /^\d{6}$/, message: t('auth.codePattern'), trigger: 'blur' }
  ]
}));

const resetPasswordRules = computed(() => ({
  newPassword: [
    { required: true, message: t('auth.newPasswordRequired'), trigger: 'blur' },
    { min: 8, message: t('auth.passwordMin'), trigger: 'blur' },
    { pattern: /^(?=.*[A-Za-z])(?=.*\d).+$/, message: t('auth.passwordPattern'), trigger: 'blur' }
  ],
  confirmNewPassword: [
    {
      validator: (_rule: unknown, value: string, callback: (error?: Error) => void) => {
        if (value !== resetForm.newPassword) {
          callback(new Error(t('auth.passwordMismatch')));
          return;
        }
        callback();
      },
      trigger: 'blur'
    }
  ]
}));

const formatCountdown = (seconds: number) => {
  return `${seconds}${t('auth.resendAfter')}`;
};

const resetLocalState = () => {
  loginForm.password = '';
  registerForm.code = '';
  registerForm.password = '';
  registerForm.confirmPassword = '';
  resetForm.code = '';
  resetForm.verifyToken = '';
  resetForm.newPassword = '';
  resetForm.confirmNewPassword = '';
  resetStep.value = 1;
};

const handleClosed = () => {
  resetLocalState();
  closeAuthModal();
};

const startCountdown = (target: typeof registerState | typeof resetState) => {
  if (target.timer) {
    clearInterval(target.timer);
  }

  target.isCounting = true;
  target.countdown = 60;
  target.timer = setInterval(() => {
    target.countdown -= 1;
    if (target.countdown <= 0) {
      if (target.timer) {
        clearInterval(target.timer);
      }
      target.timer = null;
      target.isCounting = false;
      target.countdown = 60;
    }
  }, 1000);
};

const handleLogin = async (forceLogin = false) => {
  const shouldForceLogin = forceLogin === true;
  if (checkTokenValid()) {
    ElMessage.info(t('auth.currentLoggedIn'));
    closeAuthModal();
    return;
  }

  if (!loginFormRef.value) {
    return;
  }

  try {
    await loginFormRef.value.validate();
  } catch {
    return;
  }

  isSubmitting.value = true;
  try {
    const response = await axios.post(`${BASE_URL}/weather/user/login/`, {
      email: loginForm.email.trim().toLowerCase(),
      password: loginForm.password,
      force_login: shouldForceLogin
    }, {
      headers: { 'Content-Type': 'application/json' },
      withCredentials: true
    });

    if (response.data.code !== 200 || !response.data.data?.token) {
      ElMessage.error(response.data.message || t('auth.loginFailed'));
      return;
    }

    setAccessToken(response.data.data.access_token || response.data.data.token);
    setSessionSignKey(response.data.data.sign_key);
    localStorage.removeItem('last_login_email');
    notifyAuthChanged();
    ElMessage.success(t('auth.loginSuccess'));
    closeAuthModal();
  } catch (error: any) {
    if (error.response?.status === 409 && error.response?.data?.code === 4091 && !shouldForceLogin) {
      try {
        await ElMessageBox.confirm(
          error.response?.data?.message || t('auth.forceLoginMessage'),
          t('auth.loginConfirm'),
          {
            confirmButtonText: t('auth.forceLoginConfirm'),
            cancelButtonText: t('profile.cancel'),
            type: 'warning',
            autofocus: false,
            customClass: 'minimal-alert-box'
          }
        );
        return handleLogin(true);
      } catch {
        return;
      }
    }
    ElMessage.error(error.response?.data?.message || t('auth.loginFailedRetry'));
  } finally {
    isSubmitting.value = false;
  }
};

const handleSendRegisterCode = async () => {
  try {
    await registerFormRef.value?.validateField('email');
  } catch {
    return;
  }

  try {
    const email = registerForm.email.trim();
    const response = await axios.post(`${BASE_URL}/weather/user/send-register-code/`, {
      email
    }, {
      headers: {
        'Content-Type': 'application/json',
        ...generateSignedHeaders({ email })
      }
    });

    if (response.data.code !== 200) {
      ElMessage.error(response.data.message || t('auth.codeSendFailed'));
      return;
    }

    ElMessage.success(t('auth.codeSent'));
    startCountdown(registerState);
  } catch (error: any) {
    ElMessage.error(error.response?.data?.message || t('auth.codeSendFailed'));
  }
};

const handleRegister = async () => {
  if (!registerFormRef.value) {
    return;
  }

  try {
    await registerFormRef.value.validate();
  } catch {
    return;
  }

  isSubmitting.value = true;
  try {
    const verifyResponse = await axios.post(`${BASE_URL}/weather/user/verify-code/`, {
      email: registerForm.email.trim(),
      code: registerForm.code
    }, {
      headers: { 'Content-Type': 'application/json' }
    });

    if (verifyResponse.data.code !== 200 || !verifyResponse.data.data?.verify_token) {
      ElMessage.error(verifyResponse.data.message || t('auth.codeVerifyFailed'));
      return;
    }

    const registerResponse = await axios.post(`${BASE_URL}/weather/user/register/`, {
      email: registerForm.email.trim(),
      password: registerForm.password,
      verify_token: verifyResponse.data.data.verify_token
    }, {
      headers: { 'Content-Type': 'application/json' }
    });

    if (registerResponse.data.code !== 200) {
      ElMessage.error(registerResponse.data.message || t('auth.registerFailed'));
      return;
    }

    ElMessage.success(t('auth.registerSuccess'));
    loginForm.email = registerForm.email.trim();
    switchAuthMode('login');
  } catch (error: any) {
    ElMessage.error(error.response?.data?.message || t('auth.registerFailedRetry'));
  } finally {
    isSubmitting.value = false;
  }
};

const handleSendResetCode = async () => {
  try {
    await resetFormRef.value?.validateField('email');
  } catch {
    return;
  }

  try {
    const email = resetForm.email.trim();

    const response = await axios.post(`${BASE_URL}/weather/user/send-reset-code/`, {
      email
    }, {
      headers: {
        'Content-Type': 'application/json',
        ...generateSignedHeaders({ email })
      }
    });

    if (response.data.code !== 200) {
      ElMessage.error(response.data.message || t('auth.codeSendFailed'));
      return;
    }

    ElMessage.success(t('auth.codeSent'));
    startCountdown(resetState);
  } catch (error: any) {
    ElMessage.error(error.response?.data?.message || t('auth.codeSendFailed'));
  }
};

const handleVerifyResetCode = async () => {
  if (!resetFormRef.value) {
    return;
  }

  try {
    await resetFormRef.value.validate();
  } catch {
    return;
  }

  isSubmitting.value = true;
  try {
    const response = await axios.post(`${BASE_URL}/weather/user/verify-code/`, {
      email: resetForm.email.trim(),
      code: resetForm.code,
      type: 'reset'
    }, {
      headers: { 'Content-Type': 'application/json' }
    });

    if (response.data.code !== 200 || !response.data.data?.verify_token) {
      ElMessage.error(response.data.message || t('auth.codeVerifyFailed'));
      return;
    }

    resetForm.verifyToken = response.data.data.verify_token;
    resetStep.value = 2;
    ElMessage.success(t('auth.codeVerified'));
  } catch (error: any) {
    ElMessage.error(error.response?.data?.message || t('auth.codeVerifyFailed'));
  } finally {
    isSubmitting.value = false;
  }
};

const handleResetPassword = async () => {
  if (!resetFormRef.value) {
    return;
  }

  try {
    await resetFormRef.value.validate();
  } catch {
    return;
  }

  isSubmitting.value = true;
  try {
    const response = await axios.post(`${BASE_URL}/weather/user/reset-password/`, {
      email: resetForm.email.trim(),
      new_password: resetForm.newPassword,
      verify_token: resetForm.verifyToken
    }, {
      headers: { 'Content-Type': 'application/json' }
    });

    if (response.data.code !== 200) {
      ElMessage.error(response.data.message || t('auth.resetFailed'));
      return;
    }

    ElMessage.success(t('auth.resetSuccess'));
    loginForm.email = resetForm.email.trim();
    resetStep.value = 1;
    switchAuthMode('login');
  } catch (error: any) {
    ElMessage.error(error.response?.data?.message || t('auth.resetFailed'));
  } finally {
    isSubmitting.value = false;
  }
};

watch(
  () => authModalState.open,
  (open) => {
    if (open && checkTokenValid()) {
      closeAuthModal();
    }
  }
);
</script>

<style scoped>
.auth-dialog-header {
  display: flex;
  align-items: flex-start;
  justify-content: flex-start;
}

.auth-dialog-copy {
  flex: 1;
  min-width: 0;
}

.auth-dialog-meta {
  margin-bottom: 6px;
  color: #7b8aa0;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0;
}

.auth-dialog-copy h3 {
  margin: 0;
  font-size: 30px;
  line-height: 1.12;
  font-weight: 800;
  letter-spacing: 0;
  color: #111827;
}

.auth-dialog-reason,
.auth-dialog-subtitle {
  margin: 12px 0 0;
  max-width: 360px;
  font-size: 13px;
  line-height: 1.7;
  color: #64748b;
}

.inline-link-btn {
  border: none;
  background: transparent;
  padding: 0;
  color: #60a5fa;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: color 0.2s ease, opacity 0.2s ease;
}

.inline-link-btn:hover {
  color: #3b82f6;
}

.auth-mode-switcher {
  display: flex;
  gap: 3px;
  margin: 10px 0 24px;
  padding: 3px;
  border-radius: 14px;
  background: #f8fafc;
  border: 1px solid #e6edf5;
}

.auth-mode-chip {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  flex: 1;
  border: 1px solid transparent;
  background: transparent;
  color: #718096;
  border-radius: 11px;
  min-height: 38px;
  padding: 0 12px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 600;
  transition: all 0.2s ease;
}

.auth-mode-chip.active {
  background: #ffffff;
  border-color: #e6edf5;
  color: #111827;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.06);
}

.chip-dot {
  width: 4px;
  height: 4px;
  border-radius: 999px;
  background: currentColor;
  opacity: 0.28;
}

.auth-mode-chip.active .chip-dot {
  opacity: 0.9;
}

.auth-form-shell {
  padding: 2px 2px 0;
}

.auth-field {
  margin-bottom: 8px;
  min-height: 102px;
}

.field-label {
  margin: 0 0 8px 2px;
  color: #7b8aa0;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0;
}

.auth-inline-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin: 8px 0 4px;
  padding-left: 2px;
}

.auth-inline-tip {
  color: #94a3b8;
  font-size: 12px;
  line-height: 1.5;
}

.inline-action-row {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 10px;
  width: 100%;
}

.auth-submit-btn {
  width: 100%;
  min-height: 48px;
  margin-top: 12px;
  border: none !important;
  border-radius: 12px !important;
  background: #111827 !important;
  color: #ffffff !important;
  font-size: 15px !important;
  font-weight: 700 !important;
  box-shadow: 0 10px 22px rgba(15, 23, 42, 0.16) !important;
}

.auth-submit-btn:hover,
.auth-submit-btn:focus-visible {
  background: #1f2937 !important;
  box-shadow: 0 12px 26px rgba(15, 23, 42, 0.2) !important;
}

.secondary-action-btn {
  min-width: 112px;
  border-radius: 11px !important;
  border: 1px solid #e2e8f0 !important;
  background: #ffffff !important;
  color: #334155 !important;
  font-weight: 700 !important;
}

:global(.global-auth-dialog .el-dialog) {
  border-radius: 20px;
  overflow: hidden;
  background: #ffffff !important;
  box-shadow: 0 24px 70px rgba(15, 23, 42, 0.2) !important;
  border: 1px solid #e7edf5 !important;
}

:global(.global-auth-dialog .el-dialog__header) {
  padding: 26px 28px 8px;
}

:global(.global-auth-dialog .el-dialog__body) {
  padding: 8px 28px 28px;
}

:global(.global-auth-dialog .el-dialog__headerbtn) {
  top: 20px;
  right: 20px;
}

:global(.global-auth-dialog .el-dialog__headerbtn .el-dialog__close) {
  width: 30px;
  height: 30px;
  border-radius: 999px;
  color: #94a3b8;
  background: transparent;
  padding: 6px;
  transition: all 0.2s ease;
}

:global(.global-auth-dialog .el-dialog__headerbtn .el-dialog__close:hover) {
  color: #111827;
  background: #f8fafc;
}

:global(.global-auth-dialog .auth-dialog-quick-switch),
:global(.global-auth-dialog .quick-switch-label),
:global(.global-auth-dialog .quick-switch-link) {
  display: none !important;
}

:global(.global-auth-dialog .el-form-item__label) {
  color: #94a3b8 !important;
}

:global(.global-auth-dialog .auth-field .el-form-item__content) {
  position: relative;
  display: block;
  min-height: 78px;
  padding-bottom: 24px;
}

:global(.global-auth-dialog .el-form-item__error) {
  left: 2px;
  right: 0;
  top: auto;
  bottom: 0;
  padding-top: 0;
  padding-left: 2px;
  font-size: 12px;
  line-height: 1.35;
  min-height: 18px;
  transform: none;
  white-space: normal;
}

:global(.global-auth-dialog .el-input__wrapper) {
  min-height: 50px;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: none !important;
  border: 1px solid #dbe4ee;
  background: #ffffff !important;
  padding: 0 14px;
  transition:
    border-color 0.22s ease,
    box-shadow 0.22s ease,
    background-color 0.22s ease;
}

:global(.global-auth-dialog .el-input__wrapper:hover) {
  border-color: #c6d4e3;
  background: #ffffff !important;
}

:global(.global-auth-dialog .el-input__wrapper.is-focus) {
  border-color: #93c5fd !important;
  box-shadow:
    0 0 0 3px rgba(96, 165, 250, 0.12) !important;
  background: #ffffff !important;
}

:global(.global-auth-dialog .el-input__inner) {
  background: transparent !important;
  box-shadow: none !important;
  color: #111827 !important;
  font-size: 15px;
  font-weight: 500;
  letter-spacing: 0;
  -webkit-text-fill-color: #111827 !important;
}

:global(.global-auth-dialog .el-input__inner::placeholder) {
  color: #a3b2c4 !important;
  -webkit-text-fill-color: #a3b2c4 !important;
}

:global(.global-auth-dialog .el-input__inner:-webkit-autofill),
:global(.global-auth-dialog .el-input__inner:-webkit-autofill:hover),
:global(.global-auth-dialog .el-input__inner:-webkit-autofill:focus),
:global(.global-auth-dialog .el-input__inner:-webkit-autofill:active) {
  -webkit-text-fill-color: #111827 !important;
  -webkit-box-shadow: 0 0 0 1000px transparent inset !important;
  box-shadow: 0 0 0 1000px transparent inset !important;
  transition: background-color 9999s ease-out 0s;
}

:global(.global-auth-dialog .el-input__suffix-inner),
:global(.global-auth-dialog .el-input__icon) {
  color: #9aa9bb !important;
  font-size: 16px !important;
}

:global(.global-auth-dialog .el-input__suffix),
:global(.global-auth-dialog .el-input__prefix) {
  background: transparent !important;
}

:global(.global-auth-dialog .el-input__suffix-inner > *),
:global(.global-auth-dialog .el-input__prefix-inner > *) {
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

:global(.global-auth-dialog .el-input__clear),
:global(.global-auth-dialog .el-input__password) {
  color: #9aa9bb !important;
  transition: color 0.2s ease, transform 0.2s ease;
}

:global(.global-auth-dialog .el-input__clear:hover),
:global(.global-auth-dialog .el-input__password:hover) {
  color: #64748b !important;
  transform: scale(1.04);
}

:global(.global-auth-dialog .el-button) {
  min-height: 48px;
}

:global(.global-auth-dialog .el-overlay) {
  background: rgba(17, 24, 39, 0.38);
  backdrop-filter: blur(10px);
}

:global(html.dark .global-auth-dialog),
:global(body.site-dark-mode .global-auth-dialog) {
  color-scheme: dark;
}

:global(html.dark .global-auth-dialog.el-dialog),
:global(body.site-dark-mode .global-auth-dialog.el-dialog),
:global(html.dark .global-auth-dialog .el-dialog),
:global(body.site-dark-mode .global-auth-dialog .el-dialog) {
  background: #101827 !important;
  border-color: rgba(148, 163, 184, 0.16) !important;
  box-shadow: 0 30px 80px rgba(2, 6, 23, 0.58) !important;
}

:global(html.dark .global-auth-dialog .auth-dialog-meta),
:global(body.site-dark-mode .global-auth-dialog .auth-dialog-meta) {
  color: #94a3b8;
}

:global(html.dark .global-auth-dialog .auth-dialog-copy h3),
:global(body.site-dark-mode .global-auth-dialog .auth-dialog-copy h3) {
  color: #f8fafc;
}

:global(html.dark .global-auth-dialog .auth-dialog-reason),
:global(html.dark .global-auth-dialog .auth-dialog-subtitle),
:global(body.site-dark-mode .global-auth-dialog .auth-dialog-reason),
:global(body.site-dark-mode .global-auth-dialog .auth-dialog-subtitle) {
  color: #94a3b8;
}

:global(html.dark .global-auth-dialog .quick-switch-label),
:global(body.site-dark-mode .global-auth-dialog .quick-switch-label) {
  color: #64748b;
}

:global(html.dark .global-auth-dialog .inline-link-btn),
:global(body.site-dark-mode .global-auth-dialog .inline-link-btn) {
  color: #93c5fd;
}

:global(html.dark .global-auth-dialog .auth-mode-switcher),
:global(body.site-dark-mode .global-auth-dialog .auth-mode-switcher) {
  background: rgba(255, 255, 255, 0.035);
  border-color: rgba(148, 163, 184, 0.14);
}

:global(html.dark .global-auth-dialog .auth-mode-chip),
:global(body.site-dark-mode .global-auth-dialog .auth-mode-chip) {
  color: #94a3b8;
}

:global(html.dark .global-auth-dialog .auth-mode-chip.active),
:global(body.site-dark-mode .global-auth-dialog .auth-mode-chip.active) {
  background: rgba(255, 255, 255, 0.075);
  border-color: rgba(255, 255, 255, 0.08);
  color: #f8fafc;
  box-shadow: none;
}

:global(html.dark .global-auth-dialog .field-label),
:global(html.dark .global-auth-dialog .auth-inline-tip),
:global(body.site-dark-mode .global-auth-dialog .field-label),
:global(body.site-dark-mode .global-auth-dialog .auth-inline-tip) {
  color: #64748b;
}

:global(html.dark .global-auth-dialog .el-dialog__headerbtn .el-dialog__close),
:global(body.site-dark-mode .global-auth-dialog .el-dialog__headerbtn .el-dialog__close) {
  color: #94a3b8;
}

:global(html.dark .global-auth-dialog .el-dialog__headerbtn .el-dialog__close:hover),
:global(body.site-dark-mode .global-auth-dialog .el-dialog__headerbtn .el-dialog__close:hover) {
  color: #f8fafc;
  background: rgba(255, 255, 255, 0.05);
}

:global(html.dark .global-auth-dialog .el-form-item__label),
:global(body.site-dark-mode .global-auth-dialog .el-form-item__label) {
  color: #64748b !important;
}

:global(html.dark .global-auth-dialog .el-input__wrapper),
:global(body.site-dark-mode .global-auth-dialog .el-input__wrapper) {
  background: #111827 !important;
  border-color: rgba(148, 163, 184, 0.18) !important;
}

:global(html.dark .global-auth-dialog .el-input__wrapper:hover),
:global(body.site-dark-mode .global-auth-dialog .el-input__wrapper:hover) {
  border-color: rgba(191, 219, 254, 0.28) !important;
}

:global(html.dark .global-auth-dialog .el-input__wrapper.is-focus),
:global(body.site-dark-mode .global-auth-dialog .el-input__wrapper.is-focus) {
  background: #111827 !important;
  border-color: #93c5fd !important;
  box-shadow:
    0 0 0 3px rgba(59, 130, 246, 0.16) !important;
}

:global(html.dark .global-auth-dialog .el-input__inner),
:global(body.site-dark-mode .global-auth-dialog .el-input__inner) {
  color: #f8fafc !important;
  -webkit-text-fill-color: #f8fafc !important;
  caret-color: #f8fafc !important;
}

:global(html.dark .global-auth-dialog .el-input__inner:-webkit-autofill),
:global(html.dark .global-auth-dialog .el-input__inner:-webkit-autofill:hover),
:global(html.dark .global-auth-dialog .el-input__inner:-webkit-autofill:focus),
:global(html.dark .global-auth-dialog .el-input__inner:-webkit-autofill:active),
:global(body.site-dark-mode .global-auth-dialog .el-input__inner:-webkit-autofill),
:global(body.site-dark-mode .global-auth-dialog .el-input__inner:-webkit-autofill:hover),
:global(body.site-dark-mode .global-auth-dialog .el-input__inner:-webkit-autofill:focus),
:global(body.site-dark-mode .global-auth-dialog .el-input__inner:-webkit-autofill:active) {
  color: #f8fafc !important;
  -webkit-text-fill-color: #f8fafc !important;
  caret-color: #f8fafc !important;
  -webkit-box-shadow: 0 0 0 1000px #111827 inset !important;
  box-shadow: 0 0 0 1000px #111827 inset !important;
  transition: background-color 9999s ease-out 0s;
}

:global(html.dark .global-auth-dialog .el-input__inner::placeholder),
:global(body.site-dark-mode .global-auth-dialog .el-input__inner::placeholder) {
  color: #607089 !important;
  -webkit-text-fill-color: #607089 !important;
}

:global(html.dark .global-auth-dialog .el-input__suffix-inner),
:global(html.dark .global-auth-dialog .el-input__icon),
:global(body.site-dark-mode .global-auth-dialog .el-input__suffix-inner),
:global(body.site-dark-mode .global-auth-dialog .el-input__icon) {
  color: #7f92ab !important;
}

:global(html.dark .global-auth-dialog .el-input__clear),
:global(html.dark .global-auth-dialog .el-input__password),
:global(body.site-dark-mode .global-auth-dialog .el-input__clear),
:global(body.site-dark-mode .global-auth-dialog .el-input__password) {
  color: #7f92ab !important;
}

:global(html.dark .global-auth-dialog .el-input__clear:hover),
:global(html.dark .global-auth-dialog .el-input__password:hover),
:global(body.site-dark-mode .global-auth-dialog .el-input__clear:hover),
:global(body.site-dark-mode .global-auth-dialog .el-input__password:hover) {
  color: #cbd5e1 !important;
}

:global(html.dark .global-auth-dialog .secondary-action-btn),
:global(body.site-dark-mode .global-auth-dialog .secondary-action-btn) {
  background: #111827 !important;
  border-color: rgba(148, 163, 184, 0.16) !important;
  color: #e2e8f0 !important;
}

:global(html.dark .global-auth-dialog .auth-submit-btn),
:global(body.site-dark-mode .global-auth-dialog .auth-submit-btn) {
  background: #f8fafc !important;
  box-shadow: none !important;
  color: #0f172a !important;
}

:global(html.dark .global-auth-dialog .auth-submit-btn:hover),
:global(body.site-dark-mode .global-auth-dialog .auth-submit-btn:hover) {
  background: #e2e8f0 !important;
}

:global(html.dark .global-auth-dialog .el-form-item__error),
:global(body.site-dark-mode .global-auth-dialog .el-form-item__error) {
  color: #fca5a5 !important;
}

@media (max-width: 560px) {
  .auth-dialog-copy h3 {
    font-size: 28px;
  }

  .auth-dialog-header {
    flex-direction: column;
    gap: 12px;
  }

  .auth-mode-switcher {
    gap: 6px;
    padding: 5px;
  }

  .auth-mode-chip {
    min-height: 40px;
    padding: 0 10px;
    font-size: 12px;
  }

  .inline-action-row {
    grid-template-columns: 1fr;
  }

  .auth-inline-meta {
    flex-direction: column;
    align-items: flex-start;
  }

  .secondary-action-btn {
    width: 100%;
  }

  :global(.global-auth-dialog .el-dialog) {
    width: calc(100vw - 24px) !important;
    max-width: 460px;
  }

  :global(.global-auth-dialog .el-dialog__header) {
    padding: 24px 20px 10px;
  }

  :global(.global-auth-dialog .el-dialog__body) {
    padding: 8px 20px 22px;
  }
}
</style>
