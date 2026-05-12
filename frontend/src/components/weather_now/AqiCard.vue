<script setup>
import { computed } from 'vue';

const props = defineProps({
  aqiData: {
    type: Object,
    default: null
  }
});

// ==========================================
// 1. 智能数据节点获取
// ==========================================
const airQualityRoot = computed(() => {
  const data = props.aqiData;
  if (!data) return {};

  if (data.air_quality && data.air_quality.indexes) {
    return data.air_quality;
  }
  
  if (data.indexes && Array.isArray(data.indexes)) {
    return data;
  }

  if (data.data && data.data.air_quality) {
    return data.data.air_quality;
  }

  return {};
});

const mainIndexNode = computed(() => {
  const root = airQualityRoot.value;
  if (!root.indexes || !Array.isArray(root.indexes) || root.indexes.length === 0) {
    return null;
  }
  return root.indexes[0];
});

const pollutantsList = computed(() => airQualityRoot.value.pollutants || []);

// ==========================================
// 2. 取值函数
// ==========================================
const getPollutantVal = (code) => {
  if (!pollutantsList.value.length) return '-';
  
  const item = pollutantsList.value.find(p => p.code === code);
  if (!item) return '-';

  const val = item.concentration?.value ?? item.value;
  
  if (val === undefined || val === null) return '-';
  return Number.isInteger(val) ? val : val.toFixed(1);
};

const metrics = computed(() => [
  { value: getPollutantVal('pm2p5'), label: 'PM2.5' },
  { value: getPollutantVal('pm10'),  label: 'PM10' },
  { value: getPollutantVal('so2'),   label: 'SO<sub>2</sub>' },
  { value: getPollutantVal('no2'),   label: 'NO<sub>2</sub>' },
  { value: getPollutantVal('o3'),    label: 'O<sub>3</sub>' },
  { value: getPollutantVal('co'),    label: 'CO' },
]);

// ==========================================
// 3. 颜色与文案配置 (修正：文字优先 + 中等判断)
// ==========================================
const uiConfig = computed(() => {
  const node = mainIndexNode.value;
  
  // A. 定义标准颜色板
  const PALETTE = {
    GREEN:  '#20C969', // 优
    YELLOW: '#FFC425', // 良
    ORANGE: '#FF9100', // 轻度
    RED:    '#FF5252', // 中度/中等
    PURPLE: '#AB47BC', // 重度
    MAROON: '#8D6E63', // 严重
    GRAY:   '#9E9E9E'  // 未知
  };

  const defaultResult = { 
    color: PALETTE.GRAY, 
    desc: '暂无详细分析', 
    label: '--', 
    category: '--' 
  };

  if (!node) return defaultResult;

  // B. 获取数据
  // 这里的 category 可能是 "优", "良", "Good", "中等", "中度污染" 等
  const apiCategory = String(node.category || node.quality || node.level || '').trim();
  const aqiVal = Number(node.aqi || node.value || 0);

  let finalColor = null; // 初始为 null，用于判断是否命中文字逻辑
  let displayCategory = apiCategory || '--';

  // C. 颜色判断逻辑 - 【第一优先级：根据 API 返回的文字】
  if (displayCategory !== '--') {
    if (displayCategory.includes('优') || displayCategory.includes('Excellent')) {
      finalColor = PALETTE.GREEN;
    } 
    else if (displayCategory.includes('良') || displayCategory.includes('Good')) {
      finalColor = PALETTE.YELLOW;
    } 
    else if (displayCategory.includes('轻度') || displayCategory.includes('Light')) {
      finalColor = PALETTE.ORANGE;
    } 
    // 【修改点】：增加对“中等”和“中度”的匹配，都归为红色
    else if (displayCategory.includes('中度') || displayCategory.includes('中等') || displayCategory.includes('Moderate')) {
      finalColor = PALETTE.RED;
    } 
    else if (displayCategory.includes('重度') || displayCategory.includes('Heavy')) {
      finalColor = PALETTE.PURPLE;
    } 
    else if (displayCategory.includes('严重') || displayCategory.includes('Severe')) {
      finalColor = PALETTE.MAROON;
    }
  }

  // D. 颜色判断逻辑 - 【第二优先级：如果文字没匹配到，使用数值兜底】
  if (!finalColor && aqiVal > 0) {
    if (aqiVal <= 50) {
      finalColor = PALETTE.GREEN;
      if (displayCategory === '--') displayCategory = '优';
    } 
    else if (aqiVal <= 100) {
      finalColor = PALETTE.YELLOW;
      if (displayCategory === '--') displayCategory = '良';
    } 
    else if (aqiVal <= 150) {
      finalColor = PALETTE.ORANGE;
      if (displayCategory === '--') displayCategory = '轻度污染';
    } 
    else if (aqiVal <= 200) {
      finalColor = PALETTE.RED;
      if (displayCategory === '--') displayCategory = '中度污染';
    } 
    else if (aqiVal <= 300) {
      finalColor = PALETTE.PURPLE;
      if (displayCategory === '--') displayCategory = '重度污染';
    } 
    else {
      finalColor = PALETTE.MAROON;
      if (displayCategory === '--') displayCategory = '严重污染';
    }
  }

  // E. 最终兜底颜色
  if (!finalColor) finalColor = PALETTE.GRAY;

  // F. 组装文案
  let desc = node.health?.effect || node.advice || '建议采取防护措施';
  

  const label = node.aqiDisplay || node.aqi || '--';

  return { 
    color: finalColor, 
    desc, 
    label, 
    category: displayCategory 
  };
});

