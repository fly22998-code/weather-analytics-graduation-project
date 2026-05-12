<template>
  <nav class="nav-bar" :class="{ 'theme-dark': isGlobalDarkMode }" v-if="showNavbar">
    <div class="system-title">
      <span class="title-text">{{ currentPageTitle }}</span>
    </div>
   
    <div class="menu-container">
      <ul class="nav-menu">
        <li :class="{ active: $route?.name === 'WeatherQuery' }">
          <router-link to="/" class="menu-link">
            <span class="label-long">{{ t('nav.history.long') }}</span>
            <span class="label-short">{{ t('nav.history.short') }}</span>
          </router-link>
        </li>
        <li :class="{ active: $route?.name === 'WeatherAnalysis' }">
          <router-link to="/analysis" class="menu-link">
            <span class="label-long">{{ t('nav.realtime.long') }}</span>
            <span class="label-short">{{ t('nav.realtime.short') }}</span>
          </router-link>
        </li>
        <li :class="{ active: $route?.name === 'TemperatureChange' }">
          <router-link to="/temperature" class="menu-link">
            <span class="label-long">{{ t('nav.forecast.long') }}</span>
            <span class="label-short">{{ t('nav.forecast.short') }}</span>
          </router-link>
        </li>
      </ul>
    </div>

    <div class="language-switcher" ref="languageMenuRef">
      <button
        class="language-toggle-btn"
        type="button"
        @click.stop="toggleLanguageMenu"
        :title="`${t('language.current')}：${currentLocaleLabel}`"
      >
        <span>{{ currentLocaleShortLabel }}</span>
      </button>

      <div class="language-mode-menu" v-show="showLanguageMenu">
        <button
          v-for="option in localeOptions"
          :key="option.value"
          type="button"
          class="language-mode-item"
          :class="{ active: currentLocale === option.value }"
          @click.stop="handleSetLocale(option.value)"
        >
          <span>{{ t(option.labelKey) }}</span>
        </button>
      </div>
    </div>

    <div class="theme-switcher" ref="themeMenuRef">
      <button
        class="theme-toggle-btn"
        type="button"
        @click.stop="toggleThemeMenu"
        :title="`${t('theme.current')}：${currentThemeLabel}`"
      >
        <svg v-if="themeMode === 'system'" viewBox="0 0 24 24" width="18" height="18" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round">
          <rect x="3" y="4" width="18" height="12" rx="2"></rect>
          <path d="M8 20h8"></path>
          <path d="M12 16v4"></path>
        </svg>
        <svg v-else-if="isGlobalDarkMode" viewBox="0 0 24 24" width="18" height="18" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path></svg>
        <svg v-else viewBox="0 0 24 24" width="18" height="18" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5"></circle><line x1="12" y1="1" x2="12" y2="3"></line><line x1="12" y1="21" x2="12" y2="23"></line><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line><line x1="1" y1="12" x2="3" y2="12"></line><line x1="21" y1="12" x2="23" y2="12"></line><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line></svg>
      </button>

      <div class="theme-mode-menu" v-show="showThemeMenu">
        <button
          v-for="option in themeOptions"
          :key="option.value"
          type="button"
          class="theme-mode-item"
          :class="{ active: themeMode === option.value }"
          @click.stop="setThemeMode(option.value)"
        >
          <span>{{ t(option.labelKey) }}</span>
        </button>
      </div>
    </div>

    <div v-if="isAuthenticated" class="user-menu" ref="userMenuRef" @mouseenter="handleMouseEnter" @mouseleave="handleMouseLeave">
      <div class="user-email" @click.stop="toggleUserDropdown">
        <img v-if="hasCustomAvatar" :src="userAvatar" :alt="t('user.profile')" class="mini-avatar">
        <div
          v-else
          class="mini-avatar fallback-avatar fallback-avatar--nav"
          :style="defaultAvatarStyle"
          aria-hidden="true"
        >{{ defaultAvatarText }}</div>
        <span class="email-text">{{ tokenInfo.email || t('user.unknown') }}</span>
        <svg class="arrow-icon" :class="{ 'rotated': showUserDropdown }" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="6 9 12 15 18 9"></polyline>
        </svg>
      </div>
     
      <div class="user-dropdown" v-show="showUserDropdown">
        <div class="dropdown-item" @click.stop="openUserDetail">
          <span>{{ t('user.profile') }}</span>
        </div>
        <div class="dropdown-item" @click.stop="handleGoToAdmin">
          <span>{{ t('user.admin') }}</span>
        </div>
        <div class="dropdown-item" @click.stop="handleLogout">
          <span>{{ t('user.logout') }}</span>
        </div>
      </div>
    </div>

    <div v-else class="guest-entry">
      <span class="guest-tag">{{ t('guest.mode') }}</span>
      <button type="button" class="guest-login-btn" @click="handleOpenLogin">
        <span class="guest-login-text">{{ t('guest.login') }}</span>
      </button>
    </div>
  </nav>

  <transition name="drawer">
    <div class="drawer-overlay" v-if="showUserDetail" @click="showUserDetail = false">
      <div class="drawer-panel" @click.stop>
       
        <div class="drawer-header">
          <h3>{{ t('user.profile') }}</h3>
          <button class="drawer-close-btn" type="button" @click="showUserDetail = false">
            <svg viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>
       
        <div class="drawer-body">
          <div class="drawer-profile-top">
            <div class="avatar-interactive-wrapper" @click="triggerFileInput" :class="{ 'is-uploading': isAvatarUploading, 'editable': isEditMode }">
              <img v-if="hasCustomAvatar" :src="userAvatar" :alt="t('user.profile')" class="interactive-avatar">
              <div
                v-else
                class="interactive-avatar fallback-avatar fallback-avatar--panel"
                :style="defaultAvatarStyle"
                aria-hidden="true"
              >{{ defaultAvatarText }}</div>
              <div class="avatar-hover-mask" v-if="isEditMode">
                <svg viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"><path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"></path><circle cx="12" cy="13" r="4"></circle></svg>
                <span>{{ t('profile.changeAvatar') }}</span>
              </div>
              <div class="avatar-loading-mask" v-if="isAvatarUploading">
                <span>{{ uploadProgress }}%</span>
              </div>
            </div>
            <input ref="fileInputRef" type="file" accept="image/jpeg,image/png" class="file-input" @change="handleFileChange" :disabled="!isEditMode || isAvatarUploading">
           
            <div class="user-static-info">
              <div class="static-email">{{ tokenInfo.email || t('user.unknownEmail') }}</div>
              <div class="static-time">{{ t('profile.registerTime') }}：{{ registerTime ? registerTime.split(' ')[0] : '--' }}</div>
            </div>
          </div>

          <div class="profile-view-mode" v-if="!isEditMode">
            <div class="info-row">
              <span class="info-label">{{ t('profile.username') }}</span>
              <span class="info-value">{{ formData.username || t('profile.notSet') }}</span>
            </div>
            <div class="info-row">
              <span class="info-label">{{ t('profile.phone') }}</span>
              <span class="info-value">{{ formData.phone || t('profile.notSet') }}</span>
            </div>
            <div class="info-row">
              <span class="info-label">{{ t('profile.gender') }}</span>
              <span class="info-value">
                {{ formatGender(formData.gender) }}
              </span>
            </div>
            <div class="info-row">
              <span class="info-label">{{ t('profile.birthday') }}</span>
              <span class="info-value">{{ formData.birthday || t('profile.notSet') }}</span>
            </div>
          </div>

          <el-form v-else ref="formRef" :model="formData" :rules="formRules" label-position="top" class="drawer-form modern-edit-form" size="default">
            <el-form-item :label="t('profile.username')" prop="username">
              <el-input v-model="formData.username" :maxlength="20" :placeholder="t('profile.usernamePlaceholder')" :loading="isCheckingUsername" clearable />
            </el-form-item>

            <el-form-item :label="t('profile.phone')" prop="phone">
              <el-input v-model="formData.phone" :maxlength="11" :placeholder="t('profile.phonePlaceholder')" @input="formatPhoneNumber" clearable />
            </el-form-item>

            <el-form-item :label="t('profile.gender')" prop="gender">
              <el-select v-model="formData.gender" :placeholder="t('profile.genderPlaceholder')" style="width: 100%" :teleported="false">
                <el-option :label="t('profile.male')" value="MALE" />
                <el-option :label="t('profile.female')" value="FEMALE" />
                <el-option :label="t('profile.other')" value="OTHER" />
                <el-option :label="t('profile.secret')" value="SECRET" />
              </el-select>
            </el-form-item>

            <el-form-item :label="t('profile.birthday')" prop="birthday">
              <el-date-picker v-model="formData.birthday" type="date" :placeholder="t('profile.birthdayPlaceholder')" value-format="YYYY-MM-DD" :disabled-date="disableFutureDate" style="width: 100%" :teleported="false" />
            </el-form-item>
          </el-form>
        </div>

        <div class="drawer-footer">
          <template v-if="!isEditMode">
            <el-button class="drawer-edit-btn" @click="isEditMode = true">
              {{ t('profile.edit') }}
            </el-button>
          </template>
          <template v-else>
            <el-button @click="cancelEdit" class="drawer-cancel-btn">{{ t('profile.cancel') }}</el-button>
            <el-button type="primary" @click="handleSave" :loading="isAvatarUploading || isSaving || isCheckingUsername" class="drawer-save-btn">
              {{ t('profile.save') }}
            </el-button>
          </template>
        </div>

      </div>
    </div>
  </transition>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed, watch, reactive } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { ElMessage, ElMessageBox } from 'element-plus';
