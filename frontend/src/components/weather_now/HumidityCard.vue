<template>
  <div class="ios-card" :class="cardThemeClass">
    <div class="card-title">湿度</div>
    
    <div class="main-body">
      <div class="chart-area">
        <div class="bar-col" v-for="(item, index) in forecastData" :key="index">
          <div class="bar-bg">
            <div 
              class="bar-fill" 
              :style="{ 
                height: item.value + '%', 
                opacity: getBarOpacity(item.value), 
                backgroundColor: getBarColor(item.value) 
              }"
            ></div>
          </div>
        </div>
      </div>

      <div class="data-area">
        <div class="big-metric">
          <span class="value text-shadow-fix">{{ currentHumidity }}%</span>
          <span class="label">相对湿度</span>
        </div>
        <div class="small-metric">
          <span class="value text-shadow-fix">{{ currentDewPoint }}°</span>
          <span class="label">露点</span>
        </div>
      </div>
    </div>

    <div class="footer-info">
       <div class="status-badge text-shadow-fix" :class="statusClass">
        {{ comfortSummary.title }}
        
        <span class="trend-icon" v-if="trendInfo.trendState === 'falling'">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 4V20M12 20L5 13M12 20L19 13"/>
          </svg>
        </span>

        <span class="trend-icon" v-else-if="trendInfo.trendState === 'rising'">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 20V4M12 4L5 11M12 4L19 11"/>
          </svg>
        </span>

        <span class="trend-icon" v-else style="background-color: #34C759;">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
             <path d="M4 12H20M20 12L13 5M20 12L13 19"/>
          </svg>
        </span>

      </div>
      <div class="analysis-text">{{ comfortSummary.desc }} {{ trendInfo.text }}</div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  humidity: { type: [Number, String], default: 0 },
  temperature: { type: [Number, String], default: 0 },
  dewPoint: { type: [Number, String], default: null }, // 新增：直接接收接口的露点温度
  hourlyData: { type: Array, default: () => [] },
  tempUnit: { type: String, default: 'C' }
});

const currentHumidity = computed(() => parseInt(props.humidity || 0));

// 1. 直接使用接口传过来的露点数据（假定接口传入值为摄氏度基准）
const rawDewPointCelsius = computed(() => {
  if (props.dewPoint === null || props.dewPoint === undefined) return null;
  const val = parseFloat(props.dewPoint);
  return isNaN(val) ? null : val;
});

// 2. 根据用户设置的单位 (C/F) 进行格式化和换算显示
const currentDewPoint = computed(() => {
  const val = rawDewPointCelsius.value;
  if (val === null) return '--';
  return props.tempUnit === 'C' ? Math.round(val) : Math.round(val * 1.8 + 32);
});

// 舒适度判断（逻辑保持不变，基于摄氏露点和湿度计算）
const comfortSummary = computed(() => {
  const h = currentHumidity.value; 
  const dpCelsius = rawDewPointCelsius.value === null ? 0 : rawDewPointCelsius.value;

  if (dpCelsius >= 24) return { title: '极度闷热', desc: '体感非常闷热，极易出汗。', class: 'muggy' };
  if (dpCelsius >= 20) return { title: '闷热', desc: '空气潮湿粘腻，体感不适。', class: 'muggy' };
  
  if (dpCelsius >= 10 && dpCelsius < 20) {
    if (h > 70) return { title: '潮湿', desc: '空气含水量高，体感微潮。', class: 'muggy' };
    return { title: '舒适', desc: '湿度适宜，体感清爽。', class: 'comfort' };
  }
  
  if (h > 65) return { title: '湿冷', desc: '露点较低且湿度大，体感阴冷。', class: 'cold-damp' };
  if (h < 30) return { title: '干燥', desc: '空气非常干燥，请注意补水。', class: 'dry' };
  
  return { title: '舒适', desc: '湿度状况处于正常范围。', class: 'comfort' };
});

const statusClass = computed(() => comfortSummary.value.class);
const cardThemeClass = computed(() => '');

// 柱状图数据处理
const forecastData = computed(() => {
  if (!props.hourlyData || props.hourlyData.length === 0) {
    return Array(8).fill({ time: '--', value: 0, temp: 0 }); 
  }
  
  const getTemp = (val) => {
      const t = parseFloat(val);
      if (isNaN(t)) return 0;
      return Math.round(props.tempUnit === 'C' ? t : (t * 1.8 + 32));
  };

  const currentItem = {
    time: '现在',
    value: parseInt(props.humidity || 0),
    temp: getTemp(props.temperature),
    timeObj: new Date()
  };
  
  const futureItems = props.hourlyData
    .filter(item => {
      if (item.isSunEvent || item.isNow) return false;
      return true; 
    })
    .slice(0, 7)
    .map(item => {
      let timeLabel = item.time;
      if (timeLabel && timeLabel.includes(':')) timeLabel = parseInt(timeLabel.split(':')[0]) + '时';
      return { 
          time: timeLabel, 
          value: parseInt(item.humidity || 0), 
          temp: getTemp(item.rawTemp || item.temp)
      };
    });
    
  return [currentItem, ...futureItems];
});

// 趋势分析逻辑
const trendInfo = computed(() => {
  const data = forecastData.value;
  if (!data || data.length < 3) return { trendState: 'stable', text: '湿度数据不足' };
  
  const currentVal = data[0].value;
  const nextFewHours = data.slice(1, 5); 
  
  if (nextFewHours.length === 0) return { trendState: 'stable', text: '' };
  
  const minVal = Math.min(...nextFewHours.map(i => i.value));
  const maxVal = Math.max(...nextFewHours.map(i => i.value));
  const minItem = nextFewHours.find(i => i.value === minVal);
  const maxItem = nextFewHours.find(i => i.value === maxVal);
  
  // 波动超过 3% 才算变化
  if (minVal < currentVal - 3) {
    return { trendState: 'falling', text: `预计湿度将下降，${minItem.time}左右降至${minItem.value}%。` };
  } else if (maxVal > currentVal + 3) {
    return { trendState: 'rising', text: `预计湿度将上升，${maxItem.time}左右升至${maxItem.value}%。` };
  }
  
  // 否则为平稳
  return { trendState: 'stable', text: "未来几小时湿度波动不大。" };
});

