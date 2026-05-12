<template>
  <div class="weather-container" :class="{ 'dark-mode': isDarkMode }" :style="bgStyle">
    <div class="top-bar" :class="{ 'is-scrolled': isScrolled }">
      <div class="left-section">
        <div class="search-wrapper" ref="searchWrapperRef">
          <div class="search-box" :class="{ 'has-shadow': searchKey }">
            <input
              v-model="searchKey"
              type="text"
              placeholder="搜索城市..."
              @input="handleRealTimeSearch"
              @keyup.esc="clearSearch"
              @keydown.enter="handleEnterSearch"
            />
            <div class="search-actions">
              <transition name="fade">
                <button class="clear-btn" @click="clearSearch" v-show="searchKey">
                  <svg viewBox="0 0 24 24" width="14" height="14" stroke="currentColor" stroke-width="2.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
                    <line x1="18" y1="6" x2="6" y2="18"></line>
                    <line x1="6" y1="6" x2="18" y2="18"></line>
                  </svg>
                </button>
              </transition>
              <i class="search-icon" @click="handleEnterSearch">
                <svg viewBox="0 0 24 24" width="18" height="18" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round">
                  <circle cx="11" cy="11" r="8"></circle>
                  <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
                </svg>
              </i>
            </div>
          </div>

          <transition name="slide-fade">
            <div class="search-result" v-if="searchKey.trim()">
              <div class="status-box" v-if="isSearching">
                <div class="loading-spinner"></div>
                <span>查找中...</span>
              </div>
              <div class="status-box empty" v-else-if="isInvalidInput">
                <svg viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round">
                  <circle cx="12" cy="12" r="10"></circle>
                  <line x1="12" y1="8" x2="12" y2="12"></line>
                  <line x1="12" y1="16" x2="12.01" y2="16"></line>
                </svg>
                <span class="empty-text">城市名称不能以数字或符号开头</span>
              </div>
              <div class="location-list" v-else-if="locationList.length > 0">
                <div class="location-item" v-for="item in locationList.slice(0, 10)" :key="item.id" @click="selectLocation(item)">
                  <div class="item-main">
                    <span class="item-name">{{ item.name }}</span>
                  </div>
                  <span class="item-path">
                    {{ item.country }} · {{ item.adm1 }}
                    <span v-if="item.adm2 && item.adm2 !== item.name"> · {{ item.adm2 }}</span>
                  </span>
                </div>
              </div>
              <div class="status-box empty" v-else>
                <svg viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round">
                  <circle cx="11" cy="11" r="8"></circle>
                  <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
                  <line x1="11" y1="8" x2="11" y2="14"></line>
                  <line x1="8" y1="11" x2="14" y2="11"></line>
                </svg>
                <span class="empty-text">搜索的城市不存在</span>
              </div>
            </div>
          </transition>
        </div>

        <div class="quick-cities-wrapper" v-if="recentCities.length > 0">
          <div
            class="cities-scroll-view"
            ref="citiesScrollRef"
            @scroll="checkScrollable"
            :class="{
              'mask-right': isScrollable && isAtLeft && !isAtRight,
              'mask-left': isScrollable && !isAtLeft && isAtRight,
              'mask-both': isScrollable && !isAtLeft && !isAtRight
            }"
          >
            <div
              class="city-pill"
              :class="{ 'is-hovered': hoveredRecentCityId === city.id }"
              :data-city-id="city.id"
              v-for="city in recentCities"
              :key="city.id"
              @mousedown.prevent
              @pointerdown="hoveredRecentCityId = city.id"
              @mouseenter="hoveredRecentCityId = city.id"
              @mouseleave="handleRecentCityMouseLeave"
              @click="handleRecentCityClick(city, $event)"
            >
              <div class="pill-content">
                <span class="city-name">{{ city.name }}</span>
                <img :src="`https://openweathermap.org/img/wn/${getWeatherIcon(city.text)}@2x.png`" :alt="city.text" class="pill-icon" />
                <span class="city-temp">{{ formatTemperature(city.tempMax) }}</span>
                <span class="delete-btn" @click.stop="removeRecentCity(city.id)" title="删除该记录">
                  <svg viewBox="0 0 24 24" stroke="currentColor" fill="none" stroke-linecap="round" stroke-linejoin="round">
                    <line x1="18" y1="6" x2="6" y2="18"></line>
                    <line x1="6" y1="6" x2="18" y2="18"></line>
                  </svg>
                </span>
              </div>
            </div>
          </div>
          <transition name="fade">
            <div class="nav-controls" v-show="isScrollable">
              <button class="nav-btn prev" @click="scrollCities('left')" title="向左滚动">
                <svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"></polyline></svg>
              </button>
              <button class="nav-btn next" @click="scrollCities('right')" title="向右滚动">
                <svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"></polyline></svg>
              </button>
            </div>
          </transition>
        </div>

        <div class="quick-cities-wrapper history-title-strip" v-else>
          <div class="history-title-pill">
            <span class="city-name">近10天历史天气</span>
            <span class="city-temp">不含今天</span>
          </div>
        </div>
      </div>

      <div class="right-section">
        <button class="unit-toggle-btn wind-unit-toggle-btn" @click="toggleWindUnit" :title="`切换风力单位：${currentWindUnitLabel}`">
          {{ currentWindUnitLabel }}
        </button>
        <button class="unit-toggle-btn" @click="toggleUnit" title="切换温度单位">
          {{ tempUnit === 'C' ? '°C' : '°F' }}
        </button>
      </div>
    </div>

    <Teleport to="body">
      <transition name="fade">
        <div class="global-loading-mask" v-if="isWeatherLoading" :style="loadingMaskStyle">
          <div class="loading-content">
            <div class="loading-spinner-large"></div>
            <span class="loading-text">正在更新数据...</span>
          </div>
        </div>
      </transition>
    </Teleport>

    <div class="content-body">
      <div v-if="!historyData" class="empty-state">
        <div class="empty-content">
          <div class="sun-decoration"></div>
          <p>请输入城市名称查看最近10天历史天气</p>
        </div>
      </div>

      <div class="main-content-wrapper" v-if="historyData">
        <aside class="side-content left-side">
          <div class="left-side-stack">
            <div class="astro-card" :key="'astro-' + animationKey">
              <div class="side-card-kicker">天文信息</div>
              <div class="moon-phase-display">
                <span :class="['moon-simple', moonPhaseClass]" aria-hidden="true"></span>
                <div class="moon-phase-copy">
                  <span>月相</span>
                  <strong>{{ historyDaily.moonPhase || '--' }}</strong>
                </div>
              </div>
              <div class="astro-list">
                <div class="astro-item">
                  <span>日出</span>
                  <strong>{{ historyDaily.sunrise || '--:--' }}</strong>
                </div>
                <div class="astro-item">
                  <span>日落</span>
                  <strong>{{ historyDaily.sunset || '--:--' }}</strong>
                </div>
                <div class="astro-item">
                  <span>昼长</span>
                  <strong>{{ daylightDuration }}</strong>
                </div>
                <div class="astro-item">
                  <span>月升</span>
                  <strong>{{ historyDaily.moonrise || '--:--' }}</strong>
                </div>
                <div class="astro-item">
                  <span>月落</span>
                  <strong>{{ historyDaily.moonset || '--:--' }}</strong>
                </div>
              </div>
            </div>

            <div class="air-trend-card" v-if="hasAirTrend" :key="'air-trend-' + animationKey">
              <div class="side-card-kicker">空气质量趋势</div>
              <div class="air-trend-head">
                <div class="air-trend-score">
                  <span>近10天平均</span>
                  <strong>{{ airTrendStats.average }}</strong>
                </div>
                <div class="air-trend-summary">
                  <span>最低 / 最高</span>
                  <strong>{{ airTrendStats.best }} - {{ airTrendStats.worst }}</strong>
                </div>
              </div>
              <div class="air-trend-bars">
                <div class="air-trend-day" v-for="item in airTrendDays" :key="item.date" :title="`${item.label} AQI ${item.aqi} ${item.category}`">
                  <span class="air-trend-track">
                    <span class="air-trend-bar" :class="item.aqiClass" :style="{ height: `${item.height}%` }"></span>
                  </span>
                  <span class="air-trend-date">{{ item.label }}</span>
                </div>
              </div>
            </div>

            <div class="air-card" v-if="hasActiveAirQuality" :key="'air-' + animationKey">
              <div class="side-card-kicker">污染物详情</div>
              <div class="air-primary-row" v-if="activeAirSummary.primary && activeAirSummary.primary !== '--'">
                <span>主要污染物</span>
                <strong>{{ activeAirSummary.primary }}</strong>
              </div>
              <div class="air-pollutants" v-if="airPollutants.length">
                <div class="air-pollutant" v-for="item in airPollutants" :key="item.label">
                  <span>{{ item.label }}</span>
                  <strong>{{ item.value }}</strong>
                </div>
              </div>
            </div>
          </div>
        </aside>

        <div class="left-content">
          <div class="weather-card" :key="'history-' + animationKey">
            <div class="card-glass-glow"></div>

            <div class="card-top-row">
              <div class="card-title">
                <h3>{{ currentLocation }}</h3>
                <div class="title-meta-row">
                  <span class="title-path" v-if="currentLocationDetail">
                    {{ currentLocationDetail.country }} · {{ currentLocationDetail.adm1 }}
                    <span v-if="currentLocationDetail.adm2 && currentLocationDetail.adm2 !== currentLocationDetail.name">
                      · {{ currentLocationDetail.adm2 }}
                    </span>
                  </span>
                  <span class="divider" v-if="currentLocationDetail">|</span>
                  <span class="update-time">最近10天历史天气，不含今天</span>
                </div>
              </div>
            </div>

            <div class="main-weather-section">
              <div class="weather-icon-wrapper">
                <img :src="`https://openweathermap.org/img/wn/${getWeatherIcon(mainWeatherText)}@4x.png`" :alt="mainWeatherText" class="main-icon"/>
              </div>
              <div class="temp-display">
                <span class="degree">{{ formatTemperature(historyDaily.tempMax) }}</span>
              </div>
              <div class="condition-group">
                <span class="condition-text">{{ mainWeatherText }}</span>
                <span class="feels-like">{{ formatHistoryDate(historyDaily.date) }} · 最低 {{ formatTemperature(historyDaily.tempMin) }}</span>
              </div>
            </div>

            <div class="weather-summary">
              当前展示 {{ formatHistoryDate(historyDaily.date) }} 的每日概况和24小时历史记录。
            </div>

            <div class="detail-grid">
              <div class="grid-item"><span class="grid-label">降水量</span><span class="grid-value color-quality">{{ formatPrecipitation(historyDaily.precip) }}</span></div>
              <div class="grid-item"><span class="grid-label">相对湿度</span><span class="grid-value">{{ historyDaily.humidity || '--' }}%</span></div>
              <div class="grid-item"><span class="grid-label">气压</span><span class="grid-value">{{ historyDaily.pressure || '--' }} hPa</span></div>
              <div class="grid-item"><span class="grid-label">风向</span><span class="grid-value">{{ primaryWindDirection }}</span></div>
              <div class="grid-item"><span class="grid-label">风力</span><span class="grid-value">{{ primaryWindStrength }}</span></div>
              <div class="grid-item"><span class="grid-label">小时记录</span><span class="grid-value">{{ hourlyRecordCount }}</span></div>
            </div>
          </div>

          <div class="history-days-card" :key="'days-' + animationKey">
            <div class="hourly-title-row">
              <div class="title-text-group">
                <span>近10天概览</span>
                <span class="hourly-summary">点击某一天可查看当天24小时记录</span>
              </div>
            </div>
            <div class="history-days-grid">
              <button
                v-for="(day, index) in historyDays"
                :key="day.date"
                type="button"
                class="history-day-item"
                :class="{ active: activeDayIndex === index }"
                @click="selectHistoryDay(index)"
              >
                <span class="day-date">{{ formatHistoryDate(getDayDaily(day)?.date) }}</span>
                <img :src="`https://openweathermap.org/img/wn/${getWeatherIcon(getDayText(day))}@2x.png`" :alt="getDayText(day)" />
                <strong>{{ formatTemperature(getDayDaily(day)?.tempMax) }}</strong>
                <small>{{ getDayText(day) }}</small>
                <div class="day-meta-row">
                  <span class="day-low-temp">低 {{ formatTemperature(getDayDaily(day)?.tempMin) }}</span>
                  <span class="day-aqi" :class="getAqiClass(getDayAirSummary(day))">
                    AQI {{ getDayAirSummary(day).aqi }} {{ getDayAirSummary(day).category }}
                  </span>
                </div>
              </button>
            </div>
          </div>

          <div class="temp-compare-card" :key="'temp-compare-' + animationKey">
            <div class="hourly-title-row">
              <div class="title-text-group">
                <span>每日最高 / 最低温</span>
                <span class="hourly-summary">查看最近10天每日高低温与温差对比</span>
              </div>
            </div>
            <div class="temp-range-board" v-if="tempComparePoints.length">
              <div class="temp-range-days">
                <div
                  v-for="point in tempComparePoints"
                  :key="point.date"
                  class="temp-range-day"
                >
                  <div class="temp-range-head">
                    <strong>{{ point.weekday }}</strong>
                    <span>{{ point.dateLabel }}</span>
                  </div>
                  <div class="temp-range-meter">
                    <span class="temp-range-value temp-range-high">{{ point.high }}°</span>
                    <div class="temp-range-rail" aria-hidden="true">
                      <span
                        class="temp-range-fill"
                        :style="{ top: `${point.rangeTop}%`, height: `${point.rangeHeight}%` }"
                      >
                        <i class="temp-range-dot high-dot"></i>
                        <i class="temp-range-dot low-dot"></i>
                      </span>
                    </div>
                    <span class="temp-range-value temp-range-low">{{ point.low }}°</span>
                  </div>
                  <div class="temp-range-spread">{{ point.spread }}°温差</div>
                </div>
              </div>
            </div>
          </div>

          <div class="hourly-card" :key="'hourly-' + animationKey">
            <div class="hourly-forecast">
              <div class="hourly-title-row">
                <div class="title-text-group">
                  <span>24小时历史记录</span>
                  <span class="hourly-summary">{{ shortTermSummary }}</span>
                </div>
                <div class="hourly-nav-group">
                  <button class="nav-arrow-btn" @click="scrollHourly('left')"><svg viewBox="0 0 24 24" width="18" height="18" stroke="currentColor" stroke-width="2.5" fill="none" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"></polyline></svg></button>
                  <button class="nav-arrow-btn" @click="scrollHourly('right')"><svg viewBox="0 0 24 24" width="18" height="18" stroke="currentColor" stroke-width="2.5" fill="none" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"></polyline></svg></button>
                </div>
              </div>
              <div class="hourly-wrapper-relative">
                <div class="hourly-scroll-container" ref="hourlyScrollRef">
                  <div class="hourly-track" :key="'hourly-track-' + hourlyLayoutKey" :style="{ width: hourlyTrackWidth + 'px' }">
                    <svg class="chart-svg" :width="hourlyTrackWidth" height="120" style="overflow: visible;">
                      <defs>
                        <linearGradient id="historyTempStrokeGradient" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="0%" stop-color="#ff9a9e" />
                          <stop offset="40%" stop-color="#fed6e3" />
                          <stop offset="100%" stop-color="#a18cd1" />
                        </linearGradient>
                      </defs>
                      <path :d="chartPath" fill="none" stroke="url(#historyTempStrokeGradient)" stroke-width="4" stroke-linecap="round" stroke-linejoin="round" style="filter: drop-shadow(0px 4px 3px rgba(0,0,0,0.15));"/>
                      <g v-for="(point, idx) in chartPoints" :key="idx">
                        <circle :cx="point.x" :cy="point.y" r="4" :fill="isDarkMode ? '#334155' : '#fff'" :stroke="point.isSunEvent ? (point.sunLabel === '日出' ? '#f59e0b' : '#3b82f6') : (isDarkMode ? 'rgba(255,255,255,0.2)' : 'rgba(0,0,0,0.1)')" :stroke-width="point.isSunEvent ? 2 : 1"/>
                        <text :x="point.x" :y="point.y - 14" :fill="point.isSunEvent ? (point.sunLabel === '日出' ? '#d97706' : '#2563eb') : chartTextColor" :font-size="point.isSunEvent ? '13' : '14'" :font-weight="point.isSunEvent ? '600' : '700'" text-anchor="middle">{{ point.isSunEvent ? point.sunLabel : `${point.temp}°` }}</text>
                      </g>
                    </svg>
                    <div class="hourly-items-row">
                      <div class="hourly-item" v-for="item in hourlyData" :key="item.time">
                        <div class="chart-spacer"></div>
                        <div class="hourly-details">
                          <div class="hourly-icon">
                            <img :src="`https://openweathermap.org/img/wn/${getWeatherIcon(item.text)}@2x.png`" :alt="item.text"/>
                          </div>
                          <div class="hourly-weather">{{ item.isSunEvent ? item.sunLabel : (item.text || '--') }}</div>
                          <div class="hourly-wind">
                            <span>{{ formatWind(item) }}</span>
                            <span v-if="!item.isSunEvent && item.windDir" class="hourly-wind-dir">{{ item.windDir }}</span>
                          </div>
                          <div class="hourly-extra">{{ item.isSunEvent ? '日照节点' : `${item.humidity || '--'}% · ${formatPrecipitation(item.precip)}` }}</div>
                          <div class="hourly-time-container"><span class="hourly-time" :class="{ 'time-sun-event': item.isSunEvent }" :style="item.isSunEvent ? { color: item.sunLabel === '日出' ? '#d97706' : '#2563eb' } : {}">{{ item.timeLabel }}</span></div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="beian-info">
      <a href="https://beian.miit.gov.cn" target="_blank" rel="noopener noreferrer">
        浙ICP备2025209216号-1
      </a>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue';
