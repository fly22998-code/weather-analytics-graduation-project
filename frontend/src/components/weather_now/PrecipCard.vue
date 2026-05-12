<template>
  <div class="precip-card" :class="precipVisualTheme">
    
    <div class="card-title">降水</div>

    <div class="circle-wrapper">
      <div class="circle-box">
        <div class="water" :style="{ height: waterHeight, opacity: currentPrecip > 0 ? 1 : 0 }">
        </div>
        
        <div class="info">
          <div class="number-group">
            <span class="number">{{ currentPrecip === 0 ? '0' : currentPrecip.toFixed(1) }}</span>
            <span class="unit">毫米</span>
          </div>
          <div class="sub-text">未来24小时</div>
        </div>
      </div>
    </div>

    <div class="footer">
      <div class="status-text" :style="{ color: trendColor }">
        {{ precipTitle }}
        <span class="trend-icon" :style="{ backgroundColor: trendColor }">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
              <path :d="trendIconPath" />
            </svg>
        </span>
      </div>
      <div class="desc-text">
        {{ precipDescription }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  hourlyData: {
    type: Array,
    default: () => []
  }
});

const maxAmount = 300; 

// =========================
// 1. 基础数据计算
// =========================

const validHourlyData = computed(() => {
  if (!props.hourlyData || props.hourlyData.length === 0) return [];
  return props.hourlyData
    .filter(item => !item.isSunEvent)
    .slice(0, 24);
});

// 未来24小时累计降水量
const currentPrecip = computed(() => {
  if (validHourlyData.value.length === 0) return 0;
  
  const total = validHourlyData.value.reduce((sum, item) => {
    const p = parseFloat(item.precip || 0);
    return sum + (isNaN(p) ? 0 : p);
  }, 0);
  return parseFloat(total.toFixed(1));
});

// 降水类型判断
const precipTypeAnalysis = computed(() => {
  const list = validHourlyData.value;
  if (list.length === 0) return 'rain';

  let hasRain = false;
  let hasSnow = false;

  list.forEach(item => {
    const txt = item.text || '';
    if (txt.includes('雪') || txt.includes('冰')) hasSnow = true;
    if (txt.includes('雨')) hasRain = true;
  });

  if (hasSnow && hasRain) return 'mixed'; 
  if (hasSnow) return 'snow';            
  return 'rain';                         
});

// =========================
// 2. 24小时趋势分析
// =========================

const precipTrend = computed(() => {
  if (currentPrecip.value <= 0) return 'stable';

  const list = validHourlyData.value;
  const len = list.length;
  if (len < 2) return 'stable';

  const mid = Math.floor(len / 2);
  const firstHalfData = list.slice(0, mid); 
  const secondHalfData = list.slice(mid);   

  const sumFirst = firstHalfData.reduce((s, i) => s + (parseFloat(i.precip) || 0), 0);
  const sumSecond = secondHalfData.reduce((s, i) => s + (parseFloat(i.precip) || 0), 0);

  const threshold = 0.5;

  if (sumSecond > sumFirst + threshold) return 'increase'; 
  if (sumFirst > sumSecond + threshold) return 'decrease'; 
  
  return 'stable'; 
});

// 图标路径
const trendIconPath = computed(() => {
  switch (precipTrend.value) {
    case 'increase': return 'M12 20V4M12 4L5 11M12 4L19 11'; 
    case 'decrease': return 'M12 4V20M12 20L5 13M12 20L19 13'; 
    default: return 'M4 12H20M20 12L13 5M20 12L13 19';        
  }
});

// 颜色逻辑：图标和文字共用
const trendColor = computed(() => {
  // 无降水 -> 绿色
  if (currentPrecip.value <= 0) return '#20C969'; 

  const type = precipTypeAnalysis.value;
  if (type === 'snow') return '#718096'; // 雪: 灰
  if (type === 'mixed') return '#64748B'; // 雨夹雪: 青灰
  return '#5b8df8'; // 雨: 蓝
});

// =========================
// 3. 文案生成 (24小时视角)
// =========================

const precipDescription = computed(() => {
  const val = currentPrecip.value;
  const type = precipTypeAnalysis.value;
  const trend = precipTrend.value;

  if (val <= 0) {
    return '未来 24 小时预计无明显降水，天气相对平稳，可以放心出门。';
  }

  let baseDesc = '';
  if (type === 'snow') {
    if (val < 2.5) baseDesc = `预计累计降雪 ${val}mm，雪势较小`;
    else if (val < 5.0) baseDesc = `预计累计降雪 ${val}mm，有薄积雪`;
    else if (val < 10.0) baseDesc = `预计累计降雪 ${val}mm，注意防滑`;
    else baseDesc = `预计有强降雪 (${val}mm)，减少外出`;
  } else if (type === 'mixed') {
    baseDesc = `预计有雨雪天气，降水 ${val}mm，路面湿滑`;
  } else {
    if (val < 10) baseDesc = `预计总降水约 ${val}mm，雨势较小`;
    else if (val < 25) baseDesc = `预计总降水达 ${val}mm，备好雨具`;
    else if (val < 50) baseDesc = `预计累计降水 ${val}mm，局部雨大`;
    else baseDesc = `预计有 ${val}mm 强降水，注意防范`;
  }

  let trendSuffix = '';
  const typeText = type === 'snow' ? '雪势' : '雨势';

  if (trend === 'increase') {
    trendSuffix = `，后半段${typeText}增强。`;
  } else if (trend === 'decrease') {
    trendSuffix = `，后半段${typeText}减弱。`;
  } else {
    trendSuffix = `，全天${typeText}平稳。`;
  }

  return baseDesc + trendSuffix;
});

