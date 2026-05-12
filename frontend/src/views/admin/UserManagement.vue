<template>
  <div class="user-management-content" :class="{ 'disable-responsive-layout': !enableResponsiveAdapt }">
    <div class="page-operations">
      <h2 class="page-title">用户管理</h2>
      <el-button
        v-if="canDeleteUsers"
        type="danger"
        class="batch-delete-btn"
        @click="handleBatchDelete"
        :disabled="selectedUserIds.length === 0"
      >
        <el-icon><Delete /></el-icon>
        批量删除
      </el-button>
    </div>

    <el-card class="filter-card" :class="{ 'disable-responsive-card': !enableResponsiveAdapt }">
      <el-row v-if="enableResponsiveAdapt" :gutter="filterGutter" class="filter-row">
        <el-col :xs="24" :sm="24" :md="12" :lg="8">
          <el-input
            v-model="searchKeyword"
            placeholder="搜索邮箱/昵称/手机号"
            prefix-icon="Search"
            clearable
            @keyup.enter="handleSearch"
          />
        </el-col>
        <el-col :xs="24" :sm="12" :md="6" :lg="6">
          <el-select
            v-model="selectedRole"
            placeholder="选择用户角色"
            clearable
          >
            <el-option label="全部角色" value="" />
            <el-option label="普通用户" value="NORMAL" />
            <el-option label="会员用户" value="VIP" />
            <el-option label="系统管理员" value="ADMIN" />
          </el-select>
        </el-col>
        <el-col :xs="24" :sm="12" :md="6" :lg="6">
          <el-select
            v-model="selectedStatus"
            placeholder="选择状态"
            clearable
          >
            <el-option label="全部状态" value="" />
            <el-option label="正常" value="active" />
            <el-option label="封禁" value="banned" />
          </el-select>
        </el-col>
        <el-col :xs="24" :sm="24" :md="24" :lg="4" class="filter-actions">
          <el-button type="primary" @click="handleSearch">搜索</el-button>
          <el-button plain @click="resetFilter">重置</el-button>
        </el-col>
      </el-row>
      <div v-else class="desktop-filter-strip">
        <div class="desktop-filter-item desktop-filter-search">
          <el-input
            v-model="searchKeyword"
            placeholder="搜索邮箱/昵称/手机号"
            prefix-icon="Search"
            clearable
            @keyup.enter="handleSearch"
          />
        </div>
        <div class="desktop-filter-item">
          <el-select
            v-model="selectedRole"
            placeholder="选择用户角色"
            clearable
          >
            <el-option label="全部角色" value="" />
            <el-option label="普通用户" value="NORMAL" />
            <el-option label="会员用户" value="VIP" />
            <el-option label="系统管理员" value="ADMIN" />
          </el-select>
        </div>
        <div class="desktop-filter-item">
          <el-select
            v-model="selectedStatus"
            placeholder="选择状态"
            clearable
          >
            <el-option label="全部状态" value="" />
            <el-option label="正常" value="active" />
            <el-option label="封禁" value="banned" />
          </el-select>
        </div>
        <div class="desktop-filter-actions">
          <el-button type="primary" @click="handleSearch">搜索</el-button>
          <el-button plain @click="resetFilter">重置</el-button>
        </div>
      </div>
    </el-card>

    <el-card class="user-table-card">
      <el-table
        :data="userList"
        class="responsive-user-table"
        border
        stripe
        row-key="id"
        style="width: 100%;"
        :cell-style="{ transition: 'background-color 0.2s', 'font-size': '12px' }"
        :loading="isRefreshing"
        loading-text="数据更新中..."
        :loading-spinner="null"
        :loading-offset="0"
        @selection-change="handleSelectionChange"
        :header-cell-style="{ 'font-size': '13px', 'font-weight': 600 }"
        empty-text="暂无用户数据"
      >
        <el-table-column type="selection" width="50" align="center" v-if="canDeleteUsers" />
        <el-table-column prop="id" label="ID" width="70" align="center" :fixed="isWideTable ? 'left' : false" />

        <el-table-column prop="email" label="邮箱" min-width="180">
          <template #default="scope">
            <span
              class="clickable-email"
              @click="openDetailDrawer(scope.row)"
              :title="scope.row?.email || '-'"
            >
              {{ scope.row?.email || '-' }}
            </span>
          </template>
        </el-table-column>

        <el-table-column v-if="showPhoneColumn" prop="phone" label="手机号" min-width="120" align="center">
          <template #default="scope">
            {{ scope.row?.phone || '-' }}
          </template>
        </el-table-column>

        <el-table-column label="用户角色" width="110" align="center">
          <template #default="scope">
            <el-tag
              v-if="scope.row"
              :type="getRoleTagType(scope.row.user_role)"
              class="role-tag"
              size="small"
            >
              {{ scope.row.user_role_display || '未知' }}
            </el-tag>
            <span v-else>-</span>
          </template>
        </el-table-column>

        <el-table-column label="状态" width="90" align="center">
          <template #default="scope">
            <el-tag
              v-if="scope.row"
              :type="scope.row.is_banned ? 'danger' : 'success'"
              :class="['status-tag', scope.row.is_banned ? 'banned-tag' : 'active-tag']"
              size="small"
            >
              {{ scope.row.is_banned ? '封禁' : '正常' }}
            </el-tag>
            <span v-else>-</span>
          </template>
        </el-table-column>

        <el-table-column v-if="showIpColumn" label="登录IP/所在地" min-width="180" align="center">
          <template #default="scope">
            <div class="ip-location-container">
              <span class="ip-text" :title="scope.row?.last_login_ip || '从未登录'">
                {{ scope.row?.last_login_ip || '从未登录' }}
              </span>
              <span class="location-text" v-if="scope.row?.last_login_location && !isLocalIp(scope.row.last_login_ip)">
                {{ scope.row.last_login_location }}
              </span>
            </div>
          </template>
        </el-table-column>

        <el-table-column v-if="showLastLoginColumn" prop="last_login_time" label="最后登录时间" min-width="160" align="center">
          <template #default="scope">
            {{ formatDateTime(scope.row?.last_login_time) }}
          </template>
        </el-table-column>

        <el-table-column v-if="showLoginCountColumn" prop="login_count" label="登录次数" width="90" align="center">
          <template #default="scope">
            {{ scope.row?.login_count || 0 }}
          </template>
        </el-table-column>

        <el-table-column v-if="showCreatedAtColumn" prop="created_at" label="注册时间" min-width="160" align="center">
          <template #default="scope">
            {{ formatDateTime(scope.row?.created_at) }}
          </template>
        </el-table-column>

        <el-table-column label="操作" :width="operationColumnWidth" align="center" :fixed="isWideTable ? 'right' : false">
          <template #default="scope">
            <el-button
              type="text"
              size="small"
              class="edit-btn"
              @click="openEditDialog(scope.row)"
              v-if="showEditButton(scope.row)"
            >
              编辑
            </el-button>

            <el-button
              v-if="canDeleteUsers && showDeleteButton(scope.row)"
              type="text"
              size="small"
              class="delete-btn"
              @click="handleDeleteUser(scope.row)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-container">
        <el-pagination
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
          :current-page="currentPage"
          :page-sizes="[10, 20, 50, 100]"
          :page-size="pageSize"
          :layout="paginationLayout"
          :total="totalUsers"
          :disabled="isRefreshing"
          background
        />
      </div>
    </el-card>

    <UserDetailDrawer
      :visible="detailVisible"
      :user="currentUser"
      :utcToShanghai="formatDateTime"
      :showEditButton="showEditButton"
      @close="detailVisible = false"
      @edit="openEditDialogFromDetail"
    />

    <UserEditDialog
      :visible="editDialogVisible"
      :user="currentUser"
      :isEditingSelf="isEditingSelf"
      :utcToShanghai="formatDateTime"
      @close="editDialogVisible = false"
      @save="submitEditForm"
      @statusChange="handleStatusChange"
    />

    <el-dialog
      v-model="deleteDialogVisible"
      title="确认删除"
      width="300px"
      :close-on-click-modal="false"
      :close-on-press-escape="false"
    >
      <div class="delete-confirm-content">
        <p>确定要删除用户 <span class="delete-email">{{ deleteTargetUser?.email }}</span> 吗？</p>
        <p class="delete-warning" v-if="deleteRestriction">
          <i class="el-icon-warning"></i>
          {{ deleteRestrictionText }}
        </p>
        <p class="delete-warning" v-else>
          <i class="el-icon-warning"></i>
          此操作不可撤销，删除后用户数据将永久丢失。
        </p>
      </div>
      <template #footer>
        <el-button @click="deleteDialogVisible = false">取消</el-button>
        <el-button
          type="danger"
          @click="confirmDeleteUser"
          :loading="isDeleting"
          :disabled="deleteRestriction"
        >
          确认删除
        </el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="batchDeleteDialogVisible"
      title="批量删除确认"
      width="350px"
      :close-on-click-modal="false"
      :close-on-press-escape="false"
    >
      <div class="batch-delete-confirm-content">
        <p>您已选择 <span class="selected-count">{{ selectedUserIds.length }}</span> 个用户，确定要批量删除吗？</p>
        <p class="delete-warning">
          <i class="el-icon-warning"></i>
          此操作不可撤销，系统将自动过滤不允许删除的用户。
        </p>
      </div>
      <template #footer>
        <el-button @click="batchDeleteDialogVisible = false">取消</el-button>
        <el-button
          type="danger"
          @click="confirmBatchDelete"
          :loading="isBatchDeleting"
          :disabled="selectedUserIds.length === 0"
        >
          确认删除
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick, watch, computed } from 'vue';
import { Delete } from '@element-plus/icons-vue';
import { ElMessage } from 'element-plus';
import request, { hasValidToken, redirectToLogin } from '@/utils/requests';
import { getUserInfo } from '@/utils/auth';
import { debounce } from 'lodash';
import type { AxiosResponse, InternalAxiosRequestConfig, AxiosError } from 'axios';
import UserDetailDrawer from './UserDetailDrawer.vue';
import UserEditDialog from './UserEditDialog.vue';

