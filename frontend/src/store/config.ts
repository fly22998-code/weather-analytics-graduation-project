// src/store/config.ts

// GitHub 公开版本使用环境变量注入接口地址，避免把部署地址写死在仓库里。
export const BASE_URL = import.meta.env.VITE_API_BASE_URL || '';
export const BASE_API = BASE_URL;
