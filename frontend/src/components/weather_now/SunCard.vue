<template>
  <div class="sun-card" v-if="sunData">
    <div class="card-title-row">
      <div class="title-left">
        <span class="sun-text-label">{{ nextSunEventLabel }}</span>
      </div>
      <span class="sun-status">{{ sunCountdownText }}</span>
    </div>

    <div class="sun-layout-vertical">
      <div class="chart-container-large">
  <svg viewBox="0 10 260 130" class="sun-svg-large">
    <defs>
      <linearGradient id="sunStrokeGradientLarge" x1="0" y1="0" x2="1" y2="0">
        <stop offset="0%" stop-color="#FF512F" />
        <stop offset="100%" stop-color="#F09819" />
      </linearGradient>
      <linearGradient id="moonStrokeGradientLarge" x1="0" y1="0" x2="1" y2="0">
        <stop offset="0%" stop-color="#2E3192" />
        <stop offset="100%" stop-color="#1BFFFF" />
      </linearGradient>
      <filter id="glowLarge" x="-50%" y="-50%" width="200%" height="200%">
        <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
        <feColorMatrix type="matrix" values="1 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 1 0" in="coloredBlur" result="coloredBlur"/>
        <feMerge><feMergeNode in="coloredBlur"/><feMergeNode in="SourceGraphic"/></feMerge>
      </filter>
    </defs>
    
    <path d="M 20,130 A 110,110 0 1,1 240,130" fill="none" :stroke="isDarkMode ? '#334155' : '#e2e8f0'" stroke-width="2" stroke-dasharray="6 6" stroke-linecap="round" />
    <line x1="10" y1="130" x2="250" y2="130" :stroke="isDarkMode ? '#475569' : '#cbd5e1'" stroke-width="1.5" stroke-dasharray="4 4" opacity="0.4"/>
    
    <path d="M 20,130 A 110,110 0 1,1 240,130" fill="none" :stroke="isNight ? 'url(#moonStrokeGradientLarge)' : 'url(#sunStrokeGradientLarge)'" stroke-width="5" stroke-linecap="round" :stroke-dasharray="circularDashArrayLarge" stroke-dashoffset="0" />
    
    <g :transform="`translate(${sunPositionLarge.x}, ${sunPositionLarge.y})`">
      <g v-if="!isNight">
        <circle r="14" fill="rgba(240, 152, 25, 0.2)" />
        <circle r="8" fill="#fff" stroke="#F09819" stroke-width="3" filter="url(#glowLarge)" />
      </g>
      <g v-else>
        <circle r="14" fill="rgba(27, 255, 255, 0.15)" />
        <path d="M 0 -8 A 8 8 0 1 1 0 8 A 6 6 0 1 0 0 -8 Z" fill="#fff" stroke="#2E3192" stroke-width="1.5" filter="url(#glowLarge)" transform="rotate(-25)"/>
      </g>
    </g>
  </svg>