import request from '@/utils/requests';
import { ElMessage } from 'element-plus';
import { canGuestQueryWeather, consumeGuestWeatherQuery } from '@/utils/guestQuota';
import { generateSignedHeaders } from '@/utils/signature';

const HOURLY_ITEM_WIDTH = 60;
const CACHE_KEY = 'recent_history_weather_cities';
const MAX_CACHE_COUNT = 10;
const ICON_MAP = {
  '晴': '01d', '少云': '02d', '晴间多云': '02d', '多云': '04d', '阴': '04d',
  '阵雨': '09d', '强阵雨': '09d', '雷阵雨': '11d', '小雨': '10d', '中雨': '10d',
  '大雨': '09d', '暴雨': '09d', '雪': '13d', '雾': '50d', '霾': '50d'
};
const BG_CONFIG = [
  { keys: ['晴'], gradient: 'linear-gradient(180deg, #A1C4FD 0%, #C2E9FB 100%)', darkGradient: 'linear-gradient(180deg, #0f172a 0%, #172554 52%, #1d4ed8 100%)' },
  { keys: ['多云'], gradient: 'linear-gradient(180deg, #C9D6FF 0%, #E2E2E2 100%)', darkGradient: 'linear-gradient(180deg, #111827 0%, #1e3a5f 50%, #365b86 100%)' },
  { keys: ['阴'], gradient: 'linear-gradient(180deg, #8e9eab 0%, #eef2f3 100%)', darkGradient: 'linear-gradient(180deg, #0f172a 0%, #1f2937 46%, #334155 100%)' },
  { keys: ['雨'], gradient: 'linear-gradient(180deg, #BCC5CE 0%, #DEE4E8 100%)', darkGradient: 'linear-gradient(180deg, #0b1120 0%, #172033 54%, #243b53 100%)' },
  { keys: ['雪'], gradient: 'linear-gradient(180deg, #E6DADA 0%, #274046 100%)', darkGradient: 'linear-gradient(180deg, #111827 0%, #1f2937 50%, #475569 100%)' }
];
const DEFAULT_BG = 'linear-gradient(180deg, #FFF5EB 0%, #E6EEF5 100%)';
const DEFAULT_DARK_BG = 'linear-gradient(180deg, #0b1120 0%, #14213d 48%, #23395d 100%)';

const searchWrapperRef = ref(null);
const citiesScrollRef = ref(null);
const hourlyScrollRef = ref(null);
const searchKey = ref('');
const locationList = ref([]);
const currentLocationDetail = ref(null);
const currentLocation = ref('');
const recentCities = ref([]);
const historyData = ref(null);
const historyDays = ref([]);
const activeDayIndex = ref(0);
const hourlyData = ref([]);
const isSearching = ref(false);
const isWeatherLoading = ref(false);
const isInvalidInput = ref(false);
const isDarkMode = ref(false);
const isScrolled = ref(false);
const tempUnit = ref('C');
const WIND_UNIT_OPTIONS = [
  { value: 'beaufort', label: '蒲福' },
  { value: 'kmh', label: 'km/h' },
  { value: 'ms', label: 'm/s' },
  { value: 'mph', label: 'mph' },
  { value: 'kn', label: 'kn' }
];
const windUnit = ref('beaufort');
const animationKey = ref(0);
const hourlyLayoutKey = ref(0);
const isScrollable = ref(false);
const isAtLeft = ref(true);
const isAtRight = ref(false);
const hoveredRecentCityId = ref(null);
const lastPointerPosition = ref({ x: 0, y: 0 });
let searchTimer = null;
let resizeFrame = 0;