const precipTitle = computed(() => {
  const val = currentPrecip.value;
  const type = precipTypeAnalysis.value;
  if (val <= 0) return '无降水';
  if (type === 'snow') return '有降雪';
  if (type === 'mixed') return '雨雪天气';
  return '有降雨';
});

const precipVisualTheme = computed(() => {
    const type = precipTypeAnalysis.value;
    if (type === 'snow') return 'snow-theme';
    if (type === 'mixed') return 'mixed-theme';
    return 'rain-theme';
});

const waterHeight = computed(() => {
  const val = currentPrecip.value;
  if (val <= 0) return '0%';
  const pct = (val / maxAmount) * 100;
  return Math.min(pct, 100) + '%';
});
</script>

<style scoped>
/* =========================================
   降水卡片样式 (精确缩小 85% & 移除波浪)
   ========================================= */
.precip-card {
  width: 272px; /* 320 * 0.85 */
  height: 187px; /* 220 * 0.85 */
  padding: 14px; /* 16 * 0.85 */
  display: flex;
  flex-direction: column;
  justify-content: flex-start; 
  gap: 10px; /* 12 * 0.85 */
  isolation: isolate;
  background: var(--glass-bg, #ffffff);
  border: 1px solid var(--glass-border, rgba(0,0,0,0.05));
  border-radius: 20px; /* 24 * 0.85 */
  box-shadow: 0 7px 27px rgba(0, 0, 0, 0.05); /* 阴影等比缩小 */
  overflow: hidden; 
  position: relative;
  z-index: 10;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  color: var(--text-primary, #000);
  transition: all 0.3s ease;
  flex-shrink: 0;
}

.dark-mode .precip-card {
  background: var(--glass-bg, rgba(30, 41, 59, 0.6));
  border-color: var(--glass-border, rgba(255, 255, 255, 0.1));
  box-shadow: 0 7px 27px rgba(0, 0, 0, 0.2);
  color: var(--text-primary, #fff);
}

.card-title {
  font-size: 12px; /* 14 * 0.85 */
  font-weight: 600;
  color: rgba(0, 0, 0, 0.85);
  margin-left: 3px;
  line-height: 1.4;
  text-align: left;
  flex-shrink: 0;
}

.dark-mode .card-title {
  color: rgba(255, 255, 255, 0.6);
}

/* =========================================
   中间圆形
   ========================================= */
.precip-card .circle-wrapper {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 0; 
  height: 68px; /* 80 * 0.85 */
}

.precip-card .circle-box {
  width: 115px; /* 135 * 0.85 */
  height: 115px; /* 135 * 0.85 */
  background-color: rgba(0, 0, 0, 0.15); 
  border-radius: 50%;
  position: relative;
  overflow: hidden;
  transform: translateZ(0);
  -webkit-mask-image: -webkit-radial-gradient(white, black);
  flex-shrink: 0;
}
.dark-mode .precip-card .circle-box { background-color: rgba(255, 255, 255, 0.2); }

/* 水位效果（纯色无波浪） */
.precip-card .water {
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  background: #5b8df8;
  z-index: 1;
  transition: height 0.5s cubic-bezier(0.4, 0, 0.2, 1), opacity 0.3s ease;
}

.precip-card .info {
  position: relative;
  z-index: 2;
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  pointer-events: none;
  padding-bottom: 2px; 
}

.precip-card .number { 
  font-size: 22px; /* 26 * 0.85 */
  font-weight: 600; 
  line-height: 1; 
  color: #000; 
  letter-spacing: -0.4px;
  font-variant-numeric: tabular-nums;
}
.dark-mode .precip-card .number { color: #fff; }

.precip-card .unit { 
  font-size: 10px; /* 12 * 0.85 */
  margin-left: 1px; 
  color: rgba(60, 60, 67, 0.7);
  font-weight: 600;
}
.dark-mode .precip-card .unit { color: rgba(235, 235, 245, 0.7); }

.precip-card .sub-text { 
  display: block !important; 
  font-size: 9px; /* 10 * 0.85 */
  color: rgb(0, 0, 0);
}
.dark-mode .precip-card .sub-text { color: rgba(255, 255, 255, 0.9); }

.precip-card .footer { 
  display: flex; 
  flex-direction: column; 
  gap: 5px; /* 6 * 0.85 */
  padding-bottom: 0;
  margin-top: 3px; /* 4 * 0.85 */
}

.precip-card .status-text { 
  font-size: 13px; /* 15 * 0.85 */
  font-weight: 600; 
  display: flex;
  align-items: center;
  gap: 5px; /* 6 * 0.85 */
  line-height: 1; /* 【防错位】限制文字行高 */
}

.trend-icon {
  width: 16px; /* 18 * 0.85 */
  height: 16px;
  border-radius: 50%; 
  display: flex; 
  align-items: center; 
  justify-content: center;
  flex-shrink: 0; /* 【防错位】禁止挤压 */
}

/* 【防错位】内部元素绝对居中限制 */
.trend-icon svg,
.trend-icon img {
  width: 60%;
  height: 60%;
  object-fit: contain;
}

.precip-card .desc-text {
  font-size: 11px; /* 13 * 0.85 */
  color: rgba(60, 60, 67, 0.8);
  line-height: 1.4; 
  white-space: normal;
  text-align: left;
  min-height: auto;
}
.dark-mode .precip-card .desc-text { color: rgba(235, 235, 245, 0.8); }

/* Theme Colors for Water & Text */
.precip-card.snow-theme .water { background: #E2E8F0; }
.dark-mode .precip-card.snow-theme .water { background: #FFFFFF; opacity: 0.9; }

.precip-card.mixed-theme .water { background: #94A3B8; }
.dark-mode .precip-card.mixed-theme .water { background: #A5B4FC; }
</style>