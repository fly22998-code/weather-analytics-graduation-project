<template>
  <aside
    class="admin-nav-shell"
    :class="{
      collapsed: collapsed && !isMobile,
      'is-mobile': isMobile,
      'is-mobile-open': isMobile && mobileOpen
    }"
  >
    <div class="sidebar-header">
      <div class="brand-block">
        <div class="brand-icon">
          <el-icon><Cloudy /></el-icon>
        </div>
        <transition name="brand-fade">
          <div v-if="!collapsed || isMobile" class="brand-copy">
            <div class="brand-title">天气分析预测系统</div>
            <div class="brand-subtitle">Admin Console</div>
          </div>
        </transition>
      </div>

      <button
        class="sidebar-toggle"
        type="button"
        :aria-label="toggleLabel"
        @click="$emit('toggle-collapse')"
      >
        <el-icon v-if="isMobile && mobileOpen"><Close /></el-icon>
        <el-icon v-else-if="collapsed && !isMobile"><Expand /></el-icon>
        <el-icon v-else><Fold /></el-icon>
      </button>
    </div>

    <div class="menu-scroll-area">
      <el-menu
        :default-active="currentRoute"
        :collapse="collapsed && !isMobile"
        :collapse-transition="false"
        class="sidebar-menu"
        background-color="#0f1733"
        text-color="#b4bccc"
        active-text-color="#ffffff"
        router
        @select="handleMenuSelect"
      >
        <el-menu-item index="/admin/usermanagement">
          <el-icon><User /></el-icon>
          <span>用户管理</span>
        </el-menu-item>

        <el-menu-item index="/admin/weather-analysis">
          <el-icon><Histogram /></el-icon>
          <span>天气数据分析</span>
        </el-menu-item>

        <el-menu-item index="/admin/forecast">
          <el-icon><Sunny /></el-icon>
          <span>天气预测</span>
        </el-menu-item>

        <template v-if="collapsed && !isMobile">
          <el-menu-item index="/admin/system-settings">
            <el-icon><Setting /></el-icon>
            <span>系统设置</span>
          </el-menu-item>
          <el-menu-item index="/admin/traffic-stats">
            <el-icon><DataLine /></el-icon>
            <span>流量统计</span>
          </el-menu-item>
          <el-menu-item index="/admin/log-management">
            <el-icon><Document /></el-icon>
            <span>日志管理</span>
          </el-menu-item>
        </template>

        <el-sub-menu v-else index="system">
          <template #title>
            <el-icon><Setting /></el-icon>
            <span>系统管理</span>
          </template>
          <el-menu-item index="/admin/system-settings">
            <el-icon><Tools /></el-icon>
            <span>系统设置</span>
          </el-menu-item>
          <el-menu-item index="/admin/traffic-stats">
            <el-icon><DataLine /></el-icon>
            <span>流量统计</span>
          </el-menu-item>
          <el-menu-item index="/admin/log-management">
            <el-icon><Document /></el-icon>
            <span>日志管理</span>
          </el-menu-item>
        </el-sub-menu>
      </el-menu>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useRoute } from 'vue-router';
import {
  Cloudy,
  Close,
  DataLine,
  Document,
  Expand,
  Fold,
  Histogram,
  Setting,
  Sunny,
  Tools,
  User
} from '@element-plus/icons-vue';

const props = withDefaults(
  defineProps<{
    collapsed?: boolean;
    isMobile?: boolean;
    mobileOpen?: boolean;
  }>(),
  {
    collapsed: false,
    isMobile: false,
    mobileOpen: false
  }
);

const emit = defineEmits<{
  (e: 'toggle-collapse'): void;
  (e: 'close-mobile'): void;
}>();

const route = useRoute();

const currentRoute = computed(() => route.path);

const toggleLabel = computed(() => {
  if (props.isMobile) {
    return props.mobileOpen ? '关闭侧边栏' : '打开侧边栏';
  }

  return props.collapsed ? '展开侧边栏' : '收起侧边栏';
});

const handleMenuSelect = () => {
  if (props.isMobile) {
    emit('close-mobile');
  }
};
</script>