import { authSessionState, getUserInfo, checkAdminPermission, logout, getRefreshTokenExpireTime, hasActiveSession } from '../utils/auth';
import { redirectToLogin } from '../utils/requests';
import request from '@/utils/requests';
import { BASE_URL } from '@/store/config';
import { openAuthModal } from '@/utils/authModal';
import { getAccessToken } from '@/utils/tokenStorage';
import { currentLocale, currentLocaleOption, localeOptions, setLocale, t, type AppLocale } from '@/utils/i18n';

const USER_INFO_API = `${BASE_URL || ''}/weather/user/current/`;
const SAVE_USER_INFO_API = `${BASE_URL || ''}/weather/user/save/`;
const UPLOAD_AVATAR_API = `${BASE_URL || ''}/weather/user/upload/avatar/`;
const CHECK_USERNAME_API = `${BASE_URL || ''}/weather/user/check-username/`;
const USER_PROFILE_CACHE_KEY = 'weather_user_profile_cache';

interface UserInfoResponse {
  code: number;
  message: string;
  data: {
    email: string;
    username: string;
    avatar?: string;
    phone?: string;
    gender?: 'MALE' | 'FEMALE' | 'OTHER' | 'SECRET';
    birthday?: string;
    role: 'ADMIN' | 'USER';
    created_at?: string;
  };
}

interface UploadAvatarResponse {
  code: number;
  message: string;
  data: { avatar_path: string; avatar_name?: string; };
}

interface CheckUsernameResponse {
  code: number;
  message: string;
  data: boolean;
}

const isAvatarUploading = ref(false);
const uploadProgress = ref(0);
const previewAvatarUrl = ref('');
const fileInputRef = ref<HTMLInputElement | null>(null);
const isSaving = ref(false);
const selectedFileSize = ref<number | null>(null);
const selectedAvatarFile = ref<File | null>(null);
const isCheckingUsername = ref(false);

const route = useRoute();
const router = useRouter();
type ThemeMode = 'light' | 'dark' | 'system';
const THEME_MODE_KEY = 'weather_theme_mode';
const LEGACY_DARK_MODE_KEY = 'weather_dark_mode';
const isGlobalDarkMode = ref(false);
const themeMode = ref<ThemeMode>('light');
const showUserDropdown = ref(false);
const showThemeMenu = ref(false);
const showLanguageMenu = ref(false);
const showUserDetail = ref(false);
const isLoading = ref(false);
const userMenuRef = ref<HTMLElement | null>(null);
const themeMenuRef = ref<HTMLElement | null>(null);
const languageMenuRef = ref<HTMLElement | null>(null);
let systemThemeMediaQuery: MediaQueryList | null = null;

let dropdownTimer: NodeJS.Timeout | null = null;
let lockedScrollTop = 0;
let themeTransitionTimer: ReturnType<typeof setTimeout> | null = null;
let sessionExpireTimer: ReturnType<typeof setTimeout> | null = null;
let userInfoRequest: Promise<void> | null = null;

const isEditMode = ref(false);

const formData = reactive({
  username: '',
  phone: '',
  gender: '' as UserInfoResponse['data']['gender'] | '',
  birthday: ''
});
const initialFormData = reactive({
  username: '',
  phone: '',
  gender: '' as UserInfoResponse['data']['gender'] | '',
  birthday: ''
});
const formRef = ref<any>(null);
const emailValue = ref('');
const registerTime = ref('2023-05-15 09:23:45');

const formRules = computed(() => ({
  username: [
    { required: true, message: t('profile.usernameRequired'), trigger: 'blur' },
    { min: 2, max: 20, message: t('profile.usernameLength'), trigger: 'blur' },
    {
      validator: async (rule: any, value: string, callback: any) => {
        if (!value || value.trim() === '') { callback(); return; }
        if (value.trim() === realTimeUsername.value) { callback(); return; }
        try {
          isCheckingUsername.value = true;
          const isValid = await checkUsernameUnique(value.trim());
          if (isValid) callback();
          else callback(new Error(t('profile.usernameTaken')));
        } catch (error: any) {
          callback(new Error(error.message || t('profile.usernameCheckFailed')));
        } finally {
          isCheckingUsername.value = false;
        }
      },
      trigger: 'blur'
    }
  ],
  phone: [
    { pattern: /^$|^1[3-9]\d{9}$/, message: t('profile.phoneInvalid'), trigger: 'blur' }
  ],
  birthday: [
    { type: 'string', pattern: /^\d{4}-\d{2}-\d{2}$|^$/, message: t('profile.dateInvalid'), trigger: 'change' }
  ]
}));

const formatGender = (gender: UserInfoResponse['data']['gender'] | '') => {
  if (gender === 'MALE') return t('profile.male');
  if (gender === 'FEMALE') return t('profile.female');
  if (gender === 'OTHER') return t('profile.other');
  if (gender === 'SECRET') return t('profile.secret');
  return t('profile.notSet');
};

const baseUserInfo = getUserInfo() || { email: '', username: '', role: 'USER' };
const cachedUserProfile = readCachedUserProfile();
const initialUserInfo = cachedUserProfile?.email && cachedUserProfile.email === baseUserInfo.email
  ? {
      email: baseUserInfo.email,
      username: cachedUserProfile.username || baseUserInfo.username,
      role: cachedUserProfile.role || baseUserInfo.role,
      avatar: cachedUserProfile.avatar || '',
    }
  : { ...baseUserInfo, avatar: '' };

const tokenInfo = ref<{ email: string; username: string; role: string; avatar?: string }>(initialUserInfo);
const realTimeUsername = ref<string | null>(null);
const hasCachedUserInfo = ref(false);

const initialAvatar = tokenInfo.value.avatar ?
  (tokenInfo.value.avatar.startsWith('/') ? `${BASE_URL || ''}${tokenInfo.value.avatar}` : tokenInfo.value.avatar)
  : null;
const realTimeAvatar = ref<string | null>(initialAvatar);