</div>

      <div class="sun-data-row">
        <div class="data-group left">
          <span class="data-label">{{ sunChartLabels.leftLabel }}</span>
          <span class="data-time">{{ sunChartLabels.leftTime }}</span>
        </div>
        <div class="data-group center">
          <span class="duration-pill" :class="{ 'night-mode': isNight }">
            {{ durationInfo.label }} {{ durationInfo.value }}
          </span>
        </div>
        <div class="data-group right">
          <span class="data-label">{{ sunChartLabels.rightLabel }}</span>
          <span class="data-time">{{ sunChartLabels.rightTime }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue';

const props = defineProps({
  sunData: { type: Object, default: () => null },
  timezoneOffset: { type: [String, Number], default: null },
  isDarkMode: { type: Boolean, default: false }
});

const currentTime = ref(new Date());
let timer = null;

onMounted(() => {
  timer = setInterval(() => { currentTime.value = new Date(); }, 1000);
});

onUnmounted(() => {
  if (timer) clearInterval(timer);
});

const parseTimezoneOffset = (offsetStr) => {
  if (typeof offsetStr === 'number') return offsetStr;
  if (!offsetStr) return 0;
  const match = offsetStr.match(/([+-])(\d{1,2}):?(\d{2})?/);
  if (!match) return 0;
  const [_, sign, hours, minutes] = match;
  const totalMinutes = parseInt(hours) * 60 + (parseInt(minutes) || 0);
  return sign === '-' ? -totalMinutes : totalMinutes;
};

const getMinutes = (timeStr) => {
  if (!timeStr || timeStr === '--:--') return 0;
  const [h, m] = timeStr.split(':').map(Number);
  return h * 60 + m;
};

const targetTime = computed(() => {
  const now = currentTime.value;
  if (!props.timezoneOffset && props.timezoneOffset !== 0) return now;
  try {
    const offsetMinutes = parseTimezoneOffset(props.timezoneOffset);
    const utcMs = now.getTime() + (now.getTimezoneOffset() * 60000);
    return new Date(utcMs + (offsetMinutes * 60000));
  } catch (e) { return now; }
});

const todaySunrise = computed(() => props.sunData?.sun?.[0]?.sunrise || '--:--');
const todaySunset = computed(() => props.sunData?.sun?.[0]?.sunset || '--:--');
const tomorrowSunrise = computed(() => props.sunData?.sun?.[1]?.sunrise || '--:--');

const currentSunState = computed(() => {
  if (todaySunrise.value === '--:--' || todaySunset.value === '--:--') return 'day';
  const nowMin = targetTime.value.getHours() * 60 + targetTime.value.getMinutes();
  if (nowMin < getMinutes(todaySunrise.value)) return 'pre_dawn';
  if (nowMin > getMinutes(todaySunset.value)) return 'post_sunset';
  return 'day';
});

const isNight = computed(() => currentSunState.value === 'pre_dawn' || currentSunState.value === 'post_sunset');

const sunChartLabels = computed(() => {
  if (isNight.value) {
    return { leftLabel: '日落', leftTime: todaySunset.value, rightLabel: '日出', rightTime: tomorrowSunrise.value };
  }
  return { leftLabel: '日出', leftTime: todaySunrise.value, rightLabel: '日落', rightTime: todaySunset.value };
});

const nextSunEventLabel = computed(() => currentSunState.value === 'day' ? '日落' : '日出');

const durationInfo = computed(() => {
  if (todaySunrise.value === '--:--' || todaySunset.value === '--:--') return { label: '日照', value: '--' };
  const riseMin = getMinutes(todaySunrise.value);
  const setMin = getMinutes(todaySunset.value);
  let duration = 0;
  let label = '日照';
  if (!isNight.value) {
    duration = setMin - riseMin;
  } else {
    label = '月照';
    const nextRise = tomorrowSunrise.value !== '--:--' ? getMinutes(tomorrowSunrise.value) : 6 * 60;
    const minsUntilMidnight = (24 * 60) - setMin;
    duration = minsUntilMidnight + nextRise;
  }
  const h = Math.floor(duration / 60);
  const m = duration % 60;
  return { label, value: `${h}小时${m}分` };
});

const sunCountdownText = computed(() => {
  const now = targetTime.value;
  if (todaySunset.value === '--:--') return '加载中';
  const nowMin = now.getHours() * 60 + now.getMinutes();
  let diffMins = 0;
  if (currentSunState.value === 'pre_dawn') diffMins = getMinutes(todaySunrise.value) - nowMin;
  else if (currentSunState.value === 'day') diffMins = getMinutes(todaySunset.value) - nowMin;
  else {
    if (tomorrowSunrise.value === '--:--') return '日落已过';
    const [nH, nM] = tomorrowSunrise.value.split(':').map(Number);
    const tmr = new Date(now); tmr.setDate(tmr.getDate() + 1); tmr.setHours(nH, nM, 0, 0);
    diffMins = Math.floor((tmr - now) / 60000);
  }
  if (diffMins <= 0) return '即将发生';
  if (diffMins < 60) return `${diffMins}分钟后`;
  return `${Math.ceil(diffMins / 60)}小时后`;
});

const sunProgressValue = computed(() => {
  if (todaySunrise.value === '--:--' || todaySunset.value === '--:--') return 0;
  const nowMin = targetTime.value.getHours() * 60 + targetTime.value.getMinutes();
  const riseMin = getMinutes(todaySunrise.value);
  const setMin = getMinutes(todaySunset.value);
  let progress = 0;
  if (currentSunState.value === 'day') progress = (nowMin - riseMin) / (setMin - riseMin);
  else {
    const nextRise = tomorrowSunrise.value !== '--:--' ? getMinutes(tomorrowSunrise.value) : 360;
    const totalNight = (24 * 60 - setMin) + nextRise;
    const elapsed = currentSunState.value === 'post_sunset' ? (nowMin - setMin) : ((24 * 60 - setMin) + nowMin);
    progress = elapsed / totalNight;
  }
  return Math.max(0, Math.min(1, progress));
});

const sunPositionLarge = computed(() => {
  const angle = Math.PI * (1 - sunProgressValue.value);
  return { x: 130 + 110 * Math.cos(angle), y: 130 - 110 * Math.sin(angle) };
});

const circularDashArrayLarge = computed(() => {
  const total = Math.PI * 110;
  return `${total * sunProgressValue.value} ${total}`;
});
</script>

<style scoped>
/* =========================================
   1. 卡片容器 (85% 等比例缩小)
   ========================================= */
.sun-card { 
  width: 272px; /* 320 * 0.85 */
  height: 187px; /* 220 * 0.85 */
  padding: 14px; /* 16 * 0.85 */
  
  /* 玻璃拟态背景 */
  background: var(--glass-bg, #ffffff); 
  backdrop-filter: blur(20px) saturate(120%); 
  
  border: 1px solid var(--glass-border, rgba(0,0,0,0.1)); 
  border-radius: 20px; /* 24 * 0.85 */
  box-shadow: 0 7px 27px rgba(0, 0, 0, 0.05); /* 阴影等比缩小 */
  
  position: relative; 
  overflow: hidden; 
  display: flex; 
  flex-direction: column; 
  justify-content: space-between; 
  animation: cardEntrance 0.6s cubic-bezier(0.2, 0.8, 0.2, 1) backwards; 
  transition: background 0.5s ease; 
  box-sizing: border-box;
  isolation: isolate; /* 独立渲染层 */
  flex-shrink: 0;
}

/* 深色模式适配 */
.dark-mode .sun-card { 
  background: var(--glass-bg, rgba(30, 41, 59, 0.6));
  border-color: var(--glass-border, rgba(255, 255, 255, 0.1));
  box-shadow: 0 7px 27px rgba(0, 0, 0, 0.2);
  color: #fff;
}

/* =========================================
   2. 标题区域
   ========================================= */
.card-title-row { 
  display: flex; 
  justify-content: space-between; 
  align-items: center; 
  margin-bottom: 0; 
  /* 确保标题行不被压缩 */
  flex-shrink: 0; 
}

.title-left { 
  display: flex; 
  align-items: center; 
  gap: 7px; /* 8 * 0.85 */
}

/* --- 核心修改：统一左上角字体样式 --- */
.sun-text-label { 
  font-size: 12px; /* 14 * 0.85 */
  font-weight: 600; 
  color: rgba(0, 0, 0, 0.85); 
  
  /* --- 关键对齐参数 --- */
  margin-left: 3px; /* 4 * 0.85 取整 */
  /* ------------------ */
  
  letter-spacing: normal;
  line-height: 1.4;
}

/* 深色模式标题 */
.dark-mode .sun-text-label { 
  color: rgba(255, 255, 255, 0.6); 
}

/* 右侧倒计时胶囊 */
.sun-status { 
  background: rgba(254, 243, 199, 0.6); 
  color: #b45309; 
  border: 1px solid rgba(251, 191, 36, 0.3); 
  padding: 2px 8px; /* 2px 10px -> 8px */
  border-radius: 17px; /* 20 * 0.85 */
  font-size: 10px; /* 12 * 0.85 */
  font-weight: 600; 
  letter-spacing: 0.4px; 
  box-shadow: 0 2px 3px rgba(245, 158, 11, 0.05); 
}

/* =========================================
   3. 中间图表 (适配矮卡片)
   ========================================= */
.sun-layout-vertical { 
  display: flex; 
  flex-direction: column; 
  align-items: center; 
  width: 100%; 
  flex: 1; 
  justify-content: space-between; 
}

.chart-container-large { 
  width: 100%; 
  display: flex; 
  justify-content: center; 
  align-items: center;
  flex: 1; 
  min-height: 0;
  /* 稍微上提一点 */
  margin-top: -7px; /* -8 * 0.85 */
}

.sun-svg-large { 
  width: 100%; 
  /* --- 高度缩小以适应 187px 卡片 --- */
  height: 72px; /* 85 * 0.85 */
  overflow: visible; 
}

/* =========================================
   4. 底部数据行
   ========================================= */
.sun-data-row { 
  display: flex; 
  justify-content: space-between; 
  align-items: flex-end; 
  width: 100%; 
  padding: 0 3px; /* 4 * 0.85 */
  box-sizing: border-box; 
  /* 稍微离底边远一点点 */
  margin-bottom: 2px;
}

.data-group { display: flex; flex-direction: column; gap: 0px; }
.data-group.left { align-items: flex-start; }
.data-group.right { align-items: flex-end; }
.data-group.center { align-items: center; padding-bottom: 2px; }

.data-label { 
  font-size: 9px; /* 11 * 0.85 */
  color: rgba(60, 60, 67, 0.6); 
  font-weight: 600; 
  text-transform: uppercase; 
  letter-spacing: 0.4px; 
}
.dark-mode .data-label { color: rgba(235, 235, 245, 0.6); }

.data-time { 
  font-size: 14px; /* 16 * 0.85 */
  color: var(--text-primary, #000); 
  font-weight: 600; 
  font-feature-settings: "tnum"; 
  letter-spacing: -0.4px; 
}
.dark-mode .data-time { color: #fff; }

.duration-pill { 
  font-size: 10px; /* 12 * 0.85 */
  color: rgba(60, 60, 67, 0.8); 
  background: rgba(255, 0, 0, 0.03); 
  backdrop-filter: blur(4px); 
  padding: 2px 8px; /* 3px 10px -> 2px 8px */
  border-radius: 17px; /* 20 * 0.85 */
  font-weight: 600; 
  border: 1px solid rgba(0,0,0,0.05); 
}

.duration-pill.night-mode { 
  background: rgba(99, 102, 241, 0.1); 
  color: #6366f1; 
  border-color: rgba(99, 102, 241, 0.2); 
}
</style>