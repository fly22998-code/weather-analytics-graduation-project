<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue';
import { ElMessage } from 'element-plus';
import request from '@/utils/requests';
import { generateSignedHeaders } from '@/utils/signature';

type LocationItem = {
  id: string;
  name: string;
  country?: string;
  adm1?: string;
  adm2?: string;
  lat?: string;
  lon?: string;
  temp?: string | number;
  text?: string;
  usageCount?: number;
};

type HistoryDay = {
  date: string;
  weatherDaily?: Record<string, any>;
  weatherHourly?: Record<string, any>[];
  airSummary?: Record<string, any>;
};

const CACHE_KEY = 'weather_prediction_recent_cities_v1';
const MAX_CACHE_COUNT = 8;

const searchKey = ref('');
const locationList = ref<LocationItem[]>([]);
const recentCities = ref<LocationItem[]>([]);
const currentLocationDetail = ref<LocationItem | null>(null);
const currentLocation = ref('');
const historyDays = ref<HistoryDay[]>([]);
const nowWeather = ref<Record<string, any> | null>(null);
const serverPrediction = ref<Record<string, any> | null>(null);
const isSearching = ref(false);
const isWeatherLoading = ref(false);
const isInvalidInput = ref(false);
const isDarkMode = ref(false);
const tempUnit = ref<'C' | 'F'>((localStorage.getItem('weather_unit_pref') as 'C' | 'F') || 'C');
const scrollContainer = ref<HTMLElement | null>(null);
const canScrollLeft = ref(false);
const canScrollRight = ref(false);
const isScrolled = ref(false);
const hoveredRecentCityId = ref<string | null>(null);
const predictionAnimationKey = ref(0);

let searchTimer: ReturnType<typeof setTimeout> | null = null;
let abortController: AbortController | null = null;
let darkModeObserver: MutationObserver | null = null;

const isFirstCharInvalid = (str: string) => /^[0-9!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?~`·！@#￥%……&*（）——+=-【】{}；：”“’。，、？～·`]/.test(str.trim()[0]);

const normalizeNumericValue = (value: unknown) => {
  const num = Number(value);
  return Number.isFinite(num) ? num : null;
};

const getDaily = (day?: HistoryDay | null) => day?.weatherDaily || (day as any)?.weather_daily || {};
const getHourly = (day?: HistoryDay | null) => day?.weatherHourly || (day as any)?.weather_hourly || [];

const convertTemperatureValue = (value: unknown) => {
  const num = normalizeNumericValue(value);
  if (num === null) return null;
  return tempUnit.value === 'F' ? Math.round((num * 9) / 5 + 32) : Math.round(num);
};

const formatTemperature = (value: unknown, fallback = '--') => {
  const converted = convertTemperatureValue(value);
  return converted === null ? fallback : `${converted}°${tempUnit.value}`;
};

const formatDate = (date: string) => {
  if (!date) return '--';
  if (/^\d{8}$/.test(date)) return `${date.slice(0, 4)}/${date.slice(4, 6)}/${date.slice(6, 8)}`;
  return date.replaceAll('-', '/');
};

const displayLocationPath = computed(() => {
  const item = currentLocationDetail.value;
  if (!item) return '';
  return [item.country, item.adm1, item.adm2].filter(Boolean).join(' · ');
});

const getDayText = (day?: HistoryDay | null) => {
  const texts = getHourly(day).map(item => item.text).filter(Boolean);
  return Array.from(new Set(texts)).slice(0, 2).join(' / ') || getDaily(day)?.text || '--';
};

const getIconCode = (text = '') => {
  if (text.includes('雷')) return '11d';
  if (text.includes('雪')) return '13d';
  if (text.includes('雨')) return '10d';
  if (text.includes('阴')) return '04d';
  if (text.includes('云')) return '02d';
  if (text.includes('晴')) return '01d';
  if (text.includes('雾') || text.includes('霾') || text.includes('沙')) return '50d';
  return '04d';
};

const getWeatherIcon = (text = '') => `https://openweathermap.org/img/wn/${getIconCode(text)}@4x.png`;
const getMiniWeatherIcon = (text = '') => `https://openweathermap.org/img/wn/${getIconCode(text)}@2x.png`;

const average = (values: number[]) => {
  const valid = values.filter(Number.isFinite);
  return valid.length ? valid.reduce((sum, item) => sum + item, 0) / valid.length : null;
};

const clamp = (value: number, min: number, max: number) => Math.max(min, Math.min(max, value));

const median = (values: number[]) => {
  const valid = values.filter(Number.isFinite).sort((a, b) => a - b);
  if (!valid.length) return null;
  const middle = Math.floor(valid.length / 2);
  return valid.length % 2 ? valid[middle] : (valid[middle - 1] + valid[middle]) / 2;
};

const weightedAverage = (values: number[]) => {
  const valid = values.filter(Number.isFinite);
  if (!valid.length) return null;
  const weights = valid.map((_, index) => Math.max(1, valid.length - index));
  const weightSum = weights.reduce((sum, item) => sum + item, 0);
  return valid.reduce((sum, item, index) => sum + item * weights[index], 0) / weightSum;
};

const getNumericSeries = (days: HistoryDay[], key: string) => (
  days.map(day => Number(getDaily(day)[key])).filter(Number.isFinite)
);

const buildTempEstimate = (values: number[]) => {
  const valid = values.filter(Number.isFinite);
  if (!valid.length) return null;

  const recentWeighted = weightedAverage(valid.slice(0, 5)) ?? weightedAverage(valid);
  const stableMedian = median(valid);
  const recent3 = average(valid.slice(0, 3));
  const older3 = average(valid.slice(3, 6));
  const trend = recent3 !== null && older3 !== null ? clamp(recent3 - older3, -3, 3) : 0;

  if (recentWeighted === null || stableMedian === null) return null;
  // 近期数据决定方向，中位数抑制异常日，趋势项只做轻微修正。
  return recentWeighted * 0.62 + stableMedian * 0.28 + trend * 0.1;
};