const hasData = computed(() => !!mainIndexNode.value);
</script>

<template>
  <div class="ios-card">
    <div class="card-title">空气质量</div>
    
    <div v-if="hasData" class="main-body">
      <div class="chart-area pollutant-grid">
        <div v-for="(item, index) in metrics" :key="index" class="mini-metric">
          <div class="mini-label" v-html="item.label"></div>
          <div class="mini-value text-shadow-fix" :style="{ color: uiConfig.color }">
            {{ item.value }}
          </div>
        </div>
      </div>

      <div class="data-area">
        <div class="big-metric">
          <span class="value text-shadow-fix" :style="{ color: uiConfig.color }">
            {{ uiConfig.label }}
          </span>
          <span class="label" :style="{ color: uiConfig.color, opacity: 0.8 }">AQI 指数</span>
        </div>
      </div>
    </div>

    <div v-else class="main-body empty-state">
      暂无空气质量数据
    </div>

    <div class="footer-info" v-if="hasData">
      <div class="status-badge text-shadow-fix" :style="{ color: uiConfig.color }">
        {{ uiConfig.category }}
        <span class="trend-icon" :style="{ backgroundColor: uiConfig.color }">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="3">
              <path d="M12 20V4M12 4L5 11M12 4L19 11" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
        </span>
      </div>
      <div class="analysis-text">{{ uiConfig.desc }}</div>
    </div>
  </div>
</template>

