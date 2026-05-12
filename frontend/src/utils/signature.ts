import md5 from 'md5';

const API_SECRET_KEY = import.meta.env.VITE_API_SIGN_SECRET || '';
const SESSION_SIGN_KEY = 'weather_session_sign_key';
const GUEST_SIGN_KEY = 'weather_guest_sign_key';

localStorage.removeItem(SESSION_SIGN_KEY);
localStorage.removeItem(GUEST_SIGN_KEY);

const makeNonce = () => {
  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
  let randomPart = '';
  for (let i = 0; i < 16; i += 1) {
    randomPart += chars.charAt(Math.floor(Math.random() * chars.length));
  }
  return `${randomPart}${Date.now().toString(16)}`;
};

export const setSessionSignKey = (signKey?: string) => {
  localStorage.removeItem(SESSION_SIGN_KEY);
  if (signKey) sessionStorage.setItem(SESSION_SIGN_KEY, signKey);
};

export const clearSessionSignKey = () => {
  sessionStorage.removeItem(SESSION_SIGN_KEY);
  localStorage.removeItem(SESSION_SIGN_KEY);
};

export const getSessionSignKey = () => sessionStorage.getItem(SESSION_SIGN_KEY) || '';

export const setGuestSignKey = (signKey?: string) => {
  localStorage.removeItem(GUEST_SIGN_KEY);
  if (signKey) sessionStorage.setItem(GUEST_SIGN_KEY, signKey);
};

export const clearGuestSignKey = () => {
  sessionStorage.removeItem(GUEST_SIGN_KEY);
  localStorage.removeItem(GUEST_SIGN_KEY);
};

export const getGuestSignKey = () => sessionStorage.getItem(GUEST_SIGN_KEY) || '';

export const generateSignedHeaders = (params: Record<string, string | number> = {}, signKey = API_SECRET_KEY) => {
  const timestamp = `${Date.now()}`;
  const nonce = makeNonce();
  const sortedKeys = Object.keys(params).sort();
  const paramStr = sortedKeys.map((key) => `${key}=${params[key]}`).join('&');
  const raw = `${paramStr}&timestamp=${timestamp}&nonce=${nonce}&secret=${signKey}`;

  return {
    'X-Sign': md5(raw).toUpperCase(),
    'X-Timestamp': timestamp,
    'X-Nonce': nonce
  };
};

export const generateSessionSignedHeaders = (params: Record<string, string | number> = {}) =>
  generateSignedHeaders(params, getSessionSignKey());

export const generateGuestSignedHeaders = (params: Record<string, string | number> = {}) =>
  generateSignedHeaders(params, getGuestSignKey());