const makePredictionFromDays = (days: HistoryDay[]) => {
  const maxTemps = getNumericSeries(days, 'tempMax');
  const minTemps = getNumericSeries(days, 'tempMin');
  const tempMax = buildTempEstimate(maxTemps);
  const tempMin = buildTempEstimate(minTemps);

  return {
    tempMax,
    tempMin,
    tempAvg: tempMax === null || tempMin === null ? null : (tempMax + tempMin) / 2
  };
};

const calculateBacktestConfidence = (days: HistoryDay[]) => {
  if (days.length < 5) return 72;

  const errors: number[] = [];
  const weatherMatches: number[] = [];
  const testCount = Math.min(5, days.length - 3);

  for (let index = 0; index < testCount; index += 1) {
    const actualDaily = getDaily(days[index]);
    const trainDays = days.slice(index + 1);
    const estimate = makePredictionFromDays(trainDays);
    const actualMax = Number(actualDaily.tempMax);
    const actualMin = Number(actualDaily.tempMin);

    if (estimate.tempMax !== null && Number.isFinite(actualMax)) {
      errors.push(Math.abs(actualMax - estimate.tempMax));
    }
    if (estimate.tempMin !== null && Number.isFinite(actualMin)) {
      errors.push(Math.abs(actualMin - estimate.tempMin));
    }

    const predictedText = voteWeatherText(trainDays.slice(0, 3));
    const actualText = getDayText(days[index]);
    if (predictedText !== '--' && actualText !== '--') {
      weatherMatches.push(actualText.includes(predictedText) || predictedText.includes(actualText) ? 1 : 0);
    }
  }

  const mae = average(errors) ?? 4;
  const weatherMatchRate = average(weatherMatches) ?? 0.55;
  const temperatureScore = clamp(100 - mae * 7.5, 50, 96);
  const weatherScore = 62 + weatherMatchRate * 30;

  return Math.round(clamp(temperatureScore * 0.72 + weatherScore * 0.28, 55, 95));
};

const voteWeatherText = (days: HistoryDay[]) => {
  const scores = new Map<string, number>();
  days.forEach((day, index) => {
    const text = getDayText(day);
    if (!text || text === '--') return;
    text.split('/').map(item => item.trim()).filter(Boolean).forEach((item) => {
      scores.set(item, (scores.get(item) || 0) + Math.max(1, days.length - index));
    });
  });
  return Array.from(scores.entries()).sort((a, b) => b[1] - a[1])[0]?.[0] || '--';
};

const prediction = computed(() => {
  const days = historyDays.value;
  const modelPrediction = serverPrediction.value;
  if (!days.length && !modelPrediction) return null;

  const maxTemps = getNumericSeries(days, 'tempMax');
  const minTemps = getNumericSeries(days, 'tempMin');
  const humidity = days.map(day => Number(getDaily(day).humidity)).filter(Number.isFinite);
  const pressure = days.map(day => Number(getDaily(day).pressure)).filter(Number.isFinite);
  const precip = days.map(day => Number(getDaily(day).precip)).filter(Number.isFinite);
  const recent3 = days.slice(0, 3);

  if (modelPrediction) {
    const tempMax = normalizeNumericValue(modelPrediction.tempMax);
    const tempMin = normalizeNumericValue(modelPrediction.tempMin);
    const tempAvg = normalizeNumericValue(modelPrediction.tempAvg);

    return {
      tempMax,
      tempMin,
      tempAvg,
      humidity: normalizeNumericValue(modelPrediction.humidity),
      pressure: normalizeNumericValue(modelPrediction.pressure),
      precip: normalizeNumericValue(modelPrediction.precip),
      weatherText: String(modelPrediction.weatherText || '--'),
      confidence: Math.round(normalizeNumericValue(modelPrediction.confidence) || 0),
      temperatureConfidence: Math.round(
        normalizeNumericValue(modelPrediction.temperatureConfidence)
        ?? normalizeNumericValue(modelPrediction.confidence)
        ?? 0
      ),
      recentMaxAvg: average(maxTemps.slice(0, 3)),
      recentMinAvg: average(minTemps.slice(0, 3)),
      tenDayMaxAvg: average(maxTemps),
      tenDayMinAvg: average(minTemps),
      trend: normalizeNumericValue(modelPrediction.trend) || 0,
      model: modelPrediction.model || null
    };
  }

  const estimate = makePredictionFromDays(days);
  const tempMax = estimate.tempMax;
  const tempMin = estimate.tempMin;
  const weatherText = voteWeatherText(recent3.length ? recent3 : days);
  const confidence = calculateBacktestConfidence(days);

  return {
    tempMax: tempMax === null ? null : Math.round(tempMax),
    tempMin: tempMin === null ? null : Math.round(tempMin),
    tempAvg: tempMax === null || tempMin === null ? null : Math.round((tempMax + tempMin) / 2),
    humidity: average(humidity),
    pressure: average(pressure),
    precip: average(precip),
    weatherText,
    confidence,
    temperatureConfidence: confidence,
    recentMaxAvg: average(maxTemps.slice(0, 3)),
    recentMinAvg: average(minTemps.slice(0, 3)),
    tenDayMaxAvg: average(maxTemps),
    tenDayMinAvg: average(minTemps),
    trend: maxTemps.length >= 2 ? maxTemps[0] - maxTemps[Math.min(2, maxTemps.length - 1)] : 0
  };
});

const currentComparison = computed(() => {
  const now = nowWeather.value;
  if (!now || !prediction.value) return null;
  const nowTemp = Number(now.temp);
  const predictedCurrent = normalizeNumericValue((serverPrediction.value || {}).currentHourTemp ?? prediction.value.tempAvg);
  const diff = Number.isFinite(nowTemp) && predictedCurrent !== null ? Math.round(nowTemp - predictedCurrent) : null;
  return {
    temp: now.temp,
    text: now.text || '--',
    humidity: now.humidity || '--',
    pressure: now.pressure || '--',
    diff,
    predictedCurrent,
    currentHour: normalizeNumericValue((serverPrediction.value || {}).currentHour ?? null)
  };
});