const getBarOpacity = (val) => 0.5 + (val / 200);
const getBarColor = (val) => {
  if (val < 40) return '#87CEFA';
  if (val > 70) return '#4169E1';
  return '#5B8FF9'; 
};
</script>

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
  isolation: isolate;
  background: var(--glass-bg, #ffffff); 
  border: 1px solid var(--glass-border, rgba(0,0,0,0.1));
  border-radius: 20px; /* 24 * 0.85 */
  box-shadow: 0 7px 27px rgba(0, 0, 0, 0.05); /* 阴影等比缩小 */
  overflow: hidden; 
  position: relative;
  z-index: 10;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  color: var(--text-primary, #000);
  transition: all 0.3s ease;
  box-sizing: border-box; /* 统一盒子模型 */
}

/* 统一字体阴影防错位 */
.text-shadow-fix {
  text-shadow: 0px 0px 1px rgba(0,0,0,0.15); 
}

.dark-mode .ios-card {
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
}
.dark-mode .card-title { color: rgba(255, 255, 255, 0.6); }

.main-body { 
  display: flex; 
  justify-content: space-between; 
  align-items: flex-end;
  height: 68px; /* 80 * 0.85 */
}

.chart-area { 
  display: flex; 
  align-items: flex-end; 
  gap: 5px; /* 6 * 0.85 */
  height: 100%; 
  padding-bottom: 4px; /* 5 * 0.85 */
  flex: 1;
}

.bar-col { 
  width: 7px; /* 8 * 0.85 */
  height: 100%; 
  display: flex; 
  align-items: flex-end; 
}

.bar-bg { 
  width: 100%; 
  height: 100%; 
  background-color: rgba(0, 0, 0, 0.15); 
  border-radius: 8px; /* 10 * 0.85 */
  position: relative; 
  overflow: hidden; 
}
.dark-mode .bar-bg { background-color: rgba(255, 255, 255, 0.2); }

.bar-fill { 
  width: 100%; 
  position: absolute; 
  bottom: 0; 
  border-radius: 8px; /* 10 * 0.85 */
  transition: height 0.6s cubic-bezier(0.34, 1.56, 0.64, 1), background-color 0.3s ease; 
}

.data-area { 
  display: flex; 
  flex-direction: column; 
  text-align: right; 
  width: 119px; /* 140 * 0.85 */
  flex-shrink: 0; 
  padding-right: 3px; 
  justify-content: center; 
  height: 100%;
}

.big-metric { margin-bottom: 5px; }

.value { 
  display: block; 
  font-size: 29px; /* 34 * 0.85 */
  font-weight: 500; 
  line-height: 1; 
  color: #000; 
  letter-spacing: -0.4px; 
  font-variant-numeric: tabular-nums; 
}
.dark-mode .value { color: #fff; }

.label { 
  display: block; 
  font-size: 10px; /* 12 * 0.85 */
  font-weight: 600; 
  color: rgba(60, 60, 67, 0.6); 
  margin-top: 3px; 
}
.dark-mode .label { color: rgba(235, 235, 245, 0.6); }

.footer-info { 
  display: flex; 
  flex-direction: column; 
  gap: 3px; /* 缝隙修正为 3px 统一对齐 */
  margin-top: 0px; 
  padding-top: 7px;
}

.status-badge {
  font-size: 13px; /* 15 * 0.85 */
  font-weight: 600; 
  display: flex; 
  align-items: center; 
  gap: 5px; /* 6 * 0.85 */
  line-height: 1; /* 【防错位】约束文字行高 */
}

.status-badge.cold-damp { color: #5B8FF9; }
.status-badge.muggy     { color: #FF9500; }
.status-badge.comfort   { color: #34C759; }
.status-badge.dry       { color: #00C7BE; }

.dark-mode .status-badge.cold-damp { color: #7CA6FF; }
.dark-mode .status-badge.muggy     { color: #FFAB2E; }
.dark-mode .status-badge.comfort   { color: #4CD964; }
.dark-mode .status-badge.dry       { color: #30D1C8; }

.trend-icon {
  width: 16px; /* 18 * 0.85 -> 保持偶数防模糊 */
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

/* 其他图标颜色由父级 class 决定，平稳状态的绿色由 inline-style 控制 */
.status-badge.cold-damp .trend-icon { background-color: #5B8FF9; }
.status-badge.muggy .trend-icon     { background-color: #FF9500; }
.status-badge.comfort .trend-icon   { background-color: #34C759; }
.status-badge.dry .trend-icon       { background-color: #00C7BE; }

.dark-mode .status-badge.cold-damp .trend-icon { background-color: #7CA6FF; }
.dark-mode .status-badge.muggy .trend-icon     { background-color: #FFAB2E; }
.dark-mode .status-badge.comfort .trend-icon   { background-color: #4CD964; }
.dark-mode .status-badge.dry .trend-icon       { background-color: #30D1C8; }

.analysis-text { 
  font-size: 11px; /* 13 * 0.85 */
  color: rgba(60, 60, 67, 0.8); 
  line-height: 1.4; 
  margin: 0; 
}
.dark-mode .analysis-text { color: rgba(235, 235, 245, 0.8); }
</style>