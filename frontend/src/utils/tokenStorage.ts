const ACCESS_TOKEN_KEY = 'token';
const REFRESH_TOKEN_KEY = 'refresh_token';

export const cleanupLegacyAuthStorage = () => {
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
};

export const getAccessToken = () => sessionStorage.getItem(ACCESS_TOKEN_KEY) || '';

export const setAccessToken = (token?: string) => {
  cleanupLegacyAuthStorage();
  if (token) {
    sessionStorage.setItem(ACCESS_TOKEN_KEY, token);
  }
};

export const clearAccessToken = () => {
  cleanupLegacyAuthStorage();
  sessionStorage.removeItem(ACCESS_TOKEN_KEY);
};