const sortedRecentCities = computed(() => [...recentCities.value].sort((a, b) => Number(b.usageCount || 0) - Number(a.usageCount || 0)));

const loadingMaskStyle = computed(() => ({
  '--weather-loading-mask-bg': isDarkMode.value ? 'rgba(2, 6, 23, 0.52)' : 'rgba(255, 255, 255, 0.3)',
  '--weather-loading-content-bg': isDarkMode.value ? 'rgba(15, 23, 42, 0.9)' : 'rgba(255, 255, 255, 0.8)',
  '--weather-loading-text-color': isDarkMode.value ? '#e2e8f0' : '#475569',
  '--weather-loading-shadow': isDarkMode.value ? '0 12px 40px rgba(2, 6, 23, 0.42)' : '0 8px 34px rgba(0,0,0,0.1)'
}));

const checkScrollable = () => {
  const el = scrollContainer.value;
  if (!el) return;
  canScrollLeft.value = el.scrollLeft > 0;
  canScrollRight.value = el.scrollLeft + el.clientWidth < el.scrollWidth - 2;
};

const scrollCities = (direction: 'left' | 'right') => {
  scrollContainer.value?.scrollBy({ left: direction === 'left' ? -260 : 260, behavior: 'smooth' });
  setTimeout(checkScrollable, 260);
};

const loadRecentCities = () => {
  try {
    const cached = localStorage.getItem(CACHE_KEY);
    recentCities.value = cached ? JSON.parse(cached) : [];
  } catch {
    recentCities.value = [];
  }
};

const upsertCache = async (item: LocationItem, day?: HistoryDay) => {
  const id = item.id || `${item.lat}:${item.lon}`;
  if (!id || !item.name) return;
  const daily = getDaily(day);
  const previous = recentCities.value.find(city => city.id === id);
  const newItem = {
    ...item,
    id,
    temp: daily.tempMax,
    text: getDayText(day),
    usageCount: Number(previous?.usageCount || 0) + 1
  };
  recentCities.value = [newItem, ...recentCities.value.filter(city => city.id !== id)].slice(0, MAX_CACHE_COUNT);
  localStorage.setItem(CACHE_KEY, JSON.stringify(recentCities.value));
  await nextTick();
  checkScrollable();
};

const searchLocations = async (keyword: string) => {
  isSearching.value = true;
  if (abortController) abortController.abort();
  abortController = new AbortController();
  try {
    const params = { q: keyword };
    const response = await request.get('/weather/user/location/search', {
      params,
      headers: generateSignedHeaders(params),
      signal: abortController.signal,
      timeout: 8000
    });
    locationList.value = Array.isArray(response.data?.data) ? response.data.data : [];
  } catch (error: any) {
    if (error?.name !== 'CanceledError') locationList.value = [];
  } finally {
    isSearching.value = false;
  }
};

const handleSearchInput = () => {
  if (searchTimer) clearTimeout(searchTimer);
  const keyword = searchKey.value.trim();
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
  searchTimer = setTimeout(() => searchLocations(keyword), 260);
};

const fetchPredictionData = async () => {
  if (!currentLocationDetail.value) return;
  isWeatherLoading.value = true;
  try {
    const location = currentLocationDetail.value;
    const nowLocation = location.lat && location.lon ? `${location.lat}:${location.lon}` : location.id;
    const params = { location: location.id, now_location: nowLocation, lang: 'zh', unit: 'm' };
    const response = await request.get('/weather/user/weather/predict', {
      params,
      headers: generateSignedHeaders(params),
      timeout: 26000
    });

    if (response.data?.code !== 200) {
      ElMessage.warning(response.data?.message || '暂无可用于预测的历史天气数据');
      historyDays.value = [];
      nowWeather.value = null;
      serverPrediction.value = null;
      return;
    }

    const data = response.data?.data || {};
    historyDays.value = data.history || data.history_days || [];
    serverPrediction.value = data.prediction || null;
    if (!historyDays.value.length) {
      ElMessage.warning('近10天历史天气暂无可展示数据');
      serverPrediction.value = null;
      return;
    }

    nowWeather.value = data.now || null;
    await upsertCache(location, historyDays.value[0]);
    predictionAnimationKey.value += 1;
  } catch (error: any) {
    historyDays.value = [];
    nowWeather.value = null;
    serverPrediction.value = null;
    ElMessage.warning(error?.response?.data?.message || '天气预测生成失败，请稍后再试');
  } finally {
    isWeatherLoading.value = false;
  }
};

const selectLocation = (item: LocationItem) => {
  currentLocationDetail.value = item;
  currentLocation.value = item.name;
  searchKey.value = '';
  locationList.value = [];
  fetchPredictionData();
};

const handleEnterSearch = () => {
  if (locationList.value.length) selectLocation(locationList.value[0]);
};

const removeRecentCity = async (cityId: string, event: MouseEvent) => {
  event.stopPropagation();
  recentCities.value = recentCities.value.filter(city => city.id !== cityId);
  localStorage.setItem(CACHE_KEY, JSON.stringify(recentCities.value));
  await nextTick();
  checkScrollable();
};

const handleWindowScroll = (event?: Event) => {
  let currentScrollTop = window.pageYOffset || document.documentElement.scrollTop || document.body.scrollTop || 0;
  const target = event?.target as HTMLElement | null;
  if (target && typeof target.scrollTop === 'number') {
    currentScrollTop = Math.max(currentScrollTop, target.scrollTop);
  }
  isScrolled.value = currentScrollTop >= 60;
};

const toggleUnit = () => {
  tempUnit.value = tempUnit.value === 'C' ? 'F' : 'C';
  localStorage.setItem('weather_unit_pref', tempUnit.value);
};

const updateDarkMode = () => {
  isDarkMode.value = document.body.classList.contains('site-dark-mode') || localStorage.getItem('weather_theme') === 'dark';
};

