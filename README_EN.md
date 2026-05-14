<div align="center">

# Weather Analytics Graduation Project

**[中文](./README.md) | English**

A full-stack weather data query and analytics platform built with `Vue 3 + Django`.

[![Vue 3](https://img.shields.io/badge/Vue-3-42b883?style=flat-square&logo=vue.js)](https://vuejs.org/)
[![Django](https://img.shields.io/badge/Django-4.2-0c4b33?style=flat-square&logo=django)](https://www.djangoproject.com/)
[![MySQL](https://img.shields.io/badge/MySQL-8.0-4479a1?style=flat-square&logo=mysql&logoColor=white)](https://www.mysql.com/)
[![Redis](https://img.shields.io/badge/Redis-Cache-dc382d?style=flat-square&logo=redis&logoColor=white)](https://redis.io/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ed?style=flat-square&logo=docker&logoColor=white)](https://docs.docker.com/compose/)

**[Live Demo](https://www.weaquery.com) · [Docker Deployment](#docker-compose-deployment) · [API Docs](./docs/API.md) · [Frontend Guide](./frontend/README.md) · [Backend Guide](./backend/README.md)**

</div>

---

## Contents

- [Demo](#demo)
- [Overview](#overview)
- [Highlights](#highlights)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Docker Compose Deployment](#docker-compose-deployment)
- [Local Development](#local-development)
- [Documentation](#documentation)
- [Future Work](#future-work)

## Demo

| Item | Info |
| --- | --- |
| Live Demo | [www.weaquery.com](https://www.weaquery.com) |
| Contact | `B2431678846` |

---

## Overview

This project is a full-stack weather data query and analytics system. The frontend is built with `Vue 3 + TypeScript + Vite`, while the backend uses `Django + MySQL + Redis`. It integrates third-party weather APIs to provide real-time weather, historical weather, historical air quality, weather prediction, admin management, and traffic statistics.

---

## Highlights

| Module | Description |
| --- | --- |
| Real-time Weather | Query city weather, temperature, humidity, wind, precipitation, and more |
| Historical Weather | Fetch recent 10-day historical weather and hourly records |
| Air Quality | Display historical AQI, pollutant metrics, and trend data |
| Weather Prediction | Predict weather trends based on historical samples and compare with real-time data |
| User System | Login, registration, password recovery, guest mode, and query quota limits |
| Admin Console | User management, traffic statistics, API call analytics, and error statistics |
| Deployment Practice | Docker Compose, Nginx, Gunicorn, MySQL, Redis, and Cloudflare |

---

## Tech Stack

| Area | Technologies |
| --- | --- |
| Frontend | Vue 3, TypeScript, Vite, Vue Router, Axios, Element Plus, ECharts |
| Backend | Python, Django, MySQL, Redis, Gunicorn, PyJWT, django-redis |
| DevOps | Linux, Docker Compose, Nginx, containerd, nerdctl, Cloudflare |

---

## Project Structure

```text
weather-analytics-graduation-project/
  backend/               Django backend service
  frontend/              Vue 3 frontend app
  docs/                  Public API and project documents
  docker-compose.yml     One-command Docker Compose deployment
  .env.example           Root deployment environment template
```

---

## Docker Compose Deployment

Docker Compose is the recommended way to run this project. It starts `MySQL`, `Redis`, `Django`, and `Vue + Nginx` together. In this mode, you only need to edit the root-level `.env` file. You do not need separate `backend/.env` or `frontend/.env` files.

> [!TIP]
> Start with Docker Compose if you want the simplest deployment path. The root `.env` file is the only environment file you need to configure manually in Docker mode.

### What to edit in Docker mode

Only edit these values in the root `.env` file:

- `MYSQL_DATABASE` `MYSQL_USER` `MYSQL_PASSWORD` `MYSQL_ROOT_PASSWORD`
- `DJANGO_SECRET_KEY` `JWT_SECRET_KEY`
- `EMAIL_HOST_USER` `EMAIL_HOST_PASSWORD` `DEFAULT_FROM_EMAIL`
- `SENIVERSE_API_KEY` `QWEATHER_PRIVATE_KEY` `QWEATHER_KID` `QWEATHER_SUB`
- `API_SIGN_SECRET` `VITE_API_SIGN_SECRET`
- If you want to change exposed ports, edit `FRONTEND_PORT` `BACKEND_PORT` `MYSQL_PORT` `REDIS_PORT`

The internal database and cache addresses are already configured:

- `DB_HOST=db`
- `DB_PORT=3306`
- `REDIS_URL=redis://redis:6379/1`

This means you do not need to change the database host to `localhost` in Docker mode, and you do not need to repeatedly fill in `DB_NAME`, `DB_USER`, or `DB_PASSWORD`. The backend reuses `MYSQL_DATABASE`, `MYSQL_USER`, and `MYSQL_PASSWORD` by default.

`MYSQL_PORT` is the host-side mapped port for MySQL, such as `3307` in `3307:3306`. `DB_PORT` is the internal port used by the Django container to connect to the MySQL container, and it should stay `3306` in Docker mode.

### Quick Start with Docker

```bash
# 1. Clone the repository
git clone https://github.com/fly22998-code/weather-analytics-graduation-project.git
cd weather-analytics-graduation-project

# 2. Create the root environment file
cp .env.example .env

# 3. Edit the root .env, choose one editor
# Use nano
nano .env

# Or use vim
vim .env

# 4. Start all services
docker compose up -d --build
```

Note: The current public frontend image can be built in a standard Docker environment without installing extra image-compression build tools such as `gifsicle` or `autoreconf`.

Windows PowerShell:

```powershell
git clone https://github.com/fly22998-code/weather-analytics-graduation-project.git
cd weather-analytics-graduation-project
Copy-Item .env.example .env
notepad .env
docker compose up -d --build
```

Default service URLs:

| Service | URL |
| --- | --- |
| Frontend | `http://localhost:8080` |
| Backend | `http://localhost:8000` |
| MySQL | `localhost:${MYSQL_PORT}` |
| Redis | `localhost:6379` |

> [!IMPORTANT]
> For Docker Compose deployment, only use the root `.env.example` / `.env`.
> `backend/.env.example` and `frontend/.env.example` are for separate local development, not required Docker deployment files.
> Decide the `MYSQL_*` username and password before the first deployment. If the database volume has already been initialized and you later change these values, run `docker compose down -v` and start again.

---

## Local Development

If you are not using Docker and want to run the backend and frontend separately on your machine, use this workflow instead. In this mode, you need your own local `MySQL` and `Redis` services.

### What to edit in local development

#### Backend

Use `backend/.env.example`:

- `DB_HOST=localhost`
- `DB_PORT=3306`
- `REDIS_URL=redis://127.0.0.1:6379/1`
- Fill in the remaining database, JWT, mail, weather API, and request signature settings according to your local environment

```bash
cd backend
cp .env.example .env
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

#### Frontend

Use `frontend/.env.example`:

- `VITE_API_BASE_URL=http://localhost:8000`
- `VITE_API_SIGN_SECRET` must match the backend signing secret

```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

### Difference between the two modes

| Mode | Config file | MySQL / Redis source |
| --- | --- | --- |
| Docker Compose deployment | Root `.env` | Containers started by Compose |
| Separate local development | `backend/.env` + `frontend/.env` | Locally installed services |

---

## Documentation

- Frontend Guide: [frontend/README.md](./frontend/README.md)
- Backend Guide: [backend/README.md](./backend/README.md)
- API Document: [docs/API.md](./docs/API.md)

---

## Future Work

- Improve the weather prediction model and backtesting workflow
- Improve admin analytics and visualization
- Add tests and CI workflows
- Continue improving caching, authentication, and deployment stability
