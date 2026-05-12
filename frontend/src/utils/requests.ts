// 1. 导入必要依赖
import axios from 'axios';
import type { InternalAxiosRequestConfig, AxiosError } from 'axios';
import { BASE_URL } from '@/store/config';
import { ElMessage, ElMessageBox } from 'element-plus';
import router from '@/router';
import { openAuthModal } from './authModal';
import { checkRefreshTokenValid, checkTokenValid, notifyAuthChanged } from './auth';
import { clearGuestToken, getGuestToken, setGuestToken, shouldUseGuestToken, syncGuestQuotaFromHeaders } from './guestQuota';
import { clearSessionSignKey, generateGuestSignedHeaders, generateSessionSignedHeaders, generateSignedHeaders, getGuestSignKey, getSessionSignKey, setSessionSignKey } from './signature';
import { clearAccessToken, getAccessToken, setAccessToken } from './tokenStorage';
import { t } from './i18n';

// 2. 创建axios实例
const request = axios.create({
  baseURL: BASE_URL,
  timeout: 5000,
  withCredentials: true,
  headers: { 'Content-Type': 'application/json;charset=utf-8' }
});

// 3. 全局状态（防止重复弹窗）
let isHandlingAuthError = false;
let disableAuthModal = false;
let refreshTokenTask: Promise<string | null> | null = null;
let guestTokenTask: Promise<string | null> | null = null;
let lastSessionReplacedHandledAt = 0;
const SESSION_REPLACED_NOTICE_INTERVAL = 2000;

interface RetriableRequestConfig extends InternalAxiosRequestConfig {
  _retry?: boolean;
  _guestRetry?: boolean;
}

const readHeader = (headers: any, key: string) => {
  if (!headers) return undefined;
  if (typeof headers.get === 'function') return headers.get(key);
  const headerKey = Object.keys(headers).find((item) => item.toLowerCase() === key.toLowerCase());
  return headerKey ? headers[headerKey] : undefined;
};

const writeHeaders = (headers: any, nextHeaders: Record<string, string>) => {
  Object.entries(nextHeaders).forEach(([key, value]) => {
    if (typeof headers.set === 'function') {
      headers.set(key, value);
    } else {
      headers[key] = value;
    }
  });
};

const deleteHeader = (headers: any, key: string) => {
  if (!headers) return;
  if (typeof headers.delete === 'function') {
    headers.delete(key);
    return;
  }
  const headerKey = Object.keys(headers).find((item) => item.toLowerCase() === key.toLowerCase());
  if (headerKey) delete headers[headerKey];
};

const getSignParamsFromConfig = (config: RetriableRequestConfig) => {
  const params: Record<string, string | number> = {};
  const [, queryString = ''] = (config.url || '').split('?');

  if (queryString) {
    new URLSearchParams(queryString).forEach((value, key) => {
      params[key] = value;
    });
  }

  if (config.params && typeof config.params === 'object') {
    Object.entries(config.params as Record<string, unknown>).forEach(([key, value]) => {
      if (typeof value === 'string' || typeof value === 'number') {
        params[key] = value;
      }
    });
  }

  return params;
};

const refreshSignedHeadersForRetry = (config: RetriableRequestConfig) => {
  if (!readHeader(config.headers, 'X-Sign')) return;
  const hasAuthToken = !!readHeader(config.headers, 'Authorization');
  const hasGuestToken = !!readHeader(config.headers, 'X-Guest-Token');
  writeHeaders(
    config.headers,
    hasAuthToken
      ? generateSessionSignedHeaders(getSignParamsFromConfig(config))
      : hasGuestToken
        ? generateGuestSignedHeaders(getSignParamsFromConfig(config))
      : generateSignedHeaders(getSignParamsFromConfig(config))
  );
};

const retryWithFreshAccessToken = async (config: RetriableRequestConfig | undefined) => {
  if (!config || config._retry || !checkRefreshTokenValid()) return null;

  config._retry = true;
  const nextToken = await refreshAccessToken();
  if (!nextToken) return null;

  config.headers.Authorization = `Bearer ${nextToken}`;
  refreshSignedHeadersForRetry(config);
  return request(config);
};

// 检查Token有效性
export const hasValidToken = () => {
  const token = getAccessToken();
  return !!token && token.trim() !== '';
};

