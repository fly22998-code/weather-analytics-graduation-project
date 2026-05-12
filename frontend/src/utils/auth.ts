import { ElMessage, ElMessageBox } from 'element-plus';
import router from '@/router';
import { reactive } from 'vue';
import { openAuthModal } from './authModal';
import { BASE_URL } from '@/store/config';
import { clearSessionSignKey } from './signature';
import { clearAccessToken, getAccessToken } from './tokenStorage';
import { t } from './i18n';

// 状态管理（全局唯一状态）
export const authState = {
  isProcessing: false, // 防止弹窗重复触发的锁
  needShowExpiredAlert: false // 是否需要显示过期提示
};

export const authSessionState = reactive({
  version: 0
});

export const notifyAuthChanged = () => {
  authSessionState.version += 1;
  if (typeof window !== 'undefined') {
    window.dispatchEvent(new CustomEvent('weather-auth-change'));
  }
};

/**
 * 解析 JWT Token 的 Payload 部分
 */
const parseTokenPayload = (): Record<string, any> | null => {
  try {
    const token = getAccessToken();
    if (!token) return null;

    // JWT结构：header.payload.signature，提取payload
    const payloadBase64 = token.split('.')[1];
    if (!payloadBase64) return null;

    // 处理Base64填充问题
    const paddedPayload = payloadBase64.padEnd(
      payloadBase64.length + (4 - (payloadBase64.length % 4)) % 4,
      '='
    );

    // 解码并解析JSON
    const decoded = atob(paddedPayload);
    return JSON.parse(decoded);
  } catch (error) {
    console.error('Token解析失败:', error);
    return null;
  }
};

const parseRawTokenPayload = (token: string): Record<string, any> | null => {
  try {
    const payloadBase64 = token.split('.')[1];
    if (!payloadBase64) return null;
    const paddedPayload = payloadBase64.padEnd(
      payloadBase64.length + (4 - (payloadBase64.length % 4)) % 4,
      '='
    );
    return JSON.parse(atob(paddedPayload));
  } catch {
    return null;
  }
};

export const getRefreshTokenExpireTime = (): number | null => {
  return null;
};

export const checkRefreshTokenValid = (): boolean => {
  return true;
};

/**
 * 检查Token是否有效（未过期且格式正确）
 */
export const checkTokenValid = (): boolean => {
  const payload = parseTokenPayload();
  if (!payload) return false;

  // 校验过期时间（JWT的exp是UTC时间戳）
  const currentTime = Math.floor(Date.now() / 1000); // 当前UTC时间戳（秒）
  return payload.exp && typeof payload.exp === 'number' && currentTime <= payload.exp;
};

export const hasActiveSession = (): boolean => {
  return checkTokenValid();
};

/**
 * 处理Token过期逻辑（返回登录页路由配置）
 */
export const handleTokenExpired = (): { path: string; query: Record<string, string> } => {
  clearAccessToken();
  clearSessionSignKey();
  notifyAuthChanged();
  return {
    path: '/userlogin',
    query: { redirect: router.currentRoute.value.fullPath } // 携带重定向参数
  };
};

/**
 * 显示Token过期提示并跳转登录页（修复关闭弹窗不跳转）
 */
export const showExpiredAlert = (): void => {
  // 防止重复触发
  if (authState.isProcessing || !authState.needShowExpiredAlert) return;

  authState.isProcessing = true;

  // 使用立即执行函数包裹，确保错误被完全捕获
  (async () => {
    try {
      await ElMessageBox.alert(
        t('auth.expiredRelogin'),
        t('profile.prompt'),
        {
          confirmButtonText: t('profile.confirm'),
          type: 'warning',
          showClose: true,
          closeOnClickModal: false,
          autofocus: false,
          customClass: 'minimal-alert-box'
        }
      );

      authState.needShowExpiredAlert = false;
      await router.push(handleTokenExpired());
    } catch (error) {
      if (error === 'cancel' || error === 'close') {
        authState.needShowExpiredAlert = false;
      } else {
        console.error('弹窗操作异常:', error);
      }
    } finally {
      authState.isProcessing = false;
    }
  })();
};

/**
 * 检查是否有管理员权限
 */
export const checkAdminPermission = (): boolean => {
  const payload = parseTokenPayload();
  if (!payload) return false;
  return payload.user_role === 'ADMIN';
};

/**
 * 从Token获取用户信息（新增username字段）
 */
export const getUserInfo = (): { email: string; username: string; role: string } => {
  const payload = parseTokenPayload();
  if (!payload) {
    return { email: '未登录', username: '未登录用户', role: 'NORMAL' };
  }

  return {
    email: (payload.email as string) || '未知用户',
    username: (payload.username as string) || '未知用户名', // 提取数据库的username
    role: (payload.user_role as string) || 'NORMAL'
  };
};

/**
 * 退出登录
 */
export const logout = (): void => {
  const accessToken = getAccessToken();
  fetch(`${BASE_URL}/weather/user/logout/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {})
    },
    credentials: 'include',
    keepalive: true
  }).catch(() => {});

  clearAccessToken();
  localStorage.removeItem('user');
  clearSessionSignKey();
  notifyAuthChanged();
  ElMessage.success(t('auth.logoutSuccess'));
  router.replace({ path: '/weather' }).catch((err: unknown) => {
    console.error('退出登录跳转失败:', err);
  });
};

/**
 * 获取当前Token
 */
export const getToken = (): string => {
  return getAccessToken();
};

/**
 * 检查是否已登录
 */
export const isLoggedIn = (): boolean => {
  return !!getToken() && parseTokenPayload() !== null && hasActiveSession();
};

export const requireLogin = (reason = t('auth.loginFirst')): boolean => {
  if (isLoggedIn()) {
    return true;
  }

  openAuthModal('login', reason);
  return false;
};

// 状态查询方法
export const getAuthState = () => ({ ...authState });
