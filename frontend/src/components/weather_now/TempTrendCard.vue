<template>
  <div class="ios-card" :class="{ 'dark-mode': isDark }">
    <div class="card-title">温度</div>
    
    <div class="main-body">
      <div class="chart-area">
        <div class="chart-wrapper">
          <svg class="temp-chart" viewBox="0 0 122 64">
            <defs>
              <linearGradient id="tempArea" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" :stop-color="themeColor" stop-opacity="0.55" />
                <stop offset="50%" :stop-color="themeColor" stop-opacity="0.15" />
                <stop offset="100%" :stop-color="themeColor" stop-opacity="0.0" />
              </linearGradient>

              <clipPath id="clipPassed">
                <rect x="-10" y="-20" :width="nowX + 10" height="120" />
              </clipPath>
            </defs>

            <path 
              :d="splinePath" 
              fill="none" 
              :stroke="isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.06)'" 
              stroke-width="3" 
              stroke-linecap="round" 
              stroke-linejoin="round"
            />

            <path 
              :d="areaPath" 
              fill="url(#tempArea)" 
              clip-path="url(#clipPassed)" 
            />
            
            <path 
              :d="splinePath" 
              fill="none" 
              :stroke="themeColor" 
              stroke-width="3.5" 
              stroke-linecap="round" 
              stroke-linejoin="round"
              clip-path="url(#clipPassed)" 
            />
            
            <circle 
              v-if="currentPoint"
              class="current-dot"
              :cx="currentPoint.x" 
              :cy="currentPoint.y" 
              r="5.5" 
              :fill="themeColor" 
              :stroke="isDark ? '#333333' : '#ffffff'" 
              stroke-width="2.5"
            />
          </svg>
        </div>
      </div>

      <div class="data-area">
        <div class="big-metric">
          <span class="value text-shadow-fix">{{ displayCurrentTemp }}°</span>
          <span class="label text-shadow-fix">当前气温</span>
        </div>
        <div class="small-metric">
          <span class="value sub-val text-shadow-fix">{{ maxTemp }}° / {{ minTemp }}°</span>
          <span class="label text-shadow-fix">全天极值</span>
        </div>
      </div>
    </div>

    <div class="footer-info">
      <div class="status-badge text-shadow-fix" :class="statusClass">
        {{ tempTrendTitle }}
        <span class="trend-icon" v-if="analysis.trendType === 'warming'">
          <svg viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20V4M12 4L5 11M12 4L19 11"/></svg>
        </span>
        <span class="trend-icon" v-else-if="analysis.trendType === 'cooling'">
          <svg viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M12 4V20M12 20L5 13M12 20L19 13"/></svg>
        </span>
        <span class="trend-icon" v-else>
          <svg viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
        </span>
      </div>
      <div class="analysis-text text-shadow-fix">{{ tempDescription }}</div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  currentTemp: { type: [Number, String], required: true },
  hourlyData: { type: Array, required: true },
  isDark: { type: Boolean, default: false },
  cityLocalHour: { type: Number, required: false },
  tempUnit: { type: String, default: 'C' }
});

const convertTemperature = (value) => {
  const parsed = parseFloat(value);
  if (Number.isNaN(parsed)) return null;
  return props.tempUnit === 'C' ? Math.round(parsed) : Math.round((parsed * 1.8) + 32);
};

const nowHour = computed(() => {
  return props.cityLocalHour !== undefined ? props.cityLocalHour % 24 : new Date().getHours();
});

const formatHour = (h) => {
  if (h === 0) return '午夜12:00';
  if (h < 12) return `上午${h}:00`;
  if (h === 12) return '中午12:00';
  return `下午${h - 12}:00`;
};

// ==============================
// 趋势与极值分析
// ==============================
const analysis = computed(() => {
  const futureData = (props.hourlyData || []).slice(0, 24).map(d => parseFloat(d.rawTemp || d.temp || 0));
  if (futureData.length === 0) futureData.push(parseFloat(props.currentTemp));

  let maxIdx = 0, minIdx = 0;
  for (let i = 1; i < futureData.length; i++) {
    if (futureData[i] > futureData[maxIdx]) maxIdx = i;
    if (futureData[i] < futureData[minIdx]) minIdx = i;
  }

  const current = parseFloat(props.currentTemp);
  const isWarming = maxIdx <= minIdx; 
  
  let targetIdx = isWarming ? maxIdx : minIdx;
  if (targetIdx === 0) targetIdx = isWarming ? minIdx : maxIdx; 
  const targetTemp = futureData[targetIdx];
  const targetHour = (nowHour.value + targetIdx) % 24;

  const startHour = isWarming ? 6 : 15; 
  let startTemp = isWarming ? futureData[minIdx] : futureData[maxIdx];

  const minTotal = Math.round(Math.min(...futureData, startTemp, current));
  const maxTotal = Math.round(Math.max(...futureData, startTemp, current));

  // 🌟 修复一：优化平稳的判定逻辑
  let trendType = isWarming ? 'warming' : 'cooling';
  // 只有当全天温差极小(<=3度)，或者当前这一段的波动极小(<=2度)时，才算作“平稳”
  const segmentRange = Math.max(startTemp, current, targetTemp) - Math.min(startTemp, current, targetTemp);
  if ((maxTotal - minTotal) <= 3 || segmentRange <= 2) {
    trendType = 'stable';
  }

  return { trendType, targetTemp, targetHour, startTemp, startHour, current, minTotal, maxTotal };
});

