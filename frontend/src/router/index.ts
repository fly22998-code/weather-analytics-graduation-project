import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router';
import type { RouteLocationNormalized, NavigationGuardNext } from 'vue-router';
import { ElMessage } from 'element-plus';
// 导入权限工具函数
import { authState, checkTokenValid, handleTokenExpired, checkAdminPermission, showExpiredAlert } from '../utils/auth';
import { openAuthModal } from '@/utils/authModal';
import { t } from '@/utils/i18n';

// 移除所有页面组件的静态import，改为路由内懒加载

const routes: RouteRecordRaw[] = [
  { path: '/', redirect: '/weather' },
  {
    path: '/weather',
    name: 'WeatherQuery',
    component: () => import('../views/user/WeatherApp.vue'), // 懒加载
    meta: { requiresAuth: false, title: '历史天气' }
  },
  {
    path: '/analysis',
    name: 'WeatherAnalysis',
    component: () => import('../views/user/WeatherAnalysis.vue'), // 懒加载
    meta: { requiresAuth: false, title: '世界实时天气' }
  },
  {
    path: '/temperature',
    name: 'TemperatureChange',
    component: () => import('../views/user/TemperatureChange.vue'), // 懒加载
    meta: { requiresAuth: false, title: '天气预测' }
  },
  {
    path: '/userlogin',
    component: () => import('../views/user/UserLogin.vue'), // 懒加载
    meta: { requiresAuth: false, title: '用户登录' }
  },
  {
    path: '/register',
    component: () => import('../views/user/UserRegister.vue'), // 懒加载
    meta: { requiresAuth: false, title: '用户注册' }
  },
  {
    path: '/password-reset',
    component: () => import('../views/user/PasswordReset.vue'), // 懒加载
    meta: { requiresAuth: false, title: '重置密码' }
  },
  
  // 管理员相关路由（懒加载）
  {
    path: '/admin/usermanagement',
    name: 'UserManagement',
    component: () => import('../views/admin/UserManagement.vue'), // 懒加载
    meta: { requiresAuth: true, role: 'ADMIN', title: '用户管理' }
  },
  {
    path: '/admin/weather-analysis',
    name: 'AdminWeatherAnalysis',
    component: () => import('../views/admin/WeatherAnalysis.vue'), // 懒加载
    meta: { requiresAuth: true, role: 'ADMIN', title: '天气分析' }
  },
  {
    path: '/admin/forecast',
    name: 'AdminForecast',
    component: () => import('../views/admin/Forecast.vue'), // 懒加载
    meta: { requiresAuth: true, role: 'ADMIN', title: '天气预报管理' }
  },
  {
    path: '/admin/system-settings',
    name: 'AdminSystemSettings',
    component: () => import('../views/admin/SystemSettings.vue'), // 懒加载
    meta: { requiresAuth: true, role: 'ADMIN', title: '系统设置' }
  },
  {
    path: '/admin/traffic-stats',
    name: 'AdminTrafficStats',
    component: () => import('../views/admin/TrafficStats.vue'), // 懒加载
    meta: { requiresAuth: true, role: 'ADMIN', title: '流量统计' }
  },
  
  {
    path: '/:pathMatch(.*)*',
    redirect: '/weather'
  }
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

// 路由守卫：统一Token验证 + 权限区分（保留原有逻辑）
router.beforeEach((
  to: RouteLocationNormalized, 
  from: RouteLocationNormalized, 
  next: NavigationGuardNext
) => {
  // 防止重复处理
  if (authState.isProcessing) {
    next(false);
    return;
  }
  authState.isProcessing = true;

  // 1. 验证Token有效性
  const isTokenValid = checkTokenValid();

  if (!to.meta.requiresAuth && ['/userlogin', '/register', '/password-reset'].includes(to.path) && isTokenValid) {
    const redirectPath = to.query.redirect as string || '/weather';
    authState.isProcessing = false;
    next(redirectPath);
    return;
  }

  // 2. 管理员权限校验
  if (to.meta.role === 'ADMIN' && !isTokenValid) {
    authState.isProcessing = false;
    openAuthModal('login', t('auth.adminLoginRequired'));
    next('/weather');
    return;
  }

  if (to.meta.role === 'ADMIN' && !checkAdminPermission()) {
    ElMessage.error(t('auth.adminAccessDenied'));
    authState.isProcessing = false;
    next(from.path || '/weather');
    return;
  }

  // 3. 所有验证通过，正常跳转
  authState.isProcessing = false;
  next();
});

// 登录过期提示处理（保持原有逻辑）
router.afterEach(() => {
  if (authState.needShowExpiredAlert) {
    showExpiredAlert();
  }
});

export default router;