const defaultAvatarText = computed(() => {
  const email = (tokenInfo.value.email || '').trim();
  const emailPrefix = email.includes('@') ? email.split('@')[0].trim() : email;
  if (!emailPrefix) return 'U';

  const normalized = emailPrefix.replace(/[^a-zA-Z0-9]/g, '');
  const avatarText = (normalized || emailPrefix).slice(0, 2);
  return avatarText.toUpperCase();
});

const avatarColorPairs = [
  ['#4f46e5', '#06b6d4'],
  ['#2563eb', '#14b8a6'],
  ['#7c3aed', '#ec4899'],
  ['#db2777', '#f97316'],
  ['#ea580c', '#facc15'],
  ['#16a34a', '#0ea5e9'],
  ['#0891b2', '#6366f1'],
  ['#9333ea', '#3b82f6'],
  ['#c026d3', '#8b5cf6'],
  ['#0f766e', '#22c55e'],
];

const defaultAvatarStyle = computed(() => {
  const identity = tokenInfo.value.email || 'U';
  let hash = 0;
  for (let i = 0; i < identity.length; i++) {
    hash = identity.charCodeAt(i) + ((hash << 5) - hash);
  }
  const [startColor, endColor] = avatarColorPairs[Math.abs(hash) % avatarColorPairs.length];

  return {
    background: endColor,
  };
});

const themeOptions: Array<{ value: ThemeMode; labelKey: 'theme.light' | 'theme.dark' | 'theme.system' }> = [
  { value: 'light', labelKey: 'theme.light' },
  { value: 'dark', labelKey: 'theme.dark' },
  { value: 'system', labelKey: 'theme.system' },
];

const currentThemeLabel = computed(() => {
  const activeOption = themeOptions.find((option) => option.value === themeMode.value);
  return activeOption ? t(activeOption.labelKey) : t('theme.light');
});

const currentLocaleLabel = computed(() => t(currentLocaleOption.value.labelKey));
const currentLocaleShortLabel = computed(() => currentLocaleOption.value.shortLabel);

const currentPageTitle = computed(() => {
  switch (route.name) {
    case 'WeatherQuery':
      return t('page.history');
    case 'WeatherAnalysis':
      return t('page.realtime');
    case 'TemperatureChange':
      return t('page.forecast');
    case 'UserManagement':
      return t('page.userManagement');
    case 'AdminWeatherAnalysis':
      return t('page.weatherAnalysis');
    case 'AdminForecast':
      return t('page.forecastAdmin');
    case 'AdminSystemSettings':
      return t('page.systemSettings');
    default:
      return t('page.default');
  }
});

const customAvatarSrc = computed(() => {
  const avatar = previewAvatarUrl.value || realTimeAvatar.value || '';
  return typeof avatar === 'string' ? avatar.trim() : '';
});

const hasCustomAvatar = computed(() => customAvatarSrc.value !== '');

const userAvatar = computed(() => customAvatarSrc.value);
const isAuthenticated = ref(hasActiveSession());

const showNavbar = computed(() => {
  const isAdminRoute = route.path.startsWith('/admin');
  return !isAdminRoute;
});

const syncUserInfoFromToken = () => {
  const nextUserInfo = getUserInfo() || { email: '', username: '', role: 'USER' };
  tokenInfo.value = {
    email: nextUserInfo.email === '未登录' ? '' : nextUserInfo.email || '',
    username: nextUserInfo.username === '未登录用户' ? '' : nextUserInfo.username || '',
    role: nextUserInfo.role || 'USER',
    avatar: tokenInfo.value.avatar || ''
  };

  if (!tokenInfo.value.email) {
    realTimeAvatar.value = null;
    realTimeUsername.value = null;
  }
};

const resetUserDisplayToGuest = () => {
  tokenInfo.value = { email: '', username: '', role: 'USER', avatar: '' };
  realTimeAvatar.value = null;
  realTimeUsername.value = null;
  previewAvatarUrl.value = '';
  hasCachedUserInfo.value = false;
  showUserDropdown.value = false;
  showUserDetail.value = false;
  isEditMode.value = false;
  localStorage.removeItem(USER_PROFILE_CACHE_KEY);
};

const syncAuthDisplayState = () => {
  isAuthenticated.value = hasActiveSession();
  syncUserInfoFromToken();
  scheduleSessionExpiryCheck();

  if (isAuthenticated.value) {
    hasCachedUserInfo.value = false;
    fetchLatestUserInfo(true).catch(() => {});
    return;
  }

  resetUserDisplayToGuest();
};

const getSystemPrefersDark = () => {
  if (typeof window === 'undefined' || typeof window.matchMedia !== 'function') {
    return false;
  }
  return window.matchMedia('(prefers-color-scheme: dark)').matches;
};

const resolveStoredThemeMode = (): ThemeMode => {
  const savedMode = localStorage.getItem(THEME_MODE_KEY);
  if (savedMode === 'light' || savedMode === 'dark' || savedMode === 'system') {
    return savedMode;
  }
  return localStorage.getItem(LEGACY_DARK_MODE_KEY) === 'true' ? 'dark' : 'light';
};

const applyGlobalTheme = (dark: boolean) => {
  if (typeof document !== 'undefined') {
    document.documentElement.classList.add('theme-transitioning');
    document.body.classList.add('theme-transitioning');
    if (themeTransitionTimer) clearTimeout(themeTransitionTimer);
  }

  isGlobalDarkMode.value = dark;
  document.body.classList.toggle('site-dark-mode', dark);
  document.documentElement.classList.toggle('site-dark-mode', dark);
  document.documentElement.classList.toggle('dark', dark);

  if (typeof document !== 'undefined') {
    themeTransitionTimer = setTimeout(() => {
      document.documentElement.classList.remove('theme-transitioning');
      document.body.classList.remove('theme-transitioning');
    }, 320);
  }
};

const syncGlobalTheme = (preferredMode?: ThemeMode) => {
  const nextMode = preferredMode || resolveStoredThemeMode();
  themeMode.value = nextMode;
  const resolvedDark = nextMode === 'system' ? getSystemPrefersDark() : nextMode === 'dark';
  localStorage.setItem(THEME_MODE_KEY, nextMode);
  localStorage.setItem(LEGACY_DARK_MODE_KEY, String(resolvedDark));
  applyGlobalTheme(resolvedDark);
};

const dispatchThemeChange = () => {
  window.dispatchEvent(new CustomEvent('weather-theme-change', {
    detail: {
      mode: themeMode.value,
      dark: isGlobalDarkMode.value,
    },
  }));
};

const handleGlobalThemeChange = (event: Event) => {
  const customEvent = event as CustomEvent<{ dark?: boolean; mode?: ThemeMode }>;
  if (customEvent.detail?.mode === 'light' || customEvent.detail?.mode === 'dark' || customEvent.detail?.mode === 'system') {
    syncGlobalTheme(customEvent.detail.mode);
    return;
  }
  if (typeof customEvent.detail?.dark === 'boolean') {
    applyGlobalTheme(customEvent.detail.dark);
    return;
  }
  syncGlobalTheme();
};

const setThemeMode = (mode: ThemeMode) => {
  syncGlobalTheme(mode);
  showThemeMenu.value = false;
  dispatchThemeChange();
};

const handleSetLocale = (locale: AppLocale) => {
  setLocale(locale);
  showLanguageMenu.value = false;
};

const toggleLanguageMenu = () => {
  showUserDropdown.value = false;
  showThemeMenu.value = false;
  showLanguageMenu.value = !showLanguageMenu.value;
};

const toggleThemeMenu = () => {
  showUserDropdown.value = false;
  showLanguageMenu.value = false;
  showThemeMenu.value = !showThemeMenu.value;
};

