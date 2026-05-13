# Weather Analytics Graduation Project

> 毕业设计｜基于 `Vue 3 + Django` 的天气数据查询与分析平台。
> Graduation Project | A full-stack weather analytics platform built with `Vue 3 + Django`.

[![Vue 3](https://img.shields.io/badge/Vue-3-42b883?style=flat-square&logo=vue.js)](https://vuejs.org/)
[![Django](https://img.shields.io/badge/Django-4.2-0c4b33?style=flat-square&logo=django)](https://www.djangoproject.com/)
[![MySQL](https://img.shields.io/badge/MySQL-8.0-4479a1?style=flat-square&logo=mysql&logoColor=white)](https://www.mysql.com/)
[![Redis](https://img.shields.io/badge/Redis-Cache-dc382d?style=flat-square&logo=redis&logoColor=white)](https://redis.io/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ed?style=flat-square&logo=docker&logoColor=white)](https://docs.docker.com/compose/)

## 项目展示 / Demo

- 在线展示 / Live Demo: [www.weaquery.com](https://www.weaquery.com)
- 联系方式 / Contact: `B2431678846`

## 项目简介 / Overview

这是一个以前后端分离方式实现的天气数据查询与分析系统。前端使用 `Vue 3 + TypeScript + Vite`，后端使用 `Django + MySQL + Redis`，并对接第三方天气服务实现实时天气、历史天气、历史空气质量、天气预测、后台管理和访问统计等功能。

This project is a full-stack weather data query and analytics system. The frontend is built with `Vue 3 + TypeScript + Vite`, while the backend uses `Django + MySQL + Redis`. It integrates third-party weather APIs to provide real-time weather, historical weather, historical air quality, weather prediction, admin management, and traffic statistics.

## 功能亮点 / Highlights

| 模块 / Module | 说明 / Description |
| --- | --- |
| 实时天气 / Real-time Weather | 查询城市实时天气、温度、湿度、风力、降水等信息 |
| 历史天气 / Historical Weather | 获取近 10 天历史天气与逐小时记录 |
| 空气质量 / Air Quality | 展示历史 AQI、污染物指标与趋势信息 |
| 天气预测 / Weather Prediction | 基于历史样本进行天气趋势预测与实时对比 |
| 用户系统 / User System | 登录、注册、找回密码、游客模式和查询次数限制 |
| 后台管理 / Admin Console | 用户管理、流量统计、接口调用分析和异常统计 |
| 部署实践 / Deployment | Docker Compose、Nginx、Gunicorn、MySQL、Redis、Cloudflare |

## 技术栈 / Tech Stack

| 方向 / Area | 技术 / Technologies |
| --- | --- |
| Frontend | Vue 3, TypeScript, Vite, Vue Router, Axios, Element Plus, ECharts |
| Backend | Python, Django, MySQL, Redis, Gunicorn, PyJWT, django-redis |
| DevOps | Linux, Docker Compose, Nginx, containerd, nerdctl, Cloudflare |

## 项目结构 / Structure

```text
weather-analytics-graduation-project/
  backend/               Django backend service
  frontend/              Vue 3 frontend app
  docs/                  Public API and project documents
  docker-compose.yml     One-command Docker Compose deployment
  .env.example           Root deployment environment template
```

## Docker Compose 部署 / Docker Compose Deployment

推荐使用 Docker Compose 快速部署。项目会自动启动 MySQL、Redis、Django 后端和 Vue 前端，后端容器启动时会自动等待数据库并执行迁移。

Docker Compose is the recommended deployment method. It starts MySQL, Redis, the Django backend, and the Vue frontend. The backend container automatically waits for MySQL and runs migrations on startup.

```bash
# 克隆项目 / Clone the repository
git clone https://github.com/fly22998-code/weather-analytics-graduation-project.git
cd weather-analytics-graduation-project

# 复制环境变量模板 / Create your environment file
cp .env.example .env

# 修改必要配置 / Edit required configuration
nano .env

# 启动全部服务 / Start all services
docker compose up -d --build
```

Windows PowerShell:

```powershell
git clone https://github.com/fly22998-code/weather-analytics-graduation-project.git
cd weather-analytics-graduation-project
Copy-Item .env.example .env
notepad .env
docker compose up -d --build
```

启动后默认访问地址：

| 服务 / Service | 地址 / URL |
| --- | --- |
| Frontend | `http://localhost:8080` |
| Backend | `http://localhost:8000` |
| MySQL | `localhost:3306` |
| Redis | `localhost:6379` |

> [!IMPORTANT]
> `.env.example` 只是模板。启动前请先填写 MySQL、Django、JWT、邮件、第三方天气 API 和签名密钥等配置。
> `.env.example` is only a template. Before starting, fill in MySQL, Django, JWT, mail, third-party weather API, and signing configuration.

## 本地开发 / Local Development

如果你希望分开启动前后端进行开发，可以使用下面的方式。

### Backend

```bash
cd backend
cp .env.example .env
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

### Frontend

```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

## 文档 / Documentation

- 前端说明 / Frontend Guide: [frontend/README.md](./frontend/README.md)
- 后端说明 / Backend Guide: [backend/README.md](./backend/README.md)
- 接口文档 / API Document: [docs/API.md](./docs/API.md)

## 维护方向 / Future Work

- 优化天气预测模型与回测方式 / Improve prediction model and backtesting
- 完善后台统计与可视化 / Improve admin analytics and visualization
- 增加测试与 CI 流程 / Add tests and CI workflows
- 持续优化缓存、鉴权和部署稳定性 / Improve caching, authentication, and deployment stability