const activeDay = computed(() => historyDays.value[activeDayIndex.value] || historyData.value || null);
const historyDaily = computed(() => activeDay.value?.weatherDaily || activeDay.value?.weather_daily || {});
const getDayAirHourly = (day) => day?.airHourly || day?.air_hourly || [];
const activeAirSummary = computed(() => getDayAirSummary(activeDay.value));
const activeAirHourly = computed(() => getDayAirHourly(activeDay.value));
const hasActiveAirQuality = computed(() => {
  const aqi = Number(activeAirSummary.value?.aqi);
  return Number.isFinite(aqi) && aqi > 0;
});
const airPollutants = computed(() => {
  const hourly = activeAirHourly.value;
  if (!hourly.length) return [];

  const average = (key) => {
    const values = hourly
      .map(item => Number(item?.[key]))
      .filter(Number.isFinite);
    if (!values.length) return '--';
    const avg = values.reduce((sum, value) => sum + value, 0) / values.length;
    return avg >= 10 ? String(Math.round(avg)) : avg.toFixed(1);
  };

  return [
    { label: 'PM10', value: average('pm10') },
    { label: 'PM2.5', value: average('pm2p5') },
    { label: 'NO₂', value: average('no2') },
    { label: 'SO₂', value: average('so2') },
    { label: 'CO', value: average('co') },
    { label: 'O₃', value: average('o3') },
  ].filter(item => item.value !== '--');
});
const airTrendDays = computed(() => {
  const source = historyDays.value
    .map((day) => {
      const summary = getDayAirSummary(day);
      const aqi = Number(summary?.aqi);
      if (!Number.isFinite(aqi) || aqi <= 0) return null;
      const date = getDayDaily(day)?.date || day?.date || '';
      return {
        date,
        label: formatShortDate(date),
        aqi,
        category: summary?.category || '--',
        aqiClass: getAqiClass(summary)
      };
    })
    .filter(Boolean);

  if (!source.length) return [];
  const maxAqi = Math.max(...source.map(item => item.aqi), 100);
  return source.map((item) => ({
    ...item,
    height: Math.max(18, Math.round((item.aqi / maxAqi) * 100))
  }));
});
const hasAirTrend = computed(() => airTrendDays.value.length > 0);
const airTrendStats = computed(() => {
  if (!airTrendDays.value.length) {
    return { average: '--', best: '--', worst: '--', bestLabel: '--' };
  }
  const aqiList = airTrendDays.value.map(item => item.aqi);
  const average = Math.round(aqiList.reduce((sum, value) => sum + value, 0) / aqiList.length);
  const best = Math.min(...aqiList);
  const worst = Math.max(...aqiList);
  return {
    average,
    best,
    worst,
    bestLabel: best <= 50 ? '优' : best <= 100 ? '良' : best <= 150 ? '轻度' : best <= 200 ? '中度' : best <= 300 ? '重度' : '严重'
  };
});
const moonPhaseClass = computed(() => {
  const phase = String(historyDaily.value?.moonPhase || '');
  if (phase.includes('新月')) return 'moon-new';
  if (phase.includes('上弦')) return 'moon-first-quarter';
  if (phase.includes('盈凸')) return 'moon-waxing-gibbous';
  if (phase.includes('满月') || phase.includes('望')) return 'moon-full';
  if (phase.includes('亏凸')) return 'moon-waning-gibbous';
  if (phase.includes('下弦')) return 'moon-last-quarter';
  if (phase.includes('残月')) return 'moon-waning-crescent';
  if (phase.includes('眉月')) return 'moon-waxing-crescent';
  return 'moon-waxing-crescent';
});
const mainWeatherText = computed(() => {
  const texts = hourlyData.value.map(item => item.text).filter(Boolean);
  return Array.from(new Set(texts)).slice(0, 3).join(' / ') || '历史天气';
});
const shortTermSummary = computed(() => hourlyData.value.length ? `${mainWeatherText.value}，共 ${hourlyData.value.length} 条记录` : '暂无逐小时数据');
const bgStyle = computed(() => {
  const defaultGradient = isDarkMode.value ? DEFAULT_DARK_BG : DEFAULT_BG;
  const match = BG_CONFIG.find(item => item.keys.some(key => mainWeatherText.value.includes(key)));
  return { background: `${match ? (isDarkMode.value ? match.darkGradient : match.gradient) : defaultGradient} !important` };
});
const loadingMaskStyle = computed(() => ({
  '--weather-loading-mask-bg': isDarkMode.value ? 'rgba(2, 6, 23, 0.52)' : 'rgba(255, 255, 255, 0.3)',
  '--weather-loading-content-bg': isDarkMode.value ? 'rgba(15, 23, 42, 0.9)' : 'rgba(255, 255, 255, 0.8)',
  '--weather-loading-text-color': isDarkMode.value ? '#e2e8f0' : '#475569',
  '--weather-loading-shadow': isDarkMode.value ? '0 12px 40px rgba(2, 6, 23, 0.42)' : '0 8px 34px rgba(0,0,0,0.1)'
}));
const chartTextColor = computed(() => isDarkMode.value ? '#e2e8f0' : '#475569');
const hourlyTrackWidth = computed(() => Math.max(hourlyData.value.length * HOURLY_ITEM_WIDTH, 360));
const currentWindUnitLabel = computed(() => WIND_UNIT_OPTIONS.find(item => item.value === windUnit.value)?.label || '蒲福');
const hourlyWeatherRecords = computed(() => hourlyData.value.filter(item => !item.isSunEvent));
const primaryWindRecord = computed(() => {
  const records = hourlyWeatherRecords.value.filter(item => item.windDir || item.windScale || item.windSpeed);
  if (!records.length) return null;
  return records.reduce((strongest, item) => {
    const itemSpeed = normalizeNumericValue(item.windSpeed) ?? -1;
    const strongestSpeed = normalizeNumericValue(strongest.windSpeed) ?? -1;
    return itemSpeed > strongestSpeed ? item : strongest;
  }, records[0]);
});
const primaryWindDirection = computed(() => primaryWindRecord.value?.windDir || '--');
const primaryWindStrength = computed(() => primaryWindRecord.value ? formatWind(primaryWindRecord.value) : '--');
const hourlyRecordCount = computed(() => `${hourlyWeatherRecords.value.length || 0}条`);
const normalizeNumericValue = (value) => {
  if (value === undefined || value === null || value === '') return null;
  const numberValue = Number(value);
  return Number.isFinite(numberValue) ? numberValue : null;
};
const convertTemperatureValue = (value) => {
  const numberValue = normalizeNumericValue(value);
  if (numberValue === null) return null;
  const converted = tempUnit.value === 'F' ? numberValue * 9 / 5 + 32 : numberValue;
  return Math.round(converted);
};
const convertPrecipitationValue = (value) => {
  const numberValue = normalizeNumericValue(value);
  if (numberValue === null) return null;
  const converted = tempUnit.value === 'F' ? numberValue / 25.4 : numberValue;
  return tempUnit.value === 'F' ? converted.toFixed(1) : numberValue.toFixed(1);
};
const chartPoints = computed(() => {
  const temps = hourlyData.value.map(item => convertTemperatureValue(item.temp)).filter(Number.isFinite);
  if (!temps.length) return [];
  const min = Math.min(...temps);
  const max = Math.max(...temps);
  const range = Math.max(max - min, 1);
  return hourlyData.value.map((item, index) => {
    const temp = convertTemperatureValue(item.temp) ?? 0;
    return {
      x: index * HOURLY_ITEM_WIDTH + HOURLY_ITEM_WIDTH / 2,
      y: 65 - ((temp - min) / range) * 38,
      temp,
      isSunEvent: item.isSunEvent,
      sunLabel: item.sunLabel
    };
  });
});
const chartPath = computed(() => chartPoints.value.map((point, index) => `${index === 0 ? 'M' : 'L'} ${point.x} ${point.y}`).join(' '));
const tempCompareSource = computed(() => historyDays.value
  .map((day, dayIndex) => {
    const daily = getDayDaily(day);
    const high = convertTemperatureValue(daily.tempMax);
    const low = convertTemperatureValue(daily.tempMin);
    if (high === null || low === null) return null;
    const date = daily.date || day?.date || '';
    return {
      date,
      label: formatShortDate(date),
      dateLabel: formatShortDate(date),
      weekday: formatWeekday(date),
      dayText: getRepresentativeWeatherText(day, 12, 'day'),
      nightText: getRepresentativeWeatherText(day, 21, 'night'),
      dayIndex,
      high,
      low
    };
  })
  .filter(Boolean));
const tempComparePoints = computed(() => {
  const source = tempCompareSource.value;
  if (!source.length) return [];

  const highValues = source.map(item => item.high);
  const lowValues = source.map(item => item.low);
  const tempMin = Math.min(...highValues, ...lowValues);
  const tempMax = Math.max(...highValues, ...lowValues);
  const tempRange = Math.max(tempMax - tempMin, 1);

  return source.map((item) => {
    const highTopPercent = ((tempMax - item.high) / tempRange) * 100;
    const lowTopPercent = ((tempMax - item.low) / tempRange) * 100;
    const rawHeight = lowTopPercent - highTopPercent;

    return {
      ...item,
      spread: Math.max(item.high - item.low, 0),
      rangeTop: Math.max(4, Math.min(88, highTopPercent)),
      rangeHeight: Math.max(12, Math.min(86, rawHeight))
    };
  });
});
const daylightDuration = computed(() => {
  const sunrise = historyDaily.value?.sunrise;
  const sunset = historyDaily.value?.sunset;
  if (!sunrise || !sunset || sunrise === '--:--' || sunset === '--:--') return '--';

  const [riseHour, riseMinute] = sunrise.split(':').map(Number);
  const [setHour, setMinute] = sunset.split(':').map(Number);
  if (![riseHour, riseMinute, setHour, setMinute].every(Number.isFinite)) return '--';

  const diff = (setHour * 60 + setMinute) - (riseHour * 60 + riseMinute);
  if (diff <= 0) return '--';

  const hours = Math.floor(diff / 60);
  const minutes = diff % 60;
  return `${hours}小时${minutes ? `${minutes}分` : ''}`;
});
const clearSearch = () => {
  searchKey.value = '';
  locationList.value = [];
  isInvalidInput.value = false;
};

const isFirstCharInvalid = (str) => /^[0-9!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?~`·！@#￥%……&*（）——+=-【】{}；：”“’。，、？～·`]/.test(str.trim()[0]);

const handleRealTimeSearch = () => {
  clearTimeout(searchTimer);
  const keyword = searchKey.value.trim();
  historyData.value = historyData.value && currentLocationDetail.value ? historyData.value : null;
  if (!keyword) {
    locationList.value = [];
    isInvalidInput.value = false;
    return;
  }
  if (isFirstCharInvalid(keyword)) {
    locationList.value = [];
    isInvalidInput.value = true;
    return;
  }
  isInvalidInput.value = false;
  searchTimer = setTimeout(() => searchLocations(keyword), 250);
};

const searchLocations = async (keyword) => {
  isSearching.value = true;
  try {
    const params = { q: keyword };
    const response = await request.get('/weather/user/location/search', {
      params,
      headers: generateSignedHeaders(params),
      timeout: 8000
    });
    locationList.value = Array.isArray(response.data?.data) ? response.data.data : [];
  } catch {
    locationList.value = [];
  } finally {
    isSearching.value = false;
  }
};

const handleEnterSearch = () => {
  if (locationList.value.length) {
    selectLocation(locationList.value[0]);
  }
};

const selectLocation = (item) => {
  currentLocationDetail.value = item;
  currentLocation.value = item.name;
  searchKey.value = '';
  locationList.value = [];
  fetchHistoricalWeather();
};

const handleRecentCityClick = async (city) => {
  hoveredRecentCityId.value = city.id;
  selectLocation(city);
  await nextTick();
  hoveredRecentCityId.value = city.id;
};

const handleRecentCityMouseLeave = () => {
  if (isWeatherLoading.value) return;
  hoveredRecentCityId.value = null;
};

const handleGlobalPointerMove = (event) => {
  lastPointerPosition.value = { x: event.clientX, y: event.clientY };
};

const syncHoveredRecentCityFromPointer = () => {
  const { x, y } = lastPointerPosition.value;
  if (!x && !y) return;
  const element = document.elementFromPoint(x, y);
  const cityPill = element?.closest?.('.city-pill');
  hoveredRecentCityId.value = cityPill?.dataset?.cityId || null;
};

const removeRecentCity = async (cityId) => {
  hoveredRecentCityId.value = null;
  recentCities.value = recentCities.value.filter(city => city.id !== cityId);
  localStorage.setItem(CACHE_KEY, JSON.stringify(recentCities.value));
  await nextTick();
  checkScrollable();
};

const upsertCache = async (item, day) => {
  try {
    const daily = getDayDaily(day);
    const id = item.id || item.location || item.locationId;
    if (!id || !item.name) return;

    const index = recentCities.value.findIndex(city => city.id === id);
    const previousUsageCount = index > -1 ? Number(recentCities.value[index].usageCount || 0) : 0;
    const newItem = {
      id,
      name: item.name,
      country: item.country,
      adm1: item.adm1,
      adm2: item.adm2,
      lat: item.lat,
      lon: item.lon,
      tempMax: daily.tempMax,
      tempMin: daily.tempMin,
      text: getDayText(day),
      usageCount: previousUsageCount + 1
    };

    const cities = index > -1
      ? recentCities.value.map(city => city.id === id ? newItem : city)
      : [newItem, ...recentCities.value].slice(0, MAX_CACHE_COUNT);

    recentCities.value = cities;
    localStorage.setItem(CACHE_KEY, JSON.stringify(cities));
    await nextTick();
    checkScrollable();
  } catch (error) {
    console.error('History weather cache error', error);
  }
};

const loadFromCache = () => {
  try {
    const cached = localStorage.getItem(CACHE_KEY);
    if (cached) recentCities.value = JSON.parse(cached);
  } catch {
    recentCities.value = [];
  }
};

watch(() => recentCities.value.length, () => {
  nextTick(() => checkScrollable());
}, { immediate: true });

const getDayText = (day) => {
  const texts = (getDayHourly(day) || []).map(item => item.text).filter(Boolean);
  return Array.from(new Set(texts)).slice(0, 2).join(' / ') || getDayDaily(day)?.text || '--';
};

