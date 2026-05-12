import { reactive } from 'vue';
import { isLoggedIn } from './auth';
import { openAuthModal } from './authModal';
import { clearGuestSignKey, setGuestSignKey } from './signature';
import { getAccessToken } from './tokenStorage';
import { t } from './i18n';

const STORAGE_KEY = 'weather_guest_quota_state_v2';
const GUEST_TOKEN_KEY = 'weather_guest_token';
const WEATHER_QUERY_LIMIT = 10;

localStorage.removeItem(GUEST_TOKEN_KEY);

interface GuestQuotaStorage {
  date: string;
  weatherQueryCount: number;
}

export const guestQuotaState = reactive({
  version: 0
});

let lastServerQuotaSyncAt = 0;

const bumpVersion = () => {
  guestQuotaState.version += 1;
};

const getTodayKey = () => {
  const now = new Date();
  const year = now.getFullYear();
  const month = `${now.getMonth() + 1}`.padStart(2, '0');
  const day = `${now.getDate()}`.padStart(2, '0');
  return `${year}-${month}-${day}`;
};

const readStorage = (): GuestQuotaStorage => {
  const today = getTodayKey();

  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) {
      return { date: today, weatherQueryCount: 0 };
    }

    const parsed = JSON.parse(raw) as Partial<GuestQuotaStorage>;
    if (parsed.date !== today) {
      return { date: today, weatherQueryCount: 0 };
    }

    return {
      date: parsed.date || today,
      weatherQueryCount: Number(parsed.weatherQueryCount || 0)
    };
  } catch {
    return { date: today, weatherQueryCount: 0 };
  }
};

const writeStorage = (storage: GuestQuotaStorage) => {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(storage));
  bumpVersion();
};

const hasUserSessionCandidate = () => {
  return isLoggedIn() || !!getAccessToken();
};

export const getGuestToken = () => sessionStorage.getItem(GUEST_TOKEN_KEY) || '';

export const setGuestToken = (token: string, signKey?: string) => {
  if (!token) return;
  localStorage.removeItem(GUEST_TOKEN_KEY);
  sessionStorage.setItem(GUEST_TOKEN_KEY, token);
  setGuestSignKey(signKey);
};

export const clearGuestToken = () => {
  sessionStorage.removeItem(GUEST_TOKEN_KEY);
  localStorage.removeItem(GUEST_TOKEN_KEY);
  clearGuestSignKey();
};

export const shouldUseGuestToken = (url?: string) => {
  if (!url) return false;
  return url.includes('/weather/user/weather/')
    || url.includes('/weather/user/weather/history/')
    || url.includes('/weather/user/historical/weather/')
    || url.includes('/weather/user/location/search');
};

export const syncGuestQuotaFromHeaders = (headers: Record<string, any>) => {
  if (hasUserSessionCandidate()) return;

  const used = Number(headers['x-guest-quota-used']);
  if (!Number.isFinite(used)) return;

  lastServerQuotaSyncAt = Date.now();
  writeStorage({
    date: getTodayKey(),
    weatherQueryCount: Math.max(0, used)
  });
};

export const getGuestWeatherQueryQuota = () => {
  if (hasUserSessionCandidate()) {
    return {
      isGuest: false,
      used: 0,
      remaining: WEATHER_QUERY_LIMIT,
      limit: WEATHER_QUERY_LIMIT
    };
  }

  const storage = readStorage();
  const used = Math.min(storage.weatherQueryCount, WEATHER_QUERY_LIMIT);

  return {
    isGuest: true,
    used,
    remaining: Math.max(WEATHER_QUERY_LIMIT - used, 0),
    limit: WEATHER_QUERY_LIMIT
  };
};

export const canGuestQueryWeather = () => {
  if (hasUserSessionCandidate()) {
    return true;
  }

  const quota = getGuestWeatherQueryQuota();
  if (quota.remaining > 0) {
    return true;
  }

  openAuthModal('login', t('guest.quotaUsed'));
  return false;
};

export const consumeGuestWeatherQuery = () => {
  if (hasUserSessionCandidate()) {
    return;
  }

  if (Date.now() - lastServerQuotaSyncAt < 1500) {
    return;
  }

  const storage = readStorage();
  storage.weatherQueryCount += 1;
  writeStorage(storage);
};
