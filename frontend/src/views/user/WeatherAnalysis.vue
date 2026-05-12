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
                @keyup.esc="searchKey = ''"
                @keydown.enter="handleEnterSearch"
              />
            <div class="search-actions">
              <transition name="fade">
                <button class="clear-btn" @click="searchKey = ''" v-show="searchKey">
                  <svg viewBox="0 0 24 24" width="14" height="14" stroke="currentColor" stroke-width="2.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
                    <line x1="18" y1="6" x2="6" y2="18"></line>
                    <line x1="6" y1="6" x2="18" y2="18"></line>
                  </svg>
                </button>
              </transition>
              
              <i class="search-icon" @click="handleEnterSearch" style="cursor: pointer;">
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
                <svg viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
                <span class="empty-text">城市名称不能以数字或符号开头</span>
              </div>
              
              <div class="location-list" v-else-if="locationList.length > 0">
                <div class="location-item" v-for="(item, index) in locationList.slice(0,10)" :key="index" @click="selectLocation(item)">
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
                <svg viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line><line x1="11" y1="8" x2="11" y2="14"></line><line x1="8" y1="11" x2="14" y2="11"></line></svg>
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
            <div class="city-pill" v-for="city in recentCities" :key="city.id" @click="handleRecentCityClick(city)">
              <div class="pill-content">
                <span class="city-name">{{ city.name }}</span>
                <img :src="`https://openweathermap.org/img/wn/${getWeatherIcon(city.text)}@2x.png`" :alt="city.text" class="pill-icon"/>
                <span class="city-temp">{{ formatTemperature(city.temp, { withUnit: true }) }}</span>
                
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
              <button class="nav-btn prev" @click="scrollCities('left')">
                <svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"></polyline></svg>
              </button>
              <button class="nav-btn next" @click="scrollCities('right')">
                <svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"></polyline></svg>
              </button>
            </div>
          </transition>
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
      <div v-if="!searchKey.trim() && !weatherData" class="empty-state">
        <div class="empty-content">
          <div class="sun-decoration"></div>
          <p>请输入城市名称查看天气</p>
        </div>
      </div>

      <div class="main-content-wrapper" v-if="weatherData">
        <div class="left-content">
          
          <div class="weather-card" :key="'weather-' + animationKey">
            <div class="card-glass-glow"></div>
            
              <div class="card-top-row" style="margin-bottom: 17px;">
              
              <div class="card-title" style="display: flex; align-items: baseline; flex-wrap: wrap;">
                
                <h3 style="margin: 0 10px 0 0; padding: 0; font-size: 17px; font-weight: 700;">
                  {{ currentLocation }}
                </h3>
                
                <div class="title-meta-row" style="display: flex; align-items: center; gap: 0px;">
                  
                  <span class="title-path" v-if="currentLocationDetail" style="font-size: 12px; font-weight: 500; color: var(--text-secondary);">
                    {{ currentLocationDetail.country }} · {{ currentLocationDetail.adm1 }}
                    <span v-if="currentLocationDetail.adm2 && currentLocationDetail.adm2 !== currentLocationDetail.name">
                      · {{ currentLocationDetail.adm2 }}
                    </span>
                  </span>
                  
                  <span class="divider" v-if="currentLocationDetail" style="color: rgba(150,150,150,0.3); font-size: 11px;">|</span>
                  
                  <span class="update-time" style="font-size: 11px; color: var(--text-tertiary); font-weight: 500;">
                    数据更新于 {{ formatUpdateTime(weatherData.updateTime) }}
                  </span>
                  
                </div>

              </div>
            </div>
            <div class="main-weather-section">
              <div class="weather-icon-wrapper">
                <img :src="`https://openweathermap.org/img/wn/${getWeatherIcon(weatherData.now.text)}@4x.png`" :alt="weatherData.now.text" class="main-icon"/>
              </div>
              <div class="temp-display">
                <span class="degree">{{ currentWeatherDisplay.temp }}</span>
              </div>
              <div class="condition-group">
                <span class="condition-text">{{ weatherData.now.text }}</span>
                <span class="feels-like">体感 {{ currentWeatherDisplay.feelsLike }}</span>
              </div>
            </div>

            <div class="weather-summary">
              今天预计天气{{ weatherData.now.text }}。当前气温 {{ currentWeatherDisplay.temp }}，
              风力 {{ currentWindDisplay }}。
            </div>

            <div class="detail-grid">
              <div class="grid-item"><span class="grid-label">云量</span><span class="grid-value color-quality">{{ weatherData.now.cloud }}%</span></div>
              <div class="grid-item"><span class="grid-label">风向/风速</span><span class="grid-value">{{ weatherData.now.windDir }} {{ currentWindDisplay }}</span></div>
              <div class="grid-item"><span class="grid-label">相对湿度</span><span class="grid-value">{{ weatherData.now.humidity }}%</span></div>
              <div class="grid-item"><span class="grid-label">能见度</span><span class="grid-value">{{ formatVisibility(weatherData.now.vis) }} km</span></div>
              <div class="grid-item"><span class="grid-label">气压</span><span class="grid-value">{{ weatherData.now.pressure }} hPa</span></div>
              <div class="grid-item"><span class="grid-label">风向角</span><span class="grid-value">{{ weatherData.now.wind360 }}°</span></div>
            </div>
          </div>

          <div class="hourly-card" :key="'hourly-'+animationKey" style="animation-delay: 0.1s">
            <div class="hourly-forecast">
              <div class="hourly-title-row">
                <div class="title-text-group">
                  <span>24小时预报</span>
                  <span class="hourly-summary">{{ shortTermForecast }}</span>
                </div>
                <div class="hourly-nav-group">
                  <button class="nav-arrow-btn" @click="scrollHourly('left')"><svg viewBox="0 0 24 24" width="18" height="18" stroke="currentColor" stroke-width="2.5" fill="none" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"></polyline></svg></button>
                  <button class="nav-arrow-btn" @click="scrollHourly('right')"><svg viewBox="0 0 24 24" width="18" height="18" stroke="currentColor" stroke-width="2.5" fill="none" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"></polyline></svg></button>
                </div>
              </div>
              <div class="hourly-wrapper-relative">
                <div class="hourly-scroll-container" ref="hourlyScrollRef">
                  <div class="hourly-track" :style="{ width: hourlyTrackWidth + 'px' }">
                    <svg class="chart-svg" :width="hourlyTrackWidth" height="120" style="overflow: visible;">
                      <defs>
                        <linearGradient id="tempStrokeGradient" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#ff9a9e" /><stop offset="40%" stop-color="#fed6e3" /><stop offset="100%" stop-color="#a18cd1" /></linearGradient>
                      </defs>
                      <path :d="chartPath" fill="none" stroke="url(#tempStrokeGradient)" stroke-width="4" stroke-linecap="round" stroke-linejoin="round" style="filter: drop-shadow(0px 4px 3px rgba(0,0,0,0.15));"/>
                      <g v-for="(point, idx) in chartPoints" :key="idx">
                          <line v-if="point.isNow" :x1="point.x" :y1="point.y" :x2="point.x" y2="90" :stroke="isDarkMode ? 'rgba(255,255,255,0.4)' : 'rgba(255,255,255,0.8)'" stroke-width="1.5" stroke-dasharray="4 4" />
                          <circle :cx="point.x" :cy="point.y" :r="point.isNow ? 5 : 4" :fill="point.isNow ? '#fbbf24' : (isDarkMode ? '#334155' : '#fff')" :stroke="point.isNow ? '#fff' : (point.isSunEvent ? (point.sunLabel === '日出' ? '#f59e0b' : '#3b82f6') : (isDarkMode ? 'rgba(255,255,255,0.2)' : 'rgba(0,0,0,0.1)'))" :stroke-width="point.isNow || point.isSunEvent ? 2 : 1"/>
                          <text :x="point.x" :y="point.y - 14" :fill="point.isSunEvent ? (point.sunLabel === '日出' ? '#d97706' : '#2563eb') : chartTextColor" :font-size="point.isSunEvent ? '13' : '14'" :font-weight="point.isSunEvent ? '600' : '700'" text-anchor="middle">{{ point.isSunEvent ? point.sunLabel : point.temp + '°' }}</text>
                      </g>
                    </svg>
                    <div class="hourly-items-row">
                      <div class="hourly-item" v-for="(item, index) in hourlyData" :key="index">
                        <div class="chart-spacer"></div>
                        <div class="hourly-details">
                          <div class="hourly-icon"><img :src="`https://openweathermap.org/img/wn/${getWeatherIcon(item.text)}@2x.png`" :alt="item.text"/></div>
                          <div class="hourly-wind">{{ formatWind(item) }}</div>
                          <div class="hourly-time-container"><span class="hourly-time" :class="{ 'time-now': item.isNow, 'time-sun-event': item.isSunEvent }" :style="item.isSunEvent ? { color: item.sunLabel === '日出' ? '#d97706' : '#2563eb' } : {}">{{ item.time }}</span></div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div class="bottom-cards-row" :key="'bottom-cards-' + animationKey">
            <div v-if="sunData" class="bottom-card-shell" style="animation-delay: 0.18s">
              <SunCard :sun-data="sunData" :timezone-offset="timezoneOffset" :is-dark-mode="isDarkMode" />
            </div>
            <div class="bottom-card-shell" style="animation-delay: 0.26s">
              <AqiCard :aqiData="aqiData" />
            </div>
            <div class="bottom-card-shell" style="animation-delay: 0.34s">
              <HumidityCard :humidity="weatherData.now.humidity" :temperature="weatherData.now.temp" :hourly-data="hourlyData" :dew-point="weatherData.now.dew" :temp-unit="tempUnit" />
            </div>
            <div class="bottom-card-shell" style="animation-delay: 0.42s">
              <PrecipCard :hourly-data="hourlyData" />
            </div>
            <div class="bottom-card-shell" style="animation-delay: 0.5s">
              <TempTrendCard :current-temp="weatherData.now.temp" :hourly-data="hourlyData" :is-dark="isDarkMode" :temp-unit="tempUnit" />
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import HumidityCard from '@/components/weather_now/HumidityCard.vue'; 
import PrecipCard from '@/components/weather_now/PrecipCard.vue';
import SunCard from '@/components/weather_now/SunCard.vue'; 
import AqiCard from '@/components/weather_now/AqiCard.vue'; 
import TempTrendCard from '@/components/weather_now/TempTrendCard.vue'; 
import { ref, onMounted, onUnmounted, computed, watch, nextTick } from 'vue';
import request from '@/utils/requests';
import { ElMessage } from 'element-plus';
import md5 from 'js-md5';
import { canGuestQueryWeather, consumeGuestWeatherQuery } from '@/utils/guestQuota';