// ========== 鏍稿績绫诲瀷瀹氫箟锛堜慨澶嶇被鍨嬬粨鏋勶級 ==========
interface BaseUser {
  id: string | number;
  email: string;
  [key: string]: any;
}

interface UserListItem extends BaseUser {
  phone?: string;
  user_role: string;
  user_role_display: string;
  is_banned: boolean;
  last_login_ip?: string;
  last_login_location?: string;
  last_login_time?: string;
  login_count?: number;
  created_at?: string;
}

interface UserInfo extends BaseUser {
  username?: string;
  gender?: string;
  birthday?: string;
  ban_reason?: string;
  phone?: string;
}

// 淇鍝嶅簲鏁版嵁缁撴瀯瀹氫箟
interface ApiResponseData<T = any> {
  code?: number | string;
  status?: string;
  data: T;
  total?: number;
  message?: string;
}

// 瀹屾暣鐨凙xios鍝嶅簲绫诲瀷锛堟纭畾涔夛級
type ApiResponse<T = any> = AxiosResponse<ApiResponseData<T>>;

interface EditFormData extends UserInfo {
  status: string;
  userRole: string;
  banReason: string;
}

// ========== 鍏ㄥ眬澹版槑 ==========
declare global {
  interface Window {
    cacheCleanupInterval?: NodeJS.Timeout;
    _resizeObservers?: ResizeObserver[];
  }
}

