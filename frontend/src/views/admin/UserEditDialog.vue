<template>
  <el-dialog 
    v-model="visible" 
    title="编辑用户" 
    width="600px"
    :before-close="handleClose"
  >
    <el-form 
      :model="editForm" 
      :rules="editRules"
      ref="editFormRef"
      label-width="100px"
      class="edit-form"
    >
      <el-form-item label="用户ID">
        <el-input v-model="editForm.id" disabled />
      </el-form-item>
      
      <el-form-item label="邮箱">
        <el-input v-model="editForm.email" disabled />
      </el-form-item>

      <el-form-item label="用户名" prop="username">
        <el-input 
          v-model="editForm.username" 
          placeholder="请输入用户名（选填）"
          maxlength="20"
        />
      </el-form-item>
      
      <el-form-item label="手机号" prop="phone">
        <el-input 
          v-model="editForm.phone" 
          placeholder="请输入手机号（选填）"
          maxlength="11"
        />
      </el-form-item>

      <el-form-item label="性别" prop="gender">
        <el-select 
          v-model="editForm.gender" 
          placeholder="请选择性别（选填）"
          clearable
          teleported
          popper-class="user-edit-select-popper"
        >
          <el-option label="男" value="MALE" />
          <el-option label="女" value="FEMALE" />
          <el-option label="其他" value="OTHER" />
          <el-option label="保密" value="SECRET" />
        </el-select>
      </el-form-item>

      <el-form-item label="生日" prop="birthday">
        <el-date-picker
          v-model="editForm.birthday"
          type="date"
          placeholder="请选择生日（选填）"
          value-format="YYYY-MM-DD"
          :disabled-date="disableFutureDate"
          teleported
          popper-class="user-edit-picker-popper"
        />
      </el-form-item>
      
      <el-form-item label="用户角色" prop="userRole">
        <el-select 
          v-model="editForm.userRole" 
          placeholder="请选择用户角色"
          :disabled="isEditingSelf"
          teleported
          popper-class="user-edit-select-popper"
        >
          <el-option label="普通用户" value="NORMAL" />
          <el-option label="会员用户" value="VIP" />
          <el-option label="系统管理员" value="ADMIN" />
        </el-select>
      </el-form-item>
      
      <el-form-item label="用户状态" prop="status">
        <el-select 
          v-model="editForm.status" 
          placeholder="请选择用户状态"
          class="status-select"
          @change="handleStatusChange"
          :disabled="isEditingSelf"
          teleported
          popper-class="user-edit-select-popper"
        >
          <el-option label="正常" value="active" class="status-option active-option" />
          <el-option label="封禁" value="banned" class="status-option banned-option" />
        </el-select>
      </el-form-item>
      
      <el-form-item 
        label="封禁原因" 
        prop="banReason"
        v-if="editForm.status === 'banned'"
      >
        <el-input 
          v-model="editForm.banReason" 
          placeholder="请输入封禁原因"
          type="textarea"
          :rows="3" 
        />
      </el-form-item>
      
      <el-form-item label="注册时间">
        <el-input v-model="editForm.registerTime" disabled />
      </el-form-item>
    </el-form>
    
    <template #footer>
      <el-button @click="handleClose">取消</el-button>
      <el-button type="primary" @click="submitForm">保存</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, watch, nextTick, onMounted } from 'vue';
import { ElForm, ElMessage, FormItemRule } from 'element-plus';

// 定义用户类型接口（替代any，增强类型安全）
interface User {
  id?: number | string;
  email?: string;
  username?: string;
  phone?: string;
  gender?: 'MALE' | 'FEMALE' | 'OTHER' | 'SECRET' | string;
  birthday?: string;
  user_role?: 'NORMAL' | 'VIP' | 'ADMIN' | string;
  is_banned?: boolean;
  ban_reason?: string;
  created_at?: string;
  [key: string]: any; // 兼容额外属性
}

interface Props {
  visible: boolean;
  user?: User; // 改为可选，避免空值错误
  isEditingSelf: boolean;
  utcToShanghai: (utcTime: string) => string;
}

interface Emits {
  (e: 'close'): void;
  (e: 'save', formData: typeof editForm): void; // 精确类型，替代any
  (e: 'statusChange', value: string): void;
}

const props = defineProps<Props>();
const emits = defineEmits<Emits>();

const visible = ref(props.visible);
const editFormRef = ref<InstanceType<typeof ElForm> | null>(null); // 增加null类型，避免空值错误

// 编辑表单数据（精确类型定义）
const editForm = reactive({
  id: '',
  email: '',
  username: '',
  phone: '',
  gender: '' as 'MALE' | 'FEMALE' | 'OTHER' | 'SECRET' | '',
  birthday: '',
  userRole: '' as 'NORMAL' | 'VIP' | 'ADMIN' | '',
  status: '' as 'active' | 'banned' | '',
  banReason: '',
  registerTime: '',
  originalIsBanned: false,
  originalBanReason: ''
});