onMounted(() => {
  loadRecentCities();
  updateDarkMode();
  nextTick(checkScrollable);
  window.addEventListener('resize', checkScrollable);
  window.addEventListener('storage', updateDarkMode);
  window.addEventListener('scroll', handleWindowScroll, true);
  darkModeObserver = new MutationObserver(updateDarkMode);
  darkModeObserver.observe(document.body, { attributes: true, attributeFilter: ['class'] });
});

onUnmounted(() => {
  if (searchTimer) clearTimeout(searchTimer);
  if (abortController) abortController.abort();
  if (darkModeObserver) darkModeObserver.disconnect();
  window.removeEventListener('resize', checkScrollable);
  window.removeEventListener('storage', updateDarkMode);
  window.removeEventListener('scroll', handleWindowScroll, true);
});

watch(() => recentCities.value.length, () => nextTick(checkScrollable));
</script>

<template>
  <div class="weather-container forecast-page" :class="{ 'dark-mode': isDarkMode }">
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

    <div class="top-bar" :class="{ 'is-scrolled': isScrolled }">
      <div class="left-section">
        <div class="search-wrapper" ref="searchWrapperRef">
          <div class="search-box" :class="{ 'has-shadow': searchKey, invalid: isInvalidInput }">
            <input
              v-model="searchKey"
              type="text"
              placeholder="搜索城市..."
              @input="handleSearchInput"
              @keydown.enter="handleEnterSearch"
              @keyup.esc="searchKey = ''; locationList = []"
            />
            <div class="search-actions">
              <transition name="fade">
                <button class="clear-btn" v-show="searchKey" @click="searchKey = ''; locationList = []">
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
                <div
                  v-for="item in locationList.slice(0, 10)"
                  :key="`${item.id}-${item.name}`"
                  class="location-item"
                  @click="selectLocation(item)"
                >
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

        <div class="quick-cities-wrapper history-title-strip prediction-strip">
          <div class="history-title-pill prediction-title-pill">
            <span class="city-name">天气预测</span>
            <span class="city-temp">模型分析</span>
          </div>
          <template v-if="recentCities.length > 0">
            <div
              ref="scrollContainer"
              class="cities-scroll-view"
              @scroll="checkScrollable"
              :class="{
                'mask-right': !canScrollLeft && canScrollRight,
                'mask-left': canScrollLeft && !canScrollRight,
                'mask-both': canScrollLeft && canScrollRight
              }"
            >
              <div
                v-for="city in sortedRecentCities"
                :key="city.id"
                class="city-pill"
                :class="{ 'is-hovered': hoveredRecentCityId === city.id }"
                @mouseenter="hoveredRecentCityId = city.id"
                @mouseleave="hoveredRecentCityId = null"
                @mousedown.prevent
                @click="selectLocation(city)"
              >
                <div class="pill-content">
                  <span class="city-name">{{ city.name }}</span>
                  <img v-if="city.text" :src="getMiniWeatherIcon(city.text)" alt="" class="pill-icon" />
                  <span class="city-temp">{{ city.temp !== undefined && city.temp !== null ? formatTemperature(city.temp) : '--' }}</span>
                  <span class="delete-btn" @click.stop="removeRecentCity(city.id, $event)" title="删除该记录">
                    <svg viewBox="0 0 24 24" stroke="currentColor" fill="none" stroke-linecap="round" stroke-linejoin="round">
                      <line x1="18" y1="6" x2="6" y2="18"></line>
                      <line x1="6" y1="6" x2="18" y2="18"></line>
                    </svg>
                  </span>
                </div>
              </div>
            </div>
            <transition name="fade">
              <div class="nav-controls" v-show="canScrollLeft || canScrollRight">
                <button class="nav-btn prev" @click="scrollCities('left')" title="向左滚动">
                  <svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"></polyline></svg>
                </button>
                <button class="nav-btn next" @click="scrollCities('right')" title="向右滚动">
                  <svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"></polyline></svg>
                </button>
              </div>
            </transition>
          </template>
        </div>
      </div>

      <div class="right-section">
        <button class="unit-toggle-btn" @click="toggleUnit" title="切换温度单位">
          {{ tempUnit === 'C' ? '°C' : '°F' }}
        </button>
      </div>
    </div>

    <div class="content-body">
      <div v-if="!searchKey.trim() && !prediction" class="empty-state">
        <div class="empty-content">
          <div class="sun-decoration"></div>
          <p>请输入城市名称生成天气预测</p>
        </div>
      </div>

      <template v-else>
        <section class="main-content-wrapper prediction-layout">
          <aside class="side-content prediction-side">
            <div class="prediction-side-stack">
              <article class="compare-card" :key="`compare-${predictionAnimationKey}`">
                <div class="side-card-kicker">当前时段对比</div>
                <div v-if="currentComparison" class="compare-main">
                  <strong>{{ formatTemperature(currentComparison.temp) }}</strong>
                  <p>{{ currentComparison.text }}</p>
                </div>
                <div class="compare-subline" v-if="currentComparison?.predictedCurrent !== null">
                  <span>参考时段</span>
                  <strong>
                    {{ currentComparison.currentHour === null ? '当前时段' : `${String(currentComparison.currentHour).padStart(2, '0')}:00` }}
                    · {{ formatTemperature(currentComparison.predictedCurrent) }}
                  </strong>
                </div>
                <p v-if="currentComparison?.diff !== null" class="diff-text" :class="{ warm: Number(currentComparison?.diff) > 0, cool: Number(currentComparison?.diff) < 0 }">
                  较时段参考 {{ Number(currentComparison?.diff) > 0 ? '+' : '' }}{{ currentComparison?.diff }}°
                </p>
                <p v-else class="muted">暂无实时天气可对比</p>
              </article>

              <article class="confidence-card" :key="`confidence-${predictionAnimationKey}`">
                <div class="side-card-kicker">预测说明</div>
                <strong :class="{ warm: Number(prediction.trend) > 0, cool: Number(prediction.trend) < 0 }">
                  {{ Number(prediction.trend) > 0 ? '升温趋势' : Number(prediction.trend) < 0 ? '降温趋势' : '温度平稳' }}
                </strong>
                <p>主预测目标为今日最高温、最低温；当前温度仅按近10天同小时历史做参考对比。</p>
              </article>
            </div>
          </aside>

          <div class="left-content prediction-main">
            <article class="weather-card prediction-weather-card" :key="`prediction-${predictionAnimationKey}`">
              <div class="card-glass-glow"></div>
              <div class="card-top-row prediction-top-row">
                <div class="card-title">
                  <h3>{{ currentLocation }}</h3>
                  <div class="title-meta-row">
                    <span class="title-path">{{ displayLocationPath || '天气预测' }}</span>
                    <span v-if="displayLocationPath" class="divider">|</span>
                    <span class="update-time">今日趋势预测</span>
                  </div>
                </div>
                <span class="prediction-badge">缓存优先预测</span>
              </div>

              <div class="main-weather-section prediction-main-weather">
                <div class="weather-icon-wrapper">
                  <img :src="getWeatherIcon(prediction.weatherText)" alt="" class="main-icon" />
                </div>
                <div class="temp-display">
                  <span class="degree">{{ formatTemperature(prediction.tempMax) }}</span>
                </div>
                <div class="condition-group">
                  <span class="condition-text">{{ prediction.weatherText }}</span>
                  <span class="feels-like">预计最低 {{ formatTemperature(prediction.tempMin) }}</span>
                </div>
              </div>

              <p class="weather-summary">
                当前预测基于近10天历史天气样本生成，主结果为今日最高温、最低温；并结合近10天逐小时历史温度推算当前时段参考值。
              </p>

              <div class="detail-grid prediction-detail-grid">
                <div class="grid-item">
                  <span class="grid-label">温度预测准确率</span>
                  <span class="grid-value">{{ prediction.temperatureConfidence }}%</span>
                </div>
                <div class="grid-item">
                  <span class="grid-label">预计最低温</span>
                  <span class="grid-value">{{ formatTemperature(prediction.tempMin) }}</span>
                </div>
                <div class="grid-item">
                  <span class="grid-label">参考时段</span>
                  <span class="grid-value">{{ currentComparison?.currentHour === null || currentComparison?.currentHour === undefined ? '--' : `${String(currentComparison.currentHour).padStart(2, '0')}:00` }}</span>
                </div>
                <div class="grid-item">
                  <span class="grid-label">预计湿度</span>
                  <span class="grid-value">{{ prediction.humidity === null ? '--' : `${Math.round(prediction.humidity)}%` }}</span>
                </div>
                <div class="grid-item">
                  <span class="grid-label">预计气压</span>
                  <span class="grid-value">{{ prediction.pressure === null ? '--' : `${Math.round(prediction.pressure)} hPa` }}</span>
                </div>
                <div class="grid-item">
                  <span class="grid-label">趋势判断</span>
                  <span class="grid-value" :class="{ warm: Number(prediction.trend) > 0, cool: Number(prediction.trend) < 0 }">
                    {{ Number(prediction.trend) > 0 ? '升温' : Number(prediction.trend) < 0 ? '降温' : '平稳' }}
                  </span>
                </div>
              </div>
            </article>
          </div>
        </section>
      </template>
    </div>
  </div>