// ========== 甯搁噺瀹氫箟 ==========
const PROTECTED_EMAIL = 'admin@example.com';
const STORAGE_KEY = 'user_management_state';
const CACHE_EXPIRE_TIME = 5 * 60 * 1000;
const LIST_CACHE_PREFIX = 'user_management_list_cache:';

const BASE_URL = import.meta.env.VITE_API_BASE_URL || '';
const USER_LIST_API = `${BASE_URL}/weather/admin/users/`;
const USER_DETAIL_API = (id: string | number) => `${BASE_URL}/weather/admin/users/${id}/info/`;
const USER_EDIT_API = (id: string | number) => `${BASE_URL}/weather/admin/users/${id}/edit/`;
const USER_DELETE_API = (id: string | number) => `${BASE_URL}/weather/admin/users/${id}/delete/`;
const USER_BATCH_DELETE_API = `${BASE_URL}/weather/admin/users/batch-delete/`;

// ========== 鍝嶅簲寮忕姸鎬?==========
let isComponentMounted = false;

const isRefreshing = ref(false);
const searchKeyword = ref('');
const selectedRole = ref('');
const selectedStatus = ref('');
const currentPage = ref(1);
const pageSize = ref(10);
const totalUsers = ref(0);
const userList = ref<UserListItem[]>([]);

const selectedUserIds = ref<(string | number)[]>([]);
const selectedUsers = ref<UserListItem[]>([]);
const batchDeleteDialogVisible = ref(false);
const isBatchDeleting = ref(false);

const deleteDialogVisible = ref(false);
const deleteTargetUser = ref<BaseUser>({ id: '', email: '' });
const isDeleting = ref(false);

const detailVisible = ref(false);
const currentUser = ref<BaseUser>({ id: '', email: '' });
const editDialogVisible = ref(false);
const isEditingSelf = ref(false);

const requestCache = ref<Map<string, any>>(new Map());
const abortControllers = ref<Map<string, AbortController>>(new Map());
const activeRequests = ref<Set<string>>(new Set());
const viewportWidth = ref(typeof window !== 'undefined' ? window.innerWidth : 1440);

// ========== 璁＄畻灞炴€?==========
const currentUserInfo = computed((): BaseUser => {
  const rawInfo = getUserInfo() as any;
  return {
    id: rawInfo?.id || '',
    email: rawInfo?.email || '',
    ...(rawInfo || {})
  };
});

const canDeleteUsers = computed(() => {
  return currentUserInfo.value.email === PROTECTED_EMAIL;
});

const enableResponsiveAdapt = computed(() => viewportWidth.value > 600);
const filterGutter = computed(() => enableResponsiveAdapt.value && viewportWidth.value <= 768 ? 12 : 20);
const isWideTable = computed(() => !enableResponsiveAdapt.value || viewportWidth.value > 1320);
const showPhoneColumn = computed(() => !enableResponsiveAdapt.value || viewportWidth.value > 700);
const showIpColumn = computed(() => !enableResponsiveAdapt.value || viewportWidth.value > 1100);
const showLastLoginColumn = computed(() => !enableResponsiveAdapt.value || viewportWidth.value > 880);
const showLoginCountColumn = computed(() => !enableResponsiveAdapt.value || viewportWidth.value > 1180);
const showCreatedAtColumn = computed(() => !enableResponsiveAdapt.value || viewportWidth.value > 1380);
const operationColumnWidth = computed(() => {
  if (!enableResponsiveAdapt.value) return 160;
  if (viewportWidth.value <= 576) return 110;
  if (viewportWidth.value <= 768) return 124;
  return 160;
});
const paginationLayout = computed(() => {
  if (!enableResponsiveAdapt.value) return 'total, sizes, prev, pager, next, jumper';
  if (viewportWidth.value <= 576) return 'prev, pager, next';
  if (viewportWidth.value <= 768) return 'total, prev, pager, next';
  return 'total, sizes, prev, pager, next, jumper';
});

const deleteRestriction = computed(() => {
  return isDeletingSelf.value || isDeletingAdmin.value || isDeletingProtected.value;
});

const deleteRestrictionText = computed(() => {
  if (isDeletingSelf.value) return '无法删除当前登录用户，请选择其他操作';
  if (isDeletingAdmin.value) return '无法删除管理员账号，请选择其他操作';
  if (isDeletingProtected.value) return '无法删除受保护账号，请选择其他操作';
  return '';
});

const isDeletingSelf = computed(() => {
  if (!deleteTargetUser.value) return false;
  return (
    currentUserInfo.value.id === deleteTargetUser.value.id ||
    currentUserInfo.value.email === deleteTargetUser.value.email
  );
});

const isDeletingAdmin = computed(() => {
  return deleteTargetUser.value?.user_role === 'ADMIN';
});

const isDeletingProtected = computed(() => {
  return deleteTargetUser.value?.email === PROTECTED_EMAIL;
});

// ========== 宸ュ叿鍑芥暟 ==========
const fixResizeObserverWarning = () => {
  const originalError = console.error;
  console.error = (...args: any[]) => {
    if (args[0] && typeof args[0] === 'string' && 
        (args[0].includes('ResizeObserver loop') || args[0].includes('getComputedStyle'))) {
      return;
    }
    originalError.apply(console, args);
  };
};

const formatDateTime = (utcTime?: string): string => {
  if (!utcTime) return '从未登录';
  const hasTimezone = /(?:Z|[+-]\d{2}:?\d{2})$/i.test(utcTime);
  const normalized = utcTime.includes('T')
    ? (hasTimezone ? utcTime : `${utcTime}Z`)
    : `${utcTime.replace(' ', 'T')}${hasTimezone ? '' : 'Z'}`;
  const utcDate = new Date(normalized);
  if (isNaN(utcDate.getTime())) return '无效时间';
  return utcDate.toLocaleString('zh-CN', {
    timeZone: 'Asia/Shanghai',
    year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit', second: '2-digit'
  }).replace(',', '');
};