const getDayDaily = (day) => day?.weatherDaily || day?.weather_daily || {};
const getDayHourly = (day) => day?.weatherHourly || day?.weather_hourly || [];
function getDayAirSummary(day) {
  const summary = day?.airSummary || day?.air_summary || getDayDaily(day)?.airQuality || {};
  return {
    aqi: summary.aqi || '--',
    level: String(summary.level || ''),
    category: summary.category || '--',
    primary: summary.primary || '--'
  };
}
const getAqiClass = (summary) => {
  const level = Number(summary?.level);
  const aqi = Number(summary?.aqi);
  const normalizedLevel = Number.isFinite(level) && level > 0
    ? level
    : Number.isFinite(aqi)
      ? (aqi <= 50 ? 1 : aqi <= 100 ? 2 : aqi <= 150 ? 3 : aqi <= 200 ? 4 : aqi <= 300 ? 5 : 6)
      : 0;
  return `aqi-level-${normalizedLevel || 'unknown'}`;
};

const buildHistoricalHourlyTimeline = (day) => {
  const daily = getDayDaily(day);
  const hourly = getDayHourly(day);
  if (!hourly.length) return [];

  const list = hourly.map((item) => {
    const temp = Number(item.temp);
    const timeText = item.time || '';
    return {
      ...item,
      timeObj: new Date(timeText.replace(' ', 'T')),
      temp: Number.isFinite(temp) ? temp : 0,
      timeLabel: timeText.slice(11, 16) || '--',
      isSunEvent: false
    };
  }).sort((a, b) => a.timeObj - b.timeObj);

  const datePrefix = daily.date || day?.date;
  const sunEvents = [
    { label: '日出', time: daily.sunrise },
    { label: '日落', time: daily.sunset }
  ].filter(item => datePrefix && item.time && item.time !== '--:--');

  sunEvents.forEach((event) => {
    const eventTimeObj = new Date(`${datePrefix}T${event.time}`);
    if (Number.isNaN(eventTimeObj.getTime())) return;

    const nextIndex = list.findIndex(item => item.timeObj > eventTimeObj);
    const prevItem = list[Math.max(0, nextIndex - 1)] || list[0];
    const nextItem = list[nextIndex] || prevItem;

    if (!prevItem) return;

    list.push({
      time: `${datePrefix} ${event.time}`,
      timeObj: eventTimeObj,
      temp: Number.isFinite(Number(prevItem.temp)) ? Number(prevItem.temp) : Number(nextItem?.temp || 0),
      text: nextItem?.text || prevItem.text || '',
      precip: '0.0',
      windScale: nextItem?.windScale || prevItem.windScale || '',
      humidity: nextItem?.humidity || prevItem.humidity || '',
      timeLabel: event.time,
      isSunEvent: true,
      sunLabel: event.label
    });
  });

  return list.sort((a, b) => a.timeObj - b.timeObj);
};

const setActiveDay = (index) => {
  activeDayIndex.value = index;
  const day = historyDays.value[index];
  hourlyData.value = buildHistoricalHourlyTimeline(day);
};

const selectHistoryDay = (index) => {
  setActiveDay(index);
  animationKey.value += 1;
};

const fetchHistoricalWeather = async () => {
  if (!currentLocationDetail.value) {
    ElMessage.warning('请先选择城市');
    return;
  }
  if (!canGuestQueryWeather()) return;

  isWeatherLoading.value = true;
  try {
    const params = {
      location: currentLocationDetail.value.id,
      lang: 'zh',
      unit: 'm'
    };
    const response = await request.get('/weather/user/weather/history', {
      params,
      headers: generateSignedHeaders(params),
      timeout: 20000
    });
    if (response.data?.code !== 200 || !response.data?.data) {
      ElMessage.warning(response.data?.message || '暂无历史天气数据');
      return;
    }
    historyData.value = response.data.data;
    historyDays.value = response.data.data.history || response.data.data.history_days || [];
    if (!historyDays.value.length) {
      ElMessage.warning('近10天历史天气暂无可展示数据');
      historyData.value = null;
      hourlyData.value = [];
      return;
    }
    setActiveDay(0);
    animationKey.value += 1;
    await upsertCache(currentLocationDetail.value, historyDays.value[0]);
    consumeGuestWeatherQuery();
  } catch {
    historyData.value = null;
    historyDays.value = [];
    hourlyData.value = [];
  } finally {
    isWeatherLoading.value = false;
    await nextTick();
    requestAnimationFrame(syncHoveredRecentCityFromPointer);
  }
};

const toggleUnit = () => {
  tempUnit.value = tempUnit.value === 'C' ? 'F' : 'C';
  localStorage.setItem('weather_unit_pref', tempUnit.value);
  animationKey.value += 1;
};

const toggleWindUnit = () => {
  const currentIndex = WIND_UNIT_OPTIONS.findIndex(item => item.value === windUnit.value);
  const nextIndex = currentIndex >= 0 ? (currentIndex + 1) % WIND_UNIT_OPTIONS.length : 0;
  windUnit.value = WIND_UNIT_OPTIONS[nextIndex].value;
  localStorage.setItem('weather_wind_unit_pref', windUnit.value);
};

const formatTemperature = (value) => {
  const converted = convertTemperatureValue(value);
  return converted === null ? '--' : `${converted}°${tempUnit.value}`;
};

const formatPrecipitation = (value) => {
  const converted = convertPrecipitationValue(value);
  return converted === null ? `-- ${tempUnit.value === 'F' ? 'in' : 'mm'}` : `${converted} ${tempUnit.value === 'F' ? 'in' : 'mm'}`;
};

const formatWind = (item) => {
  if (!item || item.isSunEvent) return '天文';
  if (windUnit.value === 'beaufort') return `${item.windScale || '--'}级`;

  const kmh = normalizeNumericValue(item.windSpeed);
  if (kmh === null) return '--';

  if (windUnit.value === 'kmh') return `${Math.round(kmh)}km/h`;
  if (windUnit.value === 'ms') return `${(kmh / 3.6).toFixed(1)}m/s`;
  if (windUnit.value === 'mph') return `${(kmh * 0.621371).toFixed(1)}mph`;
  if (windUnit.value === 'kn') return `${(kmh * 0.539957).toFixed(1)}kn`;
  return `${item.windScale || '--'}级`;
};

const formatHistoryDate = (dateText) => dateText ? dateText.replace(/-/g, '/') : '--';
const formatShortDate = (dateText) => {
  if (!dateText) return '--';
  const normalized = String(dateText).replace(/-/g, '/');
  const parts = normalized.split('/');
  return parts.length >= 3 ? `${Number(parts[1])}/${Number(parts[2])}` : normalized;
};

const formatWeekday = (dateText) => {
  if (!dateText) return '--';
  const date = new Date(`${String(dateText).replace(/\//g, '-')}T00:00:00`);
  if (Number.isNaN(date.getTime())) return '--';

  const today = new Date();
  const todayStart = new Date(today.getFullYear(), today.getMonth(), today.getDate()).getTime();
  const dateStart = new Date(date.getFullYear(), date.getMonth(), date.getDate()).getTime();
  const diffDays = Math.round((dateStart - todayStart) / 86400000);
  if (diffDays === -1) return '昨天';
  if (diffDays === 0) return '今天';
  if (diffDays === 1) return '明天';

  return ['周日', '周一', '周二', '周三', '周四', '周五', '周六'][date.getDay()];
};

const getHourFromHistoryTime = (timeText) => {
  if (!timeText) return null;
  const match = String(timeText).match(/(\d{1,2}):\d{2}/);
  if (!match) return null;
  const hour = Number(match[1]);
  return Number.isFinite(hour) ? hour : null;
};

const splitWeatherText = (text) => {
  if (!text) return [];
  return String(text)
    .split(/(?:\s*\/\s*|\s*转\s*|\s*到\s*)/)
    .map(item => item.trim())
    .filter(Boolean);
};

const getRepresentativeWeatherText = (day, targetHour, period) => {
  const hourly = getDayHourly(day).filter(item => item && !item.isSunEvent && item.text);
  if (hourly.length) {
    const withHour = hourly
      .map(item => ({ item, hour: getHourFromHistoryTime(item.time) }))
      .filter(({ hour }) => hour !== null);
    const preferred = withHour.filter(({ hour }) => period === 'day' ? hour >= 6 && hour <= 17 : hour < 6 || hour >= 18);
    const pool = preferred.length ? preferred : withHour;

    if (pool.length) {
      return pool
        .slice()
        .sort((a, b) => Math.abs(a.hour - targetHour) - Math.abs(b.hour - targetHour))[0]
        .item.text;
    }
  }

  const parts = splitWeatherText(getDayText(day));
  return period === 'night' ? (parts[1] || parts[0] || '--') : (parts[0] || '--');
};

const getWeatherIcon = (text) => {
  if (!text) return '04d';
  if (ICON_MAP[text]) return ICON_MAP[text];
  if (text.includes('雷')) return '11d';
  if (text.includes('雨')) return '10d';
  if (text.includes('雪')) return '13d';
  if (text.includes('云')) return '04d';
  if (text.includes('晴')) return '01d';
  if (text.includes('雾') || text.includes('霾')) return '50d';
  return '04d';
};

const checkScrollable = () => {
  if (!citiesScrollRef.value) {
    isScrollable.value = false;
    return;
  }

  const el = citiesScrollRef.value;
  isScrollable.value = el.scrollWidth > el.clientWidth;
  isAtLeft.value = el.scrollLeft <= 0;
  isAtRight.value = Math.ceil(el.scrollLeft + el.clientWidth) >= el.scrollWidth;
};

const scrollCities = (direction) => {
  citiesScrollRef.value?.scrollBy({
    left: direction === 'left' ? -200 : 200,
    behavior: 'smooth'
  });
};

const scrollHourly = (direction) => {
  hourlyScrollRef.value?.scrollBy({ left: direction === 'left' ? -300 : 300, behavior: 'smooth' });
};

const resetHourlyLayoutAfterResize = () => {
  if (resizeFrame) cancelAnimationFrame(resizeFrame);
  resizeFrame = requestAnimationFrame(() => {
    checkScrollable();
    if (hourlyScrollRef.value) {
      hourlyScrollRef.value.scrollLeft = 0;
    }
    hourlyLayoutKey.value += 1;
    resizeFrame = 0;
  });
};

const getResolvedThemeDark = () => {
  const themeMode = localStorage.getItem('weather_theme_mode');
  if (themeMode === 'system') return window.matchMedia?.('(prefers-color-scheme: dark)').matches || false;
  if (themeMode === 'dark') return true;
  if (themeMode === 'light') return false;
  return localStorage.getItem('weather_dark_mode') === 'true';
};

const handleGlobalThemeChange = (event) => {
  if (typeof event?.detail?.dark === 'boolean') {
    isDarkMode.value = event.detail.dark;
    return;
  }
  isDarkMode.value = getResolvedThemeDark();
};

const handleWindowScroll = (event) => {
  let currentScrollTop = window.pageYOffset || document.documentElement.scrollTop || document.body.scrollTop || 0;

  if (event?.target && event.target.scrollTop !== undefined) {
    currentScrollTop = Math.max(currentScrollTop, event.target.scrollTop);
  }

  isScrolled.value = currentScrollTop >= 60;
};

const handleClickOutside = (event) => {
  if (searchWrapperRef.value && !searchWrapperRef.value.contains(event.target)) {
    clearSearch();
  }
};

