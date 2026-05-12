# Weather Analytics Frontend

基于 Vue 3、Vite、TypeScript 和 Element Plus 构建的天气数据可视化前端项目，提供实时天气、历史天气、空气质量、天气预测、后台管理等页面能力。

A weather data visualization frontend built with Vue 3, Vite, TypeScript, and Element Plus. It provides real-time weather, historical weather, air quality, weather prediction, and admin management pages.

这份目录是适合公开到 GitHub 的前端版本，重点用于项目展示、持续维护和部署说明。

This directory is a GitHub-ready public frontend version, intended for project showcasing, long-term maintenance, and deployment documentation.

## 项目亮点 / Highlights

- 支持实时天气、历史天气、历史空气质量、天气预测等多场景查询
- Supports real-time weather, historical weather, historical air quality, and weather prediction scenarios
- 提供游客模式、登录态、单账号登录控制、全局鉴权联动
- Includes guest mode, login state management, single-session control, and global auth linkage
- 支持深色 / 浅色模式、多语言切换和后台管理页面
- Supports dark/light mode, language switching, and admin management pages
- 前端对查询链路、状态提示、异常处理和交互动画做了统一封装
- Frontend logic is unified around request flow, status feedback, error handling, and interaction animations

## 技术栈 / Tech Stack

- Vue 3
- TypeScript
- Vite
- Vue Router
- Axios
- Element Plus
- ECharts

## 目录结构 / Project Structure

```text
src/
  components/     公共组件与业务卡片 / shared components and business cards
  router/         路由配置 / route configuration
  store/          基础配置 / base config
  utils/          请求、鉴权、签名、语言切换等工具 / request, auth, signing, i18n utilities
  views/          用户端与后台页面 / user and admin pages
public/           静态资源 / static assets
```

## 主要页面 / Main Pages

- 实时天气查询 / Real-time weather
- 历史天气与历史空气质量分析 / Historical weather and historical air quality analysis
- 天气预测 / Weather prediction
- 用户登录 / 注册 / 找回密码 / Login, register, password reset
- 后台用户管理 / Admin user management
- 后台流量统计 / Admin traffic statistics

## 快速启动 / Quick Start

### 方式一：本地联调 / Option 1: Local development

1. 进入前端目录 / Enter the frontend directory
2. 安装依赖 / Install dependencies

```bash
npm install
```

3. 复制环境变量模板 / Copy the environment template

```bash
cp .env.example .env
```

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

4. 修改接口地址 / Update the backend API URL

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_API_SIGN_SECRET=replace-with-your-sign-secret
```

5. 启动开发环境 / Start the dev server

```bash
npm run dev
```

默认访问地址通常为 / Default frontend URL is usually:

```text
http://localhost:3000
```

### 方式二：构建产物 / Option 2: Build for production

```bash
npm run build
```

构建输出目录 / Build output directory:

```text
dist/
```

## 与后端的配合能力 / Backend Dependencies

前端默认对接 Django 后端，依赖以下接口能力：

The frontend is designed to work with a Django backend and depends on the following API capabilities:

- 实时天气查询 / Real-time weather query
- 历史天气查询 / Historical weather query
- 历史空气质量查询 / Historical air quality query
- 城市搜索 / City search
- 游客 Token 与游客限流 / Guest token and guest quota limit
- Access Token / Refresh Token / Access token and refresh token
- 用户管理与后台统计 / User management and admin statistics

## 本地开发说明 / Local Development Notes

- `npm install` 后会安装 `vue-tsc`，否则 `npm run build` 会报错
- `VITE_API_BASE_URL` 必须指向已启动的后端服务
- 如果后端启用了签名校验，需要同步配置 `VITE_API_SIGN_SECRET`

- `vue-tsc` will be installed after `npm install`; otherwise `npm run build` will fail
- `VITE_API_BASE_URL` must point to a running backend service
- If backend-side request signing is enabled, keep `VITE_API_SIGN_SECRET` aligned

## 安全说明 / Security Notes

这份 GitHub 版本已移除仓库中的真实部署地址和前端写死配置入口，改为环境变量读取。

This GitHub version removes hardcoded deployment addresses and frontend config entries from the repository and replaces them with environment variables.

仍建议你在正式公开前再次确认：

Before publishing publicly, you should still confirm the following:

- 不提交真实 `.env` / Do not commit the real `.env`
- 不提交生产 API 地址、数据库密码、邮箱授权码、JWT 密钥 / Do not commit production API URLs, database passwords, mail auth codes, or JWT secrets
- 如果历史提交里出现过敏感信息，要先轮换密钥再公开仓库 / If secrets appeared in commit history, rotate them before making the repository public

## 展示建议 / Showcase Suggestions

如果你打算把这个项目写进简历或 GitHub 主页，建议补充：

If you plan to present this project on your resume or GitHub profile, consider adding:

- 页面截图 / Screenshots
- 接口文档 / API documentation
- 部署架构图 / Deployment architecture diagram
- Redis 缓存与鉴权策略说明 / Redis caching and auth strategy notes
- Docker / containerd / nerdctl 部署过程 / Docker, containerd, and nerdctl deployment notes