const isLocalIp = (ip?: string): boolean => {
  if (!ip) return false;
  const localIps = ['127.0.0.1', 'localhost', '::1', '0.0.0.0'];
  return localIps.includes(ip.toLowerCase());
};

const getRoleTagType = (role?: string): string => {
  switch (role) {
    case 'ADMIN': return 'primary';
    case 'VIP': return 'success';
    default: return 'info';
  }
};

const buildRequestParams = () => ({
  page: currentPage.value,
  page_size: pageSize.value,
  search: searchKeyword.value || undefined,
  role: selectedRole.value || undefined,
  is_banned: selectedStatus.value === 'banned' ? 'true' : 
             selectedStatus.value === 'active' ? 'false' : undefined
});

const generateCacheKey = (params: any): string => JSON.stringify(params);

const generateSessionListCacheKey = (cacheKey: string): string => `${LIST_CACHE_PREFIX}${cacheKey}`;

const getSessionCachedList = (cacheKey: string): { data: UserListItem[]; total: number } | null => {
  try {
    const raw = sessionStorage.getItem(generateSessionListCacheKey(cacheKey));
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    if (!parsed?.expires || parsed.expires <= Date.now()) {
      sessionStorage.removeItem(generateSessionListCacheKey(cacheKey));
      return null;
    }
    return {
      data: Array.isArray(parsed.data) ? parsed.data : [],
      total: typeof parsed.total === 'number' ? parsed.total : 0
    };
  } catch {
    return null;
  }
};

const setSessionCachedList = (cacheKey: string, data: UserListItem[], total: number): void => {
  try {
    sessionStorage.setItem(generateSessionListCacheKey(cacheKey), JSON.stringify({
      data,
      total,
      expires: Date.now() + 60 * 1000
    }));
  } catch (error) {
    console.error('保存用户列表缓存失败:', error);
  }
};

const clearRequestCache = (key?: string): void => {
  if (key) {
    requestCache.value.delete(key);
    try {
      sessionStorage.removeItem(generateSessionListCacheKey(key));
    } catch {}
    return;
  }

  requestCache.value.clear();
  try {
    Object.keys(sessionStorage)
      .filter(sessionKey => sessionKey.startsWith(LIST_CACHE_PREFIX))
      .forEach(sessionKey => sessionStorage.removeItem(sessionKey));
  } catch {}
};

const cancelPreviousRequest = (cacheKey: string): void => {
  const controller = abortControllers.value.get(cacheKey);
  if (controller) {
    controller.abort();
    abortControllers.value.delete(cacheKey);
  }
};

const isRequestAborted = (error: any): boolean => {
  return error?.name === 'AbortError' || 
         error?.message === 'canceled' || 
         error?.message === 'Network Error' ||
         error?.message?.includes('Failed to fetch') ||
         error?.message?.includes('request aborted') ||
         error?.message?.includes('The user aborted a request');
};

const updateViewportWidth = (): void => {
  if (typeof window === 'undefined') return;
  viewportWidth.value = window.innerWidth;
};

// ========== 浼氳瘽瀛樺偍 ==========
const loadStateFromSession = (): void => {
  try {
    const savedState = sessionStorage.getItem(STORAGE_KEY);
    if (savedState) {
      const parsed = JSON.parse(savedState);
      currentPage.value = parsed.currentPage && typeof parsed.currentPage === 'number' && parsed.currentPage > 0 
        ? parsed.currentPage 
        : 1;
      pageSize.value = parsed.pageSize && [10, 20, 50, 100].includes(parsed.pageSize)
        ? parsed.pageSize
        : 10;
      searchKeyword.value = parsed.searchKeyword || '';
      selectedRole.value = parsed.selectedRole || '';
      selectedStatus.value = parsed.selectedStatus || '';
    }
  } catch (error) {
    console.error('鍔犺浇浼氳瘽鐘舵€佸け璐?', error);
  }
};

const saveStateToSession = debounce((): void => {
  if (!isComponentMounted) return;
  try {
    const state = {
      currentPage: currentPage.value,
      pageSize: pageSize.value,
      searchKeyword: searchKeyword.value,
      selectedRole: selectedRole.value,
      selectedStatus: selectedStatus.value
    };
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  } catch (error) {
    console.error('保存状态失败:', error);
  }
}, 300);

const resetStateInSession = (): void => {
  try {
    sessionStorage.removeItem(STORAGE_KEY);
    currentPage.value = 1;
    pageSize.value = 10;
    searchKeyword.value = '';
    selectedRole.value = '';
    selectedStatus.value = '';
  } catch (error) {
    console.error('閲嶇疆鐘舵€佸け璐?', error);
  }
};

