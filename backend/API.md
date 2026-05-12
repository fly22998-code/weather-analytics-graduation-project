# 天气项目公开接口文档 / Public API Overview

> 本文档仅保留适合公开展示的业务接口说明，不包含登录鉴权、签名生成、后台管理等敏感实现细节。
>
> This document only keeps business APIs suitable for public showcase. Sensitive implementation details such as authentication, request signing, and admin APIs are intentionally omitted.

## 1. 项目说明 / Overview

该项目是一个天气数据查询与分析平台，支持城市搜索、实时天气、历史天气和天气趋势预测等功能。

This project is a weather data query and analysis platform that supports city search, real-time weather, historical weather, and weather trend prediction.

## 2. 接口前缀 / Base Path

```text
/weather/
```

本地示例 / Local example:

```text
http://localhost:8000/weather/
```

## 3. 通用返回格式 / Common Response Format

```json
{
  "code": 200,
  "message": "查询成功",
  "data": {}
}
```

## 4. 公开业务接口 / Public Business APIs

### 4.1 城市搜索 / City Search

- **Path**: `/weather/user/location/search`
- **Method**: `GET`
- **Description**: 根据关键字搜索城市 / Search cities by keyword

Query 参数 / Query params:

- `q`: 城市关键字 / city keyword

示例 / Example:

```text
GET /weather/user/location/search?q=hangzhou
```

---

### 4.2 实时天气查询 / Real-Time Weather Query

- **Path**: `/weather/user/weather/now`
- **Method**: `GET`
- **Description**: 查询指定城市的实时天气 / Query real-time weather for a city

Query 参数 / Query params:

- `location`: 城市名称或城市 LocationID / city name or city location ID

示例 / Example:

```text
GET /weather/user/weather/now?location=101210101
```

常见返回字段 / Common response fields:

- 当前温度 / current temperature
- 天气现象 / weather condition
- 湿度 / humidity
- 风速 / wind speed
- 风向 / wind direction
- 体感温度 / feels-like temperature

---

### 4.3 历史天气查询 / Historical Weather Query

- **Path**: `/weather/user/historical/weather/`
- **Method**: `GET`
- **Description**: 查询最近 10 天历史天气 / Query recent 10-day historical weather

Query 参数 / Query params:

- `location`: 城市 LocationID / city location ID
- `lang`: 语言，可选 / language, optional
- `unit`: 单位，可选，`m` 或 `i` / unit, optional, `m` or `i`

示例 / Example:

```text
GET /weather/user/historical/weather/?location=101210101&lang=zh&unit=m
```

常见返回内容 / Common response data:

- 每日最高温 / daily max temperature
- 每日最低温 / daily min temperature
- 日出日落 / sunrise and sunset
- 月相 / moon phase
- 逐小时历史天气 / hourly historical weather
- 空气质量补充数据 / supplementary air-quality data

---

### 4.4 天气预测 / Weather Prediction

- **Path**: `/weather/user/weather/predict`
- **Method**: `GET`
- **Description**: 基于近 10 天历史天气数据生成今日趋势预测 / Generate today's trend prediction based on recent 10-day historical data

Query 参数 / Query params:

- `location`: 城市 LocationID / city location ID
- `lang`: 语言，可选 / language, optional
- `unit`: 单位，可选，`m` 或 `i` / unit, optional, `m` or `i`

示例 / Example:

```text
GET /weather/user/weather/predict?location=101210101&lang=zh&unit=m
```

常见返回内容 / Common response data:

- 预测最高温 / predicted max temperature
- 预测最低温 / predicted min temperature
- 当前时段参考温度 / current-hour reference temperature
- 与实时天气的对比信息 / comparison with current real-time weather
- 模型说明 / model metadata

---

### 4.5 天气聚合查询 / Weather Aggregate Query

- **Path**: `/weather/user/weather/`
- **Method**: `GET`
- **Description**: 项目中的综合天气查询入口 / Aggregated weather query entry used by the project

## 5. 说明 / Notes

- 本文档仅用于项目展示，不作为完整生产环境接口手册。
- 登录、刷新令牌、签名校验、游客令牌、后台管理等接口未在公开文档中展示。
- 如需二次开发，建议在私有环境中维护完整内部接口文档。

- This document is intended for showcase only, not as a complete production API manual.
- Authentication, token refresh, request signing, guest token, and admin APIs are intentionally omitted.
- For secondary development, maintain a full internal API document in a private environment.
