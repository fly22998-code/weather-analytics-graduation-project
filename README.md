# Weather Analytics Graduation Project

实时气象数据查询与分析平台（毕业设计）  
A Full-Stack Weather Analytics Platform (Graduation Project)

## 项目简介 / Project Overview

这是一个以前后端分离方式实现的天气数据查询与分析系统，项目以 `Vue 3 + TypeScript + Vite` 作为前端技术栈，以 `Django + MySQL + Redis` 作为后端核心支撑，并结合第三方天气服务完成实时天气、历史天气、空气质量与天气预测等功能。

This is a full-stack weather data query and analytics system built with a separated frontend-backend architecture. The frontend is based on `Vue 3 + TypeScript + Vite`, while the backend uses `Django + MySQL + Redis`, combined with third-party weather services to provide real-time weather, historical weather, air quality, and weather prediction features.

## 毕业设计定位 / Graduation Project Positioning

本项目可作为天气数据服务、全栈开发、运维部署与接口安全结合的综合型毕业设计项目，重点体现以下能力：

- 天气数据接入与可视化展示
- 用户系统、游客限制与登录态管理
- Redis 缓存、流量统计与接口优化
- Nginx / HTTPS / Cloudflare / 容器化部署实践
- 运维开发、接口联调、服务排障与项目上线能力

This project can be presented as a comprehensive graduation project combining weather data services, full-stack development, operations deployment, and API security, with a focus on:

- Weather data integration and visualization
- User system, guest quota control, and login-state management
- Redis caching, traffic statistics, and API optimization
- Nginx / HTTPS / Cloudflare / containerized deployment practice
- DevOps-oriented development, API debugging, troubleshooting, and production deployment

## 功能亮点 / Key Features

- 实时天气查询 / Real-time weather query
- 历史天气与历史空气质量查询 / Historical weather and historical air quality query
- 天气趋势预测 / Weather trend prediction
- 城市搜索与常用城市气泡交互 / City search and frequent-city bubble interaction
- 登录 / 注册 / 找回密码 / Login, register, password reset
- 游客模式与查询次数限制 / Guest mode and quota limitation
- 单账号登录控制 / Single-session login control
- 后台用户管理 / Admin user management
- 后台流量统计与访问分析 / Admin traffic statistics and usage analysis
- 深色 / 浅色模式与多语言切换 / Dark-light mode and multilingual switching

## 技术栈 / Tech Stack

### 前端 / Frontend
- Vue 3
- TypeScript
- Vite
- Vue Router
- Axios
- Element Plus
- ECharts

### 后端 / Backend
- Python
- Django
- MySQL
- Redis
- Gunicorn
- PyJWT
- django-cors-headers
- django-redis
- python-dotenv

### 运维与部署 / DevOps and Deployment
- Linux
- Nginx
- Docker / Docker Compose
- containerd / nerdctl
- Cloudflare

## 项目结构 / Project Structure

```text
weather-analytics-graduation-project/
  frontend/    Vue3 前端项目 / Vue3 frontend
  backend/     Django 后端项目 / Django backend
  docs/        项目文档 / project documents
```

## 快速启动 / Quick Start

### 1. 启动后端 / Start the backend

进入后端目录：

```bash
cd backend
```

复制环境变量模板：

```bash
cp .env.example .env
```

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

安装依赖并启动：

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

默认后端地址：

```text
http://127.0.0.1:8000
```

### 2. 启动前端 / Start the frontend

进入前端目录：

```bash
cd frontend
```

复制环境变量模板：

```bash
cp .env.example .env
```

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

建议至少配置：

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_API_SIGN_SECRET=replace-with-your-sign-secret
```

安装依赖并启动：

```bash
npm install
npm run dev
```

默认前端地址：

```text
http://localhost:3000
```

## 文档说明 / Documentation

- 前端说明 / Frontend guide: [frontend/README.md](./frontend/README.md)
- 后端说明 / Backend guide: [backend/README.md](./backend/README.md)
- 接口文档 / API document: [docs/API.md](./docs/API.md)

## GitHub 展示建议 / GitHub Showcase Suggestions

建议在 GitHub 仓库描述或 Topics 中加入以下关键词：

Recommended GitHub description keywords / topics:

- weather
- weather-analytics
- vue3
- django
- redis
- mysql
- devops
- graduation-project
- 毕业设计
- fullstack-project

建议仓库名 / Suggested repository name:

```text
weather-analytics-graduation-project
```

## 安全说明 / Security Notes

该公开版本已尽量移除真实密钥、真实部署配置和敏感接口说明，但在正式公开前，仍建议你再次确认：

- 不提交真实 `.env`
- 不提交服务器账号、数据库密码、邮箱授权码
- 不提交历史中曾使用过的真实 JWT 密钥、签名密钥、第三方天气 Key
- 如果生产环境曾暴露过敏感配置，应先完成密钥轮换

This public version has been sanitized as much as possible, but before making the repository public, you should still confirm:

- Do not commit the real `.env`
- Do not commit server credentials, database passwords, or mail auth codes
- Do not commit any real JWT secrets, signing secrets, or third-party API keys ever used in production
- Rotate keys first if any production secrets were previously exposed

## 维护方向 / Future Maintenance Directions

- 优化天气预测模型 / Improve the weather prediction model
- 完善接口文档与部署文档 / Improve API and deployment documentation
- 增加测试与 CI 流程 / Add tests and CI workflows
- 优化后台统计与可视化能力 / Improve admin analytics and visualization
- 持续优化缓存、鉴权与系统性能 / Continue optimizing caching, auth, and performance
