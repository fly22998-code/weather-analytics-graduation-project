import datetime
import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd
import requests
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from .guest_quota import GUEST_WEATHER_DAILY_LIMIT, guest_weather_quota
from .redis_config import redis_client
from .weather_day import (
    QWEATHER_GEO_URL,
    fetch_weather_now_qweather,
    generate_cache_key,
    get_valid_qweather_token,
    session,
    verify_signature,
)


logger = logging.getLogger(__name__)


def _qweather_base_url():
    return QWEATHER_GEO_URL if "re.qweatherapi" in QWEATHER_GEO_URL else "https://devapi.qweather.com"


def _recent_history_dates():
    today = timezone.localdate()
    return [
        (today - datetime.timedelta(days=offset)).strftime("%Y%m%d")
        for offset in range(1, 11)
    ]


def _seconds_until_midnight():
    now = timezone.localtime()
    tomorrow_midnight = (now + datetime.timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    seconds = (tomorrow_midnight - now).total_seconds()
    return int(max(seconds, 300))


def _session_get(url, **kwargs):
    return session.get(url, **kwargs)


def _build_weather_data(weather_daily, weather_hourly):
    air_quality = weather_daily.get("airQuality") or {}
    weather_text = " / ".join(
        dict.fromkeys(item.get("text", "") for item in weather_hourly[:8] if item.get("text"))
    )
    return [{
        "date": weather_daily.get("date", ""),
        "weather": weather_text or "--",
        "max_temp": weather_daily.get("tempMax", "--"),
        "min_temp": weather_daily.get("tempMin", "--"),
        "wind": weather_hourly[0].get("windDir", "--") if weather_hourly else "--",
        "aqi": air_quality.get("aqi", "--"),
        "aqi_category": air_quality.get("category", "--"),
        "humidity": weather_daily.get("humidity", "--"),
        "pressure": weather_daily.get("pressure", "--"),
        "precip": weather_daily.get("precip", "--"),
    }]


def _air_category_from_aqi(aqi_value):
    try:
        aqi = int(float(aqi_value))
    except (TypeError, ValueError):
        return {"level": "", "category": "--"}

    if aqi <= 50:
        return {"level": "1", "category": "优"}
    if aqi <= 100:
        return {"level": "2", "category": "良"}
    if aqi <= 150:
        return {"level": "3", "category": "轻度污染"}
    if aqi <= 200:
        return {"level": "4", "category": "中度污染"}
    if aqi <= 300:
        return {"level": "5", "category": "重度污染"}
    return {"level": "6", "category": "严重污染"}


def _build_air_summary(air_hourly):
    valid_items = []
    for item in air_hourly or []:
        try:
            valid_items.append((int(float(item.get("aqi"))), item))
        except (TypeError, ValueError):
            continue

    if not valid_items:
        return {"aqi": "--", "level": "", "category": "--", "primary": "--"}

    avg_aqi = round(sum(aqi for aqi, _ in valid_items) / len(valid_items))
    category = _air_category_from_aqi(avg_aqi)
    primary_values = [
        item.get("primary")
        for _, item in valid_items
        if item.get("primary") and item.get("primary") != "NA"
    ]

    return {
        "aqi": str(avg_aqi),
        "level": category["level"],
        "category": category["category"],
        "primary": primary_values[0] if primary_values else "无",
    }


def fetch_historical_weather(location, date_value, lang="zh", unit="m"):
    """
    调用和风天气官方「天气时光机」接口。
    官方上游路径：/v7/historical/weather
    """
    # 与 /weather/user/weather/history 共用缓存，预测页可直接复用前面查过的历史天气。
    cache_key = generate_cache_key("weather_history_qweather", f"{location}:{date_value}:{lang}:{unit}")

    if redis_client:
        try:
            cached_data = redis_client.get(cache_key)
            if cached_data:
                return {"code": 200, "data": json.loads(cached_data)}, 200
        except Exception as exc:
            logger.warning(f"历史天气缓存读取失败: {exc}")

    try:
        token = get_valid_qweather_token()
        response = session.get(
            f"{_qweather_base_url()}/v7/historical/weather",
            params={"location": location, "date": date_value, "lang": lang, "unit": unit},
            headers={"Authorization": f"Bearer {token}", "Accept-Encoding": "gzip"},
            timeout=8,
        )

        if response.status_code != 200:
            logger.error(f"和风历史天气接口HTTP错误: {response.status_code}, {response.text}")
            return {"code": 502, "message": "第三方历史天气服务异常"}, 502

        result = response.json()
        if str(result.get("code")) != "200":
            return {
                "code": 400,
                "message": f"历史天气查询失败，第三方返回码：{result.get('code')}",
            }, 400

        if redis_client:
            redis_client.setex(cache_key, _seconds_until_midnight(), json.dumps(result, ensure_ascii=False))

        return {"code": 200, "data": result}, 200
    except requests.exceptions.Timeout:
        return {"code": 504, "message": "历史天气请求超时，请稍后再试"}, 504
    except Exception as exc:
        logger.error(f"获取历史天气异常: {exc}", exc_info=True)
        return {"code": 500, "message": "服务端内部错误"}, 500


def fetch_historical_air(location, date_value, lang="zh"):
    """
    调用和风天气官方「空气质量时光机」接口。
    官方上游路径：/v7/historical/air
    """
    # 与 /weather/user/weather/history 共用缓存，避免预测页重复请求空气质量时光机。
    cache_key = generate_cache_key("air_history_qweather_v2", f"{location}:{date_value}:{lang}")

    if redis_client:
        try:
            cached_data = redis_client.get(cache_key)
            if cached_data:
                return {"code": 200, "data": json.loads(cached_data)}, 200
        except Exception as exc:
            logger.warning(f"历史空气质量缓存读取失败: {exc}")

    try:
        token = get_valid_qweather_token()
        response = session.get(
            f"{_qweather_base_url()}/v7/historical/air",
            params={"location": location, "date": date_value, "lang": lang},
            headers={"Authorization": f"Bearer {token}", "Accept-Encoding": "gzip"},
            timeout=8,
        )

        if response.status_code != 200:
            logger.warning(f"和风历史空气质量接口HTTP错误: {response.status_code}, {response.text}")
            return {"code": 502, "message": "第三方历史空气质量服务异常"}, 502

        result = response.json()
        if str(result.get("code")) != "200":
            return {
                "code": 400,
                "message": f"历史空气质量查询失败，第三方返回码：{result.get('code')}",
            }, 400

        if redis_client:
            redis_client.setex(cache_key, _seconds_until_midnight(), json.dumps(result, ensure_ascii=False))

        return {"code": 200, "data": result}, 200
    except requests.exceptions.Timeout:
        return {"code": 504, "message": "历史空气质量请求超时，请稍后再试"}, 504
    except Exception as exc:
        logger.error(f"获取历史空气质量异常: {exc}", exc_info=True)
        return {"code": 500, "message": "服务端内部错误"}, 500


def fetch_historical_weather_with_air(location, date_value, lang="zh", unit="m"):
    with ThreadPoolExecutor(max_workers=2, thread_name_prefix="HistoryAliasWorker") as executor:
        weather_future = executor.submit(fetch_historical_weather, location, date_value, lang, unit)
        air_future = executor.submit(fetch_historical_air, location, date_value, lang)
        weather_result, weather_status = weather_future.result()
        air_result, air_status = air_future.result()

    if weather_result.get("code") != 200:
        return weather_result, weather_status

    raw_weather = weather_result.get("data") or {}
    raw_air = (air_result.get("data") or {}) if air_result.get("code") == 200 else {}
    air_hourly = raw_air.get("airHourly") or []
    air_summary = _build_air_summary(air_hourly)

    return {
        "code": 200,
        "data": {
            "weather": raw_weather,
            "air": raw_air,
            "air_error": None if air_result.get("code") == 200 else {
                "code": air_result.get("code", air_status),
                "message": air_result.get("message", "历史空气质量查询失败"),
            },
            "air_summary": air_summary,
        },
    }, 200


def fetch_recent_historical_weather(location, lang="zh", unit="m"):
    dates = _recent_history_dates()
    results = []
    errors = []

    with ThreadPoolExecutor(max_workers=5, thread_name_prefix="HistoryWeatherWorker") as executor:
        future_map = {
            executor.submit(fetch_historical_weather_with_air, location, date_value, lang, unit): date_value
            for date_value in dates
        }

        for future in as_completed(future_map):
            date_value = future_map[future]
            try:
                result, status = future.result()
            except Exception as exc:
                logger.error(f"历史天气批量查询异常({date_value}): {exc}", exc_info=True)
                errors.append({"date": date_value, "code": 500, "message": "服务端内部错误"})
                continue

            if result.get("code") != 200:
                errors.append({
                    "date": date_value,
                    "code": result.get("code", status),
                    "message": result.get("message", "历史天气查询失败"),
                })
                continue

            combined_data = result.get("data") or {}
            raw_data = combined_data.get("weather") or {}
            raw_air = combined_data.get("air") or {}
            air_hourly = raw_air.get("airHourly") or []
            air_summary = combined_data.get("air_summary") or _build_air_summary(air_hourly)
            weather_daily = raw_data.get("weatherDaily") or {}
            weather_hourly = raw_data.get("weatherHourly") or []
            weather_daily["airQuality"] = air_summary
            results.append({
                "date": date_value,
                "fx_link": raw_data.get("fxLink"),
                "weather_daily": weather_daily,
                "weather_hourly": weather_hourly,
                "air_hourly": air_hourly,
                "air_summary": air_summary,
                "weather_data": _build_weather_data(weather_daily, weather_hourly),
                "refer": {
                    "weather": raw_data.get("refer"),
                    "air": raw_air.get("refer"),
                },
            })
            if combined_data.get("air_error"):
                errors.append({
                    "date": date_value,
                    "type": "air",
                    **combined_data["air_error"],
                })

    results.sort(key=lambda item: item["date"], reverse=True)
    return results, errors


def _safe_float(value):
    try:
        number = float(value)
        return number if number == number else None
    except (TypeError, ValueError):
        return None


def _average(values):
    valid = [item for item in values if item is not None]
    return sum(valid) / len(valid) if valid else None


def _median(values):
    valid = sorted(item for item in values if item is not None)
    if not valid:
        return None
    middle = len(valid) // 2
    if len(valid) % 2:
        return valid[middle]
    return (valid[middle - 1] + valid[middle]) / 2


def _clamp(value, min_value, max_value):
    return max(min_value, min(max_value, value))


def _weighted_recent_average(values):
    valid = [item for item in values if item is not None]
    if not valid:
        return None
    weights = [max(1, len(valid) - index) for index in range(len(valid))]
    weight_sum = sum(weights)
    return sum(item * weights[index] for index, item in enumerate(valid)) / weight_sum


def _daily_number_series(history_days, key):
    return [_safe_float((day.get("weather_daily") or {}).get(key)) for day in history_days]


def _series_to_training_frame(values, lag_count=3):
    chronological = [item for item in reversed(values) if item is not None]
    rows = []
    for index in range(lag_count, len(chronological)):
        window = chronological[index - lag_count:index]
        target = chronological[index]
        rolling_mean = sum(window) / len(window)
        trend = window[-1] - window[0]
        rows.append({
            "lag1": window[-1],
            "lag2": window[-2],
            "lag3": window[-3],
            "mean3": rolling_mean,
            "trend3": trend,
            "target": target,
        })
    return pd.DataFrame(rows)


def _solve_linear_regression(feature_rows, targets, ridge_lambda=0.35):
    sample_count = len(feature_rows)
    if sample_count == 0:
        return None
    feature_count = len(feature_rows[0])
    x_matrix = [[1.0] + [float(value) for value in row] for row in feature_rows]
    y_vector = [float(item) for item in targets]

    xtx = [[0.0 for _ in range(feature_count + 1)] for _ in range(feature_count + 1)]
    xty = [0.0 for _ in range(feature_count + 1)]

    for row_index in range(sample_count):
        row = x_matrix[row_index]
        target = y_vector[row_index]
        for i in range(feature_count + 1):
            xty[i] += row[i] * target
            for j in range(feature_count + 1):
                xtx[i][j] += row[i] * row[j]

    for diagonal in range(1, feature_count + 1):
        xtx[diagonal][diagonal] += ridge_lambda

    size = feature_count + 1
    augmented = [xtx[index] + [xty[index]] for index in range(size)]

    for pivot in range(size):
        pivot_row = max(range(pivot, size), key=lambda row_index: abs(augmented[row_index][pivot]))
        if abs(augmented[pivot_row][pivot]) < 1e-8:
            return None
        if pivot_row != pivot:
            augmented[pivot], augmented[pivot_row] = augmented[pivot_row], augmented[pivot]

        pivot_value = augmented[pivot][pivot]
        augmented[pivot] = [value / pivot_value for value in augmented[pivot]]

        for row_index in range(size):
            if row_index == pivot:
                continue
            factor = augmented[row_index][pivot]
            augmented[row_index] = [
                augmented[row_index][col_index] - factor * augmented[pivot][col_index]
                for col_index in range(size + 1)
            ]

    return [augmented[index][-1] for index in range(size)]


def _predict_with_coefficients(coefficients, feature_row):
    if not coefficients:
        return None
    total = coefficients[0]
    for index, value in enumerate(feature_row, start=1):
        total += coefficients[index] * float(value)
    return total


def _train_temperature_autoreg(values):
    frame = _series_to_training_frame(values)
    valid = [item for item in reversed(values) if item is not None]
    if len(valid) < 4:
        return None

    latest_window = valid[-3:]
    latest_features = [
        latest_window[-1],
        latest_window[-2],
        latest_window[-3],
        sum(latest_window) / 3,
        latest_window[-1] - latest_window[0],
    ]

    if frame.empty:
        fallback = latest_window[-1] + (latest_window[-1] - latest_window[-2]) * 0.35
        return {
            "prediction": fallback,
            "train_mae": abs(latest_window[-1] - latest_window[-2]),
            "sample_count": 1,
            "features": latest_features,
        }

    feature_columns = ["lag1", "lag2", "lag3", "mean3", "trend3"]
    feature_rows = frame[feature_columns].values.tolist()
    targets = frame["target"].tolist()
    coefficients = _solve_linear_regression(feature_rows, targets)

    if not coefficients:
        fallback = _weighted_recent_average(list(reversed(valid[-5:]))) or latest_window[-1]
        train_errors = [abs(targets[i] - feature_rows[i][0]) for i in range(len(targets))]
        return {
            "prediction": fallback,
            "train_mae": _average(train_errors) or 3.5,
            "sample_count": len(targets),
            "features": latest_features,
        }

    predictions = [_predict_with_coefficients(coefficients, row) for row in feature_rows]
    train_errors = [abs(targets[index] - predictions[index]) for index in range(len(targets))]
    next_prediction = _predict_with_coefficients(coefficients, latest_features)

    return {
        "prediction": next_prediction,
        "train_mae": _average(train_errors) or 0,
        "sample_count": len(targets),
        "features": latest_features,
        "coefficients": coefficients,
    }


def _estimate_temperature_baseline(values):
    valid = [item for item in values if item is not None]
    if not valid:
        return None

    recent_weighted = _weighted_recent_average(valid[:5]) or _weighted_recent_average(valid)
    stable_median = _median(valid)
    recent3 = _average(valid[:3])
    older3 = _average(valid[3:6])
    recent2 = _average(valid[:2])
    trend = _clamp((recent3 - older3), -3, 3) if recent3 is not None and older3 is not None else 0
    momentum = _clamp((recent2 - recent3), -2, 2) if recent2 is not None and recent3 is not None else 0

    if recent_weighted is None or stable_median is None:
        return valid[0]

    return recent_weighted * 0.56 + stable_median * 0.26 + trend * 0.12 + momentum * 0.06


def _evaluate_temperature_models(values):
    valid = [item for item in values if item is not None]
    if len(valid) < 6:
        baseline_prediction = _estimate_temperature_baseline(values)
        autoreg_model = _train_temperature_autoreg(values)
        autoreg_prediction = autoreg_model["prediction"] if autoreg_model else baseline_prediction
        return {
            "prediction": autoreg_prediction if autoreg_prediction is not None else baseline_prediction,
            "train_mae": autoreg_model["train_mae"] if autoreg_model else 4.0,
            "sample_count": autoreg_model["sample_count"] if autoreg_model else 1,
            "blend_weight": 0.55,
            "baseline_prediction": baseline_prediction,
            "autoreg_prediction": autoreg_prediction,
        }

    chronological = list(reversed(valid))
    baseline_errors = []
    autoreg_errors = []

    for index in range(4, len(chronological)):
        prefix = list(reversed(chronological[:index]))
        target = chronological[index]

        baseline_estimate = _estimate_temperature_baseline(prefix)
        autoreg_model = _train_temperature_autoreg(prefix)
        autoreg_estimate = autoreg_model["prediction"] if autoreg_model else None

        if baseline_estimate is not None:
            baseline_errors.append(abs(target - baseline_estimate))
        if autoreg_estimate is not None:
            autoreg_errors.append(abs(target - autoreg_estimate))

    baseline_mae = _average(baseline_errors) or 4.5
    autoreg_model = _train_temperature_autoreg(values)
    autoreg_prediction = autoreg_model["prediction"] if autoreg_model else None
    autoreg_mae = _average(autoreg_errors) or (autoreg_model["train_mae"] if autoreg_model else 4.5)
    baseline_prediction = _estimate_temperature_baseline(values)

    total_error = baseline_mae + autoreg_mae
    autoreg_weight = 0.5 if total_error <= 0 else baseline_mae / total_error
    autoreg_weight = _clamp(autoreg_weight, 0.35, 0.72)

    if autoreg_prediction is None and baseline_prediction is None:
        return None
    if autoreg_prediction is None:
        final_prediction = baseline_prediction
        final_mae = baseline_mae
    elif baseline_prediction is None:
        final_prediction = autoreg_prediction
        final_mae = autoreg_mae
    else:
        final_prediction = autoreg_prediction * autoreg_weight + baseline_prediction * (1 - autoreg_weight)
        final_mae = autoreg_mae * autoreg_weight + baseline_mae * (1 - autoreg_weight)

    return {
        "prediction": final_prediction,
        "train_mae": final_mae,
        "sample_count": autoreg_model["sample_count"] if autoreg_model else max(len(chronological) - 4, 1),
        "blend_weight": round(autoreg_weight, 2),
        "baseline_prediction": baseline_prediction,
        "autoreg_prediction": autoreg_prediction,
        "baseline_mae": baseline_mae,
        "autoreg_mae": autoreg_mae,
    }


def _build_weather_feature(day):
    daily = day.get("weather_daily") or {}
    air = day.get("air_summary") or {}
    return {
        "tempMax": _safe_float(daily.get("tempMax")) or 0.0,
        "tempMin": _safe_float(daily.get("tempMin")) or 0.0,
        "humidity": _safe_float(daily.get("humidity")) or 0.0,
        "pressure": _safe_float(daily.get("pressure")) or 0.0,
        "precip": _safe_float(daily.get("precip")) or 0.0,
        "aqi": _safe_float(air.get("aqi")) or 0.0,
    }


def _hour_value_from_text(time_text):
    if not time_text or len(time_text) < 13:
        return None
    try:
        return int(str(time_text)[11:13])
    except (TypeError, ValueError):
        return None


def _build_day_context(day, reference_hour=None):
    daily = day.get("weather_daily") or {}
    air = day.get("air_summary") or {}
    hourly = day.get("weather_hourly") or []

    hourly_temps = []
    morning_temps = []
    afternoon_temps = []
    night_temps = []
    hourly_winds = []
    ref_temp = None
    near_ref_temp = None

    for item in hourly:
        temp = _safe_float(item.get("temp"))
        wind_speed = _safe_float(item.get("windSpeed"))
        hour_value = _hour_value_from_text(item.get("time"))

        if temp is not None:
            hourly_temps.append(temp)
            if hour_value is not None:
                if 6 <= hour_value <= 11:
                    morning_temps.append(temp)
                elif 12 <= hour_value <= 17:
                    afternoon_temps.append(temp)
                else:
                    night_temps.append(temp)

                if reference_hour is not None and hour_value == reference_hour:
                    ref_temp = temp
                elif (
                    reference_hour is not None
                    and near_ref_temp is None
                    and abs(hour_value - reference_hour) <= 1
                ):
                    near_ref_temp = temp

        if wind_speed is not None:
            hourly_winds.append(wind_speed)

    temp_max = _safe_float(daily.get("tempMax"))
    temp_min = _safe_float(daily.get("tempMin"))
    if temp_max is None and hourly_temps:
        temp_max = max(hourly_temps)
    if temp_min is None and hourly_temps:
        temp_min = min(hourly_temps)

    return {
        "tempMax": temp_max,
        "tempMin": temp_min,
        "humidity": _safe_float(daily.get("humidity")) or 0.0,
        "pressure": _safe_float(daily.get("pressure")) or 0.0,
        "precip": _safe_float(daily.get("precip")) or 0.0,
        "aqi": _safe_float(air.get("aqi")) or 0.0,
        "avgWind": _average(hourly_winds) or 0.0,
        "avgTemp": _average(hourly_temps) or 0.0,
        "morningTemp": _average(morning_temps) or (_average(hourly_temps) or 0.0),
        "afternoonTemp": _average(afternoon_temps) or (_average(hourly_temps) or 0.0),
        "nightTemp": _average(night_temps) or (_average(hourly_temps) or 0.0),
        "dayRange": (temp_max - temp_min) if temp_max is not None and temp_min is not None else 0.0,
        "refHourTemp": ref_temp if ref_temp is not None else near_ref_temp,
    }


def _context_value(context, key):
    value = context.get(key)
    return float(value) if value is not None else 0.0


def _build_temperature_feature_row(prev1, prev2, prev3, target_key):
    lag1 = _context_value(prev1, target_key)
    lag2 = _context_value(prev2, target_key)
    lag3 = _context_value(prev3, target_key)
    target_avg = _average([lag1, lag2, lag3]) or lag1
    humidity_avg = _average([
        _context_value(prev1, "humidity"),
        _context_value(prev2, "humidity"),
        _context_value(prev3, "humidity"),
    ]) or 0.0
    pressure_avg = _average([
        _context_value(prev1, "pressure"),
        _context_value(prev2, "pressure"),
        _context_value(prev3, "pressure"),
    ]) or 0.0
    precip_avg = _average([
        _context_value(prev1, "precip"),
        _context_value(prev2, "precip"),
        _context_value(prev3, "precip"),
    ]) or 0.0
    aqi_avg = _average([
        _context_value(prev1, "aqi"),
        _context_value(prev2, "aqi"),
        _context_value(prev3, "aqi"),
    ]) or 0.0

    if target_key == "tempMax":
        temp_signal = _context_value(prev1, "afternoonTemp")
    elif target_key == "tempMin":
        temp_signal = _context_value(prev1, "nightTemp")
    elif target_key == "humidity":
        temp_signal = _context_value(prev1, "morningTemp")
    else:
        temp_signal = _context_value(prev1, "avgTemp")

    return [
        lag1,
        lag2,
        lag3,
        target_avg,
        lag1 - lag3,
        _context_value(prev1, "humidity"),
        humidity_avg,
        _context_value(prev1, "pressure"),
        pressure_avg,
        _context_value(prev1, "precip"),
        precip_avg,
        _context_value(prev1, "aqi"),
        aqi_avg,
        _context_value(prev1, "avgWind"),
        _context_value(prev1, "dayRange"),
        _context_value(prev1, "avgTemp"),
        temp_signal,
    ]


def _train_temperature_multifeature(history_days, target_key, reference_hour=None):
    chronological = list(reversed(history_days))
    contexts = [_build_day_context(day, reference_hour=reference_hour) for day in chronological]
    if len(contexts) < 4:
        return None

    feature_rows = []
    targets = []
    for index in range(3, len(contexts)):
        target = contexts[index].get(target_key)
        if target is None:
            continue
        feature_rows.append(
            _build_temperature_feature_row(
                contexts[index - 1],
                contexts[index - 2],
                contexts[index - 3],
                target_key,
            )
        )
        targets.append(float(target))

    if not feature_rows:
        return None

    latest_features = _build_temperature_feature_row(contexts[-1], contexts[-2], contexts[-3], target_key)
    coefficients = _solve_linear_regression(feature_rows, targets, ridge_lambda=1.1)

    if not coefficients:
        return None

    predictions = [_predict_with_coefficients(coefficients, row) for row in feature_rows]
    train_errors = [abs(targets[index] - predictions[index]) for index in range(len(targets))]
    next_prediction = _predict_with_coefficients(coefficients, latest_features)

    return {
        "prediction": next_prediction,
        "train_mae": _average(train_errors) or 0.0,
        "sample_count": len(targets),
        "coefficients": coefficients,
        "features": latest_features,
    }


def _build_analog_signature(contexts):
    values = {}
    for key in ("tempMax", "tempMin", "humidity", "pressure", "precip", "aqi", "avgWind", "avgTemp", "morningTemp", "afternoonTemp", "nightTemp", "dayRange"):
        values[key] = _average([_context_value(context, key) for context in contexts]) or 0.0
    return values


def _analog_distance(sample_signature, current_signature):
    weights = {
        "tempMax": 1.4,
        "tempMin": 1.3,
        "humidity": 0.28,
        "pressure": 0.05,
        "precip": 1.1,
        "aqi": 0.06,
        "avgWind": 0.3,
        "avgTemp": 0.8,
        "morningTemp": 0.55,
        "afternoonTemp": 0.75,
        "nightTemp": 0.55,
        "dayRange": 0.7,
    }
    return sum(abs(sample_signature[key] - current_signature[key]) * weights[key] for key in weights)


def _predict_by_analog_days(history_days, target_key, reference_hour=None):
    chronological = list(reversed(history_days))
    contexts = [_build_day_context(day, reference_hour=reference_hour) for day in chronological]
    if len(contexts) < 4:
        return None

    current_signature = _build_analog_signature(contexts[-3:])
    candidate_samples = []
    for index in range(3, len(contexts)):
        target_value = contexts[index].get(target_key)
        if target_value is None:
            continue
        sample_signature = _build_analog_signature(contexts[index - 3:index])
        distance = _analog_distance(sample_signature, current_signature)
        candidate_samples.append((float(target_value), distance))

    if not candidate_samples:
        return None

    candidate_samples.sort(key=lambda item: item[1])
    top_samples = candidate_samples[:3]
    weighted_sum = 0.0
    total_weight = 0.0
    distance_values = []
    for value, distance in top_samples:
        safe_distance = max(distance, 0.6)
        weight = 1 / safe_distance
        weighted_sum += value * weight
        total_weight += weight
        distance_values.append(safe_distance)

    prediction = weighted_sum / total_weight if total_weight else None

    validation_errors = []
    for index in range(4, len(contexts)):
        validation_signature = _build_analog_signature(contexts[index - 3:index])
        local_candidates = []
        for label_index in range(3, index):
            candidate_target = contexts[label_index].get(target_key)
            if candidate_target is None:
                continue
            candidate_signature = _build_analog_signature(contexts[label_index - 3:label_index])
            local_distance = _analog_distance(candidate_signature, validation_signature)
            local_candidates.append((float(candidate_target), local_distance))
        if not local_candidates:
            continue
        local_candidates.sort(key=lambda item: item[1])
        local_top = local_candidates[:3]
        local_sum = 0.0
        local_weight = 0.0
        for value, distance in local_top:
            safe_distance = max(distance, 0.6)
            analog_weight = 1 / safe_distance
            local_sum += value * analog_weight
            local_weight += analog_weight
        if local_weight:
            local_prediction = local_sum / local_weight
            validation_errors.append(abs((contexts[index].get(target_key) or 0.0) - local_prediction))

    return {
        "prediction": prediction,
        "train_mae": _average(validation_errors) or (_average(distance_values) or 3.0) * 0.45,
        "sample_count": len(top_samples),
        "distance": _average(distance_values) or 0.0,
    }


def _weather_distance(sample_features, current_features):
    weights = {
        "tempMax": 1.6,
        "tempMin": 1.4,
        "humidity": 0.35,
        "pressure": 0.05,
        "precip": 1.2,
        "aqi": 0.08,
    }
    return sum(
        abs(sample_features[key] - current_features[key]) * weights[key]
        for key in weights
    )


def _predict_weather_text_by_similarity(history_days):
    chronological = list(reversed(history_days))
    if len(chronological) < 4:
        return _vote_weather_text(history_days[:5]), 0.0

    current_context = chronological[-3:]
    current_features = {
        key: _average([_build_weather_feature(day)[key] for day in current_context]) or 0.0
        for key in ("tempMax", "tempMin", "humidity", "pressure", "precip", "aqi")
    }

    scored_labels = []
    for index in range(3, len(chronological)):
        train_context = chronological[index - 3:index]
        label_day = chronological[index]
        sample_features = {
            key: _average([_build_weather_feature(day)[key] for day in train_context]) or 0.0
            for key in ("tempMax", "tempMin", "humidity", "pressure", "precip", "aqi")
        }
        label = _vote_weather_text([label_day])
        if label == "--":
            continue
        distance = _weather_distance(sample_features, current_features)
        scored_labels.append((label, distance))

    if not scored_labels:
        return _vote_weather_text(history_days[:5]), 0.0

    scored_labels.sort(key=lambda item: item[1])
    top_samples = scored_labels[:3]
    scores = {}
    for label, distance in top_samples:
        weight = 1 / max(distance, 0.8)
        scores[label] = scores.get(label, 0) + weight

    selected_label = max(scores.items(), key=lambda item: item[1])[0]
    average_distance = _average([item[1] for item in top_samples]) or 0
    return selected_label, average_distance


def _vote_weather_text(history_days):
    scores = {}
    for index, day in enumerate(history_days):
        hourly = day.get("weather_hourly") or []
        texts = []
        for item in hourly[:8]:
            text = item.get("text")
            if text and text not in texts:
                texts.append(text)
        if not texts:
            daily = day.get("weather_daily") or {}
            if daily.get("text"):
                texts.append(daily["text"])
        weight = max(1, len(history_days) - index)
        for text in texts[:2]:
            scores[text] = scores.get(text, 0) + weight
    return max(scores.items(), key=lambda item: item[1])[0] if scores else "--"


def _hourly_temp_series_for_hour(history_days, target_hour):
    series = []
    for day in history_days:
        hourly = day.get("weather_hourly") or []
        matched_temp = None
        near_temp = None
        for item in hourly:
            temp = _safe_float(item.get("temp"))
            if temp is None:
                continue
            time_text = str(item.get("time") or "")
            hour_value = None
            if len(time_text) >= 13:
                try:
                    hour_value = int(time_text[11:13])
                except (TypeError, ValueError):
                    hour_value = None
            if hour_value == target_hour:
                matched_temp = temp
                break
            if near_temp is None and hour_value is not None and abs(hour_value - target_hour) <= 1:
                near_temp = temp
        series.append(matched_temp if matched_temp is not None else near_temp)
    return series


def _predict_reference_hour_temp(history_days, target_hour):
    hour_series = _hourly_temp_series_for_hour(history_days, target_hour)
    valid_series = [item for item in hour_series if item is not None]
    if not valid_series:
        return None

    hour_model = _evaluate_temperature_models(valid_series)
    multifeature_model = _train_temperature_multifeature(history_days, "refHourTemp", reference_hour=target_hour)
    analog_model = _predict_by_analog_days(history_days, "refHourTemp", reference_hour=target_hour)
    baseline_prediction = _estimate_temperature_baseline(valid_series)
    autoreg_prediction = hour_model["prediction"] if hour_model else None
    multifeature_prediction = multifeature_model["prediction"] if multifeature_model else None

    candidates = []
    if baseline_prediction is not None:
        candidates.append((baseline_prediction, (hour_model or {}).get("baseline_mae", 3.4)))
    if autoreg_prediction is not None:
        candidates.append((autoreg_prediction, (hour_model or {}).get("autoreg_mae", (hour_model or {}).get("train_mae", 3.0))))
    if multifeature_prediction is not None:
        candidates.append((multifeature_prediction, multifeature_model["train_mae"]))
    if analog_model and analog_model.get("prediction") is not None:
        candidates.append((analog_model["prediction"], analog_model["train_mae"]))

    if not candidates:
        return None

    weighted_sum = 0.0
    total_weight = 0.0
    mae_values = []
    for prediction_value, mae_value in candidates:
        safe_mae = max(float(mae_value or 3.0), 0.55)
        weight = 1 / safe_mae
        weighted_sum += prediction_value * weight
        total_weight += weight
        mae_values.append(safe_mae)

    final_prediction = weighted_sum / total_weight if total_weight else None
    train_mae = _average(mae_values) or 3.0

    return {
        "temp": round(final_prediction) if final_prediction is not None else None,
        "sample_count": len(valid_series),
        "train_mae": round(train_mae, 2),
        "basis_hour": target_hour,
    }


def build_prediction_from_history(history_days):
    max_temps = _daily_number_series(history_days, "tempMax")
    min_temps = _daily_number_series(history_days, "tempMin")
    humidity = _daily_number_series(history_days, "humidity")
    pressure = _daily_number_series(history_days, "pressure")
    precip = _daily_number_series(history_days, "precip")

    max_model = _evaluate_temperature_models(max_temps)
    min_model = _evaluate_temperature_models(min_temps)
    humidity_model = _evaluate_temperature_models(humidity)
    max_feature_model = _train_temperature_multifeature(history_days, "tempMax")
    min_feature_model = _train_temperature_multifeature(history_days, "tempMin")
    humidity_feature_model = _train_temperature_multifeature(history_days, "humidity")
    max_analog_model = _predict_by_analog_days(history_days, "tempMax")
    min_analog_model = _predict_by_analog_days(history_days, "tempMin")
    humidity_analog_model = _predict_by_analog_days(history_days, "humidity")

    def _merge_predictions(primary_model, feature_model, analog_model=None):
        baseline_prediction = (primary_model or {}).get("baseline_prediction")
        autoreg_prediction = (primary_model or {}).get("autoreg_prediction")
        feature_prediction = (feature_model or {}).get("prediction")
        candidates = []
        if baseline_prediction is not None:
            candidates.append((baseline_prediction, (primary_model or {}).get("baseline_mae", 3.8)))
        if autoreg_prediction is not None:
            candidates.append((autoreg_prediction, (primary_model or {}).get("autoreg_mae", (primary_model or {}).get("train_mae", 3.2))))
        if feature_prediction is not None:
            candidates.append((feature_prediction, (feature_model or {}).get("train_mae", 2.8)))
        if analog_model and analog_model.get("prediction") is not None:
            candidates.append((analog_model["prediction"], analog_model.get("train_mae", 2.7)))
        if not candidates:
            return None, 4.5
        weighted_sum = 0.0
        total_weight = 0.0
        mae_values = []
        for prediction_value, mae_value in candidates:
            safe_mae = max(float(mae_value or 3.0), 0.55)
            weight = 1 / safe_mae
            weighted_sum += prediction_value * weight
            total_weight += weight
            mae_values.append(safe_mae)
        return weighted_sum / total_weight if total_weight else None, (_average(mae_values) or 4.5)

    temp_max, max_combined_mae = _merge_predictions(max_model, max_feature_model, max_analog_model)
    temp_min, min_combined_mae = _merge_predictions(min_model, min_feature_model, min_analog_model)
    predicted_humidity, humidity_combined_mae = _merge_predictions(humidity_model, humidity_feature_model, humidity_analog_model)
    temp_avg = (temp_max + temp_min) / 2 if temp_max is not None and temp_min is not None else None
    weather_text, weather_distance = _predict_weather_text_by_similarity(history_days)
    reference_hour = timezone.localtime().hour
    current_hour_model = _predict_reference_hour_temp(history_days, reference_hour)

    max_valid = [item for item in max_temps if item is not None]
    min_valid = [item for item in min_temps if item is not None]
    recent3_max = _average(max_valid[:3])
    older3_max = _average(max_valid[3:6])
    trend = (recent3_max - older3_max) if recent3_max is not None and older3_max is not None else 0

    max_mae = max_combined_mae if temp_max is not None else (max_model["train_mae"] if max_model else 4.5)
    min_mae = min_combined_mae if temp_min is not None else (min_model["train_mae"] if min_model else 4.5)
    avg_mae = _average([max_mae, min_mae]) or 4.5
    hour_mae = (current_hour_model or {}).get("train_mae", avg_mae)
    humidity_mae = humidity_combined_mae if predicted_humidity is not None else 8.5
    avg_temp_range = _average([
        ((_safe_float((day.get("weather_daily") or {}).get("tempMax")) or 0) - (_safe_float((day.get("weather_daily") or {}).get("tempMin")) or 0))
        for day in history_days
    ]) or 12
    normalized_temp_score = 100 - ((avg_mae / max(avg_temp_range, 6)) * 100 * 0.72)
    hour_score = 100 - ((hour_mae / max(avg_temp_range * 0.65, 4)) * 100 * 0.42)
    temp_confidence = round(_clamp(normalized_temp_score * 0.78 + hour_score * 0.22, 68, 97))
    overall_confidence = round(_clamp(temp_confidence * 0.82 + (100 - humidity_mae * 1.35) * 0.1 + (100 - weather_distance * 2.2) * 0.08, 64, 96))

    return {
        "tempMax": round(temp_max) if temp_max is not None else None,
        "tempMin": round(temp_min) if temp_min is not None else None,
        "tempAvg": round(temp_avg) if temp_avg is not None else None,
        "currentHourTemp": (current_hour_model or {}).get("temp"),
        "currentHour": reference_hour,
        "weatherText": weather_text,
        "confidence": overall_confidence,
        "temperatureConfidence": temp_confidence,
        "humidity": round(predicted_humidity) if predicted_humidity is not None else (round(_average([item for item in humidity if item is not None])) if _average([item for item in humidity if item is not None]) is not None else None),
        "pressure": round(_average([item for item in pressure if item is not None])) if _average([item for item in pressure if item is not None]) is not None else None,
        "precip": round(_average([item for item in precip if item is not None]) or 0, 1),
        "trend": round(trend, 1),
        "model": {
            "name": "autoregressive-ridge-lite",
            "description": "轻量自回归回归模型与稳健统计基线融合 + 相似天气分类",
            "storage": "none",
            "temperature_train_samples": min(max_model["sample_count"] if max_model else 0, min_model["sample_count"] if min_model else 0),
            "temperature_train_mae": round(avg_mae, 2),
            "humidity_train_mae": round(humidity_mae, 2),
            "multifeature_train_mae": round(_average([
                (max_feature_model or {}).get("train_mae"),
                (min_feature_model or {}).get("train_mae"),
            ]) or avg_mae, 2),
            "analog_train_mae": round(_average([
                (max_analog_model or {}).get("train_mae"),
                (min_analog_model or {}).get("train_mae"),
            ]) or avg_mae, 2),
            "reference_hour_train_mae": hour_mae,
            "weather_similarity_distance": round(weather_distance, 2),
            "temperature_blend_weight": round(_average([
                max_model["blend_weight"] if max_model else None,
                min_model["blend_weight"] if min_model else None,
            ]) or 0.5, 2),
        },
    }


# -------------------------- 天气预测接口 --------------------------
@csrf_exempt
@verify_signature
@guest_weather_quota(limit=GUEST_WEATHER_DAILY_LIMIT)
def weather_prediction_view(request):
    """
    前端请求：/weather/user/weather/predict
    后端不落库，优先复用历史天气和实时天气缓存；缓存缺失时只补调缺失数据。
    """
    if request.method != "GET":
        return JsonResponse({"code": 405, "message": "仅支持 GET 请求"}, status=405)

    location = request.GET.get("location", "").strip()
    now_location = request.GET.get("now_location", "").strip() or location
    lang = request.GET.get("lang", "zh").strip() or "zh"
    unit = request.GET.get("unit", "m").strip() or "m"

    if not location:
        return JsonResponse({"code": 400, "message": "请选择城市"}, status=400)
    if ":" in location or "," in location:
        return JsonResponse({"code": 400, "message": "预测历史样本仅支持城市LocationID"}, status=400)
    if unit not in ("m", "i"):
        return JsonResponse({"code": 400, "message": "unit参数仅支持 m 或 i"}, status=400)

    with ThreadPoolExecutor(max_workers=2, thread_name_prefix="WeatherPredictWorker") as executor:
        history_future = executor.submit(fetch_recent_historical_weather, location, lang, unit)
        now_future = executor.submit(fetch_weather_now_qweather, now_location)
        history_days, errors = history_future.result()
        now_result, _ = now_future.result()

    if not history_days:
        first_error = errors[0] if errors else {"code": 502, "message": "预测所需历史天气查询失败"}
        return JsonResponse({
            "code": first_error.get("code", 502),
            "message": first_error.get("message", "预测所需历史天气查询失败"),
            "data": {"errors": errors},
        }, status=502 if first_error.get("code") == 502 else 400)

    prediction = build_prediction_from_history(history_days)
    now_weather = (now_result.get("data") or {}).get("now") if now_result.get("code") == 200 else None
    now_temp = _safe_float((now_weather or {}).get("temp"))
    diff = round(now_temp - prediction["currentHourTemp"]) if now_temp is not None and prediction.get("currentHourTemp") is not None else None

    return JsonResponse({
        "code": 200,
        "message": "预测成功" if now_weather else "预测成功（实时天气暂不可用）",
        "data": {
            "source_api": ["/v7/historical/weather", "/v7/historical/air", "/v7/weather/now"],
            "query_dates": _recent_history_dates(),
            "history_days": history_days,
            "prediction": prediction,
            "now": now_weather,
            "comparison": {
                "temperatureDiff": diff,
                "basis": "当前实时温度 - 预测当前时段参考温度",
            },
            "errors": errors,
            "selected_params": {
                "location": location,
                "now_location": now_location,
                "lang": lang,
                "unit": unit,
            },
        },
    })


# -------------------------- 历史天气查询接口 --------------------------
@csrf_exempt
@verify_signature
@guest_weather_quota(limit=GUEST_WEATHER_DAILY_LIMIT)
def historical_weather_view(request):
    """
    项目后端历史天气接口，命名和实时天气 /weather/user/weather/now 保持一致：
    前端请求：/weather/user/weather/history
    后端内部批量调用和风：/v7/historical/weather
    """
    if request.method != "GET":
        return JsonResponse({"code": 405, "message": "仅支持 GET 请求"}, status=405)

    location = request.GET.get("location", "").strip()
    lang = request.GET.get("lang", "zh").strip() or "zh"
    unit = request.GET.get("unit", "m").strip() or "m"

    if not location:
        return JsonResponse({"code": 400, "message": "请选择城市"}, status=400)
    if ":" in location or "," in location:
        return JsonResponse({"code": 400, "message": "历史天气仅支持城市LocationID"}, status=400)
    if unit not in ("m", "i"):
        return JsonResponse({"code": 400, "message": "unit参数仅支持 m 或 i"}, status=400)

    history_days, errors = fetch_recent_historical_weather(location, lang, unit)
    if not history_days:
        first_error = errors[0] if errors else {"code": 502, "message": "历史天气查询失败"}
        return JsonResponse({
            "code": first_error.get("code", 502),
            "message": first_error.get("message", "历史天气查询失败"),
            "data": {"errors": errors},
        }, status=502 if first_error.get("code") == 502 else 400)

    latest_day = history_days[0]

    return JsonResponse({
        "code": 200,
        "message": "查询成功" if not errors else "部分日期数据暂不可用",
        "data": {
            "source_api": ["/v7/historical/weather", "/v7/historical/air"],
            "query_dates": _recent_history_dates(),
            "history_days": history_days,
            "fx_link": latest_day.get("fx_link"),
            "weather_daily": latest_day.get("weather_daily"),
            "weather_hourly": latest_day.get("weather_hourly"),
            "weather_data": [
                item
                for day in history_days
                for item in day.get("weather_data", [])
            ],
            "refer": latest_day.get("refer"),
            "errors": errors,
            "selected_params": {
                "location": location,
                "lang": lang,
                "unit": unit,
            },
        },
    })


def get_filter_options():
    return {"dates": _recent_history_dates()}


# 兼容旧路由，避免旧页面或脚本立即失效；新前端只调用 historical_weather_view。
weather_view = historical_weather_view