// ========== API璇锋眰锛堟牳蹇冧慨澶嶏細瑙ｅ喅 res.data 绫诲瀷閿欒锛?==========
const fetchUserList = debounce(async (): Promise<void> => {
  if (!isComponentMounted) return;
  isRefreshing.value = true;

  if (!hasValidToken()) {
    redirectToLogin();
    isRefreshing.value = false;
    return;
  }

  const params = buildRequestParams();
  const cacheKey = generateCacheKey(params);

  if (requestCache.value.has(cacheKey)) {
    const cachedData = requestCache.value.get(cacheKey);
    userList.value = cachedData.data || [];
    totalUsers.value = cachedData.total || 0;
    isRefreshing.value = false;
    
    if (currentPage.value > 1 && userList.value.length === 0 && totalUsers.value > 0) {
      currentPage.value = 1;
      return fetchUserList();
    }
    return;
  }

  const sessionCachedList = getSessionCachedList(cacheKey);
  if (sessionCachedList) {
    userList.value = sessionCachedList.data;
    totalUsers.value = sessionCachedList.total;
    requestCache.value.set(cacheKey, {
      data: sessionCachedList.data,
      total: sessionCachedList.total,
      timestamp: Date.now(),
      expires: Date.now() + CACHE_EXPIRE_TIME
    });
    isRefreshing.value = false;

    if (currentPage.value > 1 && userList.value.length === 0 && totalUsers.value > 0) {
      currentPage.value = 1;
      return fetchUserList();
    }
    return;
  }

  cancelPreviousRequest(cacheKey);
  const controller = new AbortController();
  abortControllers.value.set(cacheKey, controller);

  try {
    // 鏍稿績淇1锛氭媶鍒?Promise.race锛屽厛瀹氫箟璇锋眰Promise骞舵寚瀹氱被鍨?
    const requestPromise = request.get<ApiResponseData<UserListItem[]>>(USER_LIST_API, {
      params,
      signal: controller.signal,
      timeout: 20000
    }) as Promise<ApiResponse<UserListItem[]>>;
    
    // 鏍稿績淇2锛氳秴鏃禤romise鎸囧畾绫诲瀷
    const timeoutPromise = new Promise<never>((_, reject) => 
      setTimeout(() => reject(new Error('请求超时')), 18000)
    );

    // 鏍稿績淇3锛氭樉寮忔寚瀹?race 杩斿洖绫诲瀷
    const res = await Promise.race<ApiResponse<UserListItem[]> | never>([
      requestPromise,
      timeoutPromise
    ]);

    if (!isComponentMounted) return;

    // 姝ゆ椂 res 绫诲瀷鏄庣‘涓?ApiResponse锛屽彲瀹夊叏璁块棶 res.data
    const responseData = res.data;
    const code = String(responseData.code || responseData.status);
    
    if (['200', 'success'].includes(code)) {
      requestCache.value.set(cacheKey, {
        data: responseData.data || [],
        total: responseData.total || 0,
        timestamp: Date.now(),
        expires: Date.now() + CACHE_EXPIRE_TIME
      });
      setSessionCachedList(cacheKey, responseData.data || [], responseData.total || 0);
      userList.value = responseData.data || [];
      totalUsers.value = responseData.total || 0;

      if (currentPage.value > 1 && userList.value.length === 0 && totalUsers.value > 0) {
        currentPage.value = 1;
        return fetchUserList();
      }
    } else {
      ElMessage.error(responseData.message || '获取用户列表失败');
    }
  } catch (error: any) {
    if (isRequestAborted(error)) {
      console.log('请求中断:', error.message);
      return;
    }

    console.error('获取用户列表失败:', error);
    if (error.message === '请求超时' && requestCache.value.has(cacheKey)) {
      const cachedData = requestCache.value.get(cacheKey);
      userList.value = cachedData.data || [];
      totalUsers.value = cachedData.total || 0;
      return;
    }

    ElMessage.error('获取用户列表失败，请稍后重试');
  } finally {
    abortControllers.value.delete(cacheKey);
    isRefreshing.value = false;
  }
}, 100);

const fetchUserDetail = async (userId: string | number): Promise<UserInfo | null> => {
  if (!isComponentMounted || !hasValidToken()) {
    redirectToLogin();
    return null;
  }

  const detailCacheKey = `detail_${userId}`;
  if (requestCache.value.has(detailCacheKey)) {
    const cachedData = requestCache.value.get(detailCacheKey);
    if (cachedData.expires && cachedData.expires > Date.now()) {
      return cachedData;
    }
  }

  try {
    const res = await request.get<ApiResponseData<UserInfo>>(USER_DETAIL_API(userId), {
      timeout: 15000
    }) as ApiResponse<UserInfo>;

    if (!isComponentMounted) return null;

    const responseData = res.data;
    const code = String(responseData.code || responseData.status);
    
    if (['200', 'success'].includes(code)) {
      const userData = responseData.data;
      const completeUserData: UserInfo = {
        id: userData.id || userId,
        email: userData.email || '',
        ...userData
      };
      
      requestCache.value.set(detailCacheKey, {
        ...completeUserData,
        timestamp: Date.now(),
        expires: Date.now() + CACHE_EXPIRE_TIME
      });
      return completeUserData;
    } else {
      ElMessage.error(responseData.message || '获取用户详情失败');
      return null;
    }
  } catch (error: any) {
    if (isRequestAborted(error)) {
      console.log('请求中断');
      return null;
    }

    console.error('获取用户详情失败:', error);
    if (error.message === '请求超时' && requestCache.value.has(detailCacheKey)) {
      return requestCache.value.get(detailCacheKey);
    }

    ElMessage.error('获取用户详情失败');
    return null;
  }
};

// ========== 涓氬姟閫昏緫 ==========
const showEditButton = (row: UserListItem): boolean => {
  if (!row) return false;
  if (row.email === PROTECTED_EMAIL) {
    return currentUserInfo.value.email === PROTECTED_EMAIL;
  }
  return true;
};

const showDeleteButton = (row: UserListItem): boolean => {
  if (!row) return false;
  if (row.email === PROTECTED_EMAIL) return false;
  if (row.user_role === 'ADMIN') return false;
  if (currentUserInfo.value.id === row.id || currentUserInfo.value.email === row.email) return false;
  return true;
};

const handleSelectionChange = (selection: UserListItem[]): void => {
  selectedUsers.value = selection;
  selectedUserIds.value = selection.map(user => user.id);
};

const handleBatchDelete = (): void => {
  if (selectedUserIds.value.length === 0) {
    ElMessage.warning('请先选择要删除的用户');
    return;
  }
  batchDeleteDialogVisible.value = true;
};