const minTemp = computed(() => convertTemperature(analysis.value.minTotal) ?? '--');
const maxTemp = computed(() => convertTemperature(analysis.value.maxTotal) ?? '--');
const displayCurrentTemp = computed(() => convertTemperature(props.currentTemp) ?? '--');

const tempTrendTitle = computed(() => {
  const t = analysis.value.trendType;
  if (t === 'stable') return '气温平稳';
  return t === 'warming' ? '上升' : '下降';
});

const tempDescription = computed(() => {
  const a = analysis.value;
  if (a.trendType === 'stable') return '全天气温整体波动较小，体感较为舒适。';
  
  const tTime = formatHour(a.targetHour);
  const sTime = formatHour(a.startHour);
  const tTemp = convertTemperature(a.targetTemp) ?? '--';
  const sTemp = convertTemperature(a.startTemp) ?? '--';
  
  if (a.trendType === 'warming') {
    return `预计将于 ${sTime} 到 ${tTime} 升温至 ${tTemp}°。 ${sTime} 达到夜间最低 ${sTemp}°。`;
  } else {
    return `预计将于 ${sTime} 到 ${tTime} 降温至 ${tTemp}°。 ${sTime} 达到白天最高 ${sTemp}°。`;
  }
});

const statusClass = computed(() => {
  const t = analysis.value.trendType;
  if (t === 'stable') return 'stable-mild';
  return t === 'warming' ? 'muggy' : 'cold-damp';
});

const themeColor = computed(() => {
  const t = analysis.value.trendType;
  if (t === 'stable') return '#34C759'; 
  return t === 'warming' ? '#D93025' : '#1A73E8'; 
});

// ==============================
// 绘图核心：基于 Monotone-X 算法的完美平滑曲线
// ==============================
const svgWidth = 122; 
const svgHeight = 64; 
const paddingSide = 8; 
const paddingTop = 14; 
const paddingBottom = 14;

const layout = computed(() => {
  const a = analysis.value;
  
  // 🌟 修复二：将全天的极值纳入 Y 轴计算，避免局部波动被过度放大
  let minVisual = Math.min(a.startTemp, a.current, a.targetTemp, a.minTotal);
  let maxVisual = Math.max(a.startTemp, a.current, a.targetTemp, a.maxTotal);
  let range = maxVisual - minVisual;
  
  // 增加一点上下边距，防止曲线“顶天立地”
  minVisual -= range * 0.1;
  maxVisual += range * 0.1;
  range = maxVisual - minVisual;

  // 如果整体温差小于 8 度，强行固定标尺跨度，强制压平曲线
  if (range < 8) {
    const center = (maxVisual + minVisual) / 2 || 0;
    minVisual = center - 4;
    maxVisual = center + 4;
    range = 8;
  }

  const w = svgWidth - paddingSide * 2;
  const h = svgHeight - paddingTop - paddingBottom;
  const getY = (temp) => paddingTop + h - ((temp - minVisual) / range) * h;

  // 2. 精确计算 X 轴的时间进度
  let hSinceStart = (nowHour.value - a.startHour + 24) % 24;
  let hToTarget = (a.targetHour - nowHour.value + 24) % 24;
  if (hToTarget === 0 && hSinceStart === 0) hToTarget = 1; 
  
  let progress = hSinceStart / (hSinceStart + hToTarget);
  progress = Math.max(0.05, Math.min(0.95, progress)); 
  const nowXVal = paddingSide + progress * w;

  const keyPoints = [
    { x: paddingSide, y: getY(a.startTemp) },
    { x: nowXVal, y: getY(a.current) },
    { x: paddingSide + w, y: getY(a.targetTemp) }
  ];

  // 3. 采用 Monotone-X 算法计算控制点
  const p0 = keyPoints[0];
  const p1 = keyPoints[1];
  const p2 = keyPoints[2];

  const sec0 = (p1.y - p0.y) / (p1.x - p0.x);
  const sec1 = (p2.y - p1.y) / (p2.x - p1.x);

  let t0 = sec0;
  let t2 = sec1;
  let t1;

  if (Math.sign(sec0) !== Math.sign(sec1) || sec0 === 0 || sec1 === 0) {
    t1 = 0; 
  } else {
    t1 = 2 / (1 / sec0 + 1 / sec1);
  }

  const dx0 = (p1.x - p0.x) / 3;
  const dx1 = (p2.x - p1.x) / 3;

  let path = `M ${p0.x},${p0.y}`;
  path += ` C ${p0.x + dx0},${p0.y + t0 * dx0} ${p1.x - dx0},${p1.y - t1 * dx0} ${p1.x},${p1.y}`;
  path += ` C ${p1.x + dx1},${p1.y + t1 * dx1} ${p2.x - dx1},${p2.y - t2 * dx1} ${p2.x},${p2.y}`;

  const areaPath = `${path} L ${p2.x},${svgHeight} L ${p0.x},${svgHeight} Z`;

  return { splinePath: path, areaPath: areaPath, currentPoint: p1 };
});