<style scoped>
.admin-nav-shell {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: linear-gradient(180deg, #101935 0%, #0f1733 100%);
  color: #b4bccc;
}

.sidebar-header {
  min-height: 72px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 14px 14px 12px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.brand-block {
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 12px;
}

.brand-icon {
  width: 40px;
  height: 40px;
  border-radius: 14px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #3277ff 0%, #55b3ff 100%);
  color: #ffffff;
  font-size: 20px;
  flex-shrink: 0;
  box-shadow: 0 12px 24px rgba(50, 119, 255, 0.3);
}

.brand-copy {
  min-width: 0;
  overflow: hidden;
}

.brand-title {
  font-size: 15px;
  font-weight: 700;
  color: #ffffff;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.brand-subtitle {
  margin-top: 4px;
  font-size: 12px;
  color: rgba(180, 188, 204, 0.86);
  letter-spacing: 0.08em;
}

.sidebar-toggle {
  width: 36px;
  height: 36px;
  flex-shrink: 0;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.06);
  color: #d8e2ff;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: background-color 0.2s ease, transform 0.2s ease, border-color 0.2s ease;
}

.sidebar-toggle:hover {
  background: rgba(255, 255, 255, 0.12);
  border-color: rgba(255, 255, 255, 0.16);
  transform: translateY(-1px);
}

.menu-scroll-area {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 10px 0 16px;
  scrollbar-width: none;
}

.menu-scroll-area::-webkit-scrollbar {
  display: none;
}

.sidebar-menu {
  border-right: none;
}

:deep(.sidebar-menu.el-menu) {
  border-right: none;
}

:deep(.sidebar-menu .el-menu-item),
:deep(.sidebar-menu .el-sub-menu__title) {
  height: 48px;
  line-height: 48px;
  margin: 0 10px 6px;
  border-radius: 14px;
  transition: background-color 0.2s ease, color 0.2s ease, transform 0.2s ease;
  overflow: hidden;
}

:deep(.sidebar-menu .el-menu-item:hover),
:deep(.sidebar-menu .el-sub-menu__title:hover) {
  background: rgba(255, 255, 255, 0.1) !important;
  color: #ffffff !important;
}

:deep(.sidebar-menu .el-menu-item.is-active) {
  background: linear-gradient(135deg, #2563eb 0%, #3b82f6 100%) !important;
  color: #ffffff !important;
  box-shadow: 0 12px 24px rgba(37, 99, 235, 0.28);
}

:deep(.sidebar-menu .el-menu-item .el-icon),
:deep(.sidebar-menu .el-sub-menu__title .el-icon) {
  width: 18px;
  height: 18px;
  margin-right: 12px;
  font-size: 18px;
}

:deep(.sidebar-menu .el-sub-menu .el-menu) {
  background: rgba(255, 255, 255, 0.03);
}

:deep(.sidebar-menu .el-sub-menu .el-menu-item) {
  margin-left: 18px;
}

.collapsed .sidebar-header {
  min-height: 88px;
  justify-content: center;
  flex-direction: column;
  gap: 10px;
  padding: 14px 8px 12px;
}

.collapsed .brand-block {
  flex: 0 0 auto;
  justify-content: center;
}

.collapsed .sidebar-toggle {
  width: 32px;
  height: 32px;
  border-radius: 10px;
}

.collapsed .menu-scroll-area {
  padding-top: 12px;
}

.collapsed :deep(.sidebar-menu.el-menu--collapse) {
  width: 100%;
}

.collapsed :deep(.sidebar-menu.el-menu--collapse .el-menu-item),
.collapsed :deep(.sidebar-menu.el-menu--collapse .el-sub-menu__title) {
  width: calc(100% - 16px);
  height: 52px;
  margin: 0 8px 10px;
  padding: 0 !important;
  justify-content: center;
  border-radius: 18px;
}

.collapsed :deep(.sidebar-menu.el-menu--collapse .el-menu-item .el-icon),
.collapsed :deep(.sidebar-menu.el-menu--collapse .el-sub-menu__title .el-icon) {
  margin-right: 0;
}

.collapsed :deep(.sidebar-menu.el-menu--collapse .el-sub-menu__icon-arrow) {
  display: none;
}

.brand-fade-enter-active,
.brand-fade-leave-active {
  transition: opacity 0.18s ease, transform 0.18s ease;
}

.brand-fade-enter-from,
.brand-fade-leave-to {
  opacity: 0;
  transform: translateX(-6px);
}

@media (max-width: 768px) {
  .admin-nav-shell {
    box-shadow: 8px 0 32px rgba(15, 23, 42, 0.22);
  }

  .sidebar-header {
    min-height: 68px;
  }

  :deep(.sidebar-menu .el-menu-item),
  :deep(.sidebar-menu .el-sub-menu__title) {
    margin-left: 12px;
    margin-right: 12px;
  }
}
</style>