const confirmBatchDelete = async (): Promise<void> => {
  if (!isComponentMounted || selectedUsers.value.length === 0) return;
  
  isBatchDeleting.value = true;
  const requestId = `batch_delete_${Date.now()}`;

  try {
    const ids = selectedUsers.value.map(user => user.id);
    activeRequests.value.add(requestId);

    const res = await request.delete<ApiResponseData<any>>(USER_BATCH_DELETE_API, {
      data: { ids },
      timeout: 20000
    }) as ApiResponse<any>;

    if (!isComponentMounted || !activeRequests.value.has(requestId)) return;

    const responseData = res.data;
    const status = String(responseData.status);
    
    if (status === 'success') {
      ElMessage.success(responseData.message || '批量删除成功');
      batchDeleteDialogVisible.value = false;
      selectedUserIds.value = [];
      selectedUsers.value = [];

      userList.value = userList.value.filter(user => !ids.includes(user.id));
      totalUsers.value = Math.max(0, totalUsers.value - ids.length);

      clearRequestCache();
      fetchUserList();
    } else {
      ElMessage.error(responseData.message || '批量删除失败');
    }
  } catch (error: any) {
    if (isRequestAborted(error)) {
      console.log('批量删除请求中断');
      return;
    }

    console.error('批量删除失败:', error);
    let errorMessage = '批量删除操作失败';
    if (error.response) {
      errorMessage = error.response.data?.message || errorMessage;
    }
    ElMessage.error(errorMessage);
  } finally {
    isBatchDeleting.value = false;
    activeRequests.value.delete(requestId);
  }
};

const openDetailDrawer = async (row: UserListItem): Promise<void> => {
  if (!isComponentMounted || !row) return;
  
  if (editDialogVisible.value) {
    editDialogVisible.value = false;
    await nextTick();
  }

  currentUser.value = { ...row };
  detailVisible.value = true;

  const detail = await fetchUserDetail(row.id);
  if (detail && isComponentMounted) {
    currentUser.value = detail;
  }
};

const openEditDialogFromDetail = (): void => {
  if (!isComponentMounted || !currentUser.value.id) return;
  openEditDialog(currentUser.value as UserListItem);
  detailVisible.value = false;
};

const openEditDialog = async (row: UserListItem): Promise<void> => {
  if (!isComponentMounted || !row) return;
  
  editDialogVisible.value = false;
  await nextTick();

  currentUser.value = { ...row };
  const userDetail = await fetchUserDetail(row.id);
  if (userDetail && isComponentMounted) {
    currentUser.value = userDetail;
  }

  const isSelf = (
    currentUserInfo.value.id === currentUser.value.id ||
    currentUserInfo.value.email === currentUser.value.email
  );
  isEditingSelf.value = isSelf;

  if (isSelf && isComponentMounted) {
    ElMessage.info({
      message: '您正在编辑自己的信息，用户角色和状态不可修改',
      duration: 3000
    });
  }

  editDialogVisible.value = true;
};

const submitEditForm = async (formData: EditFormData): Promise<void> => {
  if (!isComponentMounted) return;
  
  if (formData.email === PROTECTED_EMAIL && currentUserInfo.value.email !== PROTECTED_EMAIL) {
    ElMessage.error(`该账号受保护，仅 ${PROTECTED_EMAIL} 本人可修改`);
    return;
  }

  const requestId = `edit_${formData.id}_${Date.now()}`;

  try {
    const isBanned = formData.status === 'banned';
    const submitData = {
      username: formData.username || null,
      phone: formData.phone || null,
      gender: formData.gender || null,
      birthday: formData.birthday || null,
      user_role: formData.userRole,
      is_banned: isBanned,
      ban_reason: isBanned ? formData.banReason : ''
    };

    activeRequests.value.add(requestId);

    const res = await request.put<ApiResponseData<any>>(USER_EDIT_API(formData.id), submitData, {
      timeout: 25000,
      headers: { 'Content-Type': 'application/json' }
    }) as ApiResponse<any>;

    if (!isComponentMounted || !activeRequests.value.has(requestId)) return;

    const responseData = res.data;
    const status = String(responseData.status);
    const code = String(responseData.code);
    const isSuccess = status === 'success' || code === '200' || String(res.status) === '200';

    if (isSuccess) {
      ElMessage.success('用户信息更新成功');
      editDialogVisible.value = false;

      const userIndex = userList.value.findIndex(user => user.id === formData.id);
      if (userIndex !== -1) {
        userList.value[userIndex] = {
          ...userList.value[userIndex],
          is_banned: isBanned,
          is_banned_display: isBanned ? '已封禁' : '正常',
          user_role: formData.userRole,
          user_role_display: formData.userRole === 'ADMIN'
            ? '系统管理员'
            : formData.userRole === 'VIP'
              ? '会员用户'
              : '普通用户',
          username: formData.username || userList.value[userIndex].username,
          phone: formData.phone || userList.value[userIndex].phone
        };
      }

      window.postMessage({
        type: isBanned ? 'USER_BANNED' : 'USER_UNBANNED',
        userId: formData.id
      }, window.location.origin);

      window.dispatchEvent(new Event('userStatusChanged'));

      clearRequestCache();
      fetchUserList();
    } else {
      ElMessage.error(responseData.message || '更新失败');
    }
  } catch (error: any) {
    if (isRequestAborted(error)) {
      console.log('编辑请求中断');
      return;
    }

    console.error('更新用户失败:', error);
    let errorMessage = '操作失败，请稍后重试';
    
    if (error.message === 'Network Error') {
      errorMessage = '网络连接异常，请检查您的网络设置';
    } else if (error.message.includes('timeout')) {
      errorMessage = '请求超时，请稍后重试';
    } else if (error.response) {
      const status = error.response.status;
      if (status === 403) errorMessage = '权限不足，无法执行此操作';
      else if (status === 404) errorMessage = '用户不存在或已被删除';
      else if (status === 500) errorMessage = '服务器内部错误，请联系管理员';
      else errorMessage = error.response.data?.message || '更新用户信息失败';
    }

    ElMessage.error(errorMessage);
  } finally {
    activeRequests.value.delete(requestId);
  }
};