onMounted(() => {
  const savedUnit = localStorage.getItem('weather_unit_pref');
  if (savedUnit) tempUnit.value = savedUnit;
  const savedWindUnit = localStorage.getItem('weather_wind_unit_pref');
  if (WIND_UNIT_OPTIONS.some(item => item.value === savedWindUnit)) windUnit.value = savedWindUnit;
  isDarkMode.value = getResolvedThemeDark();
  loadFromCache();
  document.addEventListener('click', handleClickOutside);
  window.addEventListener('pointermove', handleGlobalPointerMove, { passive: true });
  window.addEventListener('resize', resetHourlyLayoutAfterResize);
  window.addEventListener('weather-theme-change', handleGlobalThemeChange);
  window.addEventListener('scroll', handleWindowScroll, true);
});

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside);
  window.removeEventListener('pointermove', handleGlobalPointerMove);
  window.removeEventListener('resize', resetHourlyLayoutAfterResize);
  if (resizeFrame) cancelAnimationFrame(resizeFrame);
  window.removeEventListener('weather-theme-change', handleGlobalThemeChange);
  window.removeEventListener('scroll', handleWindowScroll, true);
});
</script>

<style scoped>
.weather-container {
  --text-primary: #1e293b; --text-secondary: #64748b; --text-tertiary: #94a3b8; --text-highlight: #0f172a;
  --glass-bg: rgba(255, 255, 255, 0.6); --glass-border: rgba(255, 255, 255, 0.6); --glass-border-top: rgba(255, 255, 255, 0.9);
  --input-bg: rgba(255, 255, 255, 0.3); --input-border: rgba(255, 255, 255, 0.4); --input-focus-bg: rgba(255, 255, 255, 0.85); --input-text: #1e293b; --input-placeholder: #64748b;
  --btn-bg: rgba(255, 255, 255, 0.4); --btn-border: rgba(255, 255, 255, 0.5); --btn-hover-bg: rgba(255, 255, 255, 0.9);
  --pill-bg: rgba(255, 255, 255, 0.45); --pill-hover-bg: rgba(255, 255, 255, 0.85); --search-dropdown-bg: rgba(255, 255, 255, 0.92); --search-item-hover: rgba(59, 130, 246, 0.08);
  --shadow-color: rgba(51, 65, 85, 0.14); --grid-border: rgba(15, 23, 42, 0.08);
}
.weather-container.dark-mode {
  --text-primary: #f8fafc; --text-secondary: #cbd5e1; --text-tertiary: #94a3b8; --text-highlight: #ffffff;
  --glass-bg: rgba(15, 23, 42, 0.72); --glass-border: rgba(255, 255, 255, 0.1); --glass-border-top: rgba(255, 255, 255, 0.18);
  --input-bg: rgba(15, 23, 42, 0.52); --input-border: rgba(255, 255, 255, 0.12); --input-focus-bg: rgba(30, 41, 59, 0.95); --input-text: #f8fafc; --input-placeholder: #94a3b8;
  --btn-bg: rgba(15, 23, 42, 0.5); --btn-border: rgba(255, 255, 255, 0.12); --btn-hover-bg: rgba(30, 41, 59, 0.95);
  --pill-bg: rgba(15, 23, 42, 0.52); --pill-hover-bg: rgba(30, 41, 59, 0.95); --search-dropdown-bg: rgba(15, 23, 42, 0.95); --search-item-hover: rgba(148, 163, 184, 0.12);
  --shadow-color: rgba(2, 6, 23, 0.36); --grid-border: rgba(255, 255, 255, 0.1);
}

