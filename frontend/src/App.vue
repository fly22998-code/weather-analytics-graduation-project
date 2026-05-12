<template>
  <div id="app" v-if="isRouterReady">
    <router-view v-if="isAuthPage" :key="`auth:${route.fullPath}`" />

    <template v-else>
      <GlobalAuthDialog />
      <NavMenu v-if="!isAdminRoute" />

      <div
        v-else
        class="admin-wrapper"
        :class="{
          'sidebar-collapsed': isAdminSidebarCollapsed && !isMobileAdminLayout,
          'sidebar-open': isMobileAdminLayout && isAdminSidebarOpen
        }"
      >
        <div
          v-if="isMobileAdminLayout && isAdminSidebarOpen"
          class="admin-sidebar-mask"
          @click="closeAdminSidebar"
        ></div>

        <AdminNavMenu
          class="admin-sidebar"
          :collapsed="isAdminSidebarCollapsed"
          :is-mobile="isMobileAdminLayout"
          :mobile-open="isAdminSidebarOpen"
          @toggle-collapse="handleAdminSidebarToggle"
          @close-mobile="closeAdminSidebar"
        />

        <div class="admin-content">
          <router-view />
        </div>
      </div>

      <router-view v-if="!isAdminRoute" :key="`main:${route.fullPath}`" class="user-content" />
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import NavMenu from './components/NavMenu.vue';
import AdminNavMenu from './components/Admin_NavMenu.vue';
import GlobalAuthDialog from './components/GlobalAuthDialog.vue';
import 'element-plus/dist/index.css';

const route = useRoute();
const router = useRouter();
const authPaths = ['/userlogin', '/register', '/password-reset'];

const isAdminSidebarCollapsed = ref(false);
const isMobileAdminLayout = ref(false);
const isAdminSidebarOpen = ref(false);
const isRouterReady = ref(false);

const isAdminRoute = computed(() => route.path.startsWith('/admin'));
const isAuthPage = computed(() => authPaths.some((path) => route.path.startsWith(path)));

const updateAdminLayoutMode = () => {
  if (typeof window === 'undefined') {
    return;
  }

  const nextIsMobile = false;
  isMobileAdminLayout.value = nextIsMobile;

  if (nextIsMobile) {
    isAdminSidebarOpen.value = false;
  }
};

const handleAdminSidebarToggle = () => {
  if (isMobileAdminLayout.value) {
    isAdminSidebarOpen.value = !isAdminSidebarOpen.value;
    return;
  }

  isAdminSidebarCollapsed.value = !isAdminSidebarCollapsed.value;
};

const closeAdminSidebar = () => {
  if (isMobileAdminLayout.value) {
    isAdminSidebarOpen.value = false;
  }
};

onMounted(() => {
  updateAdminLayoutMode();
  window.addEventListener('resize', updateAdminLayoutMode);
  router.isReady().then(() => {
    isRouterReady.value = true;
  });

  router.afterEach((to) => {
    console.log('路由切换到:', to.path);
    console.log('是否登录页?', authPaths.includes(to.path));
    console.log('是否管理员路由?', to.path.startsWith('/admin'));
  });
});

watch(
  () => route.fullPath,
  () => {
    closeAdminSidebar();
  }
);

onUnmounted(() => {
  window.removeEventListener('resize', updateAdminLayoutMode);
});

console.log('当前路径:', route.path);
console.log('是否登录页?', isAuthPage.value);
console.log('是否管理员路由?', isAdminRoute.value);
console.log('所有鉴权路径:', authPaths);
console.log('管理员路由判断:', route.path.startsWith('/admin'));

import('element-plus').then((el) => {
  console.log('Element Plus加载成功:', !!el.ElMenu);
});
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html,
body,
#app {
  width: 100%;
  max-width: 100%;
}

body {
  font-family: Arial, sans-serif;
}

html[lang="zh-TW"] body,
html[lang="ja-JP"] body,
html[lang="ko-KR"] body,
html[lang="zh-TW"] #app,
html[lang="ja-JP"] #app,
html[lang="ko-KR"] #app {
  font-family: "Microsoft JhengHei", "PingFang TC", "Noto Sans CJK TC", "Noto Sans CJK JP", "Noto Sans CJK KR", "Yu Gothic", "Malgun Gothic", Arial, sans-serif;
}