const handleDeleteUser = (row: UserListItem): void => {
  if (!isComponentMounted || !row) return;
  
  deleteTargetUser.value = { id: row.id, email: row.email, ...row };
  deleteDialogVisible.value = true;

  if (deleteRestriction.value) {
    ElMessage.warning(deleteRestrictionText.value);
  }
};

const confirmDeleteUser = async (): Promise<void> => {
  if (!isComponentMounted || deleteRestriction.value) return;
  if (!deleteTargetUser.value || !deleteTargetUser.value.id) {
    deleteDialogVisible.value = false;
    return;
  }

  isDeleting.value = true;
  const requestId = `delete_${deleteTargetUser.value.id}_${Date.now()}`;

  try {
    activeRequests.value.add(requestId);

    const res = await request.delete<ApiResponseData<any>>(USER_DELETE_API(deleteTargetUser.value.id), {
      timeout: 20000
    }) as ApiResponse<any>;

    if (!isComponentMounted || !activeRequests.value.has(requestId)) return;

    const responseData = res.data;
    const status = String(responseData.status);
    
    if (status === 'success') {
      ElMessage.success('用户删除成功');
      deleteDialogVisible.value = false;

      const userIndex = userList.value.findIndex(user => user.id === deleteTargetUser.value.id);
      if (userIndex !== -1) {
        userList.value.splice(userIndex, 1);
        totalUsers.value = Math.max(0, totalUsers.value - 1);
      }

      clearRequestCache();

      if (userList.value.length === 0 && currentPage.value > 1) {
        currentPage.value--;
      }

      fetchUserList();
    } else {
      ElMessage.error(responseData.message || '删除失败');
    }
  } catch (error: any) {
    if (isRequestAborted(error)) {
      console.log('删除请求中断');
      return;
    }

    console.error('删除用户失败:', error);
    let errorMessage = '删除用户失败';
    
    if (error.response) {
      errorMessage = error.response.data?.message || errorMessage;
      if (error.response.status === 403 && error.response.data?.message?.includes('仅系统保护账户')) {
        errorMessage = '只有系统保护账户才能执行删除操作';
      }
    } else if (error.message) {
      errorMessage = error.message.includes('timeout') ? '请求超时，请稍后重试' : error.message;
    }

    ElMessage.error(errorMessage);
  } finally {
    isDeleting.value = false;
    activeRequests.value.delete(requestId);
  }
};

const handleStatusChange = (): void => {
  clearRequestCache();
  fetchUserList();
};

const handleUserStatusChange = (): void => {
  if (!isComponentMounted) return;
  clearRequestCache();
  fetchUserList();
};

const handleSearch = (): void => {
  if (!isComponentMounted) return;
  currentPage.value = 1;
  fetchUserList();
};

const resetFilter = (): void => {
  if (!isComponentMounted) return;
  
  resetStateInSession();
  clearRequestCache();
  nextTick(() => fetchUserList());
};

const handleSizeChange = (size: number): void => {
  if (!isComponentMounted) return;
  
  pageSize.value = size;
  currentPage.value = 1;
  fetchUserList();
};

const handleCurrentChange = (page: number): void => {
  if (!isComponentMounted) return;
  
  currentPage.value = page;
  fetchUserList();
};

// ========== 鐢熷懡鍛ㄦ湡 ==========
watch([currentPage, pageSize, searchKeyword, selectedRole, selectedStatus], saveStateToSession);

onMounted(() => {
  isComponentMounted = true;
  
  fixResizeObserverWarning();
  updateViewportWidth();
  loadStateFromSession();
  
  nextTick().then(() => {
    fetchUserList();
  });

  window.addEventListener('userStatusChanged', handleUserStatusChange);
  window.addEventListener('resize', updateViewportWidth);

  window.cacheCleanupInterval = setInterval(() => {
    if (!isComponentMounted) return;
    
    const now = Date.now();
    const expiredKeys: string[] = [];

    requestCache.value.forEach((value, key) => {
      const isDetailCache = key.startsWith('detail_');
      const expireTime = isDetailCache ? CACHE_EXPIRE_TIME : 1 * 60 * 1000;
      
      if (value.timestamp && now - value.timestamp > expireTime) {
        expiredKeys.push(key);
      }
    });

    expiredKeys.forEach(key => requestCache.value.delete(key));
  }, CACHE_EXPIRE_TIME);
});

onUnmounted(() => {
  isComponentMounted = false;
  
  window.removeEventListener('userStatusChanged', handleUserStatusChange);
  window.removeEventListener('resize', updateViewportWidth);
  
  if (typeof fetchUserList.cancel === 'function') {
    fetchUserList.cancel();
  }

  abortControllers.value.forEach(controller => {
    try {
      controller.abort();
    } catch (e) {
      console.log('请求中止失败:', e);
    }
  });

  if (window.cacheCleanupInterval) {
    clearInterval(window.cacheCleanupInterval);
    delete window.cacheCleanupInterval;
  }

  abortControllers.value.clear();
  activeRequests.value.clear();
  requestCache.value.clear();
  
  userList.value = [];
  currentUser.value = { id: '', email: '' };
});
</script>

<style scoped>
.user-management-content {
  padding: 16px;
  height: 100%;
  box-sizing: border-box;
  overflow-y: auto;
  background-color: #f8fafc;
  overflow-anchor: none;
}

.page-operations {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  gap: 12px;
  flex-wrap: wrap;
}

.page-title {
  margin: 0;
  font-size: 18px;
  font-weight: 700;
  color: #1e293b;
  padding-left: 8px;
  border-left: 4px solid #409eff;
  user-select: none;
}

.batch-delete-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  padding: 8px 14px;
  transition: all 0.2s ease;
}

.batch-delete-btn:hover {
  box-shadow: 0 4px 12px rgba(245, 108, 108, 0.22);
}