const currentLocationDetail = ref(null);
const API_SECRET_KEY = import.meta.env.VITE_API_SIGN_SECRET || "";
const CACHE_KEY = 'recent_weather_cities';
const MAX_CACHE_COUNT = 10; 
const HOURLY_ITEM_WIDTH = 60; 

const ICON_MAP = { 
  '晴': '01d', '少云': '02d', '晴间多云': '02d', '多云': '04d', '阴': '04d', 
  '阵雨': '09d', '强阵雨': '09d', '雷阵雨': '11d', '强雷阵雨': '11d', '雷阵雨伴有冰雹': '11d',
  '小雨': '10d', '中雨': '10d', '大雨': '09d', '暴雨': '09d', '大暴雨': '09d', '特大暴雨': '09d', 
  '冻雨': '13d', '雨': '10d', '小到中雨': '10d', '中到大雨': '09d', '大到暴雨': '09d', '暴雨到大暴雨': '09d',
  '小雪': '13d', '中雪': '13d', '大雪': '13d', '暴雪': '13d', '阵雪': '13d', '雨夹雪': '13d', 
  '雨雪天气': '13d', '阵雨夹雪': '13d', '雪': '13d', '小到中雪': '13d', '中到大雪': '13d', '大到暴雪': '13d',
  '雾': '50d', '薄雾': '50d', '霾': '50d', '扬沙': '50d', '浮尘': '50d', '沙尘暴': '50d', 
  '强沙尘暴': '50d', '热带风暴': '50d', '龙卷风': '50d'
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
const searchKey = ref('');
const locationList = ref([]);
const isSearching = ref(false); 
const isWeatherLoading = ref(false);
const weatherData = ref(null);
const sunData = ref(null); 
const aqiData = ref(null); 
const currentLocation = ref('');
const recentCities = ref([]); 
const hourlyData = ref([]); 
const animationKey = ref(0); 
const isInvalidInput = ref(false);
const citiesScrollRef = ref(null); 
const hourlyScrollRef = ref(null);
const isScrollable = ref(false); 
const isAtLeft = ref(true);  
const isAtRight = ref(false); 
const tempUnit = ref('C');
const WIND_UNIT_OPTIONS = [
  { value: 'beaufort', label: '蒲福' },
  { value: 'kmh', label: 'km/h' },
  { value: 'ms', label: 'm/s' },
  { value: 'mph', label: 'mph' },
  { value: 'kn', label: 'kn' }
];
const windUnit = ref('beaufort');
const isDarkMode = ref(false);
const timezoneOffset = ref(null); 
const currentTime = ref(new Date()); 

// ✨ 监听系统滚动高度，判断是否变成毛玻璃吸顶态
const isScrolled = ref(false); 

let resizeObserver = null; 
let clockTimer = null; 
let searchTimer = null;
let abortController = null;

const handleClickOutside = (event) => {
  if (searchWrapperRef.value && !searchWrapperRef.value.contains(event.target)) {
    searchKey.value = ''; locationList.value = []; isInvalidInput.value = false;
  }
};

const generateSignature = (params) => {
  const timestamp = Date.now().toString();
  const nonce = Math.random().toString(36).substring(2, 15) + Date.now().toString(36);
  const sortedKeys = Object.keys(params).sort();
  const paramStr = sortedKeys.map(key => `${key}=${params[key]}`).join('&');
  const rawStr = `${paramStr}&timestamp=${timestamp}&nonce=${nonce}&secret=${API_SECRET_KEY}`;
  const sign = md5(rawStr).toUpperCase();
  return { headers: { 'X-Sign': sign, 'X-Timestamp': timestamp, 'X-Nonce': nonce } };
};

const parseTimezoneOffset = (offsetStr) => {
  if (!offsetStr) return 0;
  const match = offsetStr.match(/([+-])(\d{1,2}):?(\d{2})?/);
  if (!match) return 0;
  const [_, sign, hours, minutes] = match;
  const totalMinutes = parseInt(hours) * 60 + (parseInt(minutes) || 0);
  return sign === '-' ? -totalMinutes : totalMinutes;
};

const normalizeSearchText = (text) => (text || '').toString().trim().toLowerCase();

const formatApiTime = (isoTime) => {
  if (!isoTime) return '';
  const timeMatch = isoTime.match(/T(\d{2}:\d{2})/);
  const timeStr = timeMatch ? timeMatch[1] : '';
  if (timeStr === '00:00') {
    const dateMatch = isoTime.match(/-(\d{2})-(\d{2})T/);
    if (dateMatch) return `${parseInt(dateMatch[1])}月${parseInt(dateMatch[2])}日`;
  }
  return timeStr;
};

const getWindLevel = (speedStr) => {
  const speed = parseFloat(speedStr);
  if (isNaN(speed)) return '-';
  if (speed < 1) return '0'; if (speed <= 5) return '1'; if (speed <= 11) return '2';
  if (speed <= 19) return '3'; if (speed <= 28) return '4'; if (speed <= 38) return '5';
  if (speed <= 49) return '6'; if (speed <= 61) return '7'; if (speed <= 74) return '8';
  return '>8';
};

const normalizeNumericValue = (value) => {
  if (value === undefined || value === null || value === '') return null;
  const parsed = parseFloat(value);
  return Number.isNaN(parsed) ? null : parsed;
};

const formatWind = (item) => {
  if (!item || item.isSunEvent) return '天文';
  const windScale = item.windScale || item.wind || item.wind_scale;
  if (windUnit.value === 'beaufort') return `${windScale || '--'}级`;

  const kmh = normalizeNumericValue(item.windSpeed);
  if (kmh === null) return '--';

  if (windUnit.value === 'kmh') return `${Math.round(kmh)}km/h`;
  if (windUnit.value === 'ms') return `${(kmh / 3.6).toFixed(1)}m/s`;
  if (windUnit.value === 'mph') return `${(kmh * 0.621371).toFixed(1)}mph`;
  if (windUnit.value === 'kn') return `${(kmh * 0.539957).toFixed(1)}kn`;
  return `${windScale || '--'}级`;
};

const getRawTemperature = (value, fallback = null) => {
  const candidate = value ?? fallback;
  if (candidate == null || candidate === '') return null;
  const parsed = parseFloat(candidate);
  return Number.isNaN(parsed) ? null : parsed;
};

const convertTemperatureValue = (value, unit = tempUnit.value) => {
  const raw = getRawTemperature(value);
  if (raw == null) return null;
  return unit === 'C' ? Math.round(raw) : Math.round((raw * 1.8) + 32);
};

const formatTemperature = (value, options = {}) => {
  const { withUnit = false, fallback = '--' } = options;
  const converted = convertTemperatureValue(value);
  if (converted == null) return withUnit ? `${fallback}°${tempUnit.value}` : fallback;
  return withUnit ? `${converted}°${tempUnit.value}` : `${converted}`;
};

const bgStyle = computed(() => {
  const defaultGradient = isDarkMode.value ? DEFAULT_DARK_BG : DEFAULT_BG;
  if (!weatherData.value?.now) return { background: defaultGradient };
  const text = weatherData.value.now.text;
  const match = BG_CONFIG.find(item => item.keys.some(k => text.includes(k)));
  if (match) return { background: (isDarkMode.value ? match.darkGradient : match.gradient) + ' !important' };
  return { background: defaultGradient + ' !important' };
});
const loadingMaskStyle = computed(() => ({
  '--weather-loading-mask-bg': isDarkMode.value ? 'rgba(2, 6, 23, 0.52)' : 'rgba(255, 255, 255, 0.3)',
  '--weather-loading-content-bg': isDarkMode.value ? 'rgba(15, 23, 42, 0.9)' : 'rgba(255, 255, 255, 0.8)',
  '--weather-loading-text-color': isDarkMode.value ? '#e2e8f0' : '#475569',
  '--weather-loading-shadow': isDarkMode.value ? '0 12px 40px rgba(2, 6, 23, 0.42)' : '0 8px 34px rgba(0,0,0,0.1)'
}));

const currentWeatherDisplay = computed(() => ({
  temp: formatTemperature(weatherData.value?.now?.temp, { withUnit: true }),
  feelsLike: formatTemperature(weatherData.value?.now?.feelsLike, { withUnit: true })
}));
const currentWindUnitLabel = computed(() => WIND_UNIT_OPTIONS.find(item => item.value === windUnit.value)?.label || '蒲福');
const currentWindDisplay = computed(() => formatWind(weatherData.value?.now));

const chartTextColor = computed(() => isDarkMode.value ? '#e2e8f0' : '#475569');

const hourlyTrackWidth = computed(() => (hourlyData.value.length || 0) * HOURLY_ITEM_WIDTH); 

const shortTermForecast = computed(() => {
  if (!hourlyData.value || hourlyData.value.length === 0) return '未来短时内无降水';
  const futurePoints = hourlyData.value.filter(item => !item.isNow && !item.isSunEvent).slice(0, 4);
  const hasRain = futurePoints.some(item => item.text && item.text.includes('雨'));
  const hasSnow = futurePoints.some(item => item.text && item.text.includes('雪'));
  if (hasRain && hasSnow) return '未来几小时预计有雨雪';
  if (hasRain) return '未来几小时预计有降雨';
  if (hasSnow) return '未来几小时预计有降雪';
  const currentText = weatherData.value?.now?.text || '';
  if (currentText.includes('雨') || currentText.includes('雪')) return '降水即将停止';
  return '未来短时内无降水';
});

const chartPoints = computed(() => {
  if (!hourlyData.value.length) return [];
  const temps = hourlyData.value.map(d => {
    const converted = convertTemperatureValue(d.rawTemp);
    return converted == null ? 0 : converted;
  });
  if (temps.length === 0) return [];
  const min = Math.min(...temps); const max = Math.max(...temps); const range = max - min || 1; 
  return temps.map((t, i) => ({
    x: i * HOURLY_ITEM_WIDTH + (HOURLY_ITEM_WIDTH / 2), y: ((1 - (t - min) / range) * 50) + 25, 
    temp: Math.round(t), isNow: hourlyData.value[i].isNow, isSunEvent: hourlyData.value[i].isSunEvent,
    sunTime: hourlyData.value[i].time, sunLabel: hourlyData.value[i].sunLabel
  }));
});

const chartPath = computed(() => {
  const pts = chartPoints.value;
  return pts.length ? `M ${pts[0].x} ${pts[0].y}` + pts.slice(1).map(p => ` L ${p.x} ${p.y}`).join('') : '';
});

const fetchAndSetWeatherData = async (locationItem) => { await fetchFromApi(locationItem); };

const fetchFromApi = async (locationItem) => {
  if (!canGuestQueryWeather()) return;

  isWeatherLoading.value = true;
  try {
    const params = { location: `${locationItem.lat}:${locationItem.lon}` };
    const { headers } = generateSignature(params);
    const res = await request.get('/weather/user/weather/now', { params, headers });
    const data = res.data.data;
    if (data) {
       consumeGuestWeatherQuery();
       const hourlyList = data.hourly?.hourly || (Array.isArray(data.hourly) ? data.hourly : []);
       applyWeatherData(locationItem, data.weather, data.sun, hourlyList, data.air_quality);
    } else { handleFetchError(); }
  } catch (error) {
    handleFetchError();
  } finally { isWeatherLoading.value = false; }
};

const handleFetchError = () => { weatherData.value = null; sunData.value = null; aqiData.value = {}; timezoneOffset.value = null; hourlyData.value = []; };

const generateHourlyForecast = (hourlyRaw, weather, sun, timezoneSuffix) => {
  if (!hourlyRaw || hourlyRaw.length === 0) return [];
  let list = hourlyRaw.map((item) => {
      const tempVal = parseFloat(item.temp !== undefined ? item.temp : item.temperature);
      const timeStr = item.fxTime || item.time;
      return { 
        timeObj: new Date(timeStr), time: formatApiTime(timeStr), rawTemp: isNaN(tempVal) ? 0 : tempVal, 
        text: item.text, precip: item.precip || "0.0", wind: getWindLevel(item.windSpeed),
        windScale: item.windScale || item.wind_scale || getWindLevel(item.windSpeed),
        windSpeed: item.windSpeed,
        windDir: item.windDir,
        humidity: parseInt(item.humidity || 0), isNow: false, isSunEvent: false
      };
  });
  const nowTemp = parseFloat(weather.now.temp !== undefined ? weather.now.temp : weather.now.temperature);
  const nowItem = { 
      timeObj: new Date(), time: '现在', rawTemp: isNaN(nowTemp) ? 0 : nowTemp, 
      text: weather.now.text, precip: weather.now.precip || "0.0", 
      wind: weather.now.windScale || weather.now.wind_scale || getWindLevel(weather.now.windSpeed),
      windScale: weather.now.windScale || weather.now.wind_scale || getWindLevel(weather.now.windSpeed),
      windSpeed: weather.now.windSpeed,
      windDir: weather.now.windDir,
      humidity: parseInt(weather.now.humidity || 0), isNow: true, isSunEvent: false
  };
  list.push(nowItem); list.sort((a, b) => a.timeObj - b.timeObj);
  
  if (sun && sun.sun) {
      const startTime = list[0].timeObj; const endTime = list[list.length - 1].timeObj;
      const sunEvents = [];
      sun.sun.forEach(day => {
        const datePrefix = day.date || day.fxDate; 
        if (day.sunrise && day.sunrise !== '--:--') {
            sunEvents.push({ type: 'sunrise', label: '日出', timeStr: day.sunrise, timeObj: new Date(`${datePrefix}T${day.sunrise}${timezoneSuffix}`) });
        }
        if (day.sunset && day.sunset !== '--:--') {
            sunEvents.push({ type: 'sunset', label: '日落', timeStr: day.sunset, timeObj: new Date(`${datePrefix}T${day.sunset}${timezoneSuffix}`) });
        }
      });
      sunEvents.forEach(event => {
        if (event.timeObj >= startTime && event.timeObj <= endTime) {
          const nextIndex = list.findIndex(item => item.timeObj > event.timeObj);
          let prevItem = list[nextIndex - 1]; let nextItem = list[nextIndex];
          let interpolatedTemp = prevItem ? prevItem.rawTemp : 0;
          list.push({
            timeObj: event.timeObj, time: event.timeStr, rawTemp: interpolatedTemp, text: nextItem?.text || '', precip: "0", 
            wind: nextItem?.wind || '',
            windScale: nextItem?.windScale || nextItem?.wind || '',
            windSpeed: nextItem?.windSpeed || '',
            windDir: nextItem?.windDir || '',
            humidity: 0, isNow: false, isSunEvent: true, sunLabel: event.label
          });
        }
      });
      list.sort((a, b) => a.timeObj - b.timeObj);
  }
  return list;
};

const applyWeatherData = (locationItem, weather, sun, hourlyRaw, airQuality) => {
  if (!weather || !weather.now) return; 
  currentLocation.value = locationItem.name; weatherData.value = weather; sunData.value = sun || null; timezoneOffset.value = sun?.location?.timezone_offset || null;
  if (airQuality) { aqiData.value = { air_quality: airQuality }; } else { aqiData.value = {}; }
  let timezoneSuffix = ''; 
  if (hourlyRaw && hourlyRaw.length > 0 && hourlyRaw[0].fxTime) {
    const timeStr = hourlyRaw[0].fxTime; const match = timeStr.match(/(Z|[+-]\d{2}:?\d{2})$/); if (match) timezoneSuffix = match[1];
  }
  hourlyData.value = generateHourlyForecast(hourlyRaw, weather, sun, timezoneSuffix);
  animationKey.value = Date.now(); upsertCache(locationItem, weather, sun);
};

const getRecentCityHeat = (item) => {
  const recentIndex = recentCities.value.findIndex(city =>
    city.lat === item.lat &&
    city.lon === item.lon
  );
  if (recentIndex === -1) return 0;
  const recentCity = recentCities.value[recentIndex];
  const usageCount = Number(recentCity.usageCount || 0);
  return 260 - (recentIndex * 18) + (usageCount * 35);
};

const scoreSearchResult = (item, keyword) => {
  const query = normalizeSearchText(keyword);
  if (!query) return 0;

  const name = normalizeSearchText(item.name);
  const adm1 = normalizeSearchText(item.adm1);
  const adm2 = normalizeSearchText(item.adm2);
  const country = normalizeSearchText(item.country);
  const fullPath = [name, adm2, adm1, country].filter(Boolean).join(' ');

  let score = getRecentCityHeat(item);

  if (name === query) score += 1200;
  else if (name.startsWith(query)) score += 900;
  else if (name.includes(query)) score += 650;

  if (adm2 === query) score += 520;
  else if (adm2.startsWith(query)) score += 360;
  else if (adm2.includes(query)) score += 220;

  if (adm1 === query) score += 280;
  else if (adm1.startsWith(query)) score += 180;
  else if (adm1.includes(query)) score += 90;

  if (country === query) score += 80;
  if (fullPath.includes(query)) score += 70;

  score -= Math.min(name.length, 20);
  score -= Math.min(fullPath.length, 40) * 0.35;

  return score;
};

const processSearchResults = (results) => {
  if (!results || !Array.isArray(results)) return [];
  const seen = new Set();
  const keyword = searchKey.value;

  return results
    .map((item) => {
      const parts = (item.path || '').split(',').map(p => p.trim()).filter(Boolean);
      parts.reverse();
      const uniqueParts = [...new Set(parts)];
      const newPath = uniqueParts.join(' ');
      return {
        ...item,
        path: newPath,
        _rankScore: scoreSearchResult(item, keyword)
      };
    })
    .sort((a, b) => b._rankScore - a._rankScore)
    .reduce((acc, item) => {
      const uniqueKey = `${item.name}|${item.path}`;
      if (!seen.has(uniqueKey)) {
        seen.add(uniqueKey);
        const { _rankScore, ...cleanItem } = item;
        acc.push(cleanItem);
      }
      return acc;
    }, []);
};

const handleRealTimeSearch = async () => {
  const key = searchKey.value.trim();
  if (!key) { locationList.value = []; isSearching.value = false; isInvalidInput.value = false; return; }
  if (isFirstCharInvalid(key)) { isInvalidInput.value = true; locationList.value = []; return; }
  isInvalidInput.value = false;
  if (abortController) abortController.abort(); abortController = new AbortController();
  isSearching.value = true; clearTimeout(searchTimer);
  searchTimer = setTimeout(async () => {
    try {
      const params = { q: key }; const { headers } = generateSignature(params);
      const res = await request.get('/weather/user/location/search', { params, headers, signal: abortController.signal });
      locationList.value = processSearchResults(res.data.data);
    } catch (error) { if (error.name !== 'CanceledError') { console.error(error); locationList.value = []; } } 
    finally { if (abortController && !abortController.signal.aborted) isSearching.value = false; }
  }, 300);
};

const selectLocation = (item) => {
  if (!item.id) return; searchKey.value = ''; locationList.value = [];
  fetchAndSetWeatherData(item); currentLocationDetail.value = item;
};

const handleRecentCityClick = (city) => { fetchAndSetWeatherData(city); currentLocationDetail.value = city; };

const removeRecentCity = async (cityId) => {
  recentCities.value = recentCities.value.filter(city => city.id !== cityId);
  localStorage.setItem(CACHE_KEY, JSON.stringify(recentCities.value));
  await nextTick(); checkScrollable();
};

const upsertCache = (item, weather, sunDataInfo) => {
  try {
    let cities = [...recentCities.value]; const uniqueKey = `${item.lat}:${item.lon}`; const index = cities.findIndex(c => c.id === uniqueKey);
    const tzOffset = sunDataInfo?.location?.timezone_offset || null;
    const previousUsageCount = index > -1 ? Number(cities[index].usageCount || 0) : 0;
    const newItem = { 
        id: uniqueKey, name: item.name, temp: weather.now.temp !== undefined ? weather.now.temp : weather.now.temperature, 
        text: weather.now.text, timezoneOffset: tzOffset, lat: item.lat, lon: item.lon,
        country: item.country || currentLocationDetail.value?.country, adm1: item.adm1 || currentLocationDetail.value?.adm1, adm2: item.adm2 || currentLocationDetail.value?.adm2,
        usageCount: previousUsageCount + 1,
        lastSelectedAt: Date.now()
    };
    if (index > -1) cities[index] = newItem; else { cities.unshift(newItem); if (cities.length > MAX_CACHE_COUNT) cities.pop(); }
    recentCities.value = cities; localStorage.setItem(CACHE_KEY, JSON.stringify(cities));
  } catch (e) { console.error('Cache Error', e); }
};

const loadFromCache = () => { try { const cached = localStorage.getItem(CACHE_KEY); if (cached) recentCities.value = JSON.parse(cached); } catch (e) {} };
watch(() => recentCities.value.length, () => { nextTick(() => { checkScrollable(); }); }, { immediate: true });
const isFirstCharInvalid = (str) => /^[0-9!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?~`·！@#￥%……&*（）——+=-【】{}；：”“’。，、？～·`]/.test(str.trim()[0]);
const toggleUnit = () => { tempUnit.value = tempUnit.value === 'C' ? 'F' : 'C'; localStorage.setItem('weather_unit_pref', tempUnit.value); };
const toggleWindUnit = () => {
  const currentIndex = WIND_UNIT_OPTIONS.findIndex(item => item.value === windUnit.value);
  const nextIndex = currentIndex >= 0 ? (currentIndex + 1) % WIND_UNIT_OPTIONS.length : 0;
  windUnit.value = WIND_UNIT_OPTIONS[nextIndex].value;
  localStorage.setItem('weather_wind_unit_pref', windUnit.value);
};
const getResolvedThemeDark = () => {
  const themeMode = localStorage.getItem('weather_theme_mode');
  if (themeMode === 'system') {
    return typeof window !== 'undefined' && typeof window.matchMedia === 'function'
      ? window.matchMedia('(prefers-color-scheme: dark)').matches
      : false;
  }
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
const getWeatherIcon = (text) => {
  if (!text) return '04d'; if (ICON_MAP[text]) return ICON_MAP[text]; if (text.includes('雷')) return '11d'; 
  if (text.includes('雪') && text.includes('雨')) return '13d'; if (text.includes('雪')) return '13d';
  if (text.includes('雨')) { if (text.includes('大') || text.includes('暴')) return '09d'; return '10d'; }
  if (text.includes('云') || text.includes('阴')) return '04d'; if (text.includes('晴')) return '01d';
  if (text.includes('雾') || text.includes('霾') || text.includes('沙') || text.includes('尘')) return '50d';
  return '04d'; 
};
const formatPath = (path) => path;
const formatUpdateTime = (timeStr) => { if (!timeStr) return ''; const d = new Date(timeStr); return `${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}`; };
const formatVisibility = (val) => { const num = parseFloat(val); return (!isNaN(num) && num > 60) ? (num / 1000).toFixed(1) : (val || '--'); };
const checkScrollable = () => {
  if (citiesScrollRef.value) {
    const el = citiesScrollRef.value; isScrollable.value = el.scrollWidth > el.clientWidth; isAtLeft.value = el.scrollLeft <= 0; isAtRight.value = Math.ceil(el.scrollLeft + el.clientWidth) >= el.scrollWidth;
  } else { isScrollable.value = false; }
};
const scrollCities = (direction) => { if (!citiesScrollRef.value) return; const scrollAmount = 200; citiesScrollRef.value.scrollBy({ left: direction === 'left' ? -scrollAmount : scrollAmount, behavior: 'smooth' }); };
const scrollHourly = (direction) => { if (!hourlyScrollRef.value) return; const scrollAmount = 300; hourlyScrollRef.value.scrollBy({ left: direction === 'left' ? -scrollAmount : scrollAmount, behavior: 'smooth' }); };
const startClock = () => { if (clockTimer) return; currentTime.value = new Date(); clockTimer = setInterval(() => { currentTime.value = new Date(); }, 30000); };
const stopClock = () => { if (clockTimer) { clearInterval(clockTimer); clockTimer = null; } };
const setWeatherLoadingScrollLock = (locked) => {
  const docEl = document.documentElement;
  const body = document.body;
  if (locked) {
    const scrollbarWidth = Math.max(0, window.innerWidth - docEl.clientWidth);
    body.dataset.weatherLoadingPrevOverflow = body.style.overflow;
    body.dataset.weatherLoadingPrevPaddingRight = body.style.paddingRight;
    docEl.dataset.weatherLoadingPrevOverflow = docEl.style.overflow;

    body.style.overflow = 'hidden';
    docEl.style.overflow = 'hidden';

    if (scrollbarWidth > 0) {
      body.style.paddingRight = `${scrollbarWidth}px`;
    }
  } else {
    body.style.overflow = body.dataset.weatherLoadingPrevOverflow || '';
    body.style.paddingRight = body.dataset.weatherLoadingPrevPaddingRight || '';
    docEl.style.overflow = docEl.dataset.weatherLoadingPrevOverflow || '';

    delete body.dataset.weatherLoadingPrevOverflow;
    delete body.dataset.weatherLoadingPrevPaddingRight;
    delete docEl.dataset.weatherLoadingPrevOverflow;
  }
};

// ✨ 核心修复：捕获所有可能容器的滚动事件（彻底解决 Vue 中 #app 滚动不冒泡的大坑）
const handleWindowScroll = (e) => {
  let currentScrollTop = 0;
  
  // 1. 先尝试获取 window 级别的滚动
  currentScrollTop = window.pageYOffset || document.documentElement.scrollTop || document.body.scrollTop || 0;
  
  // 2. 如果是某个具体的局部容器（比如你的 #app）在滚动，拦截它的 scrollTop
  if (e && e.target && e.target.scrollTop !== undefined) {
    currentScrollTop = Math.max(currentScrollTop, e.target.scrollTop);
  }
  
  // NavMenu 是 64px 高度，所以往下滚超过 60px 时，搜索栏正好顶到最上面
  // 此时激活毛玻璃效果
  isScrolled.value = currentScrollTop >= 60;
};

watch(() => sunData.value, (val) => { if (val) startClock(); else stopClock(); });
watch(() => isWeatherLoading.value, (locked) => { setWeatherLoadingScrollLock(locked); });

onMounted(() => {
  loadFromCache();
  document.addEventListener('click', handleClickOutside);
  window.addEventListener('resize', checkScrollable);
  window.addEventListener('weather-theme-change', handleGlobalThemeChange);
  
  // ✨ 核心修复：挂载时开启带 capture: true 的全局滚动监听
  window.addEventListener('scroll', handleWindowScroll, true);

  const savedUnit = localStorage.getItem('weather_unit_pref'); if (savedUnit) tempUnit.value = savedUnit;
  const savedWindUnit = localStorage.getItem('weather_wind_unit_pref');
  if (WIND_UNIT_OPTIONS.some(item => item.value === savedWindUnit)) windUnit.value = savedWindUnit;
  isDarkMode.value = getResolvedThemeDark();

  resizeObserver = new ResizeObserver(() => { checkScrollable(); });
  if (citiesScrollRef.value) resizeObserver.observe(citiesScrollRef.value);
  if (sunData.value) startClock();
});

onUnmounted(() => {
  if (resizeObserver) resizeObserver.disconnect();
  stopClock(); if (searchTimer) clearTimeout(searchTimer); if (abortController) abortController.abort();
  setWeatherLoadingScrollLock(false);
  document.removeEventListener('click', handleClickOutside);
  window.removeEventListener('resize', checkScrollable);
  window.removeEventListener('weather-theme-change', handleGlobalThemeChange);
  
  // ✨ 核心修复：卸载全局滚动监听
  window.removeEventListener('scroll', handleWindowScroll, true);
});
</script>

<style scoped>
/* ✨ 重新加回你最熟悉的 @import */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

:root { --ease-spring: cubic-bezier(0.34, 1.56, 0.64, 1); --ease-smooth: cubic-bezier(0.4, 0, 0.2, 1); }

.weather-container {
  --text-primary: #1e293b; --text-secondary: #64748b; --text-tertiary: #94a3b8; --text-highlight: #0f172a;
  --glass-bg: rgba(255, 255, 255, 0.6); --glass-border: rgba(255, 255, 255, 0.6); --glass-border-top: rgba(255, 255, 255, 0.9);
  --input-bg: rgba(255, 255, 255, 0.3); --input-border: rgba(255, 255, 255, 0.4); --input-focus-bg: rgba(255, 255, 255, 0.85); --input-text: #1e293b; --input-placeholder: #64748b;
  --btn-bg: rgba(255, 255, 255, 0.4); --btn-border: rgba(255, 255, 255, 0.5); --btn-hover-bg: rgba(255, 255, 255, 0.9);
  --search-dropdown-bg: rgba(255, 255, 255, 0.95); --search-item-hover: #f1f5f9;
  --loading-mask-bg: rgba(255, 255, 255, 0.3); --loading-content-bg: rgba(255, 255, 255, 0.8);
  --pill-bg: rgba(255, 255, 255, 0.45); --pill-hover-bg: rgba(255, 255, 255, 0.9);
  --shadow-color: rgba(0,0,0,0.1); --grid-border: rgba(0, 0, 0, 0.06); --sun-track: #e2e8f0; --sun-horizon: #cbd5e1;
}

.weather-container.dark-mode {
  --text-primary: #f8fafc; --text-secondary: #cbd5e1; --text-tertiary: #94a3b8; --text-highlight: #ffffff;
  --glass-bg: rgba(15, 23, 42, 0.72); --glass-border: rgba(255, 255, 255, 0.1); --glass-border-top: rgba(255, 255, 255, 0.18);
  --input-bg: rgba(15, 23, 42, 0.52); --input-border: rgba(255, 255, 255, 0.12); --input-focus-bg: rgba(30, 41, 59, 0.95); --input-text: #f8fafc; --input-placeholder: #94a3b8;
  --btn-bg: rgba(15, 23, 42, 0.5); --btn-border: rgba(255, 255, 255, 0.12); --btn-hover-bg: rgba(30, 41, 59, 0.95);
  --search-dropdown-bg: rgba(15, 23, 42, 0.96); --search-item-hover: rgba(51, 65, 85, 0.62);
  --loading-mask-bg: rgba(2, 6, 23, 0.52); --loading-content-bg: rgba(15, 23, 42, 0.9);
  --pill-bg: rgba(15, 23, 42, 0.52); --pill-hover-bg: rgba(30, 41, 59, 0.95);
  --shadow-color: rgba(2, 6, 23, 0.34); --grid-border: rgba(255, 255, 255, 0.12); --sun-track: #334155; --sun-horizon: #475569;
}

/* ✨ 恢复到最原始的字体代码配置 */
* { 
  margin: 0; 
  padding: 0; 
  box-sizing: border-box; 
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; 
}

.weather-container { 
  width: 100%; max-width: 100%; min-width: 0; min-height: calc(100dvh - 64px); 
  transition: background 1s ease-in-out; display: flex; flex-direction: column; align-items: center; 
  padding: 0; padding-bottom: 34px; color: var(--text-primary); position: relative; 
}

/* ---------------- ✨ Top Bar 核心修改 ✨ ---------------- */
.top-bar { 
  user-select: none; -webkit-user-select: none; -moz-user-select: none; -ms-user-select: none;     
  /* 自然存在于文档流中，滚动时被吸附在页面最顶端 */
  position: sticky; 
  top: 0; 
  z-index: 1000; 
  width: 100%;
  
  /* 初始态：完全透明，和天气渐变背景融为一体 */
  background-color: transparent; 
  border-bottom: 1px solid transparent; 
  box-shadow: none; 
  backdrop-filter: none;
  -webkit-backdrop-filter: none;
  
  display: flex; justify-content: space-between; align-items: center; 
  padding: 14px 17px; gap: 17px; 
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); 
}

/* ✨ 滚动态：由于加上了 !important，无论如何都会强制生效图二的毛玻璃效果 */
.top-bar.is-scrolled {
  background-color: var(--glass-bg) !important; 
  backdrop-filter: blur(12px) !important; 
  -webkit-backdrop-filter: blur(12px) !important;
  border-bottom: 1px solid var(--glass-border) !important; 
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05) !important; 
}