// 修复表单验证规则类型（解决gender.type不兼容问题）
const editRules = {
  username: [
    { max: 20, message: '用户名长度不能超过20个字符', trigger: 'blur' } as FormItemRule
  ],
  phone: [
    { 
      pattern: /^1[3-9]\d{9}$/, 
      message: '请输入有效的11位手机号', 
      trigger: 'blur', 
      required: false 
    } as FormItemRule
  ],
  gender: [
    { 
      type: 'string' as const,
      enum: ['MALE', 'FEMALE', 'OTHER', 'SECRET', ''] as const, 
      message: '无效的性别值', 
      trigger: 'change' 
    } as FormItemRule
  ],
  birthday: [
    { 
      type: 'string' as const, 
      pattern: /^\d{4}-\d{2}-\d{2}$/, 
      message: '请选择有效的日期格式', 
      trigger: 'change', 
      required: false 
    } as FormItemRule
  ],
  userRole: [
    { required: true, message: '请选择用户角色', trigger: 'change' } as FormItemRule
  ],
  status: [
    { required: true, message: '请选择用户状态', trigger: 'change' } as FormItemRule
  ],
  banReason: [
    { required: true, message: '请输入封禁原因', trigger: 'blur' } as FormItemRule,
    { min: 2, message: '封禁原因至少输入2个字符', trigger: 'blur' } as FormItemRule
  ]
};

// 日期选择限制（不能选择未来日期）
const disableFutureDate = (time: Date | null) => {
  // 增加null判断，避免time为null时报错
  if (!time) return false;
  return time > new Date();
};

// 监听visible prop的变化
watch(() => props.visible, (newVal) => {
  visible.value = newVal;
  if (newVal) {
    nextTick(() => {
      initializeForm();
    });
  }
}, { immediate: true }); // 立即执行，确保初始值同步

// 监听内部visible的变化并通知父组件
watch(visible, (newVal) => {
  if (!newVal) {
    emits('close');
  }
});

// 初始化表单数据（增加空值保护）
const initializeForm = () => {
  if (!props.user) return;
  
  // 重置表单，避免残留数据
  Object.assign(editForm, {
    id: props.user.id?.toString() || '', // 确保为字符串类型
    email: props.user.email || '',
    username: props.user.username || '',
    phone: props.user.phone || '',
    gender: props.user.gender || '',
    birthday: props.user.birthday || '',
    userRole: (props.user.user_role as 'NORMAL' | 'VIP' | 'ADMIN') || '',
    status: props.user.is_banned ? 'banned' : 'active',
    banReason: props.user.ban_reason || '',
    registerTime: props.user.created_at ? props.utcToShanghai(props.user.created_at) : '',
    originalIsBanned: !!props.user.is_banned, // 强制布尔值
    originalBanReason: props.user.ban_reason || ''
  });
};

// 处理状态变更（增加类型保护）
const handleStatusChange = (value: string) => {
  emits('statusChange', value);
  
  if (value === 'active') {
    editForm.banReason = '';
  } else if (value === 'banned' && editForm.originalIsBanned && !editForm.banReason) {
    editForm.banReason = editForm.originalBanReason;
  }
};

// 关闭对话框
const handleClose = () => {
  visible.value = false;
};

// 提交表单（优化异步验证逻辑）
const submitForm = async () => {
  if (!editFormRef.value) {
    ElMessage.warning('表单初始化失败，请重试');
    return;
  }
  
  try {
    // 正确的表单验证写法
    await editFormRef.value.validate();
    // 深拷贝，避免响应式对象传递问题
    const formData = JSON.parse(JSON.stringify(editForm));
    emits('save', formData);
    ElMessage.success('表单验证通过，准备提交');
  } catch (err) {
    console.error('表单验证失败:', err);
    ElMessage.error('表单验证失败，请检查输入内容');
  }
};

// 组件挂载时初始化表单
onMounted(() => {
  if (props.visible) {
    nextTick(() => {
      initializeForm();
    });
  }
});
</script>

<style scoped>
.edit-form { 
  margin-top: 10px; 
}

/* 深度选择器优化样式 */
:deep(.edit-form .el-form-item) { 
  margin-bottom: 18px; 
}

:deep(.el-dialog__body) { 
  max-height: 70vh; 
  overflow-y: auto; 
  padding: 20px; /* 增加内边距，优化布局 */
}

:global(.user-edit-select-popper),
:global(.user-edit-picker-popper),
:global(.user-edit-select-popper.el-popper),
:global(.user-edit-picker-popper.el-popper) {
  z-index: 5000 !important;
}

:deep(.status-select .banned-option) {
  color: #cf1322;
  font-weight: 500;
}

:deep(.status-select .el-select-dropdown__item.selected.banned-option) { 
  background-color: #fff1f0; 
}

:deep(.status-select .active-option) { 
  color: #52c41a; 
}

:deep(.status-select .el-select-dropdown__item.selected.active-option) { 
  background-color: #f6ffed; 
}

/* 优化文本域样式 */
:deep(.el-textarea__inner) {
  resize: vertical; /* 允许垂直调整大小 */
  min-height: 80px; /* 最小高度 */
}

/* 适配小屏幕 */
@media (max-width: 768px) {
  :deep(.el-dialog) {
    width: 90% !important;
  }
  
  :deep(.el-form-item__label) {
    width: 80px !important;
  }
}
</style>
