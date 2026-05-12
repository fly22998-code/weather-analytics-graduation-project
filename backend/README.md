# Weather Analytics Backend

基于 Django 构建的天气数据服务端项目，负责对接第三方天气接口、用户鉴权、游客限流、缓存控制、后台管理和统计接口。

A Django-based backend service for weather data. It handles third-party weather API integration, user authentication, guest rate limiting, cache control, admin management, and statistics APIs.

这份目录是适合公开到 GitHub 的后端版本，重点用于展示接口设计、运维部署和服务端能力。

This directory is a GitHub-ready public backend version, intended for demonstrating API design, operations deployment, and backend capabilities.

## 核心能力 / Core Capabilities

- 实时天气接口 / Real-time weather API
- 历史天气接口 / Historical weather API
- 历史空气质量接口 / Historical air quality API
- 城市搜索接口 / City search API
- 游客 Token 与游客次数限制 / Guest token and guest quota limit
- Access Token / Refresh Token 鉴权 / Access token and refresh token authentication
- 单账号登录控制 / Single-session account control
- 管理后台用户与流量统计接口 / Admin user and traffic statistics APIs
- Redis 缓存与接口签名校验 / Redis caching and request signature verification

## 技术栈 / Tech Stack

- Python
- Django
- MySQL
- Redis
- Gunicorn
- django-cors-headers
- django-redis
- PyJWT
- python-dotenv

## 目录结构 / Project Structure

```text
weather_app/          业务应用 / business app
weather_project/      Django 配置 / Django project config
manage.py             项目入口 / project entry
requirements.txt      依赖列表 / dependency list
```

## 快速启动 / Quick Start

### 1. 安装依赖 / Install dependencies

建议先创建虚拟环境，再安装依赖。

It is recommended to create a virtual environment before installing dependencies.

```bash
pip install -r requirements.txt
```

### 2. 准备环境变量 / Prepare environment variables

复制 `.env.example` 为 `.env`：

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

这份 GitHub 版本已经内置 `.env` 自动加载逻辑。

This GitHub version already includes automatic `.env` loading.

### 3. 配置数据库、Redis、邮件和天气接口参数 / Configure DB, Redis, mail, and weather API settings

至少需要正确填写：

At minimum, configure the following values correctly:

```env
DB_NAME=weather
DB_USER=root
DB_PASSWORD=your-password
DB_HOST=127.0.0.1
DB_PORT=3306
REDIS_URL=redis://127.0.0.1:6379/1
JWT_SECRET_KEY=your-jwt-secret
SENIVERSE_API_KEY=your-seniverse-key
QWEATHER_PRIVATE_KEY=your-qweather-private-key
QWEATHER_KID=your-qweather-kid
QWEATHER_SUB=your-qweather-sub
API_SIGN_SECRET=your-sign-secret
```

### 4. 初始化数据库 / Apply database migrations

```bash
python manage.py migrate
```

### 5. 启动开发服务 / Run development server

```bash
python manage.py runserver
```

默认访问地址通常为 / Default backend URL is usually:

```text
http://127.0.0.1:8000
```

## 生产部署建议 / Production Deployment Suggestions

可以搭配以下方式部署：

Recommended deployment stack:

- Linux 云服务器 / Linux cloud server
- Nginx 反向代理 / Nginx reverse proxy
- Gunicorn 启动 Django / Gunicorn for Django
- MySQL 存储用户与业务数据 / MySQL for user and business data
- Redis 负责缓存、限流与会话辅助状态 / Redis for cache, rate limiting, and session-related state
- Docker / Docker Compose 或 containerd / nerdctl 容器化部署 / Docker, Docker Compose, or containerd with nerdctl

## 环境变量说明 / Environment Variables

重点配置包括：

Key configuration groups include:

- Django Secret Key
- MySQL 连接参数 / MySQL connection settings
- Redis 连接参数 / Redis connection settings
- JWT 密钥 / JWT secret
- 邮件 SMTP 配置 / SMTP mail configuration
- 和风天气 / 心知天气第三方接口密钥 / QWeather and Seniverse API credentials
- 接口签名密钥 / API signing secret

## 本地运行说明 / Local Runtime Notes

- 后端现在会自动读取项目根目录下的 `.env`
- 如果 MySQL 或 Redis 未启动，服务会在对应接口阶段报连接错误
- 如果第三方天气配置未填写，天气相关接口将无法返回完整数据

- The backend now loads `.env` automatically from the project root
- If MySQL or Redis is not running, related APIs will fail with connection errors
- If third-party weather credentials are missing, weather-related APIs will not return complete data

## 安全说明 / Security Notes

这份 GitHub 版本只保留了配置结构，真实密钥请通过环境变量注入，不要直接写入仓库。

This GitHub version only keeps the configuration structure. Real secrets should be injected through environment variables and should never be written directly into the repository.

公开仓库前建议再次确认：

Before publishing the repository, make sure to check the following:

- 已轮换数据库密码、邮箱授权码、JWT 密钥 / Rotate database passwords, email auth codes, and JWT secrets
- 已轮换第三方天气接口密钥 / Rotate third-party weather API keys
- 不提交真实 `.env` / Do not commit the real `.env`
- 不提交上传文件、缓存产物和日志 / Do not commit uploaded files, cache artifacts, or logs

## 项目展示建议 / Showcase Suggestions

如果你准备把这个后端作为个人项目长期维护，建议配套补充：

If you want to maintain this backend as a long-term personal project, consider adding:

- API 文档 / API documentation
- 部署文档 / Deployment documentation
- 缓存设计说明 / Cache design notes
- 鉴权流程说明 / Authentication flow notes
- Redis / MySQL / Nginx 架构图 / Redis, MySQL, and Nginx architecture diagrams
