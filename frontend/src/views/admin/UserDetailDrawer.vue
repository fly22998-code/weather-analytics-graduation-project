<template>
  <el-drawer 
    v-model="visible" 
    title="用户详情" 
    direction="rtl"
    size="50%"
    :before-close="handleClose"
  >
    <div class="user-detail-container">
      <el-card class="detail-card">
        <template #header> <!-- 替换slot="header"为Vue3标准写法 -->
          <div class="card-header">基本信息</div>
        </template>
        <!-- 修复column="1" → :column="1"（数字类型绑定） -->
        <el-descriptions :column="1" border>
          <el-descriptions-item label="用户ID">{{ user?.id || '-' }}</el-descriptions-item>
          <el-descriptions-item label="用户名">{{ user?.username || '-' }}</el-descriptions-item>
          <el-descriptions-item label="邮箱">{{ user?.email || '-' }}</el-descriptions-item>
          <el-descriptions-item label="手机号">{{ user?.phone || '未设置' }}</el-descriptions-item>
          <el-descriptions-item label="性别">{{ user?.gender_display || '未设置' }}</el-descriptions-item>
          <el-descriptions-item label="生日">{{ user?.birthday || '未设置' }}</el-descriptions-item>
          <el-descriptions-item label="最后修改密码时间">
            {{ user?.password_reset_time ? utcToShanghai(user.password_reset_time) : '从未修改' }}
          </el-descriptions-item>
          <el-descriptions-item label="用户角色">
            <el-tag 
              :type="getRoleTagType(user?.user_role)"
            >
              {{ user?.user_role_display || '未知' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="用户状态">
            <el-tag 
              :type="user?.is_banned ? 'danger' : 'success'"
            >
              {{ user?.is_banned_display || '未知' }}
            </el-tag>
          </el-descriptions-item>
        </el-descriptions>
      </el-card>

      <el-card class="detail-card" style="margin-top: 16px;">
        <template #header>
          <div class="card-header">登录信息</div>
        </template>
        <!-- 修复column="2" → :column="2"（数字类型绑定） -->
        <el-descriptions :column="2" border>
          <el-descriptions-item label="上次登录IP">{{ user?.last_login_ip || '从未登录' }}</el-descriptions-item>
          <el-descriptions-item label="最后登录时间">
            {{ user?.last_login_time ? utcToShanghai(user.last_login_time) : '从未登录' }}
          </el-descriptions-item>
          <el-descriptions-item label="登录次数">{{ user?.login_count || 0 }}</el-descriptions-item>
          <el-descriptions-item label="注册时间">
            {{ user?.created_at ? utcToShanghai(user.created_at) : '未知' }}
          </el-descriptions-item>
        </el-descriptions>
      </el-card>

      <el-card class="detail-card" style="margin-top: 16px;" v-if="user?.is_banned">
        <template #header>
          <div class="card-header">封禁信息</div>
        </template>
        <!-- 修复column="1" → :column="1"（数字类型绑定） -->
        <el-descriptions :column="1" border>
          <el-descriptions-item label="封禁时间">{{ user?.ban_time ? utcToShanghai(user.ban_time) : '未知' }}</el-descriptions-item>
          <el-descriptions-item label="封禁原因">{{ user?.ban_reason || '未填写' }}</el-descriptions-item>
        </el-descriptions>
      </el-card>

      <div class="detail-actions" style="margin-top: 20px; text-align: right;">
        <el-button @click="handleClose">关闭</el-button>
        <el-button 
          type="primary" 
          @click="handleEdit"
          v-if="showEditButton(user)"
        >
          编辑用户
        </el-button>
      </div>
    </div>
  </el-drawer>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue';

// 定义用户类型接口（替代any，增强类型安全）
interface User {
  id?: number | string;
  username?: string;
  email?: string;
  phone?: string;
  gender_display?: string;
  birthday?: string;
  password_reset_time?: string;
  user_role?: 'ADMIN' | 'VIP' | 'NORMAL' | string;
  user_role_display?: string;
  is_banned?: boolean;
  is_banned_display?: string;
  last_login_ip?: string;
  last_login_time?: string;
  login_count?: number;
  created_at?: string;
  ban_time?: string;
  ban_reason?: string;
  [key: string]: any; // 兼容额外属性
}

interface Props {
  visible: boolean;
  user?: User; // 改为可选，避免空值错误
  utcToShanghai: (utcTime: string) => string;
  showEditButton: (user?: User) => boolean; // 适配可选参数
}

interface Emits {
  (e: 'close'): void;
  (e: 'edit'): void;
}

const props = defineProps<Props>();
const emits = defineEmits<Emits>();

const visible = ref(props.visible);

// 监听visible prop的变化
watch(() => props.visible, (newVal) => {
  visible.value = newVal;
}, { immediate: true }); // 立即执行，确保初始值同步

// 监听内部visible的变化并通知父组件
watch(visible, (newVal) => {
  if (!newVal) {
    emits('close');
  }
});

// 处理关闭事件
const handleClose = () => {
  visible.value = false;
};

// 处理编辑事件
const handleEdit = () => {
  emits('edit');
};

// 封装角色标签类型逻辑（简化模板）
const getRoleTagType = computed(() => {
  return (role?: string) => {
    switch (role) {
      case 'ADMIN':
        return 'primary';
      case 'VIP':
        return 'success';
      default:
        return 'info';
    }
  };
});
</script>

<style scoped>
.user-detail-container {
  padding: 10px 0;
}

.detail-card {
  border-radius: 6px;
  margin-bottom: 16px; /* 增加底部间距，优化布局 */
}

/* 深度选择器优化样式 */
:deep(.detail-card .el-card__header) {
  padding: 12px 16px;
  border-bottom: 1px solid #f0f0f0;
  background-color: #f8fafc; /* 增加背景色，区分头部 */
}

.card-header {
  font-size: 16px;
  font-weight: 600;
  color: #1e293b;
  margin: 0; /* 重置默认margin */
}

:deep(.el-descriptions__label) {
  font-weight: 500;
  color: #64748b;
  width: 120px; /* 固定标签宽度，对齐更整齐 */
}

:deep(.el-descriptions__content) {
  color: #1e293b;
  font-weight: 400;
}

:deep(.el-tag) {
  font-size: 12px;
  padding: 2px 8px;
}

.detail-actions {
  padding: 16px;
  border-top: 1px solid #f0f0f0; /* 增加分隔线 */
  margin-top: 8px;
}

/* 适配小屏幕 */
@media (max-width: 768px) {
  :deep(.el-descriptions) {
    --el-descriptions-column: 1 !important; /* 移动端强制单列 */
  }
  
  :deep(.el-descriptions__label) {
    width: 100px;
  }
}
</style>