// 跳转登录页（根据场景携带不同参数）
export const redirectToLogin = (withRedirect = false, isExpired = false) => {
  disableAuthModal = true;
  clearAccessToken();
  localStorage.removeItem('user');
  clearSessionSignKey();
  notifyAuthChanged();

  if (withRedirect && router.currentRoute.value.path.startsWith('/admin')) {
    router.push('/weather').finally(() => {
      openAuthModal('login', isExpired ? t('auth.expiredRelogin') : t('auth.loginFirst'));
      setTimeout(() => { disableAuthModal = false; }, 100);
    });
    return;
  }

  openAuthModal('login', isExpired ? t('auth.expiredRelogin') : t('auth.loginFirst'));
  setTimeout(() => { disableAuthModal = false; }, 100);
};

const refreshAccessToken = async () => {
  if (!refreshTokenTask) {
    refreshTokenTask = axios.post(`${BASE_URL}/weather/user/refresh/`, {}, {
      headers: { 'Content-Type': 'application/json' },
      withCredentials: true,
      timeout: 8000
    }).then((response) => {
      const nextToken = response.data?.data?.access_token || response.data?.data?.token;
      if (!nextToken) return null;
      setAccessToken(nextToken);
      setSessionSignKey(response.data?.data?.sign_key);
      notifyAuthChanged();
      return nextToken as string;
    }).catch((error: AxiosError) => {
      const responseData = error.response?.data as Record<string, any> | undefined;
      if (error.response?.status === 401 && responseData?.code === 4017) {
        clearAccessToken();
        clearSessionSignKey();
        notifyAuthChanged();
        openAuthModal('login', `${responseData?.message || t('auth.sessionReplaced')}。${t('auth.sessionReplacedLoginAgain')}`);
      }
      return null;
    }).finally(() => {
      refreshTokenTask = null;
    });
  }

  return refreshTokenTask;
};

export const restoreSessionFromCookie = async () => refreshAccessToken();

export const ensureFreshAccessToken = async () => {
  const token = getAccessToken();
  if (checkTokenValid() && getSessionSignKey()) return token;
  if (!checkRefreshTokenValid()) return null;
  return refreshAccessToken();
};

const ensureGuestToken = async () => {
  const existingToken = getGuestToken();
  if (existingToken && getGuestSignKey()) return existingToken;
  if (existingToken) clearGuestToken();

  if (!guestTokenTask) {
    guestTokenTask = axios.post(`${BASE_URL}/weather/user/guest-token/`, {}, {
      headers: {
        'Content-Type': 'application/json',
        ...generateSignedHeaders()
      },
      withCredentials: true,
      timeout: 8000
    }).then((response) => {
      const nextToken = response.headers?.['x-guest-token'] || response.data?.data?.guest_token;
      const signKey = response.data?.data?.sign_key;
      if (!nextToken) return null;
      setGuestToken(nextToken, signKey);
      return nextToken as string;
    }).catch(() => null).finally(() => {
      guestTokenTask = null;
    });
  }

  return guestTokenTask;
};

// 4. 请求拦截器（保持不变）
request.interceptors.request.use(
  async (config: InternalAxiosRequestConfig) => {
    const token = getAccessToken();
    if (token) {
      const accessToken = await ensureFreshAccessToken();
      if (accessToken) {
        config.headers.Authorization = `Bearer ${accessToken}`;
      }
    } else if (!shouldUseGuestToken(config.url)) {
      const accessToken = await ensureFreshAccessToken();
      if (accessToken) {
        config.headers.Authorization = `Bearer ${accessToken}`;
      } else {
        clearSessionSignKey();
      }
    } else {
      clearSessionSignKey();
    }

    if (!readHeader(config.headers, 'Authorization') && shouldUseGuestToken(config.url)) {
      const guestToken = await ensureGuestToken();
      if (guestToken) config.headers['X-Guest-Token'] = guestToken;
    } else if (shouldUseGuestToken(config.url)) {
      delete config.headers['X-Guest-Token'];
    }

    if (readHeader(config.headers, 'X-Sign')) {
      refreshSignedHeadersForRetry(config as RetriableRequestConfig);
    }
    return config;
  },
  (error: AxiosError) => {
    console.error('请求拦截器错误:', error.message);
    return Promise.reject(error);
  }
);