.filter-card,
.user-table-card {
  border-radius: 10px;
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.06);
  transition: box-shadow 0.2s ease;
}

.filter-card {
  margin-bottom: 16px;
}

.filter-card:hover,
.user-table-card:hover {
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.08);
}

:deep(.filter-card .el-card__body) {
  padding: 16px;
}

.filter-row {
  row-gap: 12px;
}

.disable-responsive-card :deep(.el-card__body) {
  overflow-x: auto;
}

.disable-responsive-layout {
  min-width: 1180px;
}

.desktop-filter-strip {
  min-width: 920px;
  display: flex;
  align-items: center;
  gap: 20px;
}

.desktop-filter-item {
  width: 25%;
  flex: 0 0 auto;
}

.desktop-filter-search {
  width: calc(100% / 3);
}

.desktop-filter-actions {
  width: calc(100% / 6);
  flex: 0 0 auto;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
}

.desktop-filter-strip :deep(.el-input),
.desktop-filter-strip :deep(.el-select) {
  width: 100%;
}

:deep(.filter-card .el-input),
:deep(.filter-card .el-select) {
  width: 100%;
}

.filter-actions {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

:deep(.user-table-card .el-card__body) {
  padding: 0;
  overflow-x: auto;
}

:deep(.responsive-user-table) {
  min-width: 100%;
}

:deep(.responsive-user-table .cell) {
  line-height: 1.45;
}

:deep(.el-table) {
  border-radius: 10px 10px 0 0;
  border: none;
  min-height: 320px;
  width: 100%;
}

:deep(.el-table__empty-block),
:deep(.el-table__loading) {
  min-height: 320px;
  display: flex;
  align-items: center;
  justify-content: center;
}

:deep(.el-table__loading-text) {
  font-size: 13px;
  color: #64748b;
  padding: 16px 0;
}

:deep(.el-table th) {
  background-color: #f8fafc;
  border-bottom: 1px solid #e2e8f0;
  padding: 10px 0;
}

:deep(.el-table td) {
  padding: 10px 0;
}

:deep(.el-table tr:hover > td) {
  background-color: #f0f7ff;
}

.clickable-email {
  color: #409eff;
  cursor: pointer;
  text-decoration: underline;
  text-underline-offset: 2px;
  transition: color 0.2s ease;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  display: inline-block;
  max-width: 100%;
}

.clickable-email:hover {
  color: #1677ff;
}

.role-tag,
.status-tag {
  font-weight: 500;
  padding: 2px 8px;
}

.banned-tag {
  background-color: #fff1f0 !important;
  color: #cf1322 !important;
  border-color: #ffa39e !important;
  font-weight: 600 !important;
  box-shadow: 0 0 0 1px rgba(207, 19, 34, 0.1) !important;
}

.active-tag {
  background-color: #f6ffed !important;
  color: #52c41a !important;
  border-color: #b7eb8f !important;
}

.edit-btn,
.delete-btn {
  margin: 0 3px;
  font-size: 12px;
  transition: color 0.2s ease;
}

.edit-btn:hover {
  color: #409eff;
}

.delete-btn {
  color: #f56c6c;
}

.delete-btn:hover {
  color: #ff4d4f;
}

.ip-location-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 3px;
}

.ip-text {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 100%;
  display: inline-block;
}

.location-text {
  font-size: 11px;
  color: #606266;
  background-color: #f5f7fa;
  padding: 1px 6px;
  border-radius: 999px;
  white-space: nowrap;
}

.pagination-container {
  padding: 14px 16px;
  border-top: 1px solid #e2e8f0;
  display: flex;
  justify-content: flex-end;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
  box-sizing: border-box;
}

:deep(.el-pagination) {
  --el-pagination-font-size: 12px;
  flex-wrap: wrap;
  row-gap: 8px;
}

:deep(.el-pagination__item) {
  min-width: 30px;
  height: 30px;
  line-height: 30px;
  margin: 0 2px;
}

:deep(.el-button--danger.is-disabled) {
  background-color: #fff1f0 !important;
  color: #fab0b0 !important;
  border-color: #ffccc7 !important;
  cursor: not-allowed;
}

.batch-delete-confirm-content,
.delete-confirm-content {
  padding: 8px 0;
}

.selected-count,
.delete-email {
  color: #f56c6c;
  font-weight: 600;
}

.delete-warning {
  margin-top: 8px;
  color: #f56c6c;
  font-size: 12px;
  padding: 8px 10px;
  background-color: #fff1f0;
  border-radius: 6px;
  display: flex;
  align-items: center;
  gap: 6px;
}

@media (max-width: 1280px) {
  .user-management-content {
    padding: 14px;
  }

  :deep(.filter-card .el-card__body) {
    padding: 14px;
  }
}

@media (min-width: 601px) and (max-width: 992px) {
  .page-operations {
    align-items: stretch;
  }

  .batch-delete-btn {
    width: 100%;
    justify-content: center;
  }

  .filter-actions {
    justify-content: flex-start;
  }

  .pagination-container {
    justify-content: center;
  }
}

@media (min-width: 601px) and (max-width: 768px) {
  .user-management-content {
    padding: 12px;
  }

  .page-title {
    font-size: 17px;
  }

  :deep(.filter-card .el-card__body) {
    padding: 12px;
  }

  .filter-actions {
    width: 100%;
  }

  .filter-actions .el-button {
    flex: 1;
    min-width: 0;
  }

  :deep(.el-table) {
    font-size: 11px;
    min-height: 260px;
  }

  :deep(.el-table th) {
    padding: 8px 0;
  }

  :deep(.el-table td) {
    padding: 8px 0;
  }

  .pagination-container {
    padding: 12px;
  }

  :deep(.el-pagination) {
    width: 100%;
    justify-content: center;
  }
}

</style>