const handleDocumentClick = (e: MouseEvent) => {
  const userMenu = userMenuRef.value;
  if (userMenu && !userMenu.contains(e.target as Node)) { showUserDropdown.value = false; }
  const themeMenu = themeMenuRef.value;
  if (themeMenu && !themeMenu.contains(e.target as Node)) { showThemeMenu.value = false; }
  const languageMenu = languageMenuRef.value;
  if (languageMenu && !languageMenu.contains(e.target as Node)) { showLanguageMenu.value = false; }
};

const handleSystemThemeChange = () => {
  if (themeMode.value !== 'system') return;
  syncGlobalTheme('system');
  dispatchThemeChange();
};

const fetchLatestUserInfo = async (forceRefresh = false) => {
  if (!hasActiveSession()) { redirectToLogin(true); return; }
  if (userInfoRequest) return userInfoRequest;
  if (hasCachedUserInfo.value && !forceRefresh) return;
  isLoading.value = true;

  userInfoRequest = (async () => {
    try {
      const response = await request.get<UserInfoResponse>(USER_INFO_API, { timeout: 5000 });
      if (response.data.code === 200 && response.data.data) {
        const userData = response.data.data;
        realTimeUsername.value = userData.username || tokenInfo.value.username || t('user.unknown');
        realTimeAvatar.value = userData.avatar ? (userData.avatar.startsWith('/') ? `${BASE_URL || ''}${userData.avatar}` : userData.avatar) : '';
        tokenInfo.value = { email: userData.email, username: userData.username || t('user.unknown'), role: userData.role, avatar: userData.avatar };
        persistCachedUserProfile({ email: userData.email, username: userData.username || t('user.unknown'), role: userData.role, avatar: userData.avatar || '' });
        formData.username = userData.username || ''; formData.phone = userData.phone || ''; formData.gender = userData.gender || ''; formData.birthday = userData.birthday || '';
        initialFormData.username = userData.username || ''; initialFormData.phone = userData.phone || ''; initialFormData.gender = userData.gender || ''; initialFormData.birthday = userData.birthday || '';
        emailValue.value = userData.email || t('user.unknownEmail');
        if (userData.created_at) registerTime.value = formatDateTime(userData.created_at);
        hasCachedUserInfo.value = true;
      }
    } catch (error: any) {
      console.error('获取用户信息失败:', error);
    } finally {
      isLoading.value = false;
      userInfoRequest = null;
    }
  })();

  return userInfoRequest;
};

const toggleUserDropdown = () => {
  if (!isAuthenticated.value) {
    handleOpenLogin();
    return;
  }
  showThemeMenu.value = false;
  showLanguageMenu.value = false;
  showUserDropdown.value = !showUserDropdown.value;
  if (showUserDropdown.value) fetchLatestUserInfo().catch(() => {});
};

const handleOpenLogin = () => {
  if (hasActiveSession()) {
    fetchLatestUserInfo(true).catch(() => {});
    return;
  }

  openAuthModal('login', t('auth.loginRequired'));
};

const cancelEdit = () => {
  isEditMode.value = false;
  fetchLatestUserInfo(true);
  if (previewAvatarUrl.value) URL.revokeObjectURL(previewAvatarUrl.value);
  previewAvatarUrl.value = ''; selectedFileSize.value = null; selectedAvatarFile.value = null;
};