</template>

<style scoped>
.weather-container.forecast-page {
  --page-bg: linear-gradient(135deg, #f7fbff 0%, #d9edff 46%, #a8d8ff 100%);
  --panel-bg: rgba(239, 248, 255, 0.78);
  --panel-border: rgba(255, 255, 255, 0.8);
  --text-main: #101827;
  --text-muted: #64748b;
  --text-primary: #1e293b;
  --text-secondary: #64748b;
  --text-tertiary: #94a3b8;
  --text-highlight: #0f172a;
  --glass-bg: rgba(255, 255, 255, 0.6);
  --glass-border: rgba(255, 255, 255, 0.6);
  --glass-border-top: rgba(255, 255, 255, 0.9);
  --input-bg: rgba(255, 255, 255, 0.3);
  --input-border: rgba(255, 255, 255, 0.4);
  --input-focus-bg: rgba(255, 255, 255, 0.85);
  --input-text: #1e293b;
  --input-placeholder: #64748b;
  --btn-bg: rgba(255, 255, 255, 0.4);
  --btn-border: rgba(255, 255, 255, 0.5);
  --btn-hover-bg: rgba(255, 255, 255, 0.9);
  --pill-bg: rgba(255, 255, 255, 0.45);
  --pill-hover-bg: rgba(255, 255, 255, 0.85);
  --search-dropdown-bg: rgba(255, 255, 255, 0.92);
  --search-item-hover: rgba(59, 130, 246, 0.08);
  --shadow-color: rgba(51, 65, 85, 0.14);
  --blue: #2f7cff;
  --warm: #ff8a1d;
  --cool: #38bdf8;
}

.weather-container.forecast-page.dark-mode {
  --page-bg: radial-gradient(circle at 28% 8%, rgba(59, 130, 246, 0.24), transparent 34%), linear-gradient(135deg, #07101f 0%, #101a31 52%, #162c66 100%);
  --panel-bg: rgba(15, 23, 42, 0.72);
  --panel-border: rgba(148, 163, 184, 0.2);
  --text-main: #f8fafc;
  --text-muted: #94a3b8;
  --text-primary: #f8fafc;
  --text-secondary: #cbd5e1;
  --text-tertiary: #94a3b8;
  --text-highlight: #ffffff;
  --glass-bg: rgba(15, 23, 42, 0.72);
  --glass-border: rgba(255, 255, 255, 0.1);
  --glass-border-top: rgba(255, 255, 255, 0.18);
  --input-bg: rgba(15, 23, 42, 0.52);
  --input-border: rgba(255, 255, 255, 0.12);
  --input-focus-bg: rgba(30, 41, 59, 0.95);
  --input-text: #f8fafc;
  --input-placeholder: #94a3b8;
  --btn-bg: rgba(15, 23, 42, 0.5);
  --btn-border: rgba(255, 255, 255, 0.12);
  --btn-hover-bg: rgba(30, 41, 59, 0.95);
  --pill-bg: rgba(15, 23, 42, 0.52);
  --pill-hover-bg: rgba(30, 41, 59, 0.95);
  --search-dropdown-bg: rgba(15, 23, 42, 0.95);
  --search-item-hover: rgba(148, 163, 184, 0.12);
  --shadow-color: rgba(2, 6, 23, 0.36);
}

* {
  box-sizing: border-box;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
}

.weather-container.forecast-page {
  width: 100%;
  min-height: calc(100dvh - 64px);
  background: var(--page-bg);
  color: var(--text-main);
  transition: background 0.35s ease, color 0.25s ease;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 0 0 34px;
  position: relative;
}

.top-bar {
  user-select: none;
  position: sticky;
  top: 0;
  z-index: 1000;
  width: 100%;
  background-color: transparent;
  border-bottom: 1px solid transparent;
  box-shadow: none;
  backdrop-filter: none;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 17px;
  gap: 17px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.top-bar.is-scrolled {
  background-color: var(--glass-bg) !important;
  backdrop-filter: blur(12px) !important;
  -webkit-backdrop-filter: blur(12px) !important;
  border-bottom: 1px solid var(--glass-border) !important;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05) !important;
}

.left-section {
  display: flex;
  align-items: center;
  gap: 14px;
  flex: 1;
  max-width: 935px;
  min-width: 0;
}

.right-section {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 10px;
}

.unit-toggle-btn {
  background: var(--btn-bg);
  border: 1px solid var(--btn-border);
  height: 39px;
  width: 46px;
  border-radius: 11px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
  transition: all 0.3s ease;
  box-shadow: 0 3px 5px rgba(0, 0, 0, 0.01);
}

.unit-toggle-btn:hover {
  background: var(--btn-hover-bg);
  transform: translateY(-2px);
  box-shadow: 0 7px 13px rgba(0, 0, 0, 0.06);
  color: var(--text-highlight);
  border-color: var(--glass-border-top);
}

.search-wrapper {
  position: relative;
  width: 255px;
  flex-shrink: 0;
  z-index: 101;
  isolation: isolate;
}

.search-box {
  height: 39px;
  position: relative;
  display: flex;
  align-items: center;
  background: var(--input-bg);
  border: 1px solid var(--input-border);
  border-radius: 11px;
  box-shadow: 0 3px 5px rgba(0, 0, 0, 0.01);
  transition: all 0.4s cubic-bezier(0.2, 0.8, 0.2, 1);
}

.search-box:focus-within,
.search-box.has-shadow {
  background: var(--input-focus-bg);
  border-color: var(--glass-border-top);
  box-shadow: 0 7px 20px rgba(0, 0, 0, 0.08), 0 2px 3px rgba(0, 0, 0, 0.02);
}

.search-box.invalid {
  border-color: rgba(239, 68, 68, 0.65);
}

.search-box input {
  width: 100%;
  height: 100%;
  border: none;
  outline: none;
  font-size: 13px;
  color: var(--input-text);
  background: transparent;
  font-weight: 500;
  padding-left: 14px;
  padding-right: 73px;
}

.search-box input::placeholder {
  color: var(--input-placeholder);
}

.search-actions {
  position: absolute;
  right: 10px;
  top: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  gap: 5px;
}

.clear-btn {
  background: rgba(0, 0, 0, 0.06);
  border: none;
  border-radius: 50%;
  width: 17px;
  height: 17px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.2s;
}

.clear-btn:hover {
  background: rgba(0, 0, 0, 0.15);
  color: var(--text-highlight);
  transform: scale(1.1);
}

.search-icon {
  color: var(--text-secondary);
  display: flex;
  align-items: center;
  transition: color 0.3s;
  padding: 3px;
  cursor: pointer;
}

.search-box:focus-within .search-icon {
  color: #3b82f6;
}

.search-result {
  position: absolute;
  top: calc(100% + 8px);
  left: 0;
  width: 100%;
  background: var(--search-dropdown-bg);
  border: 1px solid var(--glass-border);
  border-radius: 10px;
  box-shadow: 0 14px 34px rgba(0, 0, 0, 0.12);
  overflow: hidden;
  padding: 7px;
}

.status-box {
  padding: 20px 10px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: var(--text-secondary);
  font-size: 12px;
  text-align: center;
}

.location-item {
  padding: 10px;
  cursor: pointer;
  border-radius: 7px;
  transition: all 0.2s ease;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.location-item:hover {
  background-color: var(--search-item-hover);
  transform: translateX(3px);
}

.item-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
}

.item-path {
  font-size: 10px;
  color: var(--text-tertiary);
}

.loading-spinner {
  width: 15px;
  height: 15px;
  border: 2px solid rgba(59, 130, 246, 0.1);
  border-left-color: #3b82f6;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.quick-cities-wrapper {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
  min-width: 0;
  position: relative;
  isolation: isolate;
}

.history-title-strip {
  justify-content: flex-start;
}

.prediction-strip {
  gap: 14px;
}

.history-title-pill {
  height: 39px;
  padding: 0 17px;
  background: var(--pill-bg);
  border: 1px solid var(--btn-border);
  border-radius: 11px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  box-shadow: 0 2px 3px rgba(0, 0, 0, 0.03);
}

.prediction-title-pill {
  flex: 0 0 auto;
}

.cities-scroll-view {
  display: flex;
  align-items: center;
  gap: 8px;
  overflow-x: auto;
  scroll-behavior: smooth;
  white-space: nowrap;
  width: 100%;
  padding: 8px 20px 8px 3px;
  margin: -8px 0;
  scrollbar-width: none;
  -ms-overflow-style: none;
}

.cities-scroll-view::-webkit-scrollbar {
  display: none;
}

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

.nav-controls {
  display: flex;
  align-items: center;
  gap: 7px;
  flex-shrink: 0;
  padding-right: 3px;
}

.nav-btn {
  width: 27px;
  height: 27px;
  border-radius: 50%;
  border: 1px solid var(--btn-border);
  background: var(--btn-bg);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: var(--text-secondary);
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
  box-shadow: 0 2px 7px rgba(0, 0, 0, 0.05);
  outline: none;
}

.nav-btn:hover {
  background: var(--btn-hover-bg);
  color: var(--text-highlight);
  transform: scale(1.05);
}

.city-pill {
  flex-shrink: 0;
  height: 39px;
  background: transparent;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: z-index 0.2s ease;
  position: relative;
  z-index: 1;
}

.city-pill.is-hovered {
  z-index: 10;
}

.city-pill:active,
.city-pill:focus,
.city-pill:focus-visible {
  outline: none;
}

.pill-content {
  height: 100%;
  padding: 0 17px;
  background: var(--pill-bg);
  border: 1px solid var(--btn-border);
  border-radius: 11px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 7px;
  box-shadow: 0 2px 3px rgba(0, 0, 0, 0.03);
  transition: background 0.25s ease, border-color 0.25s ease, transform 0.25s ease, box-shadow 0.25s ease;
  transform: translateZ(0);
}

.city-pill.is-hovered .pill-content {
  background: var(--pill-hover-bg);
  border-color: var(--glass-border-top);
  transform: translateY(-2px) translateZ(0);
}

.pill-icon {
  width: 19px;
  height: 19px;
  object-fit: contain;
}

.city-name {
  font-size: 12px;
  font-weight: 500;
  color: var(--text-primary);
  line-height: 1;
}

.city-temp {
  font-weight: 700;
  color: var(--text-highlight);
  font-size: 13px;
  line-height: 1;
}

.delete-btn {
  flex: 0 0 auto;
  width: 0;
  height: 12px;
  margin-left: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: #b0b0b0;
  cursor: pointer;
  transition: width 0.25s ease, margin-left 0.25s ease, opacity 0.2s ease, transform 0.2s ease, color 0.2s ease;
  overflow: hidden;
  white-space: nowrap;
  opacity: 0;
  transform: scale(0.7);
  transform-origin: center;
  pointer-events: none;
}

.city-pill.is-hovered .delete-btn {
  width: 12px;
  margin-left: 6px;
  opacity: 1;
  transform: scale(1);
  pointer-events: auto;
}

.delete-btn svg {
  width: 12px;
  height: 12px;
  stroke-width: 2px;
}

.content-body {
  width: 100%;
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1;
  min-height: 340px;
  z-index: 1;
}

.main-content-wrapper {
  width: 100%;
  max-width: 1064px;
  display: flex;
  justify-content: center;
  align-items: start;
  gap: 17px;
  padding: 0 17px;
}

.left-content {
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 0 1 765px;
  min-width: 0;
}

.side-content {
  width: 230px;
  flex: 0 0 230px;
  min-width: 230px;
}

.prediction-card,
.compare-card,
.confidence-card,
.feature-card {
  border: 1px solid var(--panel-border);
  background: var(--panel-bg);
  box-shadow: 0 22px 60px rgba(45, 75, 116, 0.16);
  backdrop-filter: blur(20px);
}

.empty-state {
  margin-top: 85px;
  text-align: center;
  color: var(--text-tertiary);
  width: 100%;
  animation: fade 1s ease;
}

.empty-content {
  display: inline-flex;
  flex-direction: column;
  align-items: center;
  gap: 0;
}

.sun-decoration {
  width: 51px;
  height: 51px;
  background: linear-gradient(135deg, #ffd700, #ff8c00);
  border-radius: 50%;
  margin: 0 auto 17px;
  box-shadow: 0 0 34px rgba(255, 215, 0, 0.6);
  opacity: 0.8;
}

.prediction-layout {
  padding-top: 0;
}

.prediction-main {
  width: 765px;
  max-width: 765px;
}

.prediction-side {
  padding-top: 34px;
}

.prediction-side-stack {
  position: sticky;
  top: 102px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.prediction-card,
.compare-card,
.confidence-card {
  width: 100%;
  border-radius: 27px;
}

.compare-card,
.confidence-card {
  min-height: 192px;
  border-radius: 27px;
  padding: 24px 22px;
}

.prediction-weather-card {
  width: 100%;
  max-width: 765px;
  position: relative;
  overflow: hidden;
  background: var(--glass-bg);
  backdrop-filter: blur(12px) saturate(120%);
  -webkit-backdrop-filter: blur(12px) saturate(120%);
  border: 1px solid var(--glass-border);
  border-top: 1px solid var(--glass-border-top);
  border-radius: 27px;
  padding: 34px 42px;
  box-shadow: 0 17px 42px -8px var(--shadow-color), 0 8px 17px -8px var(--shadow-color);
  margin: 34px auto 0;
  isolation: isolate;
  animation: predictionCardEntrance 0.62s cubic-bezier(0.22, 1, 0.36, 1);
  transform-origin: center top;
  will-change: transform, opacity;
}

.card-glass-glow {
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: radial-gradient(circle at 50% 0%, rgba(255, 255, 255, 0.1) 0%, transparent 60%);
  pointer-events: none;
  opacity: 0.8;
}

.compare-card {
  animation: predictionCardEntrance 0.62s cubic-bezier(0.22, 1, 0.36, 1) 0.06s both;
  transform-origin: center top;
}

.confidence-card {
  animation: predictionCardEntrance 0.62s cubic-bezier(0.22, 1, 0.36, 1) 0.12s both;
  transform-origin: center top;
}

@keyframes predictionCardEntrance {
  0% {
    opacity: 0;
    transform: translateY(20px) scale(0.985);
  }
  100% {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.prediction-top-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
}

.card-top-row {
  position: relative;
  z-index: 2;
}

.card-title {
  flex: 0 1 auto;
}

.card-title h3 {
  margin: 0 0 3px;
  font-size: 17px;
  font-weight: 700;
  color: var(--text-primary);
}

.title-meta-row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.title-path {
  font-size: 12px;
  font-weight: 500;
  color: var(--text-secondary);
}

.divider {
  color: rgba(148, 163, 184, 0.45);
  font-size: 11px;
}

.prediction-badge {
  flex: 0 0 auto;
  align-self: flex-start;
  padding: 9px 14px;
  border-radius: 999px;
  color: #2563eb;
  background: rgba(59, 130, 246, 0.12);
  font-size: 13px;
  font-weight: 900;
}

.main-weather-section {
  display: flex;
  align-items: center;
  margin: 8px 0 34px;
  gap: 25px;
  position: relative;
  z-index: 2;
}

.weather-icon-wrapper {
  width: 85px;
  height: 85px;
  display: flex;
  align-items: center;
  justify-content: center;
  filter: drop-shadow(0 8px 17px rgba(0, 0, 0, 0.15));
}

.main-icon {
  width: 130%;
  height: 130%;
  object-fit: contain;
}

.degree {
  font-size: 70px;
  font-weight: 600;
  color: var(--text-highlight);
  line-height: 1;
  letter-spacing: -2.5px;
}

.condition-group {
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 3px;
}

.condition-text {
  font-size: 20px;
  font-weight: 600;
  color: var(--text-primary);
}

.feels-like {
  font-size: 13px;
  color: var(--text-secondary);
  font-weight: 500;
}

.weather-summary {
  font-size: 14px;
  color: var(--text-primary);
  margin-bottom: 38px;
  line-height: 1.6;
  font-weight: 400;
  max-width: 510px;
  position: relative;
  z-index: 2;
}

.detail-grid {
  display: grid;
  gap: 17px;
  padding-top: 25px;
  border-top: 1px solid rgba(148, 163, 184, 0.2);
  position: relative;
  z-index: 2;
}

.grid-item {
  display: flex;
  flex-direction: column;
  gap: 5px;
  min-width: 0;
}

.grid-label {
  font-size: 11px;
  color: var(--text-secondary);
  font-weight: 500;
  white-space: nowrap;
  line-height: 17px;
}

.grid-value {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-highlight);
  white-space: nowrap;
  line-height: 1.4;
}

.forecast-desc,
.confidence-card p,
.muted {
  color: var(--text-muted);
  font-weight: 700;
}

.feature-card span,
.section-title span {
  color: var(--text-muted);
  font-size: 14px;
  font-weight: 900;
}

.compare-main strong {
  display: block;
  font-size: 68px;
  line-height: 0.95;
  letter-spacing: -2px;
  color: var(--text-highlight);
  font-weight: 700;
}

.compare-main p {
  margin: 8px 0 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
}

.compare-subline {
  display: flex;
  flex-direction: column;
  gap: 5px;
  padding-top: 16px;
  border-top: 1px solid rgba(148, 163, 184, 0.16);
  margin: 18px 0 12px;
}

.compare-subline span {
  color: var(--text-muted);
  font-size: 14px;
  font-weight: 900;
}

.compare-subline strong {
  font-size: 14px;
  color: var(--text-highlight);
  font-weight: 700;
}

.diff-text {
  display: inline-flex;
  padding: 8px 12px;
  border-radius: 999px;
  background: rgba(100, 116, 139, 0.1);
  font-weight: 900;
}

.warm {
  color: var(--warm);
}

.cool {
  color: var(--cool);
}

.side-card-kicker {
  font-size: 12px;
  color: var(--text-secondary);
  font-weight: 500;
  margin-bottom: 18px;
}

.confidence-card strong {
  display: inline-block;
  margin-bottom: 10px;
  font-size: 32px;
  line-height: 1.04;
  font-weight: 700;
  color: var(--text-highlight);
}

.confidence-card p {
  margin: 0;
  font-size: 14px;
  line-height: 1.7;
  font-weight: 600;
}

.prediction-detail-grid {
  grid-template-columns: repeat(6, minmax(0, 1fr));
}

.section-title {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 22px;
}

.section-title strong {
  font-size: 22px;
}

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

.loading-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 14px;
  background: var(--weather-loading-content-bg, rgba(255, 255, 255, 0.8));
  padding: 25px 42px;
  border-radius: 20px;
  box-shadow: var(--weather-loading-shadow, 0 8px 34px rgba(0,0,0,0.1));
}

.loading-spinner-large {
  width: 34px;
  height: 34px;
  border: 3px solid rgba(59, 130, 246, 0.2);
  border-left-color: #3b82f6;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.loading-text {
  font-size: 13px;
  color: var(--weather-loading-text-color, var(--text-secondary));
  font-weight: 600;
}

@media (max-width: 1024px) {
  .prediction-layout {
    flex-direction: column;
    align-items: center;
    gap: 12px;
    padding: 0 12px;
  }

  .prediction-side {
    position: static;
    padding-top: 0;
    width: 100%;
    max-width: 765px;
    flex: 0 1 auto;
  }

  .prediction-side-stack {
    position: static;
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 12px;
  }

  .prediction-main {
    width: 100%;
    max-width: 765px;
  }
}

@media (max-width: 760px) {
  .top-bar {
    height: auto;
    flex-wrap: wrap;
    padding: 14px;
  }

  .left-section {
    flex: 1 1 100%;
    flex-wrap: wrap;
  }

  .search-wrapper {
    flex: 1 1 100%;
    width: 100%;
  }

  .right-section {
    margin-left: auto;
  }

  .prediction-top-row,
  .main-weather-section {
    align-items: flex-start;
    flex-direction: column;
  }

  .prediction-detail-grid,
  .prediction-side-stack {
    grid-template-columns: 1fr;
  }

  .prediction-strip {
    flex-wrap: wrap;
    gap: 10px;
  }

  .prediction-title-pill {
    order: -1;
  }

  .prediction-card,
  .compare-card,
  .confidence-card {
    border-radius: 26px;
    padding: 22px;
  }

  .prediction-card {
    max-width: 680px;
  }

  .prediction-main {
    width: 100%;
    max-width: 680px;
  }
}
</style>