const splinePath = computed(() => layout.value.splinePath);
const areaPath = computed(() => layout.value.areaPath);
const currentPoint = computed(() => layout.value.currentPoint);
const nowX = computed(() => currentPoint.value ? currentPoint.value.x : 0);

</script>

<style scoped>
.ios-card { width: 272px; height: 187px; padding: 14px; display: flex; flex-direction: column; justify-content: space-between; gap: 10px; text-align: left; isolation: isolate; background: var(--glass-bg, #ffffff); border: 1px solid var(--glass-border, rgba(0,0,0,0.1)); border-radius: 20px; box-shadow: 0 7px 27px rgba(0, 0, 0, 0.05); overflow: hidden; position: relative; z-index: 10; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; color: var(--text-primary, #000); transition: all 0.3s ease; box-sizing: border-box; }
.text-shadow-fix { text-shadow: 0px 0px 1px rgba(0,0,0,0.15); }
.dark-mode .ios-card { background: var(--glass-bg, rgba(30, 41, 59, 0.6)); border-color: var(--glass-border, rgba(255, 255, 255, 0.1)); box-shadow: 0 7px 27px rgba(0, 0, 0, 0.2); color: var(--text-primary, #fff); }
.card-title { font-size: 12px; font-weight: 600; color: rgba(0, 0, 0, 0.85); margin-left: 3px; line-height: 1.4; }
.dark-mode .card-title { color: rgba(255, 255, 255, 0.6); }
.main-body { display: flex; justify-content: space-between; align-items: flex-end; height: 68px; }
.chart-area { display: flex; align-items: center; justify-content: center; width: 100%; height: 100%; padding-bottom: 2px; flex: 1; overflow: hidden; }
.data-area { display: flex; flex-direction: column; text-align: right; width: 110px; flex-shrink: 0; padding-right: 3px; justify-content: center; height: 100%; }
.big-metric { margin-bottom: 5px; }
.value { display: block; font-size: 29px; font-weight: 500; line-height: 1; color: #000; letter-spacing: -0.4px; font-variant-numeric: tabular-nums; }
.dark-mode .value { color: #fff; }
.label { display: block; font-size: 10px; font-weight: 600; color: rgba(60, 60, 67, 0.6); margin-top: 3px; }
.dark-mode .label { color: rgba(235, 235, 245, 0.6); }
.footer-info { display: flex; flex-direction: column; gap: 3px; margin-top: 0px; padding-top: 7px; }
.status-badge { font-size: 13px; font-weight: 600; display: flex; align-items: center; gap: 5px; line-height: 1; }

.status-badge.cold-damp { color: #1A73E8; }
.status-badge.muggy     { color: #D93025; }
.status-badge.stable-mild { color: #34C759; }
.dark-mode .status-badge.cold-damp { color: #8AB4F8; }
.dark-mode .status-badge.muggy     { color: #F28B82; }
.dark-mode .status-badge.stable-mild { color: #4CD964; }

.trend-icon { width: 16px; height: 16px; border-radius: 50%; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.trend-icon svg { width: 60%; height: 60%; }
.status-badge.cold-damp .trend-icon { background-color: #1A73E8; }
.status-badge.muggy .trend-icon     { background-color: #D93025; }
.status-badge.stable-mild .trend-icon { background-color: #34C759; }
.dark-mode .status-badge.cold-damp .trend-icon { background-color: #8AB4F8; }
.dark-mode .status-badge.muggy .trend-icon     { background-color: #F28B82; }
.dark-mode .status-badge.stable-mild .trend-icon { background-color: #4CD964; }

.analysis-text { font-size: 11px; color: rgba(60, 60, 67, 0.8); line-height: 1.4; margin: 0; }
.dark-mode .analysis-text { color: rgba(235, 235, 245, 0.8); }
.chart-wrapper { position: relative; width: 100%; height: 100%; }
.temp-chart { width: 100%; height: 100%; overflow: visible; display: block; }
.sub-val { font-size: 19px; }

/* 🌟 当前圆点的发光/阴影特效，增强原生 iOS 质感 */
.current-dot {
  filter: drop-shadow(0px 2px 4px rgba(0, 0, 0, 0.2));
  transition: all 0.3s ease;
}
.dark-mode .current-dot {
  filter: drop-shadow(0px 2px 4px rgba(0, 0, 0, 0.5));
}
</style>