const formatDateTime = (utcTime: string) => {
  if (!utcTime) return '';
  return new Date(utcTime).toLocaleString(currentLocale.value, { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit' }).replace(/\//g, '-');
};

const formatFileSize = (bytes: number) => {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
};

const disableFutureDate = (time: Date) => time && time > new Date();
const formatPhoneNumber = () => { formData.phone = formData.phone.replace(/\D/g, ''); };

function readCachedUserProfile() {
  try {
    const cached = localStorage.getItem(USER_PROFILE_CACHE_KEY);
    if (!cached) return null;
    const parsed = JSON.parse(cached);
    if (!parsed || typeof parsed !== 'object') return null;
    return parsed as { email?: string; username?: string; role?: string; avatar?: string };
  } catch (error) {
    return null;
  }
}

function persistCachedUserProfile(profile: { email: string; username: string; role: string; avatar?: string }) {
  localStorage.setItem(USER_PROFILE_CACHE_KEY, JSON.stringify(profile));
}

const openUserDetail = () => {
  if (!isAuthenticated.value) {
    handleOpenLogin();
    return;
  }
  if (dropdownTimer) { clearTimeout(dropdownTimer); dropdownTimer = null; }
  if (hasCachedUserInfo.value) showUserDetail.value = true;
  else fetchLatestUserInfo(true).then(() => { showUserDetail.value = true; });
};

const handleMouseEnter = () => { if (dropdownTimer) { clearTimeout(dropdownTimer); dropdownTimer = null; } };

const handleMouseLeave = () => {
  if (dropdownTimer) clearTimeout(dropdownTimer);
  if (showUserDropdown.value) { dropdownTimer = setTimeout(() => { showUserDropdown.value = false; dropdownTimer = null; }, 300); }
};

const handleGoToAdmin = () => {
  if (!hasActiveSession()) return redirectToLogin(true);
  if (checkAdminPermission()) window.open(`${window.location.origin}/admin/usermanagement`, '_blank');
  else {
    ElMessageBox.alert(t('profile.noAdmin'), t('profile.noPermission'), {
      type: 'warning',
      lockScroll: false,
      autofocus: false,
      customClass: 'minimal-alert-box'
    });
  }
  showUserDropdown.value = false;
};

const handleLogout = () => {
  ElMessageBox.confirm(t('profile.logoutConfirm'), t('profile.prompt'), {
    confirmButtonText: t('profile.confirm'),
    cancelButtonText: t('profile.cancel'),
    type: 'warning',
    lockScroll: false,
    autofocus: false,
    customClass: 'minimal-alert-box'
  }).then(() => {
      logout(); showUserDropdown.value = false; showUserDetail.value = false;
      localStorage.removeItem(USER_PROFILE_CACHE_KEY);
      tokenInfo.value = { email: '', username: '', role: 'USER', avatar: '' }; realTimeAvatar.value = null; realTimeUsername.value = null; previewAvatarUrl.value = ''; hasCachedUserInfo.value = false;
  }).catch(() => {});
};

const checkUsernameUnique = async (username: string): Promise<boolean> => {
  if (!hasActiveSession()) throw new Error(t('profile.authExpired'));
  const response = await request.post<CheckUsernameResponse>(CHECK_USERNAME_API, { username });
  return response.data.code === 200 ? response.data.data : false;
};

const triggerFileInput = () => {
  if (isEditMode.value && !isAvatarUploading.value) fileInputRef.value?.click();
};

const handleFileChange = (e: Event) => {
  const target = e.target as HTMLInputElement; const file = target.files?.[0];
  if (!file) return;
  selectedFileSize.value = file.size; selectedAvatarFile.value = file;
  if (!['image/jpeg', 'image/png'].includes(file.type)) return ElMessage.error(t('profile.avatarTypeError'));
  if (file.size > 2 * 1024 * 1024) return ElMessage.error(t('profile.avatarSizeError'));
  previewAvatarUrl.value = URL.createObjectURL(file); target.value = '';
};

const uploadAvatarFile = async (file: File) => {
  return new Promise<string>((resolve, reject) => {
    uploadProgress.value = 0; isAvatarUploading.value = true;
    const formData = new FormData(); formData.append('avatar', file);
    request.post<UploadAvatarResponse>(UPLOAD_AVATAR_API, formData, {
      timeout: 10000,
      headers: { 'Content-Type': 'multipart/form-data', 'Authorization': `Bearer ${getAccessToken()}` },
      onUploadProgress: (progressEvent) => { if (progressEvent.total) uploadProgress.value = Math.round((progressEvent.loaded / progressEvent.total) * 100); }
    }).then(response => {
      isAvatarUploading.value = false; uploadProgress.value = 100;
      if (response.data.code === 200) resolve(response.data.data.avatar_path);
      else throw new Error(response.data.message || t('profile.avatarUploadFailed'));
    }).catch(error => {
      isAvatarUploading.value = false; reject(new Error((error as any).message || t('profile.avatarUploadRetry')));
    });
  });
};

const handleSave = async () => {
  if (!formRef.value || isAvatarUploading.value) return;
  try {
    isSaving.value = true; await formRef.value.validate();
    const newUsername = formData.username.trim();
    const newPhone = formData.phone.trim();
    const hasProfileChanged =
      newUsername !== initialFormData.username ||
      newPhone !== initialFormData.phone ||
      formData.gender !== initialFormData.gender ||
      formData.birthday !== initialFormData.birthday;
    const hasAvatarChanged = !!selectedAvatarFile.value;

    if (!hasProfileChanged && !hasAvatarChanged) { ElMessage.success(t('profile.saved')); isEditMode.value = false; return; }
    if (newUsername !== realTimeUsername.value && !(await checkUsernameUnique(newUsername))) { ElMessage.error(t('profile.usernameTaken')); return; }
    if (selectedAvatarFile.value) await uploadAvatarFile(selectedAvatarFile.value);
   
    const res = await request.post<UserInfoResponse>(SAVE_USER_INFO_API, {
      username: newUsername, phone: newPhone, gender: formData.gender, birthday: formData.birthday
    }, { headers: { 'Authorization': `Bearer ${getAccessToken()}` } });
   
    if (res.data.code === 200) {
      ElMessage.success(t('profile.saved')); await fetchLatestUserInfo(true); isEditMode.value = false;
    } else { ElMessage.error(res.data.message); }
  } catch (e: any) { ElMessage.error(e.message || t('profile.saveFailed')); } finally { isSaving.value = false; }
};

watch(showUserDetail, (newVal) => {
  if (newVal) {
    lockedScrollTop = window.scrollY || document.documentElement.scrollTop || 0;
    document.body.classList.add('user-detail-lock');
    document.body.style.top = `-${lockedScrollTop}px`;
  } else {
    document.body.classList.remove('user-detail-lock');
    document.body.style.top = ''; document.body.style.paddingRight = '';
    window.scrollTo(0, lockedScrollTop);
    if (previewAvatarUrl.value) URL.revokeObjectURL(previewAvatarUrl.value);
    previewAvatarUrl.value = ''; selectedFileSize.value = null; selectedAvatarFile.value = null;
    uploadProgress.value = 0; isCheckingUsername.value = false; isEditMode.value = false;
  }
});

watch(route, () => { showUserDropdown.value = false; showThemeMenu.value = false; showLanguageMenu.value = false; showUserDetail.value = false; });

const scheduleSessionExpiryCheck = () => {
  if (sessionExpireTimer) {
    clearTimeout(sessionExpireTimer);
    sessionExpireTimer = null;
  }

  const refreshExpireTime = getRefreshTokenExpireTime();
  if (!refreshExpireTime) return;

  const delay = refreshExpireTime - Date.now();
  if (delay <= 0) {
    redirectToLogin(true, true);
    return;
  }

  sessionExpireTimer = setTimeout(() => {
    redirectToLogin(true, true);
  }, delay);
};

watch(
  () => authSessionState.version,
  syncAuthDisplayState,
  { immediate: true }
);

onMounted(() => {
  document.addEventListener('click', handleDocumentClick);
  window.addEventListener('weather-auth-change', syncAuthDisplayState);
  window.addEventListener('weather-theme-change', handleGlobalThemeChange as EventListener);
  if (typeof window !== 'undefined' && typeof window.matchMedia === 'function') {
    systemThemeMediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    if (typeof systemThemeMediaQuery.addEventListener === 'function') {
      systemThemeMediaQuery.addEventListener('change', handleSystemThemeChange);
    } else {
      systemThemeMediaQuery.addListener(handleSystemThemeChange);
    }
  }
  syncGlobalTheme();
  scheduleSessionExpiryCheck();
  if (hasActiveSession()) fetchLatestUserInfo();
});

onUnmounted(() => {
  if (previewAvatarUrl.value) URL.revokeObjectURL(previewAvatarUrl.value);
  if (dropdownTimer) clearTimeout(dropdownTimer);
  if (sessionExpireTimer) clearTimeout(sessionExpireTimer);
  document.removeEventListener('click', handleDocumentClick);
  window.removeEventListener('weather-auth-change', syncAuthDisplayState);
  window.removeEventListener('weather-theme-change', handleGlobalThemeChange as EventListener);
  if (systemThemeMediaQuery) {
    if (typeof systemThemeMediaQuery.removeEventListener === 'function') {
      systemThemeMediaQuery.removeEventListener('change', handleSystemThemeChange);
    } else {
      systemThemeMediaQuery.removeListener(handleSystemThemeChange);
    }
  }
  document.body.classList.remove('user-detail-lock');
  document.body.classList.remove('site-dark-mode');
  document.documentElement.classList.remove('site-dark-mode');
  document.documentElement.classList.remove('dark');
  document.body.style.top = ''; document.body.style.paddingRight = '';
});
</script>

<style scoped>
:global(html), :global(body) { margin: 0; padding: 0; width: 100%; max-width: 100%; height: 100%; box-sizing: border-box; overflow-x: hidden !important; overflow-y: auto !important; scrollbar-width: none; -ms-overflow-style: none; position: relative !important; }
:global(html::-webkit-scrollbar), :global(body::-webkit-scrollbar) { display: none !important; }

/* ✨ 全局样式变量规范化 */
:global(body) {
  --drawer-overlay-bg: rgba(15, 23, 42, 0.4);
  --drawer-overlay-blur: blur(4px);
  --drawer-panel-bg: #ffffff;
  --drawer-panel-border: #e5e7eb;
  --drawer-panel-shadow: -8px 0 32px rgba(0, 0, 0, 0.08);
  --drawer-section-border: #f3f4f6;
  --drawer-title-color: #111827;
  --drawer-close-color: #9ca3af;
  --drawer-close-hover-bg: #f3f4f6;
  --drawer-close-hover-color: #1f2937;
  --drawer-footer-bg: #ffffff;
}

:global(body.site-dark-mode) {
  --drawer-overlay-bg: rgba(2, 6, 23, 0.75);
  --drawer-overlay-blur: blur(8px);
  --drawer-panel-bg: #0f172a;
  --drawer-panel-border: rgba(255, 255, 255, 0.08);
  --drawer-panel-shadow: -8px 0 32px rgba(0, 0, 0, 0.6);
  --drawer-section-border: rgba(255, 255, 255, 0.08);
  --drawer-title-color: #f1f5f9;
  --drawer-close-color: #94a3b8;
  --drawer-close-hover-bg: rgba(255, 255, 255, 0.08);
  --drawer-close-hover-color: #ffffff;
  --drawer-footer-bg: #0f172a;
}

:global(body.el-popup-parent--hidden) { padding-right: 0 !important; overflow-x: auto !important; overflow-y: auto !important; }
:global(body.user-detail-lock) { position: fixed !important; overflow: hidden !important; width: 100% !important; left: 0 !important; right: 0 !important; touch-action: none !important; }

/* ================== Nav Bar 导航栏 ================== */
.nav-bar { display: flex; align-items: center; background: #ffffff; padding: 0 24px; height: 64px; width: 100%; min-width: 0; position: relative; z-index: 2500; box-sizing: border-box; overflow: visible !important; border: none; border-bottom: 1px solid transparent; box-shadow: none; transition: background-color 0.3s ease, border-color 0.3s ease; }
.nav-bar.theme-dark { background: #0f172a; border-bottom-color: rgba(255, 255, 255, 0.08); }

.system-title { margin-right: 40px; padding: 0; white-space: nowrap; display: flex; align-items: center; gap: 12px; flex-shrink: 0; cursor: pointer; }
.title-text { font-size: 18px; font-weight: 700; color: #111827; line-height: 1; transition: color 0.3s; }
.nav-bar.theme-dark .title-text { color: #f8fafc; }

.menu-container { flex: 1; overflow-x: auto; scrollbar-width: none; }
.menu-container::-webkit-scrollbar { display: none !important; }
.nav-menu { display: flex; list-style: none; margin: 0; padding: 0; min-width: max-content; gap: 8px; }
.nav-menu li { height: 64px; line-height: 64px; margin: 0; }
.nav-menu li a { color: #4b5563; text-decoration: none; display: block; padding: 0 16px; height: 100%; font-size: 15px; font-weight: 500; transition: all 0.2s ease; border-radius: 6px; }
.nav-menu li.active a { color: #111827; font-weight: 700; }
.nav-menu li:hover:not(.active) a { color: #1f2937; }
.nav-bar.theme-dark .nav-menu li a { color: #94a3b8; }
.nav-bar.theme-dark .nav-menu li.active a { color: #ffffff; text-shadow: 0 0 12px rgba(255,255,255,0.2); }
.nav-bar.theme-dark .nav-menu li:hover:not(.active) a { color: #f1f5f9; }

.label-long { display: inline; }
.label-short { display: none; }

.language-switcher { margin-left: auto; margin-right: 8px; position: relative; z-index: 2600; display: flex; align-items: center; height: 40px; }
.theme-switcher { margin-left: 0; margin-right: 12px; position: relative; z-index: 2600; display: flex; align-items: center; height: 40px; }
.user-menu { position: relative; z-index: 2600; }
.guest-entry { display: flex; align-items: center; gap: 10px; height: 40px; }
.guest-tag { display: inline-flex; align-items: center; height: 38px; line-height: 1; font-size: 13px; color: #64748b; white-space: nowrap; }
.guest-login-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  height: 38px;
  min-height: 38px;
  padding: 0 18px;
  box-sizing: border-box;
  border: 1px solid #dbe2ea;
  background: #111827;
  color: #ffffff;
  border-radius: 999px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 600;
  line-height: 1;
  white-space: nowrap;
  transition: all 0.2s ease;
}
.guest-login-btn:hover { background: #1f2937; }
.guest-login-text {
  display: inline-flex;
  align-items: center;
  height: 1em;
  line-height: 1;
  transform: translateY(0.5px);
}
.theme-toggle-btn, .language-toggle-btn { width: 38px; height: 38px; border-radius: 9999px; border: 1px solid #e5e7eb; background: #ffffff; color: #4b5563; position: relative; display: inline-flex; align-items: center; justify-content: center; cursor: pointer; transition: all 0.2s ease; padding: 0; box-sizing: border-box; line-height: 1; }
.theme-toggle-btn svg { position: absolute; inset: 0; display: block; width: 18px; height: 18px; margin: auto; transform: none; transform-origin: center; }
.language-toggle-btn { font-size: 12px; font-weight: 700; letter-spacing: -0.02em; }
.theme-toggle-btn:hover, .language-toggle-btn:hover { background: #f3f4f6; color: #111827; }
.nav-bar.theme-dark .theme-toggle-btn, .nav-bar.theme-dark .language-toggle-btn { border-color: rgba(255, 255, 255, 0.12); background: rgba(255, 255, 255, 0.04); color: #94a3b8; }
.nav-bar.theme-dark .theme-toggle-btn:hover, .nav-bar.theme-dark .language-toggle-btn:hover { background: rgba(255, 255, 255, 0.08); color: #ffffff; }
.theme-mode-menu, .language-mode-menu {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  min-width: 132px;
  padding: 6px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  border-radius: 12px;
  border: 1px solid #f3f4f6;
  background: #ffffff;
  box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.05);
}
.language-mode-menu { min-width: 118px; }
.theme-mode-item, .language-mode-item {
  width: 100%;
  min-height: 40px;
  border: none;
  background: transparent;
  color: #4b5563;
  text-align: left;
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  line-height: 1.2;
  transition: all 0.2s ease;
}
.theme-mode-item:hover, .language-mode-item:hover {
  background: #f3f4f6;
  color: #111827;
}
.theme-mode-item.active, .language-mode-item.active {
  background: #f3f4f6;
  color: #111827;
}
.nav-bar.theme-dark .theme-mode-menu, .nav-bar.theme-dark .language-mode-menu { background: #1e293b; border-color: rgba(255, 255, 255, 0.1); box-shadow: 0 20px 40px -10px rgba(0, 0, 0, 0.6); }
.nav-bar.theme-dark .theme-mode-item, .nav-bar.theme-dark .language-mode-item { color: #cbd5e1; }
.nav-bar.theme-dark .theme-mode-item:hover,
.nav-bar.theme-dark .theme-mode-item.active,
.nav-bar.theme-dark .language-mode-item:hover,
.nav-bar.theme-dark .language-mode-item.active { background: rgba(255, 255, 255, 0.06); color: #ffffff; }
.nav-bar.theme-dark .guest-tag { color: #94a3b8; }
.nav-bar.theme-dark .guest-login-btn {
  background: #e2e8f0;
  border-color: rgba(255, 255, 255, 0.1);
  color: #0f172a;
}
.nav-bar.theme-dark .guest-login-btn:hover { background: #f8fafc; }

.user-email { display: flex; align-items: center; gap: 8px; padding: 4px 12px 4px 5px; height: 40px; border-radius: 20px; color: #374151; cursor: pointer; transition: background-color 0.2s ease; }
.user-email:hover { background: #f3f4f6; }
.nav-bar.theme-dark .user-email { color: #e2e8f0; }
.nav-bar.theme-dark .user-email:hover { background: rgba(255, 255, 255, 0.08); }
.mini-avatar {
  width: 31px;
  height: 31px;
  min-width: 31px;
  border-radius: 9999px;
  overflow: hidden;
  object-fit: cover;
  background: transparent;
  display: block;
  flex-shrink: 0;
  aspect-ratio: 1 / 1;
}
.fallback-avatar {
  border-radius: 9999px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #ffffff;
  font-weight: 700;
  user-select: none;
  line-height: 1;
}
.fallback-avatar--nav {
  font-size: 12px;
  letter-spacing: 0.02em;
}
.fallback-avatar--panel {
  width: 100%;
  height: 100%;
  font-size: 30px;
  letter-spacing: 0.02em;
}
.email-text { max-width: 160px; overflow: hidden; text-overflow: ellipsis; font-size: 14px; font-weight: 500; }
.arrow-icon { color: #6b7280; transition: transform 0.2s; }
.nav-bar.theme-dark .arrow-icon { color: #94a3b8; }
.arrow-icon.rotated { transform: rotate(180deg); }

/* 下拉菜单深色适配 */
.user-dropdown { position: absolute; top: calc(100% + 4px); right: 0; width: 240px; background-color: #ffffff; border-radius: 12px; border: 1px solid #f3f4f6; box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.05); padding: 6px; z-index: 2601; transition: all 0.3s ease;}
.dropdown-item { padding: 10px 16px; color: #4b5563; cursor: pointer; font-size: 14px; margin: 2px 0; border-radius: 8px; transition: all 0.2s; font-weight: 500; }
.dropdown-item:hover { background-color: #f3f4f6; color: #111827; }
.nav-bar.theme-dark .user-dropdown { background-color: #1e293b; border-color: rgba(255, 255, 255, 0.1); box-shadow: 0 20px 40px -10px rgba(0, 0, 0, 0.6); }
.nav-bar.theme-dark .dropdown-item { color: #cbd5e1; }
.nav-bar.theme-dark .dropdown-item:hover { background-color: rgba(255, 255, 255, 0.06); color: #ffffff; }

/* ================== Drawer 抽屉面板 ================== */
.drawer-enter-active, .drawer-leave-active { transition: opacity 0.3s ease; }
.drawer-enter-active .drawer-panel, .drawer-leave-active .drawer-panel { transition: transform 0.3s cubic-bezier(0.2, 0.8, 0.2, 1); }
.drawer-enter-from, .drawer-leave-to { opacity: 0; }
.drawer-enter-from .drawer-panel, .drawer-leave-to .drawer-panel { transform: translateX(100%); }

.drawer-overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0; width: 100%; height: 100%; background-color: var(--drawer-overlay-bg); backdrop-filter: var(--drawer-overlay-blur); -webkit-backdrop-filter: var(--drawer-overlay-blur); z-index: 3000; display: flex; justify-content: flex-end; }
.drawer-panel { width: 100%; max-width: 400px; height: 100%; background-color: var(--drawer-panel-bg); box-shadow: var(--drawer-panel-shadow); display: flex; flex-direction: column; border-left: 1px solid var(--drawer-panel-border); }

.drawer-header { padding: 20px 24px; border-bottom: 1px solid var(--drawer-section-border); display: flex; justify-content: space-between; align-items: center; flex-shrink: 0; }
.drawer-header h3 { margin: 0; font-size: 18px; font-weight: 600; color: var(--drawer-title-color); }
.drawer-close-btn { background: transparent; border: none; color: var(--drawer-close-color); cursor: pointer; padding: 6px; border-radius: 8px; display: flex; transition: all 0.2s; outline: none; }
.drawer-close-btn:hover { background: var(--drawer-close-hover-bg); color: var(--drawer-close-hover-color); }

.drawer-body { flex: 1; overflow-y: auto; padding: 28px 24px; scrollbar-width: none; }
.drawer-body::-webkit-scrollbar { display: none; }

.drawer-profile-top { display: flex; flex-direction: column; align-items: center; margin-bottom: 36px; }
.avatar-interactive-wrapper { width: 88px; height: 88px; border-radius: 50%; position: relative; overflow: hidden; border: 1px solid #e5e7eb; background: #f9fafb; transition: all 0.2s; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }
.avatar-interactive-wrapper.editable { cursor: pointer; }
.interactive-avatar { width: 100%; height: 100%; object-fit: cover; }
.avatar-hover-mask { position: absolute; inset: 0; background: rgba(0, 0, 0, 0.5); color: white; display: flex; flex-direction: column; justify-content: center; align-items: center; opacity: 0; transition: opacity 0.2s; backdrop-filter: blur(2px); }
.avatar-interactive-wrapper.editable:hover:not(.is-uploading) .avatar-hover-mask { opacity: 1; }
.avatar-hover-mask span { font-size: 12px; margin-top: 4px; font-weight: 500; }
.avatar-loading-mask { position: absolute; inset: 0; background: rgba(0,0,0,0.6); color: #fff; display: flex; justify-content: center; align-items: center; font-size: 14px; font-weight: 600; }
.file-input { display: none; }

.user-static-info { text-align: center; margin-top: 16px; }
.static-email { font-size: 16px; color: #1f2937; font-weight: 600; line-height: 1.2; }
.static-time { font-size: 12px; color: #9ca3af; margin-top: 6px; }

:global(body.site-dark-mode .avatar-interactive-wrapper) {
  border-color: rgba(255, 255, 255, 0.1);
  background: #1e293b;
  box-shadow: 0 4px 16px rgba(0,0,0,0.3);
}
:global(body.site-dark-mode .static-email) { color: #f8fafc; }
:global(body.site-dark-mode .static-time) { color: #64748b; }

/* 状态 1: 名片展示模式 */
.profile-view-mode { display: flex; flex-direction: column; gap: 20px; padding: 8px 4px; }
.info-row { display: flex; flex-direction: column; gap: 6px; padding-bottom: 16px; border-bottom: 1px solid #f3f4f6; }
.info-row:last-child { border-bottom: none; padding-bottom: 0; }
.info-label { font-size: 13px; color: #6b7280; font-weight: 500; }
.info-value { font-size: 15px; color: #111827; font-weight: 600; word-break: break-all; }
:global(body.site-dark-mode .info-row) { border-bottom-color: rgba(255, 255, 255, 0.06); }
:global(body.site-dark-mode .info-label) { color: #64748b; }
:global(body.site-dark-mode .info-value) { color: #e2e8f0; }

/* 状态 2: 编辑表单模式 */
:deep(.modern-edit-form .el-form-item) { margin-bottom: 24px; }
:deep(.modern-edit-form .el-form-item__label) { padding-bottom: 6px; font-size: 13px; color: #4b5563; font-weight: 500; line-height: 1; }
:deep(.modern-edit-form .el-input__wrapper),
:deep(.modern-edit-form .el-select__wrapper) { border-color: #e5e7eb !important; background-color: rgba(255, 255, 255, 0.92) !important; border-radius: 10px !important; padding: 4px 12px; overflow: hidden !important; box-shadow: none !important; transition: border-color 0.2s ease, box-shadow 0.2s ease, background-color 0.2s ease !important; }
:deep(.modern-edit-form .el-input__wrapper:hover),
:deep(.modern-edit-form .el-select__wrapper:hover) { border-color: rgba(148, 163, 184, 0.4) !important; background-color: rgba(255, 255, 255, 0.98) !important; }
:deep(.modern-edit-form .el-input__wrapper.is-focus),
:deep(.modern-edit-form .el-select__wrapper.is-focused) { border-color: transparent !important; background-color: rgba(255, 255, 255, 0.98) !important; box-shadow: inset 0 0 0 1px rgba(100, 116, 139, 0.34), 0 0 0 3px rgba(100, 116, 139, 0.08) !important; }
:deep(.modern-edit-form .el-input__inner),
:deep(.modern-edit-form .el-select__placeholder) { font-size: 15px; color: #111827; font-weight: 600; }
:deep(.modern-edit-form .el-form-item.is-error .el-input__wrapper),
:deep(.modern-edit-form .el-form-item.is-error .el-select__wrapper) { border-color: transparent !important; background-color: rgba(255, 255, 255, 0.98) !important; box-shadow: inset 0 0 0 1px rgba(251, 146, 160, 0.34), 0 0 0 3px rgba(251, 146, 160, 0.08) !important; }
:deep(.modern-edit-form .el-form-item__error) { color: #e11d48; font-size: 12px; padding-top: 4px; font-weight: 500; }
:deep(.modern-edit-form .el-input__count-inner) { background: transparent; color: #9ca3af; font-size: 12px; font-weight: 400; }

/* 表单框 - 深色模式 */
:global(body.site-dark-mode .modern-edit-form .el-form-item__label) { color: #94a3b8 !important; }
:global(body.site-dark-mode .modern-edit-form .el-input__wrapper),
:global(body.site-dark-mode .modern-edit-form .el-select__wrapper) { border-color: rgba(255, 255, 255, 0.12) !important; background-color: rgba(15, 23, 42, 0.4) !important; border-radius: 10px !important; overflow: hidden !important; transition: border-color 0.2s ease, box-shadow 0.2s ease, background-color 0.2s ease !important; }
:global(body.site-dark-mode .modern-edit-form .el-input__wrapper:hover),
:global(body.site-dark-mode .modern-edit-form .el-select__wrapper:hover) { border-color: rgba(255, 255, 255, 0.25) !important; background-color: rgba(15, 23, 42, 0.62) !important; }
:global(body.site-dark-mode .modern-edit-form .el-input__wrapper.is-focus),
:global(body.site-dark-mode .modern-edit-form .el-select__wrapper.is-focused) { border-color: transparent !important; background-color: rgba(15, 23, 42, 0.78) !important; box-shadow: inset 0 0 0 1px rgba(148, 163, 184, 0.34), 0 0 0 3px rgba(148, 163, 184, 0.06) !important; }
:global(body.site-dark-mode .modern-edit-form .el-form-item.is-error .el-input__wrapper),
:global(body.site-dark-mode .modern-edit-form .el-form-item.is-error .el-select__wrapper) { border-color: transparent !important; background-color: rgba(15, 23, 42, 0.78) !important; box-shadow: inset 0 0 0 1px rgba(251, 146, 160, 0.34), 0 0 0 3px rgba(251, 146, 160, 0.06) !important; }
:global(body.site-dark-mode .modern-edit-form .el-form-item__error) { color: rgba(251, 191, 188, 0.92) !important; }
:global(body.site-dark-mode .modern-edit-form .el-input__inner),
:global(body.site-dark-mode .modern-edit-form .el-select__placeholder),
:global(body.site-dark-mode .modern-edit-form .el-select__selected-item),
:global(body.site-dark-mode .modern-edit-form .el-textarea__inner) { color: #f8fafc !important; }
:global(body.site-dark-mode .modern-edit-form .el-input__icon),
:global(body.site-dark-mode .modern-edit-form .el-input__prefix),
:global(body.site-dark-mode .modern-edit-form .el-input__suffix),
:global(body.site-dark-mode .modern-edit-form .el-select__caret),
:global(body.site-dark-mode .modern-edit-form .el-date-editor .el-range__icon) { color: #64748b !important; }
:global(body.site-dark-mode .modern-edit-form .el-input__inner::placeholder) { color: #64748b !important; -webkit-text-fill-color: #64748b !important; }
:global(body.site-dark-mode .modern-edit-form .el-input__count-inner) { color: #64748b !important; background: transparent !important; box-shadow: none !important; }

/* 修复下拉框层级 */
:global(.el-select__popper),
:global(.el-picker__popper),
:global(.el-popper.is-pure),
:global(.el-select-dropdown),
:global(.el-date-picker),
:global(.el-picker-panel) { z-index: 3200 !important; }

/* ================== ✨ Element Plus 浮层深色模式强力适配 ✨ ================== */
/* 面板主背景 */
:global(body.site-dark-mode .el-popper),
:global(body.site-dark-mode .el-select-dropdown),
:global(body.site-dark-mode .el-picker-panel),
:global(body.site-dark-mode .el-popper.is-light) {
  background-color: #1e293b !important;
  border-color: rgba(255, 255, 255, 0.1) !important;
  box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5) !important;
}

/* 弹出框小箭头 */
:global(body.site-dark-mode .el-popper.is-light .el-popper__arrow::before) {
  background-color: #1e293b !important;
  border-color: rgba(255, 255, 255, 0.1) !important;
}

/* -- Select 下拉选项 -- */
:global(body.site-dark-mode .el-select-dropdown__item) {
  color: #cbd5e1 !important;
  background-color: transparent !important;
}
:global(body.site-dark-mode .el-select-dropdown__item.hover),
:global(body.site-dark-mode .el-select-dropdown__item:hover) {
  background-color: rgba(255, 255, 255, 0.06) !important;
  color: #ffffff !important;
}
:global(body.site-dark-mode .el-select-dropdown__item.selected),
:global(body.site-dark-mode .el-select-dropdown__item.is-selected) {
  background-color: rgba(59, 130, 246, 0.15) !important; 
  color: #3b82f6 !important; 
  font-weight: bold !important;
}

/* -- Date Picker 日期面板 -- */
:global(body.site-dark-mode .el-date-picker__header-label),
:global(body.site-dark-mode .el-date-table th),
:global(body.site-dark-mode .el-date-table td .el-date-table-cell__text),
:global(body.site-dark-mode .el-picker-panel__icon-btn) {
  color: #cbd5e1 !important;
}
:global(body.site-dark-mode .el-picker-panel__icon-btn:hover) {
  color: #ffffff !important;
}
:global(body.site-dark-mode .el-date-table td.available:hover) {
  color: #3b82f6 !important;
}
:global(body.site-dark-mode .el-date-table td.current .el-date-table-cell__text) {
  background-color: #3b82f6 !important;
  color: white !important;
}
:global(body.site-dark-mode .el-date-table td.next-month .el-date-table-cell__text),
:global(body.site-dark-mode .el-date-table td.prev-month .el-date-table-cell__text) {
  color: #475569 !important;
}
:global(body.site-dark-mode .el-date-table td.disabled .el-date-table-cell__text) {
  background-color: rgba(255,255,255,0.04) !important;
  color: #334155 !important;
}
:global(body.site-dark-mode .el-date-picker__header) {
  border-bottom-color: rgba(255, 255, 255, 0.06) !important;
}

/* ================== 底部操作按钮 ================== */
.drawer-footer { padding: 20px 24px; border-top: 1px solid var(--drawer-section-border); display: flex; gap: 12px; flex-shrink: 0; background: var(--drawer-footer-bg); }
.drawer-edit-btn { width: 100%; height: 44px; border-radius: 8px; font-size: 15px; font-weight: 600; background-color: #111827; border: none; transition: background-color 0.2s; color: white; }
.drawer-edit-btn:hover { background-color: #374151; }
.drawer-cancel-btn, .drawer-save-btn { flex: 1; height: 44px; border-radius: 8px; font-size: 14px; font-weight: 600; transition: all 0.2s ease; }
.drawer-cancel-btn { border: 1px solid #e5e7eb; color: #4b5563; background: #ffffff; }
.drawer-cancel-btn:hover { background: #f9fafb; color: #111827; border-color: #d1d5db; }
.drawer-save-btn { background-color: #2563eb; border: none; color: white; }
.drawer-save-btn:hover:not(:disabled) { background-color: #1d4ed8; }

/* ✨ 深色模式：高级深邃按钮适配 ✨ */
:global(body.site-dark-mode .drawer-edit-btn) { background-color: #1e293b; color: #f8fafc; border: 1px solid rgba(255,255,255,0.1); box-shadow: 0 4px 12px rgba(0,0,0,0.2); }
:global(body.site-dark-mode .drawer-edit-btn:hover) { background-color: #334155; }

:global(body.site-dark-mode .drawer-cancel-btn) { border-color: rgba(255, 255, 255, 0.1); background: transparent; color: #94a3b8; }
:global(body.site-dark-mode .drawer-cancel-btn:hover) { background: rgba(255, 255, 255, 0.06); color: #f8fafc; }

/* 深色模式下改成更简洁的纯色按钮 */
:global(body.site-dark-mode .drawer-save-btn) { 
  background: #334155; 
  color: #f8fafc; 
  border: 1px solid rgba(71, 85, 105, 0.95);
  box-shadow: none; 
}
:global(body.site-dark-mode .drawer-save-btn:hover:not(:disabled)) { 
  background: #475569; 
  border-color: rgba(100, 116, 139, 0.95);
  box-shadow: none; 
}
:global(body.site-dark-mode .drawer-save-btn:active:not(:disabled)) {
  background: #1e293b;
  border-color: rgba(51, 65, 85, 0.95);
  box-shadow: none;
}

/* 响应式调整 */
@media (max-width: 1350px) { .label-long { display: none; } .label-short { display: inline; } .nav-menu li a { font-size: 14px; padding: 0 12px; } }
@media (max-width: 900px) {
  .nav-bar { padding: 0 12px; gap: 8px; }
  .system-title { margin-right: 12px; }
  .title-text { font-size: 16px; }
  .menu-container { min-width: 0; }
  .nav-menu { gap: 4px; }
  .nav-menu li a { padding: 0 10px; font-size: 13px; }
  .theme-toggle-btn { margin-right: 8px; width: 36px; height: 36px; }
  .user-email { padding-right: 8px; }
  .email-text { display: none; }
}

@media (max-width: 599px) {
  .nav-bar { min-width: 600px; }
}
</style>