<style scoped>
.ios-card {
  width: 272px; /* 320 * 0.85 */
  height: 187px; /* 220 * 0.85 */
  margin: 0 auto;
  padding: 14px; /* 16 * 0.85 */
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  gap: 10px; /* 12 * 0.85 */
  text-align: left;
  isolation: isolate; /* 与湿度卡片对齐 */
  background: var(--glass-bg, #ffffff); 
  border: 1px solid var(--glass-border, rgba(0,0,0,0.1));
  border-radius: 20px; /* 24 * 0.85 */
  box-shadow: 0 7px 27px rgba(0, 0, 0, 0.05); /* 阴影等比缩小 */
  overflow: hidden; /* 与湿度卡片对齐 */
  position: relative; /* 与湿度卡片对齐 */
  z-index: 10; /* 与湿度卡片对齐 */
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; /* 与湿度卡片对齐 */
  color: var(--text-primary, #000); /* 与湿度卡片对齐 */
  transition: all 0.3s ease;
  box-sizing: border-box;
}

.text-shadow-fix {
  text-shadow: 0px 0px 1px rgba(0,0,0,0.15); 
}

/* === Dark Mode 核心修改区域 === */
.dark-mode .ios-card {
  background: var(--glass-bg, rgba(30, 41, 59, 0.6));
  border-color: var(--glass-border, rgba(255, 255, 255, 0.1));
  box-shadow: 0 7px 27px rgba(0, 0, 0, 0.2);
  color: var(--text-primary, #fff); /* 与湿度卡片对齐 */
}

.card-title { 
  font-size: 12px; /* 14 * 0.85 */
  font-weight: 600; 
  color: rgba(0, 0, 0, 0.85); 
  margin-left: 3px;
  line-height: 1.4;
}
.dark-mode .card-title { 
  color: rgba(255, 255, 255, 0.6); 
}

.main-body { 
  display: flex; 
  justify-content: space-between; 
  align-items: center; 
  min-height: 68px; /* 80 * 0.85 */
}

.empty-state {
  justify-content: center;
  color: rgba(0,0,0,0.3);
  font-size: 12px; /* 14 * 0.85 */
}

.dark-mode .empty-state {
  color: rgba(235, 235, 245, 0.8);
}

.data-area { 
  display: flex; 
  flex-direction: column; 
  text-align: right; 
  width: 85px; /* 100 * 0.85 */
  flex-shrink: 0; 
  justify-content: center; 
  align-items: flex-end;
}

.value { 
  display: block; 
  font-size: 31px; /* 36 * 0.85 */
  font-weight: 600; 
  line-height: 1; 
  letter-spacing: -0.4px; 
}

.label { 
  display: block; 
  font-size: 10px; /* 12 * 0.85 */
  font-weight: 600; 
  margin-top: 3px; 
}

.chart-area.pollutant-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 7px 10px; /* 8px 12px -> 7px 10px */
  flex: 1;
  margin-right: 10px; /* 12 * 0.85 */
}

.mini-metric {
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.mini-value {
  font-size: 12px; /* 14 * 0.85 */
  font-weight: 600;
  line-height: 1.2;
}

.mini-label {
  font-size: 9px; /* 11 * 0.85 */
  color: rgba(60, 60, 67, 0.5);
  font-weight: 500;
  line-height: 1.2;
  margin-bottom: 2px;
}
.dark-mode .mini-label { color: rgba(235, 235, 245, 0.5); }

:deep(sub) {
  font-size: 0.7em;
  vertical-align: bottom;
}

.footer-info { 
  display: flex; 
  flex-direction: column; 
  gap: 3px; /* 4 * 0.85 */
  margin-top: 0px;
  padding-top: 7px; /* 8 * 0.85 */
}

.status-badge {
  font-size: 13px; /* 15 * 0.85 */
  font-weight: 600; 
  display: flex; 
  align-items: center; 
  gap: 5px; /* 6 * 0.85 */
  line-height: 1; /* 防错位：强行约束文字行高 */
}

.trend-icon {
  width: 16px; /* 18 * 0.85，保持偶数 */
  height: 16px;
  border-radius: 50%; 
  display: flex; 
  align-items: center; 
  justify-content: center;
  flex-shrink: 0; /* 防错位：防止容器被压缩 */
}

/* 防错位：强行约束内部SVG/图片大小，绝对居中 */
.trend-icon svg,
.trend-icon img {
  width: 60%;
  height: 60%;
  object-fit: contain;
}

.analysis-text { 
  font-size: 11px; /* 13 * 0.85 */
  color: rgba(60, 60, 67, 0.8); 
  line-height: 1.4; 
}
.dark-mode .analysis-text { color: rgba(235, 235, 245, 0.8); }
</style>