// 5. 响应拦截器（核心：区分封禁和过期）
request.interceptors.response.use(
  (response) => {
    syncGuestQuotaFromHeaders(response.headers as Record<string, any>);
    return response;
  },
  async (error: AxiosError) => {
    // 过滤请求中止错误（组件卸载导致）
    if (error.name === 'AbortError' || 
        error.message?.includes('aborted') || 
        error.message?.includes('canceled')) {
      console.log('请求已中止（组件卸载）:', error.message);
      return new Promise(() => {}); // 静默处理，不抛出错误
    }

    if (!error.response) {
      ElMessage.error(t('request.networkError'));
      return Promise.reject(error);
    }

    const status = error.response.status;
    const responseData = error.response.data as Record<string, any>;
    syncGuestQuotaFromHeaders(error.response.headers as Record<string, any>);
    const code = responseData?.code || status; // 优先使用后端code
    const message = responseData?.message || t('request.operationFailed');
    const originalConfig = error.config as RetriableRequestConfig | undefined;

    // 场景1：账号封禁（code=4011，后端明确标记）
    if (status === 401 && code === 4011) {
      if (disableAuthModal || isHandlingAuthError) {
        return Promise.reject(error);
      }
      isHandlingAuthError = true;

      // 显示封禁提示（错误弹窗，不可关闭）
      ElMessageBox.alert(
        message || t('request.accountBanned'),
        t('request.accountException'),
        {
          confirmButtonText: t('profile.confirm'),
          type: 'error',
          showClose: false,
          closeOnClickModal: false,
          closeOnPressEscape: false,
          autofocus: false,
          customClass: 'minimal-alert-box'
        }
      ).then(() => {
        // 跳转登录页（不带过期标记）
        redirectToLogin(false, false);
      }).finally(() => {
        isHandlingAuthError = false;
      });

      return Promise.reject(error);
    }

    // 场景2：登录过期（code=4012，后端明确标记）
    if (status === 401 && code === 4012) {
      const retryResponse = await retryWithFreshAccessToken(originalConfig);
      if (retryResponse) return retryResponse;

      if (disableAuthModal || isHandlingAuthError) {
        return Promise.reject(error);
      }
      isHandlingAuthError = true;

      // 显示过期提示（警告弹窗）
      ElMessageBox.alert(
        t('auth.expiredRelogin'),
        t('profile.prompt'),
        {
          confirmButtonText: t('profile.confirm'),
          type: 'warning',
          showClose: false,
          closeOnClickModal: false,
          closeOnPressEscape: false,
          autofocus: false,
          customClass: 'minimal-alert-box'
        }
      ).then(() => {
        // 跳转登录页（带过期标记和重定向）
        redirectToLogin(true, true);
      }).finally(() => {
        isHandlingAuthError = false;
      });

      return Promise.reject(error);
    }

    if (status === 401 && code === 4015) {
      redirectToLogin(true, true);
      return Promise.reject(error);
    }

    if (status === 401 && code === 4017) {
      clearAccessToken();
      clearSessionSignKey();
      notifyAuthChanged();

      const now = Date.now();
      if (now - lastSessionReplacedHandledAt < SESSION_REPLACED_NOTICE_INTERVAL) {
        return Promise.reject(error);
      }
      lastSessionReplacedHandledAt = now;

      const sessionReplacedMessage = message || t('auth.sessionReplaced');
      ElMessage.warning(sessionReplacedMessage);
      openAuthModal('login', `${sessionReplacedMessage}。${t('auth.sessionReplacedLoginAgain')}`);

      return Promise.reject(error);
    }

    if (status === 401 && code === 4016) {
      if (originalConfig && !originalConfig._guestRetry) {
        originalConfig._guestRetry = true;
        clearGuestToken();
        const nextGuestToken = await ensureGuestToken();
        if (nextGuestToken) {
          originalConfig.headers['X-Guest-Token'] = nextGuestToken;
          refreshSignedHeadersForRetry(originalConfig);
          return request(originalConfig);
        }
      }
      return Promise.reject(error);
    }

    // 场景3：其他401错误（未登录、Token无效等）
    if (status === 401) {
      const retryResponse = await retryWithFreshAccessToken(originalConfig);
      if (retryResponse) return retryResponse;

      ElMessage.error(message);
      redirectToLogin(true, false);
      return Promise.reject(error);
    }

    // 其他状态码处理（保持不变）
    const errorMap: Record<number, string> = {
      400: t('request.badRequest'),
      403: t('request.forbidden'),
      404: t('request.notFound'),
      500: t('request.serverError')
    };
    const errorMessage = responseData?.message || errorMap[status] || `${t('request.failedWithStatus')}（${status}）`;
    ElMessage.error(errorMessage);
    
    return Promise.reject(error);
  }
);

export default request;
