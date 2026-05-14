<div align="center">

# 天气数据查询与分析平台

**🌐 中文 | [English](./README_EN.md)**

毕业设计｜基于 `Vue 3 + Django` 的天气数据查询与分析平台。

[![Vue 3](https://img.shields.io/badge/Vue-3-42b883?style=flat-square&logo=vue.js)](https://vuejs.org/)
[![Django](https://img.shields.io/badge/Django-4.2-0c4b33?style=flat-square&logo=django)](https://www.djangoproject.com/)
[![MySQL](https://img.shields.io/badge/MySQL-8.0-4479a1?style=flat-square&logo=mysql&logoColor=white)](https://www.mysql.com/)
[![Redis](https://img.shields.io/badge/Redis-Cache-dc382d?style=flat-square&logo=redis&logoColor=white)](https://redis.io/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ed?style=flat-square&logo=docker&logoColor=white)](https://docs.docker.com/compose/)

**🌍 [在线展示](https://www.weaquery.com) · 🐳 [Docker 部署](#docker-compose-部署) · 📘 [接口文档](./docs/API.md) · 🖥️ [前端说明](./frontend/README.md) · ⚙️ [后端说明](./backend/README.md)**

</div>

---

## 📌 目录

- [🌍 项目展示](#项目展示)
- [📖 项目简介](#项目简介)
- [✨ 功能亮点](#功能亮点)
- [🧰 技术栈](#技术栈)
- [📁 项目结构](#项目结构)
- [🐳 Docker Compose 部署](#docker-compose-部署)
- [💻 本地开发](#本地开发)
- [📚 文档](#文档)
- [🚧 维护方向](#维护方向)

<a id="项目展示"></a>
## 🌍 项目展示

| 项目 | 信息 |
| --- | --- |
| 在线展示 | [www.weaquery.com](https://www.weaquery.com) |
| 联系方式 | `B2431678846` |

---

<a id="项目简介"></a>
## 📖 项目简介

这是一个以前后端分离方式实现的天气数据查询与分析系统。前端使用 `Vue 3 + TypeScript + Vite`，后端使用 `Django + MySQL + Redis`，并对接第三方天气服务实现实时天气、历史天气、历史空气质量、天气预测、后台管理和访问统计等功能。

---

<a id="功能亮点"></a>
## ✨ 功能亮点

| 模块 | 说明 |
| --- | --- |
| 🌦️ 实时天气 | 查询城市实时天气、温度、湿度、风力、降水等信息 |
| 🕰️ 历史天气 | 获取近 10 天历史天气与逐小时记录 |
| 🍃 空气质量 | 展示历史 AQI、污染物指标与趋势信息 |
| 📈 天气预测 | 基于历史样本进行天气趋势预测与实时对比 |
| 👤 用户系统 | 登录、注册、找回密码、游客模式和查询次数限制 |
| 🛠️ 后台管理 | 用户管理、流量统计、接口调用分析和异常统计 |
| 🚀 部署实践 | Docker Compose、Nginx、Gunicorn、MySQL、Redis、Cloudflare |

---

<a id="技术栈"></a>
## 🧰 技术栈

| 方向 | 技术 |
| --- | --- |
| 前端 | Vue 3, TypeScript, Vite, Vue Router, Axios, Element Plus, ECharts |
| 后端 | Python, Django, MySQL, Redis, Gunicorn, PyJWT, django-redis |
| 运维部署 | Linux, Docker Compose, Nginx, containerd, nerdctl, Cloudflare |

---

<a id="项目结构"></a>
## 📁 项目结构

```text
weather-analytics-graduation-project/
  backend/               Django 后端服务
  frontend/              Vue 3 前端应用
  docs/                  公开接口文档和项目文档
  docker-compose.yml     Docker Compose 一键部署配置
  .env.example           根目录部署环境变量模板
```

---

<a id="docker-compose-部署"></a>
## 🐳 Docker Compose 部署

推荐优先使用 Docker Compose。此方式会自动启动 `MySQL`、`Redis`、`Django` 和 `Vue + Nginx`，你只需要修改项目根目录的 `.env`，不需要再单独修改 `backend/.env` 或 `frontend/.env`。

> [!TIP]
> 推荐从 Docker Compose 开始部署。根目录 `.env` 是 Docker 模式唯一需要手动配置的环境文件。

### Docker 模式下需要改什么

只修改根目录 `.env` 中这些内容：

- `MYSQL_DATABASE` `MYSQL_USER` `MYSQL_PASSWORD` `MYSQL_ROOT_PASSWORD`
- `DJANGO_SECRET_KEY` `JWT_SECRET_KEY`
- `EMAIL_HOST_USER` `EMAIL_HOST_PASSWORD` `DEFAULT_FROM_EMAIL`
- `SENIVERSE_API_KEY` `QWEATHER_PRIVATE_KEY` `QWEATHER_KID` `QWEATHER_SUB`
- `API_SIGN_SECRET` `VITE_API_SIGN_SECRET`
- 如果你改了端口，再调整 `FRONTEND_PORT` `BACKEND_PORT` `MYSQL_PORT` `REDIS_PORT`

容器内部数据库和缓存地址已经写好：

- `DB_HOST=db`
- `DB_PORT=3306`
- `REDIS_URL=redis://redis:6379/1`

也就是说，Docker 部署时不需要把数据库主机改成 `localhost`，也不需要重复填写 `DB_NAME`、`DB_USER`、`DB_PASSWORD`。后端会默认复用 `MYSQL_DATABASE`、`MYSQL_USER`、`MYSQL_PASSWORD`。

`MYSQL_PORT` 是宿主机访问 MySQL 的映射端口，例如 `3307:3306` 中的 `3307`。`DB_PORT` 是 Django 容器连接 MySQL 容器的内部端口，Docker 模式下固定保持 `3306`。

### Docker 快速启动

```bash
# 1. 克隆项目
git clone https://github.com/fly22998-code/weather-analytics-graduation-project.git
cd weather-analytics-graduation-project

# 2. 生成根目录环境变量文件
cp .env.example .env

# 3. 编辑根目录 .env（二选一）
# 使用 nano
nano .env

# 或使用 vim
vim .env

# 4. 启动全部服务
docker compose up -d --build
```

说明：当前公开版本前端镜像可直接在常规 Docker 环境中构建，不需要额外安装 `gifsicle`、`autoreconf` 等图片压缩编译工具。

Windows PowerShell:

```powershell
git clone https://github.com/fly22998-code/weather-analytics-graduation-project.git
cd weather-analytics-graduation-project
Copy-Item .env.example .env
notepad .env
docker compose up -d --build
```

启动后默认访问地址：

| 服务 | 地址 |
| --- | --- |
| 前端 | `http://localhost:8080` |
| 后端 | `http://localhost:8000` |
| MySQL | `localhost:${MYSQL_PORT}` |
| Redis | `localhost:6379` |

> [!IMPORTANT]
> Docker Compose 部署时，只看根目录 `.env.example` / `.env`。
> `backend/.env.example` 和 `frontend/.env.example` 是给本地分开开发准备的，不是 Docker 部署必填文件。
> 首次部署前请先确定 `MYSQL_*` 用户名和密码；如果数据库卷已经初始化后又修改这些值，需要执行 `docker compose down -v` 后重新启动。

---

<a id="本地开发"></a>
## 💻 本地开发

如果你不使用 Docker，而是想在本机分别启动前后端，请使用这一套配置。此时你需要自己先安装并启动本机 `MySQL` 和 `Redis`。

### 本地开发需要改什么

#### 后端

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

#### 前端

使用 `frontend/.env.example`：

- `VITE_API_BASE_URL=http://localhost:8000`
- `VITE_API_SIGN_SECRET` 需要和后端签名密钥保持一致

```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

### 两种启动方式的区别

| 模式 | 使用的配置文件 | MySQL / Redis 来源 |
| --- | --- | --- |
| Docker Compose 部署 | 根目录 `.env` | Compose 自动启动的容器 |
| 本地分开开发 | `backend/.env` + `frontend/.env` | 你本机自己安装的服务 |

---

<a id="文档"></a>
## 📚 文档

- 前端说明：[frontend/README.md](./frontend/README.md)
- 后端说明：[backend/README.md](./backend/README.md)
- 接口文档：[docs/API.md](./docs/API.md)

---

<a id="维护方向"></a>
## 🚧 维护方向

- 优化天气预测模型与回测方式
- 完善后台统计与可视化
- 增加测试与 CI 流程
- 持续优化缓存、鉴权和部署稳定性