.left-section { display: flex; align-items: center; gap: 14px; flex: 1; max-width: 935px; min-width: 0; }
.right-section { flex-shrink: 0; display: flex; align-items: center; gap: 10px; }

.unit-toggle-btn { background: var(--btn-bg); backdrop-filter: blur(8px); -webkit-backdrop-filter: blur(8px); border: 1px solid var(--btn-border); height: 39px; width: 46px; border-radius: 11px; cursor: pointer; display: flex; align-items: center; justify-content: center; font-size: 15px; font-weight: 600; color: var(--text-primary); transition: all 0.3s ease; box-shadow: 0 3px 5px rgba(0, 0, 0, 0.01); line-height: 1; transform: translateZ(0); backface-visibility: hidden; will-change: transform; }
.unit-toggle-btn:hover { background: var(--btn-hover-bg); transform: translateY(-2px) translateZ(0); box-shadow: 0 7px 13px rgba(0,0,0,0.06); color: var(--text-highlight); border-color: var(--glass-border-top); }
.wind-unit-toggle-btn { width: 62px; font-size: 12px; letter-spacing: -0.01em; }
.search-wrapper { position: relative; width: 255px; flex-shrink: 0; z-index: 101; isolation: isolate; } 
.search-box { height: 39px; position: relative; display: flex; align-items: center; background: var(--input-bg); backdrop-filter: none; -webkit-backdrop-filter: none; border: 1px solid var(--input-border); border-radius: 11px; box-shadow: 0 3px 5px rgba(0, 0, 0, 0.01); transition: all 0.4s cubic-bezier(0.2, 0.8, 0.2, 1); }
.search-box:focus-within, .search-box.has-shadow { background: var(--input-focus-bg); border-color: var(--glass-border-top); box-shadow: 0 7px 20px rgba(0, 0, 0, 0.08), 0 2px 3px rgba(0,0,0,0.02); }
.search-box input { width: 100%; height: 100%; border: none; outline: none; font-size: 13px; color: var(--input-text); background: transparent; font-weight: 500; padding-left: 14px; padding-right: 73px; transition: padding-right 0.3s ease; }
.search-box input::placeholder { color: var(--input-placeholder); }