html {
  -ms-overflow-style: none;
  scrollbar-width: none;
}

html::-webkit-scrollbar {
  display: none;
}

body {
  overflow-x: hidden;
  margin: 0;
  padding: 0;
  min-height: 100vh;
}

html.site-dark-mode,
body.site-dark-mode,
html.site-dark-mode #app {
  background-color: #0f172a;
}

body.site-dark-mode {
  margin: 0 !important;
  padding: 0 !important;
  border: 0 !important;
  border-radius: 0 !important;
  box-shadow: none !important;
}

html.theme-transitioning,
html.theme-transitioning body,
html.theme-transitioning #app,
body.theme-transitioning,
body.theme-transitioning #app,
html.theme-transitioning .nav-bar,
html.theme-transitioning .weather-container,
html.theme-transitioning .weather-card,
html.theme-transitioning .hourly-card,
html.theme-transitioning .ios-card,
html.theme-transitioning .city-pill .pill-content,
html.theme-transitioning .search-box,
html.theme-transitioning .search-result,
html.theme-transitioning .unit-toggle-btn,
html.theme-transitioning .nav-btn,
html.theme-transitioning .nav-arrow-btn,
html.theme-transitioning .user-email,
html.theme-transitioning .user-dropdown,
html.theme-transitioning .drawer-panel,
html.theme-transitioning .drawer-header,
html.theme-transitioning .drawer-body,
html.theme-transitioning .drawer-footer,
html.theme-transitioning .info-row,
html.theme-transitioning .avatar-interactive-wrapper {
  transition:
    background-color 0.28s ease,
    background 0.28s ease,
    color 0.22s ease,
    border-color 0.28s ease,
    box-shadow 0.28s ease,
    fill 0.22s ease,
    stroke 0.22s ease !important;
}

@media (prefers-reduced-motion: reduce) {
  html.theme-transitioning,
  html.theme-transitioning body,
  html.theme-transitioning #app,
  body.theme-transitioning,
  body.theme-transitioning #app,
  html.theme-transitioning .nav-bar,
  html.theme-transitioning .weather-container,
  html.theme-transitioning .weather-card,
  html.theme-transitioning .hourly-card,
  html.theme-transitioning .ios-card,
  html.theme-transitioning .city-pill .pill-content,
  html.theme-transitioning .search-box,
  html.theme-transitioning .search-result,
  html.theme-transitioning .unit-toggle-btn,
  html.theme-transitioning .nav-btn,
  html.theme-transitioning .nav-arrow-btn,
  html.theme-transitioning .user-email,
  html.theme-transitioning .user-dropdown,
  html.theme-transitioning .drawer-panel,
  html.theme-transitioning .drawer-header,
  html.theme-transitioning .drawer-body,
  html.theme-transitioning .drawer-footer,
  html.theme-transitioning .info-row,
  html.theme-transitioning .avatar-interactive-wrapper {
    transition: none !important;
  }
}

.user-content {
  padding: 20px;
  max-width: 100%;
  margin: 0 auto;
  min-height: calc(100vh - 60px);
}

.user-content.user-content--full-bleed {
  padding: 0;
}

.admin-wrapper {
  --admin-sidebar-width: 220px;
  --admin-sidebar-collapsed-width: 88px;
  --admin-active-sidebar-width: var(--admin-sidebar-width);
  display: flex;
  min-height: 100vh;
  position: relative;
  background-color: #f5f7fa;
  overflow-x: hidden;
}

.admin-wrapper.sidebar-collapsed {
  --admin-active-sidebar-width: var(--admin-sidebar-collapsed-width);
}

.admin-sidebar-mask {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.24);
  backdrop-filter: blur(2px);
  z-index: 19;
}

.admin-sidebar {
  width: var(--admin-active-sidebar-width);
  flex-shrink: 0;
  position: fixed;
  left: 0;
  top: 0;
  height: 100vh;
  z-index: 20;
  background-color: #fff;
  border-right: 1px solid #e6e8eb;
  overflow: hidden;
  transition: width 0.28s ease, transform 0.28s ease, box-shadow 0.28s ease;
}

.admin-content {
  flex: 1;
  min-width: 0;
  margin-left: var(--admin-active-sidebar-width);
  padding: 20px;
  background-color: #f5f7fa;
  min-height: 100vh;
  transition: margin-left 0.28s ease, padding 0.28s ease;
}

</style>
