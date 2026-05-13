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

推荐优先使用 Docker Compose。此方式会自动启动 `MySQL`、`Redis`、`Django` 和 `Vue + Nginx`，你只需要修改项目根目录的 `.env`，不需要再单独修改 `backend/.env` 或 `frontend/.env`。

Docker Compose is the recommended way to run this project. It starts `MySQL`, `Redis`, `Django`, and `Vue + Nginx` together. In this mode, you only need to edit the root-level `.env` file. You do not need separate `backend/.env` or `frontend/.env` files.

### Docker 模式下需要改什么 / What to edit in Docker mode

只修改根目录 `.env` 中这些内容：

- `MYSQL_DATABASE` `MYSQL_USER` `MYSQL_PASSWORD` `MYSQL_ROOT_PASSWORD`
- `DJANGO_SECRET_KEY` `JWT_SECRET_KEY`
- `EMAIL_HOST_USER` `EMAIL_HOST_PASSWORD` `DEFAULT_FROM_EMAIL`
- `SENIVERSE_API_KEY` `QWEATHER_PRIVATE_KEY` `QWEATHER_KID` `QWEATHER_SUB`
- `API_SIGN_SECRET` `VITE_API_SIGN_SECRET`
- 如果你改了端口，再调整 `FRONTEND_PORT` `BACKEND_PORT` `MYSQL_PORT` `REDIS_PORT`

容器内部数据库和缓存地址已经写好：

- `DB_HOST=db`
- `REDIS_URL=redis://redis:6379/1`

也就是说，Docker 部署时不需要把数据库主机改成 `localhost`，因为 Django 连接的是 Compose 里启动的 `db` 容器。

### Docker 快速启动 / Quick Start with Docker

```bash
# 克隆项目 / Clone the repository
git clone https://github.com/fly22998-code/weather-analytics-graduation-project.git
cd weather-analytics-graduation-project

# 复制环境变量模板 / Create your environment file
cp .env.example .env

# 编辑根目录 .env / Edit the root .env only
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
> Docker Compose 部署时，只看根目录 `.env.example` / `.env`。
> `backend/.env.example` 和 `frontend/.env.example` 是给本地分开开发准备的，不是 Docker 部署必填文件。

## 本地开发 / Local Development

如果你不使用 Docker，而是想在本机分别启动前后端，请使用这一套配置。此时你需要自己先安装并启动本机 `MySQL` 和 `Redis`。

If you are not using Docker and want to run the backend and frontend separately on your machine, use this workflow instead. In this mode, you need your own local `MySQL` and `Redis` services.

### 本地开发需要改什么 / What to edit in local development

#### Backend

使用 `backend/.env.example`：

- `DB_HOST=localhost`
- `DB_PORT=3306`
- `REDIS_URL=redis://127.0.0.1:6379/1`
- 其余数据库、JWT、邮件、天气 API、签名相关配置按你的本机环境填写

```bash
cd backend
cp .env.example .env
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

#### Frontend

使用 `frontend/.env.example`：

- `VITE_API_BASE_URL=http://localhost:8000`
- `VITE_API_SIGN_SECRET` 需要和后端签名密钥保持一致

```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

### 两种启动方式的区别 / Difference between the two modes

| 模式 / Mode | 使用的配置文件 / Config file | MySQL / Redis 来源 |
| --- | --- | --- |
| Docker Compose 部署 | 根目录 `.env` | Compose 自动启动的容器 |
| 本地分开开发 | `backend/.env` + `frontend/.env` | 你本机自己安装的服务 |

## 文档 / Documentation

- 前端说明 / Frontend Guide: [frontend/README.md](./frontend/README.md)
- 后端说明 / Backend Guide: [backend/README.md](./backend/README.md)
- 接口文档 / API Document: [docs/API.md](./docs/API.md)

## 维护方向 / Future Work

- 优化天气预测模型与回测方式 / Improve prediction model and backtesting
- 完善后台统计与可视化 / Improve admin analytics and visualization
- 增加测试与 CI 流程 / Add tests and CI workflows
- 持续优化缓存、鉴权和部署稳定性 / Improve caching, authentication, and deployment stability
