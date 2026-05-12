// src/main.ts
import { createApp } from 'vue';
import App from './App.vue';
import router from './router';
import ElementPlus from 'element-plus';
import 'element-plus/dist/index.css';
import * as ElementPlusIconsVue from '@element-plus/icons-vue';
import { restoreSessionFromCookie } from '@/utils/requests';
import { initLocale } from '@/utils/i18n';
// 新增：引入Tailwind核心样式文件
import './style.css'; 

const app = createApp(App);
app.use(router);
app.use(ElementPlus);
initLocale();

for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component);
}

restoreSessionFromCookie().finally(() => {
  app.mount('#app');
  (window as any).app = app;

  let lastSessionCheckAt = 0;
  const silentlyCheckSession = () => {
    const now = Date.now();
    if (now - lastSessionCheckAt < 5000) return;
    lastSessionCheckAt = now;
    restoreSessionFromCookie().catch(() => {});
  };

  window.addEventListener('focus', silentlyCheckSession);
  document.addEventListener('visibilitychange', () => {
    if (!document.hidden) silentlyCheckSession();
  });
});