.search-actions { position: absolute; right: 10px; top: 0; bottom: 0; display: flex; align-items: center; gap: 5px; }
.action-btn { background: transparent; border: none; width: 22px; height: 22px; display: flex; align-items: center; justify-content: center; color: var(--text-secondary); cursor: pointer; border-radius: 3px; transition: all 0.2s; }
.action-btn:hover { background: rgba(0,0,0,0.06); color: var(--text-highlight); }
.clear-btn { background: rgba(0, 0, 0, 0.06); border: none; border-radius: 50%; width: 17px; height: 17px; display: flex; align-items: center; justify-content: center; color: var(--text-secondary); cursor: pointer; transition: all 0.2s; }
.clear-btn:hover { background: rgba(0, 0, 0, 0.15); color: var(--text-highlight); transform: scale(1.1); }
.search-icon { color: var(--text-secondary); display: flex; align-items: center; transition: color 0.3s; padding: 3px; }
.search-box:focus-within .search-icon { color: #3b82f6; }

.search-result { position: absolute; top: calc(100% + 8px); left: 0; width: 100%; background: var(--search-dropdown-bg); backdrop-filter: none; -webkit-backdrop-filter: none; border: 1px solid var(--glass-border); border-radius: 10px; box-shadow: 0 14px 34px rgba(0, 0, 0, 0.12); overflow: hidden; padding: 7px; }
.status-box { padding: 20px 10px; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 8px; color: var(--text-secondary); font-size: 12px; text-align: center; }
.location-item { padding: 10px; cursor: pointer; border-radius: 7px; transition: all 0.2s ease; display: flex; flex-direction: column; gap: 2px; }
.location-item:hover { background-color: var(--search-item-hover); transform: translateX(3px); }
.item-name { font-size: 13px; font-weight: 600; color: var(--text-primary); }
.item-path { font-size: 10px; color: var(--text-tertiary); }
.loading-spinner { width: 15px; height: 15px; border: 2px solid rgba(59, 130, 246, 0.1); border-left-color: #3b82f6; border-radius: 50%; animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

.quick-cities-wrapper { display: flex; align-items: center; gap: 10px; flex: 1; min-width: 0; position: relative; isolation: isolate; }
.cities-scroll-view { display: flex; align-items: center; gap: 8px; overflow-x: auto; scroll-behavior: smooth; white-space: nowrap; width: 100%; padding: 8px 20px 8px 3px; margin: -8px 0; scrollbar-width: none; -ms-overflow-style: none; }
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
.cities-scroll-view::-webkit-scrollbar { display: none; }

.nav-controls { display: flex; align-items: center; gap: 7px; flex-shrink: 0; padding-right: 3px; }
.nav-btn, .nav-arrow-btn { border-radius: 50%; border: 1px solid var(--btn-border); background: var(--btn-bg); backdrop-filter: none; -webkit-backdrop-filter: none; display: flex; align-items: center; justify-content: center; cursor: pointer; color: var(--text-secondary); transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1); box-shadow: 0 2px 7px rgba(0,0,0,0.05); outline: none; transform: translateZ(0); backface-visibility: hidden; will-change: transform; }
.nav-btn { width: 27px; height: 27px; }
.nav-arrow-btn { width: 27px; height: 27px; transition: all 0.2s ease; }
.nav-btn:hover, .nav-arrow-btn:hover { background: var(--btn-hover-bg); color: var(--text-highlight); box-shadow: 0 3px 10px rgba(0,0,0,0.1); transform: scale(1.05) translateZ(0); }
.nav-btn:active, .nav-arrow-btn:active { transform: scale(0.95) translateZ(0); }

.city-pill { flex-shrink: 0; height: 39px; background: transparent; display: inline-flex; align-items: center; justify-content: center; cursor: pointer; transition: all 0.4s; position: relative; z-index: 1; -webkit-font-smoothing: antialiased; -moz-osx-font-smoothing: grayscale; }
.city-pill:hover { z-index: 10; }
.pill-content { height: 100%; padding: 0 17px; background: var(--pill-bg); backdrop-filter: none; -webkit-backdrop-filter: none; border: 1px solid var(--btn-border); border-radius: 11px; display: flex; align-items: center; justify-content: center; gap: 7px; box-shadow: 0 2px 3px rgba(0,0,0,0.03); transition: inherit; transform: translateZ(0); backface-visibility: hidden; }
.city-pill:hover .pill-content { background: var(--pill-hover-bg); border-color: var(--glass-border-top); transform: translateY(-2px) translateZ(0); }
.city-name { font-size: 12px; font-weight: 500; color: var(--text-primary); line-height: 1; }
.city-temp { font-weight: 700; color: var(--text-highlight); font-size: 13px; line-height: 1; }
.pill-icon { width: 19px; height: 19px; object-fit: contain; }

.content-body { width: 100%; position: relative; display: flex; flex-direction: column; align-items: center; flex: 1; min-height: 340px; z-index: 1; }
.main-content-wrapper { width: 100%; display: flex; justify-content: center; }
.left-content { width: 100%; display: flex; flex-direction: column; align-items: center; }

.global-loading-mask {
  position: fixed;
  inset: 0;
  background: var(--weather-loading-mask-bg, rgba(255, 255, 255, 0.3));
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  z-index: 2605;
  display: flex;
  align-items: center;
  justify-content: center;
  pointer-events: auto;
  touch-action: none;
}
.loading-content { display: flex; flex-direction: column; align-items: center; gap: 14px; background: var(--weather-loading-content-bg, rgba(255, 255, 255, 0.8)); padding: 25px 42px; border-radius: 20px; box-shadow: var(--weather-loading-shadow, 0 8px 34px rgba(0,0,0,0.1)); }
.loading-spinner-large { width: 34px; height: 34px; border: 3px solid rgba(59, 130, 246, 0.2); border-left-color: #3b82f6; border-radius: 50%; animation: spin 0.8s linear infinite; }
.loading-text { font-size: 13px; color: var(--weather-loading-text-color, var(--text-secondary)); font-weight: 600; }

.weather-card { width: 100%; max-width: 765px; position: relative; overflow: hidden; background: var(--glass-bg); backdrop-filter: blur(12px) saturate(120%); -webkit-backdrop-filter: blur(12px) saturate(120%); border: 1px solid var(--glass-border); border-top: 1px solid var(--glass-border-top); border-radius: 27px; padding: 34px 42px; box-shadow: 0 17px 42px -8px var(--shadow-color), 0 8px 17px -8px var(--shadow-color); animation: cardEntrance 0.6s cubic-bezier(0.2, 0.8, 0.2, 1); margin: 34px auto 0 auto; z-index: 10; isolation: isolate; transition: background 0.5s ease; will-change: transform, opacity; }
.card-glass-glow { position: absolute; top: -50%; left: -50%; width: 200%; height: 200%; background: radial-gradient(circle at 50% 0%, rgba(255,255,255,0.1) 0%, transparent 60%); pointer-events: none; opacity: 0.8; }
@keyframes cardEntrance { 0% { opacity: 0; transform: translateY(34px)  } 100% { opacity: 1; transform: translateY(0) scale(1); } }
.card-top-row { display: flex; justify-content: flex-start !important; align-items: flex-end; margin-bottom: 17px; position: relative; z-index: 2; }
.card-title { flex: 0 0 auto !important; }
.card-title h3 { font-size: 17px; font-weight: 700; color: var(--text-primary); margin-bottom: 3px; }
.update-time { font-size: 11px; color: var(--text-secondary); font-weight: 500; }
.main-weather-section { display: flex; align-items: center; margin: 8px 0 34px 0; gap: 25px; position: relative; z-index: 2; }
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

.hourly-card { width: 100%; max-width: 765px; position: relative; overflow: hidden; background: var(--glass-bg); backdrop-filter: blur(12px) saturate(120%); -webkit-backdrop-filter: blur(12px) saturate(120%); border: 1px solid var(--glass-border); border-top: 1px solid var(--glass-border-top); border-radius: 27px; box-shadow: 0 17px 42px -8px var(--shadow-color); padding: 25px 17px; margin: 17px auto 0 auto; z-index: 1; animation: cardEntrance 0.6s cubic-bezier(0.2, 0.8, 0.2, 1) 0.1s both; transform-origin: center top; transition: background 0.5s ease; will-change: transform, opacity; }
.hourly-title-row { display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 13px; padding: 0 17px; }
.title-text-group { display: flex; flex-direction: column; gap: 3px; }
.title-text-group span:first-child { font-size: 12px; color: var(--text-secondary); font-weight: 500; }
.hourly-summary { color: var(--text-primary); font-weight: 600; font-size: 13px; }
.hourly-nav-group { display: flex; gap: 7px; }
.hourly-wrapper-relative { position: relative; width: 100%; margin: 0; }
.hourly-scroll-container { width: 100%; overflow-x: auto; scrollbar-width: none; -ms-overflow-style: none; scroll-behavior: smooth; padding: 0 17px; mask-image: linear-gradient(to right, transparent 0px, black 17px, black calc(100% - 17px), transparent 100%); -webkit-mask-image: linear-gradient(to right, transparent 0px, black 17px, black calc(100% - 17px), transparent 100%); }
.hourly-track { position: relative; height: 153px; padding: 0; } 
.chart-svg { position: absolute; top: 0; left: 0; z-index: 1; pointer-events: none; }
.hourly-items-row { display: flex; height: 100%; }
.hourly-item { width: 60px; flex-shrink: 0; display: flex; flex-direction: column; justify-content: flex-start; align-items: center; position: relative; z-index: 2; height: 100%; }
.chart-spacer { height: 68px; width: 100%; flex-shrink: 0; }
.hourly-details { display: flex; flex-direction: column; align-items: center; justify-content: flex-start; padding-top: 8px; gap: 5px; width: 100%; }
.hourly-icon img { width: 27px; height: 27px; object-fit: contain; }
.hourly-wind { font-size: 10px; color: var(--text-secondary); white-space: nowrap; transform: scale(0.9); }
.hourly-time-container { display: flex; align-items: center; justify-content: center; height: 17px; width: 100%; }
.hourly-time { font-size: 11px; color: var(--text-secondary); font-weight: 500; white-space: nowrap; line-height: 1; padding-bottom: 2px; }
.time-sun-event { color: #f59e0b; font-weight: 600; font-size: 11px; }
.sun-event-time { font-size: 10px; color: var(--text-tertiary); margin-top: -2px; }
.time-now { color: #3b82f6; font-weight: 600; }

.bottom-cards-row { display: grid; grid-template-columns: repeat(4, minmax(0, 272px)); justify-content: center; align-items: start; gap: 17px; width: 100%; max-width: 1190px; margin-top: 17px; margin-bottom: 34px; padding: 0 17px; }
.bottom-cards-row > * { width: 272px; }
.bottom-card-shell {
  width: 272px;
  opacity: 0;
  transform: translateY(18px) scale(0.985);
  animation: bottomCardEntrance 0.58s cubic-bezier(0.2, 0.8, 0.2, 1) both;
  will-change: transform, opacity;
}
.bottom-card-shell > * {
  width: 100%;
}
@keyframes bottomCardEntrance {
  0% {
    opacity: 0;
    transform: translateY(18px) scale(0.985);
    filter: blur(4px);
  }
  60% {
    opacity: 1;
    filter: blur(0);
  }
  100% {
    opacity: 1;
    transform: translateY(0) scale(1);
    filter: blur(0);
  }
}
@media (max-width: 1172px) { .bottom-cards-row { grid-template-columns: repeat(2, minmax(0, 272px)); max-width: 595px; } }
@media (max-width: 620px) { .bottom-cards-row { grid-template-columns: minmax(0, 272px); max-width: 306px; } }
@media (max-width: 900px) {
  .top-bar {
    width: 100%;
    display: grid;
    grid-template-columns: minmax(0, 1fr) auto;
    padding: 12px;
    gap: 12px;
    align-items: center;
  }

  .left-section {
    display: grid;
    grid-template-columns: 255px minmax(0, 1fr);
    align-items: center;
    gap: 12px;
    flex: initial;
    width: 100%;
    min-width: 0;
    max-width: none;
  }

  .right-section {
    align-self: auto;
    flex-shrink: 0;
  }

  .search-wrapper {
    width: 255px;
    min-width: 255px;
    max-width: 255px;
    flex: 0 0 255px;
  }

  .quick-cities-wrapper {
    width: auto;
    flex: 1 1 auto;
    min-width: 0;
  }

  .weather-card,
  .hourly-card {
    max-width: calc(100% - 24px);
  }

  .weather-card {
    padding: 24px 18px;
  }

  .hourly-card {
    padding: 20px 10px;
  }

  .hourly-title-row {
    padding: 0 10px;
  }

  .hourly-scroll-container {
    padding: 0 10px;
    mask-image: none;
    -webkit-mask-image: none;
  }

  .bottom-cards-row {
    grid-template-columns: repeat(2, minmax(0, 272px));
    max-width: 595px;
    padding: 0 12px;
  }

  .bottom-cards-row > * {
    width: 272px;
  }
}

@media (max-width: 599px) {
  .weather-container,
  .content-body,
  .main-content-wrapper,
  .left-content,
  .top-bar {
    min-width: 600px !important;
  }
}

.empty-state { margin-top: 85px; text-align: center; color: var(--text-tertiary); width: 100%; animation: fade 1s ease; }
.sun-decoration { width: 51px; height: 51px; background: linear-gradient(135deg, #ffd700, #ff8c00); border-radius: 50%; margin: 0 auto 17px; box-shadow: 0 0 34px rgba(255, 215, 0, 0.6); opacity: 0.8; }
.fade-enter-active, .fade-leave-active { transition: opacity 0.3s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
.slide-fade-enter-active { transition: all 0.3s ease-out; }
.slide-fade-leave-active { transition: all 0.2s cubic-bezier(1, 0.5, 0.8, 1); }
.slide-fade-enter-from, .slide-fade-leave-to { transform: translateY(-8px); opacity: 0; }

.title-main { display: flex; flex-direction: column; gap: 2px; }
.title-path { font-size: 12px; font-weight: 500; color: rgba(60, 60, 67, 0.6); line-height: 1.2; }
.dark-mode .title-path { color: rgba(235, 235, 245, 0.6); }

.location-list { max-height: 330px; overflow-y: auto; overflow-x: hidden; }
.location-list::-webkit-scrollbar { width: 6px; }
.location-list::-webkit-scrollbar-track { background: transparent; }
.location-list::-webkit-scrollbar-thumb { background: rgba(150, 150, 150, 0.3); border-radius: 4px; }
.location-list::-webkit-scrollbar-thumb:hover { background: rgba(150, 150, 150, 0.5); }
.dark-mode .location-list::-webkit-scrollbar-thumb { background: rgba(255, 255, 255, 0.2); }
.dark-mode .location-list::-webkit-scrollbar-thumb:hover { background: rgba(255, 255, 255, 0.3); }

.delete-btn { display: inline-flex; align-items: center; justify-content: center; color: #b0b0b0; cursor: pointer; transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1), margin-left 0.3s cubic-bezier(0.4, 0, 0.2, 1), opacity 0.3s cubic-bezier(0.4, 0, 0.2, 1), transform 0.3s cubic-bezier(0.4, 0, 0.2, 1), color 0.2s ease; overflow: hidden; white-space: nowrap; opacity: 0; width: 0; margin-left: 0; transform: scale(0.5) translateX(-4px); transform-origin: center right; pointer-events: none; }
.city-pill:hover .delete-btn { opacity: 1; width: 12px; margin-left: 6px; transform: scale(1) translateX(0); pointer-events: auto; }
.delete-btn svg { width: 12px; height: 12px; stroke-width: 2px; display: block; transform-origin: center center; transform: rotate(-180deg); transition: transform 0.4s cubic-bezier(0.34, 1.56, 0.64, 1); }
.city-pill:hover .delete-btn svg { transform: rotate(0deg); }
.delete-btn:hover { color: #ff4d4f; }
.dark-mode .delete-btn { color: #666; }
.dark-mode .delete-btn:hover { color: #ff4d4f; }
</style>