* { box-sizing: border-box; font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
.weather-container { width: 100%; min-height: calc(100dvh - 64px); transition: background 1s ease-in-out; display: flex; flex-direction: column; align-items: center; padding: 0 0 34px; color: var(--text-primary); position: relative; }
.top-bar { user-select: none; -webkit-user-select: none; -moz-user-select: none; -ms-user-select: none; position: sticky; top: 0; z-index: 1000; width: 100%; background-color: transparent; border-bottom: 1px solid transparent; box-shadow: none; backdrop-filter: none; display: flex; justify-content: space-between; align-items: center; padding: 14px 17px; gap: 17px; transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); }
.top-bar.is-scrolled { background-color: var(--glass-bg) !important; backdrop-filter: blur(12px) !important; -webkit-backdrop-filter: blur(12px) !important; border-bottom: 1px solid var(--glass-border) !important; box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05) !important; }
.left-section { display: flex; align-items: center; gap: 14px; flex: 1; max-width: 935px; min-width: 0; }
.right-section { flex-shrink: 0; display: flex; align-items: center; gap: 10px; }
.unit-toggle-btn { background: var(--btn-bg); border: 1px solid var(--btn-border); height: 39px; width: 46px; border-radius: 11px; cursor: pointer; display: flex; align-items: center; justify-content: center; font-size: 15px; font-weight: 600; color: var(--text-primary); transition: all 0.3s ease; box-shadow: 0 3px 5px rgba(0, 0, 0, 0.01); }
.unit-toggle-btn:hover { background: var(--btn-hover-bg); transform: translateY(-2px); box-shadow: 0 7px 13px rgba(0,0,0,0.06); color: var(--text-highlight); border-color: var(--glass-border-top); }
.wind-unit-toggle-btn { width: 62px; font-size: 12px; letter-spacing: -0.01em; }
.search-wrapper { position: relative; width: 255px; flex-shrink: 0; z-index: 101; isolation: isolate; }
.search-box { height: 39px; position: relative; display: flex; align-items: center; background: var(--input-bg); border: 1px solid var(--input-border); border-radius: 11px; box-shadow: 0 3px 5px rgba(0, 0, 0, 0.01); transition: all 0.4s cubic-bezier(0.2, 0.8, 0.2, 1); }
.search-box:focus-within, .search-box.has-shadow { background: var(--input-focus-bg); border-color: var(--glass-border-top); box-shadow: 0 7px 20px rgba(0, 0, 0, 0.08), 0 2px 3px rgba(0,0,0,0.02); }
.search-box input { width: 100%; height: 100%; border: none; outline: none; font-size: 13px; color: var(--input-text); background: transparent; font-weight: 500; padding-left: 14px; padding-right: 73px; }
.search-box input::placeholder { color: var(--input-placeholder); }
.search-actions { position: absolute; right: 10px; top: 0; bottom: 0; display: flex; align-items: center; gap: 5px; }
.clear-btn { background: rgba(0, 0, 0, 0.06); border: none; border-radius: 50%; width: 17px; height: 17px; display: flex; align-items: center; justify-content: center; color: var(--text-secondary); cursor: pointer; transition: all 0.2s; }
.clear-btn:hover { background: rgba(0, 0, 0, 0.15); color: var(--text-highlight); transform: scale(1.1); }
.search-icon { color: var(--text-secondary); display: flex; align-items: center; transition: color 0.3s; padding: 3px; cursor: pointer; }
.search-box:focus-within .search-icon { color: #3b82f6; }
.search-result { position: absolute; top: calc(100% + 8px); left: 0; width: 100%; background: var(--search-dropdown-bg); border: 1px solid var(--glass-border); border-radius: 10px; box-shadow: 0 14px 34px rgba(0, 0, 0, 0.12); overflow: hidden; padding: 7px; }
.status-box { padding: 20px 10px; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 8px; color: var(--text-secondary); font-size: 12px; text-align: center; }
.location-item { padding: 10px; cursor: pointer; border-radius: 7px; transition: all 0.2s ease; display: flex; flex-direction: column; gap: 2px; }
.location-item:hover { background-color: var(--search-item-hover); transform: translateX(3px); }
.item-name { font-size: 13px; font-weight: 600; color: var(--text-primary); }
.item-path { font-size: 10px; color: var(--text-tertiary); }
.loading-spinner { width: 15px; height: 15px; border: 2px solid rgba(59, 130, 246, 0.1); border-left-color: #3b82f6; border-radius: 50%; animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
.quick-cities-wrapper { display: flex; align-items: center; gap: 10px; flex: 1; min-width: 0; position: relative; isolation: isolate; }
.history-title-strip { justify-content: flex-start; }
.history-title-pill { height: 39px; padding: 0 17px; background: var(--pill-bg); border: 1px solid var(--btn-border); border-radius: 11px; display: inline-flex; align-items: center; justify-content: center; gap: 10px; box-shadow: 0 2px 3px rgba(0,0,0,0.03); }
.cities-scroll-view { display: flex; align-items: center; gap: 8px; overflow-x: auto; scroll-behavior: smooth; white-space: nowrap; width: 100%; padding: 8px 20px 8px 3px; margin: -8px 0; scrollbar-width: none; -ms-overflow-style: none; }
.cities-scroll-view::-webkit-scrollbar { display: none; }
.cities-scroll-view.mask-right {
  -webkit-mask-image: linear-gradient(to right, #000 0%, #000 calc(100% - 58px), rgba(0, 0, 0, 0.72) calc(100% - 38px), rgba(0, 0, 0, 0.28) calc(100% - 16px), transparent 100%);
  mask-image: linear-gradient(to right, #000 0%, #000 calc(100% - 58px), rgba(0, 0, 0, 0.72) calc(100% - 38px), rgba(0, 0, 0, 0.28) calc(100% - 16px), transparent 100%);
}
.cities-scroll-view.mask-left {
  -webkit-mask-image: linear-gradient(to right, transparent 0%, rgba(0, 0, 0, 0.28) 16px, rgba(0, 0, 0, 0.72) 38px, #000 58px, #000 100%);
  mask-image: linear-gradient(to right, transparent 0%, rgba(0, 0, 0, 0.28) 16px, rgba(0, 0, 0, 0.72) 38px, #000 58px, #000 100%);
}
.cities-scroll-view.mask-both {
  -webkit-mask-image: linear-gradient(to right, transparent 0%, rgba(0, 0, 0, 0.28) 16px, rgba(0, 0, 0, 0.72) 38px, #000 58px, #000 calc(100% - 58px), rgba(0, 0, 0, 0.72) calc(100% - 38px), rgba(0, 0, 0, 0.28) calc(100% - 16px), transparent 100%);
  mask-image: linear-gradient(to right, transparent 0%, rgba(0, 0, 0, 0.28) 16px, rgba(0, 0, 0, 0.72) 38px, #000 58px, #000 calc(100% - 58px), rgba(0, 0, 0, 0.72) calc(100% - 38px), rgba(0, 0, 0, 0.28) calc(100% - 16px), transparent 100%);
}
.nav-controls { display: flex; align-items: center; gap: 7px; flex-shrink: 0; padding-right: 3px; }
.nav-btn, .nav-arrow-btn { border-radius: 50%; border: 1px solid var(--btn-border); background: var(--btn-bg); backdrop-filter: none; -webkit-backdrop-filter: none; display: flex; align-items: center; justify-content: center; cursor: pointer; color: var(--text-secondary); transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1); box-shadow: 0 2px 7px rgba(0,0,0,0.05); outline: none; transform: translateZ(0); backface-visibility: hidden; will-change: transform; }
.nav-btn { width: 27px; height: 27px; }
.nav-arrow-btn { width: 27px; height: 27px; transition: all 0.2s ease; }
.nav-btn:hover, .nav-arrow-btn:hover { background: var(--btn-hover-bg); color: var(--text-highlight); box-shadow: 0 3px 10px rgba(0,0,0,0.1); transform: scale(1.05) translateZ(0); }
.nav-btn:active, .nav-arrow-btn:active { transform: scale(0.95) translateZ(0); }
.city-pill { flex-shrink: 0; height: 39px; background: transparent; display: inline-flex; align-items: center; justify-content: center; cursor: pointer; transition: z-index 0.2s ease; position: relative; z-index: 1; -webkit-font-smoothing: antialiased; -moz-osx-font-smoothing: grayscale; }
.city-pill.is-hovered { z-index: 10; }
.city-pill:active, .city-pill:focus, .city-pill:focus-visible { outline: none; }
.pill-content { height: 100%; padding: 0 17px; background: var(--pill-bg); backdrop-filter: none; -webkit-backdrop-filter: none; border: 1px solid var(--btn-border); border-radius: 11px; display: flex; align-items: center; justify-content: center; gap: 7px; box-shadow: 0 2px 3px rgba(0,0,0,0.03); transition: background 0.25s ease, border-color 0.25s ease, transform 0.25s ease, box-shadow 0.25s ease; transform: translateZ(0); backface-visibility: hidden; }
.city-pill.is-hovered .pill-content { background: var(--pill-hover-bg); border-color: var(--glass-border-top); transform: translateY(-2px) translateZ(0); }
.pill-icon { width: 19px; height: 19px; object-fit: contain; }
.city-name { font-size: 12px; font-weight: 500; color: var(--text-primary); line-height: 1; }
.city-temp { font-weight: 700; color: var(--text-highlight); font-size: 13px; line-height: 1; }
.delete-btn { flex: 0 0 auto; width: 0; height: 12px; margin-left: 0; display: inline-flex; align-items: center; justify-content: center; color: #b0b0b0; cursor: pointer; transition: width 0.25s ease, margin-left 0.25s ease, opacity 0.2s ease, transform 0.2s ease, color 0.2s ease; overflow: hidden; white-space: nowrap; opacity: 0; transform: scale(0.7); transform-origin: center; pointer-events: none; }
.city-pill.is-hovered .delete-btn { width: 12px; margin-left: 6px; opacity: 1; transform: scale(1); pointer-events: auto; }
.delete-btn svg { width: 12px; height: 12px; stroke-width: 2px; display: block; transform-origin: center center; transform: rotate(-180deg); transition: transform 0.4s cubic-bezier(0.34, 1.56, 0.64, 1); }
.city-pill.is-hovered .delete-btn svg { transform: rotate(0deg); }
.dark-mode .delete-btn { color: #666; }
.city-pill.is-hovered .delete-btn:hover { color: #ff4d4f; }
.content-body { width: 100%; position: relative; display: flex; flex-direction: column; align-items: center; flex: 1; min-height: 340px; z-index: 1; }
.main-content-wrapper { width: 100%; max-width: 1280px; display: grid; grid-template-columns: 230px minmax(0, 765px) 230px; justify-content: center; align-items: start; gap: 22px; padding: 0 24px; }
.left-content { width: 100%; display: flex; flex-direction: column; align-items: center; }
.side-content { width: 100%; min-width: 0; }
.left-side { padding-top: 34px; }
.left-side-stack { position: sticky; top: 102px; display: flex; flex-direction: column; gap: 14px; }
.astro-card { overflow: hidden; min-height: 360px; background: var(--glass-bg); backdrop-filter: blur(12px) saturate(120%); -webkit-backdrop-filter: blur(12px) saturate(120%); border: 1px solid var(--glass-border); border-top: 1px solid var(--glass-border-top); border-radius: 26px; box-shadow: 0 17px 42px -8px var(--shadow-color); padding: 22px 18px; color: var(--text-primary); animation: cardEntrance 0.6s cubic-bezier(0.2, 0.8, 0.2, 1) 0.04s both; transition: background 0.5s ease; }
.air-trend-card { overflow: hidden; background: var(--glass-bg); backdrop-filter: blur(12px) saturate(120%); -webkit-backdrop-filter: blur(12px) saturate(120%); border: 1px solid var(--glass-border); border-top: 1px solid var(--glass-border-top); border-radius: 24px; box-shadow: 0 14px 32px -12px var(--shadow-color); padding: 18px 16px 14px; color: var(--text-primary); animation: cardEntrance 0.6s cubic-bezier(0.2, 0.8, 0.2, 1) 0.08s both; transition: background 0.5s ease; }
.air-card { overflow: hidden; background: var(--glass-bg); backdrop-filter: blur(12px) saturate(120%); -webkit-backdrop-filter: blur(12px) saturate(120%); border: 1px solid var(--glass-border); border-top: 1px solid var(--glass-border-top); border-radius: 24px; box-shadow: 0 14px 32px -12px var(--shadow-color); padding: 18px 16px; color: var(--text-primary); animation: cardEntrance 0.6s cubic-bezier(0.2, 0.8, 0.2, 1) 0.12s both; transition: background 0.5s ease; }
.air-trend-head { display: flex; align-items: flex-end; justify-content: space-between; gap: 10px; margin-top: 4px; }
.air-trend-score { display: flex; flex-direction: column; gap: 3px; min-width: 0; }
.air-trend-score span { color: var(--text-tertiary); font-size: 10px; font-weight: 600; letter-spacing: 0.04em; }
.air-trend-score strong { color: var(--text-highlight); font-size: 24px; font-weight: 680; line-height: 1; letter-spacing: -0.03em; }
.air-trend-summary { display: flex; flex-direction: column; align-items: flex-end; gap: 4px; min-width: 0; }
.air-trend-summary span { color: var(--text-tertiary); font-size: 10px; font-weight: 600; }
.air-trend-summary strong { color: var(--text-secondary); font-size: 12px; font-weight: 620; line-height: 1; }
.air-trend-bars { margin-top: 14px; padding-top: 14px; border-top: 1px solid var(--grid-border); display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 10px 8px; }
.air-trend-day { display: flex; flex-direction: column; align-items: center; gap: 7px; min-width: 0; }
.air-trend-track { position: relative; width: 18px; height: 56px; display: flex; align-items: flex-end; justify-content: center; }
.air-trend-track::before {
  content: "";
  position: absolute;
  inset: 0;
  width: 8px;
  margin: 0 auto;
  border-radius: 999px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.18) 0%, rgba(148, 163, 184, 0.10) 100%);
}
.air-trend-bar {
  position: relative;
  z-index: 1;
  width: 8px;
  border-radius: 999px;
  transition: height 0.3s ease;
  box-shadow: 0 8px 18px -10px rgba(15, 23, 42, 0.28);
}
.air-trend-bar.aqi-level-1 { background: linear-gradient(180deg, #22c55e 0%, #16a34a 100%); }
.air-trend-bar.aqi-level-2 { background: linear-gradient(180deg, #f59e0b 0%, #d97706 100%); }
.air-trend-bar.aqi-level-3 { background: linear-gradient(180deg, #f97316 0%, #ea580c 100%); }
.air-trend-bar.aqi-level-4 { background: linear-gradient(180deg, #ef4444 0%, #dc2626 100%); }
.air-trend-bar.aqi-level-5 { background: linear-gradient(180deg, #a855f7 0%, #9333ea 100%); }
.air-trend-bar.aqi-level-6 { background: linear-gradient(180deg, #be123c 0%, #881337 100%); }
.air-trend-bar.aqi-level-unknown { background: linear-gradient(180deg, #94a3b8 0%, #64748b 100%); }
.air-trend-date { color: var(--text-tertiary); font-size: 9px; font-weight: 650; line-height: 1; font-variant-numeric: tabular-nums; letter-spacing: 0.01em; }
.dark-mode .air-trend-track::before {
  background: linear-gradient(180deg, rgba(148, 163, 184, 0.16) 0%, rgba(71, 85, 105, 0.22) 100%);
}
.dark-mode .air-trend-bar {
  box-shadow: 0 10px 20px -12px rgba(2, 6, 23, 0.32);
}
.dark-mode .air-trend-bar.aqi-level-1 { background: linear-gradient(180deg, #86efac 0%, #22c55e 100%); }
.dark-mode .air-trend-bar.aqi-level-2 { background: linear-gradient(180deg, #fbbf24 0%, #d97706 100%); }
.dark-mode .air-trend-bar.aqi-level-3 { background: linear-gradient(180deg, #fdba74 0%, #ea580c 100%); }
.dark-mode .air-trend-bar.aqi-level-4 { background: linear-gradient(180deg, #fca5a5 0%, #dc2626 100%); }
.dark-mode .air-trend-bar.aqi-level-5 { background: linear-gradient(180deg, #d8b4fe 0%, #9333ea 100%); }
.dark-mode .air-trend-bar.aqi-level-6 { background: linear-gradient(180deg, #fda4af 0%, #881337 100%); }
.dark-mode .air-trend-bar.aqi-level-unknown { background: linear-gradient(180deg, #cbd5e1 0%, #64748b 100%); }
.air-primary-row { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-top: 8px; padding: 10px 0 13px; border-bottom: 1px solid var(--grid-border); }
.air-primary-row span { color: var(--text-secondary); font-size: 12px; font-weight: 560; }
.air-primary-row strong { color: var(--text-highlight); font-size: 14px; font-weight: 620; text-align: right; }
.air-pollutants { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px 14px; padding-top: 12px; }
.air-pollutant { min-width: 0; display: flex; align-items: center; justify-content: space-between; gap: 8px; padding: 8px 0; border-bottom: 1px solid var(--grid-border); }
.air-pollutant:nth-last-child(-n + 2) { border-bottom: none; }
.air-pollutant span { color: var(--text-secondary); font-size: 11px; font-weight: 560; letter-spacing: 0.02em; }
.air-pollutant strong { color: var(--text-highlight); font-size: 12px; font-weight: 620; }
.side-card-kicker { color: var(--text-tertiary); font-size: 11px; font-weight: 700; letter-spacing: 0.08em; margin-bottom: 6px; }
.side-card-title { color: var(--text-highlight); font-size: 18px; font-weight: 650; letter-spacing: -0.01em; }
.moon-phase-display { position: relative; display: flex; align-items: center; gap: 14px; margin: 20px 0 18px; padding: 2px 2px 18px; border-bottom: 1px solid var(--grid-border); }
.moon-simple { position: relative; flex: 0 0 auto; width: 50px; height: 50px; border-radius: 50%; overflow: hidden; background:
  radial-gradient(ellipse 29px 52px at 78% 50%, #f7c24a 0 55%, rgba(247, 194, 74, 0.72) 61%, transparent 68%),
  radial-gradient(circle at 42% 48%, #4a5574 0 68%, #3f4a68 100%);
  box-shadow: 0 10px 22px rgba(15, 23, 42, 0.10);
}
.moon-simple::before { content: ""; position: absolute; inset: 0; border-radius: inherit; background: radial-gradient(circle at 32% 35%, rgba(255, 255, 255, 0.08), transparent 42%); }
.moon-simple::after { display: none; }
.moon-new { background: radial-gradient(circle at 42% 48%, #4a5574 0 68%, #3f4a68 100%); }
.moon-waxing-crescent { background: radial-gradient(ellipse 18px 52px at 90% 50%, #f7c24a 0 52%, rgba(247, 194, 74, 0.72) 60%, transparent 69%), radial-gradient(circle at 42% 48%, #4a5574 0 68%, #3f4a68 100%); }
.moon-first-quarter { background: radial-gradient(ellipse 24px 52px at 78% 50%, #f7c24a 0 62%, rgba(247, 194, 74, 0.82) 68%, transparent 74%), radial-gradient(circle at 42% 48%, #4a5574 0 68%, #3f4a68 100%); }
.moon-waxing-gibbous { background: radial-gradient(ellipse 42px 54px at 70% 50%, #f7c24a 0 70%, rgba(247, 194, 74, 0.84) 76%, transparent 82%), radial-gradient(circle at 42% 48%, #4a5574 0 68%, #3f4a68 100%); }
.moon-full { background: radial-gradient(circle at 42% 38%, #ffd66b 0 42%, #f7c24a 72%, #eda640 100%); }
.moon-waning-gibbous { background: radial-gradient(ellipse 42px 54px at 30% 50%, #f7c24a 0 70%, rgba(247, 194, 74, 0.84) 76%, transparent 82%), radial-gradient(circle at 58% 48%, #4a5574 0 68%, #3f4a68 100%); }
.moon-last-quarter { background: radial-gradient(ellipse 24px 52px at 22% 50%, #f7c24a 0 62%, rgba(247, 194, 74, 0.82) 68%, transparent 74%), radial-gradient(circle at 58% 48%, #4a5574 0 68%, #3f4a68 100%); }
.moon-waning-crescent { background: radial-gradient(ellipse 18px 52px at 10% 50%, #f7c24a 0 52%, rgba(247, 194, 74, 0.72) 60%, transparent 69%), radial-gradient(circle at 58% 48%, #4a5574 0 68%, #3f4a68 100%); }
.moon-phase-copy { display: flex; flex-direction: column; gap: 7px; min-width: 0; }
.moon-phase-copy span { color: var(--text-secondary); font-size: 11px; font-weight: 500; letter-spacing: 0.04em; }
.moon-phase-copy strong { color: var(--text-highlight); font-size: 25px; font-weight: 600; letter-spacing: -0.02em; line-height: 1; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.astro-list { display: flex; flex-direction: column; gap: 10px; }
.astro-item { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 10px 0; border-bottom: 1px solid var(--grid-border); }
.astro-item:last-child { border-bottom: none; }
.astro-item span { color: var(--text-secondary); font-size: 12px; font-weight: 500; }
.astro-item strong { color: var(--text-highlight); font-size: 13px; font-weight: 600; text-align: right; max-width: 120px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.global-loading-mask { position: fixed; inset: 0; background: var(--weather-loading-mask-bg, rgba(255, 255, 255, 0.3)); backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px); z-index: 2605; display: flex; align-items: center; justify-content: center; pointer-events: auto; touch-action: none; }
.loading-content { display: flex; flex-direction: column; align-items: center; gap: 14px; background: var(--weather-loading-content-bg, rgba(255, 255, 255, 0.8)); padding: 25px 42px; border-radius: 20px; box-shadow: var(--weather-loading-shadow, 0 8px 34px rgba(0,0,0,0.1)); }
.loading-spinner-large { width: 34px; height: 34px; border: 3px solid rgba(59, 130, 246, 0.2); border-left-color: #3b82f6; border-radius: 50%; animation: spin 0.8s linear infinite; }
.loading-text { font-size: 13px; color: var(--weather-loading-text-color, var(--text-secondary)); font-weight: 600; }
.weather-card { width: 100%; max-width: 765px; position: relative; overflow: hidden; background: var(--glass-bg); backdrop-filter: blur(12px) saturate(120%); -webkit-backdrop-filter: blur(12px) saturate(120%); border: 1px solid var(--glass-border); border-top: 1px solid var(--glass-border-top); border-radius: 27px; padding: 34px 42px; box-shadow: 0 17px 42px -8px var(--shadow-color), 0 8px 17px -8px var(--shadow-color); animation: cardEntrance 0.6s cubic-bezier(0.2, 0.8, 0.2, 1); margin: 34px auto 0; z-index: 10; isolation: isolate; transition: background 0.5s ease; }
.card-glass-glow { position: absolute; top: -50%; left: -50%; width: 200%; height: 200%; background: radial-gradient(circle at 50% 0%, rgba(255,255,255,0.1) 0%, transparent 60%); pointer-events: none; opacity: 0.8; }
@keyframes cardEntrance { 0% { opacity: 0; transform: translateY(34px); } 100% { opacity: 1; transform: translateY(0); } }
.card-top-row { display: flex; justify-content: flex-start !important; align-items: flex-end; margin-bottom: 17px; position: relative; z-index: 2; }
.card-title h3 { font-size: 17px; font-weight: 700; color: var(--text-primary); margin: 0 10px 3px 0; }
.title-meta-row { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.title-path { font-size: 12px; font-weight: 500; color: rgba(60, 60, 67, 0.6); line-height: 1.2; }
.dark-mode .title-path { color: rgba(235, 235, 245, 0.6); }
.divider { color: rgba(150,150,150,0.3); font-size: 11px; }
.update-time { font-size: 11px; color: var(--text-tertiary); font-weight: 500; }
.main-weather-section { display: flex; align-items: center; margin: 8px 0 34px; gap: 25px; position: relative; z-index: 2; }
.weather-icon-wrapper { width: 85px; height: 85px; display: flex; align-items: center; justify-content: center; filter: drop-shadow(0 8px 17px rgba(0,0,0,0.15)); }
.main-icon { width: 130%; height: 130%; object-fit: contain; }
.degree { font-size: 70px; font-weight: 600; color: var(--text-highlight); line-height: 1; letter-spacing: -2.5px; }
.condition-group { display: flex; flex-direction: column; justify-content: center; gap: 3px; }
.condition-text { font-size: 20px; font-weight: 600; color: var(--text-primary); }
.feels-like { font-size: 13px; color: var(--text-secondary); font-weight: 500; }
.weather-summary { font-size: 14px; color: var(--text-primary); margin-bottom: 38px; line-height: 1.6; font-weight: 400; max-width: 510px; position: relative; z-index: 2; }
.detail-grid { display: grid; grid-template-columns: repeat(6, 1fr); gap: 17px; padding-top: 25px; border-top: 1px solid var(--grid-border); position: relative; z-index: 2; }
.grid-item { display: flex; flex-direction: column; gap: 5px; min-width: 0; }
.grid-label { font-size: 11px; color: var(--text-secondary); font-weight: 500; white-space: nowrap; height: 17px; line-height: 17px; overflow: hidden; text-overflow: ellipsis; }
.grid-value { font-size: 14px; font-weight: 600; color: var(--text-highlight); white-space: nowrap; line-height: 1.4; position: relative; top: -1.5px; }
.color-quality { color: #f59e0b; }
.history-days-card { width: 100%; max-width: 765px; position: relative; overflow: hidden; background: var(--glass-bg); backdrop-filter: blur(12px) saturate(120%); -webkit-backdrop-filter: blur(12px) saturate(120%); border: 1px solid var(--glass-border); border-top: 1px solid var(--glass-border-top); border-radius: 27px; box-shadow: 0 17px 42px -8px var(--shadow-color); padding: 25px 17px; margin: 17px auto 0; z-index: 1; animation: cardEntrance 0.6s cubic-bezier(0.2, 0.8, 0.2, 1) 0.05s both; transition: background 0.5s ease; }
.history-days-grid { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 10px; padding: 0 17px 2px; }
.history-day-item { min-height: 132px; padding: 12px 8px; border: 1px solid var(--btn-border); border-radius: 18px; background: var(--pill-bg); color: var(--text-primary); display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 5px; cursor: pointer; transition: all 0.25s ease; }
.history-day-item:hover, .history-day-item.active { background: var(--pill-hover-bg); border-color: var(--glass-border-top); transform: translateY(-2px); box-shadow: 0 10px 22px rgba(0,0,0,0.08); }
.history-day-item img { width: 36px; height: 36px; object-fit: contain; filter: drop-shadow(0 4px 8px rgba(0,0,0,0.12)); }
.history-day-item strong { font-size: 18px; color: var(--text-highlight); line-height: 1; }
.history-day-item small { max-width: 100%; color: var(--text-secondary); font-size: 10px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.day-meta-row { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); align-items: center; gap: 5px; width: 100%; max-width: 122px; margin-top: 1px; font-size: 10px; white-space: nowrap; }
.day-low-temp, .day-aqi { display: inline-flex; align-items: center; justify-content: center; min-width: 0; width: 100%; padding: 2px 5px; border-radius: 999px; font-weight: 700; line-height: 1.2; }
.day-low-temp { color: #2563eb; background: rgba(59, 130, 246, 0.12); }
.day-aqi { font-size: 9px; letter-spacing: -0.02em; }
.aqi-level-1 { color: #16a34a; background: rgba(34, 197, 94, 0.14); }
.aqi-level-2 { color: #d97706; background: rgba(245, 158, 11, 0.15); }
.aqi-level-3 { color: #ea580c; background: rgba(249, 115, 22, 0.15); }
.aqi-level-4 { color: #dc2626; background: rgba(239, 68, 68, 0.14); }
.aqi-level-5 { color: #9333ea; background: rgba(168, 85, 247, 0.15); }
.aqi-level-6 { color: #881337; background: rgba(190, 18, 60, 0.16); }
.aqi-level-unknown { color: var(--text-secondary); background: rgba(148, 163, 184, 0.14); }
.dark-mode .day-low-temp { color: #93c5fd; background: rgba(59, 130, 246, 0.18); }
.dark-mode .aqi-level-1 { color: #86efac; background: rgba(34, 197, 94, 0.16); }
.dark-mode .aqi-level-2 { color: #fbbf24; background: rgba(245, 158, 11, 0.17); }
.dark-mode .aqi-level-3 { color: #fdba74; background: rgba(249, 115, 22, 0.17); }
.dark-mode .aqi-level-4 { color: #fca5a5; background: rgba(239, 68, 68, 0.16); }
.dark-mode .aqi-level-5 { color: #d8b4fe; background: rgba(168, 85, 247, 0.18); }
.dark-mode .aqi-level-6 { color: #fda4af; background: rgba(190, 18, 60, 0.18); }
.day-date { color: var(--text-tertiary); font-size: 11px; font-weight: 700; }
.temp-compare-card, .hourly-card { width: 100%; max-width: 765px; position: relative; overflow: hidden; background: var(--glass-bg); border: 1px solid var(--glass-border); border-top: 1px solid var(--glass-border-top); border-radius: 27px; box-shadow: 0 17px 42px -8px var(--shadow-color); padding: 25px 17px; margin: 17px auto 0; z-index: 1; animation: cardEntrance 0.6s cubic-bezier(0.2, 0.8, 0.2, 1) 0.1s both; transition: background 0.5s ease; }
.hourly-card { backdrop-filter: blur(12px) saturate(120%); -webkit-backdrop-filter: blur(12px) saturate(120%); }
.temp-compare-card {
  animation-delay: 0.08s;
  isolation: isolate;
  background: transparent;
  padding: 28px 24px 30px;
}
.temp-compare-card::before {
  content: "";
  position: absolute;
  inset: 0;
  z-index: 0;
  border-radius: inherit;
  background:
    radial-gradient(circle at 50% 0%, rgba(255, 255, 255, 0.28), transparent 48%),
    var(--glass-bg);
  pointer-events: none;
}
.dark-mode .temp-compare-card::before {
  background: var(--glass-bg);
}
.temp-compare-card > * {
  position: relative;
  z-index: 1;
}
.hourly-title-row { display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 13px; padding: 0 17px; }
.title-text-group { display: flex; flex-direction: column; gap: 3px; }
.title-text-group span:first-child { font-size: 12px; color: var(--text-secondary); font-weight: 500; }
.hourly-summary { color: var(--text-primary); font-weight: 600; font-size: 13px; }
.temp-compare-card .hourly-title-row { margin-bottom: 6px; align-items: flex-start; padding: 0 6px; }
.temp-compare-card .title-text-group { gap: 5px; }
.temp-compare-card .title-text-group span:first-child { font-size: 12px; color: var(--text-secondary); font-weight: 500; letter-spacing: normal; }
.temp-compare-card .hourly-summary { color: var(--text-primary); font-weight: 600; font-size: 13px; line-height: 1.45; }
.temp-range-board { width: 100%; padding: 9px 0 0; }
.temp-range-days { display: grid; grid-template-columns: repeat(10, minmax(0, 1fr)); gap: 9px; align-items: stretch; }
.temp-range-day {
  min-width: 0;
  height: 274px;
  border: 0;
  outline: none;
  background: transparent;
  color: var(--text-primary);
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 13px 4px 12px;
  border-radius: 22px;
  cursor: default;
  appearance: none;
  box-shadow: none;
}
.temp-range-day:hover,
.temp-range-day:focus,
.temp-range-day:focus-visible,
.temp-range-day:active {
  background: transparent;
  outline: none;
  transform: none;
  box-shadow: none;
}
.dark-mode .temp-range-day {
  background: transparent;
  box-shadow: none;
}
.dark-mode .temp-range-day:hover,
.dark-mode .temp-range-day:focus,
.dark-mode .temp-range-day:focus-visible,
.dark-mode .temp-range-day:active {
  background: transparent;
  box-shadow: none;
}
.temp-range-head { display: flex; flex-direction: column; align-items: center; gap: 5px; min-height: 38px; }
.temp-range-head strong { color: var(--text-highlight); font-size: 15px; font-weight: 700; letter-spacing: 0.005em; line-height: 1; }
.temp-range-head span { color: var(--text-tertiary); font-size: 11px; font-weight: 600; line-height: 1; font-variant-numeric: tabular-nums; }
.temp-range-meter { position: relative; flex: 1 1 auto; width: 100%; min-height: 166px; margin-top: 11px; display: flex; align-items: center; justify-content: center; }
.temp-range-value { position: absolute; left: 50%; color: var(--text-highlight); font-size: 13px; font-weight: 720; line-height: 1; white-space: nowrap; font-variant-numeric: tabular-nums; text-shadow: none; }
.temp-range-high { top: calc(50% - 48px); transform: translate(-34px, -50%); color: #f97316; }
.temp-range-low { top: calc(50% + 48px); transform: translate(14px, -50%); color: #2563eb; }
.dark-mode .temp-range-low { color: #60a5fa; }
.temp-range-rail { position: relative; width: 5px; height: 156px; border-radius: 999px; background: rgba(100, 116, 139, 0.12); overflow: visible; }
.dark-mode .temp-range-rail { background: rgba(148, 163, 184, 0.11); }
.temp-range-fill { position: absolute; left: 0; width: 100%; min-height: 18px; border-radius: 999px; background: linear-gradient(180deg, #fb923c 0%, #facc15 45%, #38bdf8 100%); box-shadow: 0 8px 15px rgba(96, 165, 250, 0.11); }
.temp-range-dot { position: absolute; left: 50%; z-index: 2; display: block; width: 7px; height: 7px; box-sizing: border-box; border-radius: 50%; transform: translate3d(-50%, -50%, 0); background: #fff; box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.82), 0 0 0 2px rgba(15, 23, 42, 0.08), 0 2px 5px rgba(15, 23, 42, 0.12); }
.high-dot { top: 0; }
.low-dot { top: 100%; }
.dark-mode .temp-range-dot { background: #fff; box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.55), 0 0 0 2px rgba(15, 23, 42, 0.28), 0 2px 6px rgba(0, 0, 0, 0.32); }
.temp-range-spread { display: inline-flex; align-items: center; justify-content: center; min-height: 21px; margin-top: 10px; padding: 0 10px; border-radius: 999px; background: rgba(148, 163, 184, 0.11); color: var(--text-secondary); font-size: 10px; font-weight: 650; line-height: 1; letter-spacing: 0.01em; white-space: nowrap; }
.dark-mode .temp-range-spread { background: rgba(148, 163, 184, 0.16); color: rgba(226, 232, 240, 0.78); }
.hourly-nav-group { display: flex; gap: 7px; }
.hourly-wrapper-relative { position: relative; width: 100%; height: 182px; margin: 0; overflow: hidden; }
.hourly-scroll-container { width: 100%; height: 182px; overflow-x: auto; overflow-y: hidden; scrollbar-width: none; -ms-overflow-style: none; scroll-behavior: smooth; padding: 0 17px; mask-image: linear-gradient(to right, transparent 0px, black 17px, black calc(100% - 17px), transparent 100%); -webkit-mask-image: linear-gradient(to right, transparent 0px, black 17px, black calc(100% - 17px), transparent 100%); }
.hourly-scroll-container::-webkit-scrollbar { display: none; }
.hourly-track { position: relative; height: 182px; min-height: 182px; padding: 0; transform: translateZ(0); }
.chart-svg { position: absolute; top: 0; left: 0; z-index: 1; pointer-events: none; overflow: visible; }
.hourly-items-row { display: flex; height: 100%; }
.hourly-item { width: 60px; flex-shrink: 0; display: flex; flex-direction: column; justify-content: flex-start; align-items: center; position: relative; z-index: 2; height: 100%; }
.chart-spacer { height: 68px; width: 100%; flex-shrink: 0; }
.hourly-details { display: flex; flex-direction: column; align-items: center; justify-content: flex-start; padding-top: 8px; gap: 0; width: 100%; }
.hourly-icon { height: 29px; display: flex; align-items: center; justify-content: center; }
.hourly-icon img { width: 27px; height: 27px; object-fit: contain; }
.hourly-weather { display: flex; align-items: center; justify-content: center; height: 18px; max-width: 54px; font-size: 10px; line-height: 18px; color: var(--text-primary); font-weight: 700; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.hourly-wind { display: flex; align-items: center; justify-content: center; gap: 3px; height: 16px; max-width: 58px; font-size: 10px; line-height: 16px; color: var(--text-secondary); white-space: nowrap; transform: scale(0.9); transform-origin: center; overflow: hidden; }
.hourly-wind-dir { color: var(--text-tertiary); max-width: 30px; overflow: hidden; text-overflow: ellipsis; }
.hourly-extra { display: flex; align-items: center; justify-content: center; height: 16px; font-size: 9px; line-height: 16px; color: var(--text-tertiary); white-space: nowrap; transform: scale(0.9); transform-origin: center; }
.hourly-time-container { display: flex; align-items: center; justify-content: center; height: 18px; width: 100%; }
.hourly-time { font-size: 11px; color: var(--text-secondary); font-weight: 500; white-space: nowrap; line-height: 18px; padding-bottom: 0; }
.time-sun-event { font-weight: 600; font-size: 11px; }
.empty-state { margin-top: 85px; text-align: center; color: var(--text-tertiary); width: 100%; animation: fade 1s ease; }
.sun-decoration { width: 51px; height: 51px; background: linear-gradient(135deg, #ffd700, #ff8c00); border-radius: 50%; margin: 0 auto 17px; box-shadow: 0 0 34px rgba(255, 215, 0, 0.6); opacity: 0.8; }
.beian-info { text-align: center; padding: 14px 0; font-size: 11px; color: var(--text-tertiary); margin-top: auto; }
.beian-info a { color: var(--text-tertiary); text-decoration: none; }
.beian-info a:hover { color: var(--text-highlight); text-decoration: underline; }
.fade-enter-active, .fade-leave-active { transition: opacity 0.3s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
.slide-fade-enter-active { transition: all 0.3s ease-out; }
.slide-fade-leave-active { transition: all 0.2s cubic-bezier(1, 0.5, 0.8, 1); }
.slide-fade-enter-from, .slide-fade-leave-to { transform: translateY(-8px); opacity: 0; }
.location-list { max-height: 330px; overflow-y: auto; overflow-x: hidden; }
.location-list::-webkit-scrollbar { width: 6px; }
.location-list::-webkit-scrollbar-track { background: transparent; }
.location-list::-webkit-scrollbar-thumb { background: rgba(150, 150, 150, 0.3); border-radius: 4px; }
.dark-mode .location-list::-webkit-scrollbar-thumb { background: rgba(255, 255, 255, 0.2); }

@media (max-width: 1280px) {
  .main-content-wrapper {
    max-width: 820px;
    grid-template-columns: minmax(0, 1fr);
    justify-items: center;
    gap: 16px;
    padding: 0 16px;
  }

  .left-content {
    order: 1;
    width: 100%;
    max-width: 765px;
  }

  .left-side {
    order: 2;
    padding-top: 0;
  }

  .left-side-stack {
    position: static;
    top: auto;
  }

  .weather-card,
  .history-days-card,
  .temp-compare-card,
  .hourly-card,
  .astro-card,
  .air-trend-card,
  .air-card {
    width: 100%;
    max-width: 765px;
  }

  .astro-card,
  .air-trend-card,
  .air-card {
    position: relative;
    top: auto;
    min-height: auto;
    margin: 0 auto;
    padding: 24px 28px;
  }
  .air-card { margin-top: 12px; }

  .astro-list {
    display: grid;
    grid-template-columns: repeat(5, minmax(0, 1fr));
    gap: 10px 18px;
  }

  .astro-item {
    flex-direction: column;
    align-items: flex-start;
    padding: 9px 0;
  }

  .astro-item strong {
    max-width: 100%;
    text-align: left;
  }
}

@media (max-width: 900px) {
  .top-bar { width: 100%; display: grid; grid-template-columns: minmax(0, 1fr) auto; padding: 12px; gap: 12px; align-items: center; }
  .left-section { display: grid; grid-template-columns: 255px minmax(0, 1fr); align-items: center; gap: 12px; flex: initial; width: 100%; min-width: 0; max-width: none; }
  .search-wrapper { width: 255px; min-width: 255px; max-width: 255px; flex: 0 0 255px; }
  .quick-cities-wrapper { width: auto; flex: 1 1 auto; min-width: 0; }
  .main-content-wrapper { max-width: none; grid-template-columns: 1fr; gap: 12px; padding: 0 12px; }
  .left-content { max-width: 680px; }
  .left-side { padding-top: 12px; }
  .left-side-stack { position: static; top: auto; }
  .astro-card, .air-trend-card, .air-card { position: relative; top: auto; min-height: auto; max-width: 680px; margin-left: auto; margin-right: auto; }
  .air-card { margin-top: 12px; }
  .astro-list { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 8px 12px; }
  .astro-item { flex-direction: column; align-items: flex-start; padding: 8px 0; }
  .astro-item strong { max-width: 100%; text-align: left; }
  .weather-card, .history-days-card, .temp-compare-card, .hourly-card { max-width: 680px; }
  .weather-card { padding: 24px 18px; }
  .temp-compare-card, .hourly-card { padding: 20px 10px; }
  .history-days-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); padding: 0 10px 2px; }
  .hourly-title-row { padding: 0 10px; }
  .hourly-scroll-container { padding: 0 10px; mask-image: none; -webkit-mask-image: none; }
  .wind-unit-toggle-btn { width: 58px; }
}

@media (min-width: 600px) and (max-width: 800px) {
  .top-bar {
    padding: 10px;
    gap: 10px;
  }

  .left-section {
    grid-template-columns: minmax(220px, 255px) minmax(0, 1fr);
    gap: 10px;
  }

  .search-wrapper {
    width: 100%;
    min-width: 220px;
    max-width: 255px;
  }

  .cities-scroll-view {
    padding-right: 12px;
  }

  .pill-content {
    padding: 0 13px;
  }

  .city-name {
    max-width: 150px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .main-content-wrapper {
    width: 100%;
    max-width: 720px;
    padding: 0 10px;
  }

  .left-content {
    max-width: 640px;
  }

  .weather-card,
  .history-days-card,
  .temp-compare-card,
  .hourly-card,
  .astro-card,
  .air-card {
    width: 100%;
    max-width: 640px;
    margin-left: auto;
    margin-right: auto;
  }

  .weather-card {
    padding: 22px 18px;
  }

  .card-top-row {
    margin-bottom: 14px;
  }

  .title-meta-row {
    gap: 6px;
  }

  .main-weather-section {
    gap: 18px;
    margin: 6px 0 26px;
  }

  .weather-icon-wrapper {
    width: 72px;
    height: 72px;
  }

  .degree {
    font-size: 58px;
    letter-spacing: -2px;
  }

  .condition-text {
    font-size: 18px;
  }

  .weather-summary {
    max-width: none;
    margin-bottom: 28px;
  }

  .detail-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 14px 16px;
  }

  .history-days-grid {
    grid-template-columns: repeat(2, minmax(190px, 1fr));
    gap: 10px;
    padding: 0 10px 2px;
  }

  .history-day-item {
    min-height: 122px;
  }

  .hourly-title-row {
    align-items: flex-start;
    gap: 12px;
  }

  .temp-range-days {
    gap: 7px;
  }

  .temp-range-day {
    height: 244px;
    padding: 11px 3px 9px;
    border-radius: 18px;
  }

  .temp-range-meter {
    min-height: 112px;
    column-gap: 3px;
  }

  .temp-range-rail {
    height: 114px;
  }

  .temp-range-head strong {
    font-size: 13px;
  }

  .temp-range-value {
    font-size: 12px;
  }

  .temp-range-spread {
    min-height: 20px;
    padding: 0 8px;
    font-size: 9px;
  }

  .astro-card,
  .air-card {
    padding: 22px 24px;
  }

  .astro-list {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 599px) {
  .weather-container, .content-body, .main-content-wrapper, .left-content, .top-bar { min-width: 600px !important; }
}
</style>
