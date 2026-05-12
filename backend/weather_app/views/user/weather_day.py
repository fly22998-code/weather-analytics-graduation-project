import requests
import logging
import hashlib
import json
import jwt
import traceback
import datetime
from urllib.parse import urlparse
from functools import wraps, lru_cache
from concurrent.futures import ThreadPoolExecutor, as_completed
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from requests.adapters import HTTPAdapter
from .redis_config import *
from .user_utils import *
from .guest_quota import GUEST_WEATHER_DAILY_LIMIT, guest_weather_quota

logger = logging.getLogger(__name__)

# --- 配置区 ---
QWEATHER_GEO_URL = "https://nc5ctva2ht.re.qweatherapi.com"
SENIVERSE_API_KEY = getattr(settings, 'SENIVERSE_API_KEY', '')
SENIVERSE_BASE_URL = 'https://api.seniverse.com/v3'

# 全局 HTTP Session
session = requests.Session()
adapter = HTTPAdapter(pool_connections=10, pool_maxsize=20, max_retries=2)
session.mount('https://', adapter)
session.mount('http://', adapter)

# 全局线程池
GLOBAL_EXECUTOR = ThreadPoolExecutor(max_workers=10, thread_name_prefix="WeatherWorker")


def _session_get(url, **kwargs):
    return session.get(url, **kwargs)


# ===================== 签名校验装饰器 =====================
def verify_signature(func):
    @wraps(func)
    def wrapper(request, *args, **kwargs):
        verify_result, verify_msg = verify_signed_headers(request, request.GET.dict(), require_session_key=True)
        if not verify_result:
            if verify_msg in ("游客签名已失效", "游客身份无效，请重新获取游客Token", "游客Token类型无效", "游客身份无效"):
                return JsonResponse({'code': 4016, 'message': '游客身份无效，请重新获取游客Token'}, status=401)
            if verify_msg == "账号已在其他设备登录":
                return JsonResponse({
                    'code': 4017,
                    'message': '账号已在其他设备登录，当前会话已切换为游客模式'
                }, status=401)
            if verify_msg in ("Access Token 已过期", "会话签名已失效", "缺少会话签名标识", "Token 无效", "Token 类型无效"):
                return JsonResponse({'code': 4012, 'message': 'Access Token 已过期'}, status=401)
            status = 500 if verify_msg == "内部校验服务异常" else 403
            return JsonResponse({'code': status, 'message': verify_msg}, status=status)

        return func(request, *args, **kwargs)
    
    return wrapper

# ===================== 工具函数 =====================

@lru_cache(maxsize=1)
def load_private_key_cached(raw_key_str):
    clean_key = raw_key_str.strip().replace("\\n", "\n")
    return serialization.load_pem_private_key(
        clean_key.encode('utf-8'),
        password=None,
        backend=default_backend()
    )

def generate_cache_key(prefix: str, value: str) -> str:
    if not value: return ""
    clean_val = str(value).strip().lower() # 增加 str() 强转防止报错
    return f"weather:{prefix}:{hashlib.md5(clean_val.encode('utf-8')).hexdigest()}"


def normalize_search_keyword(keyword: str) -> str:
    return " ".join(str(keyword).strip().split())


def build_location_path(item: dict) -> str:
    parts = [
        str(item.get("country") or "").strip(),
        str(item.get("adm1") or "").strip(),
        str(item.get("adm2") or "").strip(),
    ]
    return ", ".join(part for part in parts if part)


def simplify_location_item(item: dict) -> dict:
    return {
        "id": str(item.get("id") or "").strip(),
        "name": str(item.get("name") or "").strip(),
        "country": str(item.get("country") or "").strip(),
        "adm1": str(item.get("adm1") or "").strip(),
        "adm2": str(item.get("adm2") or "").strip(),
        "lat": str(item.get("lat") or "").strip(),
        "lon": str(item.get("lon") or "").strip(),
        "path": build_location_path(item),
    }


def serialize_location_results(items, limit: int = 12):
    simplified_results = []
    seen = set()

    for item in items or []:
        simplified = simplify_location_item(item)
        unique_key = simplified["id"] or f'{simplified["lat"]}:{simplified["lon"]}:{simplified["name"]}'
        if not unique_key or unique_key in seen:
            continue

        seen.add(unique_key)
        simplified_results.append(simplified)

        if len(simplified_results) >= limit:
            break

    return simplified_results

def is_invalid_first_char(text: str) -> bool:
    if not text or not text.strip(): return False
    first_char = text.strip()[0]
    return not (first_char.isalnum() or '\u4e00' <= first_char <= '\u9fa5')

def fetch_data_with_cache(api_suffix: str, params: dict, cache_key: str, expire_time: int):
    # 1. 读缓存
    if redis_client:
        try:
            cached_data = redis_client.get(cache_key)
            if cached_data:
                return {'code': 200, 'data': json.loads(cached_data)}, 200
        except Exception as e:
            logger.warning(f"Redis 读取失败: {e}")

    # 2. 调用 API
    try:
        if not SENIVERSE_API_KEY:
            return {'code': 500, 'data': None}, 500

        url = f"{SENIVERSE_BASE_URL}{api_suffix}"
        req_params = {'key': SENIVERSE_API_KEY, 'language': 'zh-Hans'}
        req_params.update(params)

        response = session.get(url, params=req_params, timeout=5)
        
        if response.status_code != 200:
            logger.error(f"第三方API错误({api_suffix}): {response.text}")
            return {'code': 400, 'data': None}, 400

        result = response.json()

        # 3. 写缓存
        if redis_client:
            try:
                redis_client.setex(cache_key, expire_time, json.dumps(result))
            except Exception as e:
                logger.warning(f"Redis 写入失败: {e}")

        return {'code': 200, 'data': result}, 200

    except requests.exceptions.Timeout:
        return {'code': 504, 'data': None}, 504
    except Exception as e:
        logger.error(f"系统内部错误({api_suffix}): {e}")
        return {'code': 500, 'data': None}, 500

def get_seconds_until_midnight():
    now = timezone.localtime()
    tomorrow_midnight = (now + datetime.timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    seconds = (tomorrow_midnight - now).total_seconds()
    return int(max(seconds, 300))

def get_seconds_until_next_hour():
    now = timezone.now()
    next_hour = now.replace(minute=0, second=0, microsecond=0) + datetime.timedelta(hours=1)
    seconds = (next_hour - now).total_seconds()
    return int(max(seconds, 60))

# ===================== 业务数据获取函数 =====================

def fetch_sun_data(location: str):
    """
    获取日出日落数据 (和风天气 QWeather)
    API文档: /v7/astronomy/sun
    """
    expire_time = get_seconds_until_midnight()
    
    # 和风天文接口需要 YYYYMMDD 格式的日期
    now_date = timezone.now()
    today_str_api = now_date.strftime('%Y%m%d')
    tomorrow_str_api = (now_date + datetime.timedelta(days=1)).strftime('%Y%m%d')
    
    # 用于返回给前端的 YYYY-MM-DD 格式
    today_str_format = now_date.strftime('%Y-%m-%d')
    tomorrow_str_format = (now_date + datetime.timedelta(days=1)).strftime('%Y-%m-%d')

    cache_key = generate_cache_key('sun_qweather', f"{location}_{today_str_api}")

    # 1. 读缓存
    if redis_client:
        try:
            cached_data = redis_client.get(cache_key)
            if cached_data:
                return {'code': 200, 'data': json.loads(cached_data)}, 200
        except Exception:
            pass

    # 2. 调用 API
    try:
        token = get_valid_qweather_token()
        
        # --- 位置参数处理 ---
        req_loc = location
        if ":" in location:
            parts = location.split(":")
            if len(parts) >= 2 and parts[0] != 'undefined':
                req_loc = f"{parts[1]},{parts[0]}"
        
        # --- URL 构造 ---
        base_url = QWEATHER_GEO_URL
        if "re.qweatherapi" not in base_url:
            base_url = "https://devapi.qweather.com"
        api_url = f"{base_url}/v7/astronomy/sun"

        headers = {"Authorization": f"Bearer {token}", "Accept-Encoding": "gzip"}
        
        # 和风天文接口一次只能查一天，但今天/明天两次请求可以并发执行。
        with ThreadPoolExecutor(max_workers=2, thread_name_prefix="SunWeatherWorker") as executor:
            future_today = executor.submit(
                _session_get,
                api_url,
                params={'location': req_loc, 'date': today_str_api, 'lang': 'zh'},
                headers=headers,
                timeout=5
            )
            future_tomorrow = executor.submit(
                _session_get,
                api_url,
                params={'location': req_loc, 'date': tomorrow_str_api, 'lang': 'zh'},
                headers=headers,
                timeout=5
            )
            res_today = future_today.result()
            res_tomorrow = future_tomorrow.result()
        
        if res_today.status_code != 200 or res_tomorrow.status_code != 200:
            logger.error(f"和风天文接口错误: 今天{res_today.status_code}, 明天{res_tomorrow.status_code}")
            return {'code': 400, 'message': '天文数据获取失败'}, 400

        data_today = res_today.json()
        data_tomorrow = res_tomorrow.json()

        if str(data_today.get('code')) != '200' or str(data_tomorrow.get('code')) != '200':
            return {'code': 400, 'message': f"和风天文错误: {data_today.get('code')}"}, 400

        # 3. 数据转换：伪装成以前心知天气的结构，这样前端 Vue 代码一行都不用改！
        def extract_time(iso_time_str):
            # 将和风的 "2021-02-16T07:05+08:00" 转换为 "07:05"
            if not iso_time_str: return '--:--'
            return iso_time_str[11:16]

        # 提取时区偏移，例如 "+08:00"
        tz_offset = "+08:00"
        if data_today.get('sunrise') and len(data_today['sunrise']) >= 6:
            tz_offset = data_today['sunrise'][-6:]

        mapped_data = {
            "location": {
                "timezone_offset": tz_offset
            },
            "sun": [
                {
                    "date": today_str_format,
                    "sunrise": extract_time(data_today.get('sunrise')),
                    "sunset": extract_time(data_today.get('sunset'))
                },
                {
                    "date": tomorrow_str_format,
                    "sunrise": extract_time(data_tomorrow.get('sunrise')),
                    "sunset": extract_time(data_tomorrow.get('sunset'))
                }
            ]
        }

        # 4. 写缓存
        if redis_client:
            redis_client.setex(cache_key, expire_time, json.dumps(mapped_data))

        return {'code': 200, 'data': mapped_data}, 200

    except requests.exceptions.Timeout:
        return {'code': 504, 'message': '天文请求超时'}, 504
    except Exception as e:
        logger.error(f"获取日出日落异常: {e}")
        return {'code': 500, 'message': '服务端内部错误'}, 500

def fetch_hourly_data(location: str):
    expire_time = get_seconds_until_next_hour()
    cache_key = generate_cache_key('weather_hourly_qweather', location)

    if redis_client:
        try:
            cached_data = redis_client.get(cache_key)
            if cached_data:
                return {'code': 200, 'data': json.loads(cached_data)}, 200
        except Exception:
            pass

    try:
        token = get_valid_qweather_token()
        
        req_loc = location
        if ":" in location:
            parts = location.split(":")
            if len(parts) >= 2 and parts[0] != 'undefined':
                req_loc = f"{parts[1]},{parts[0]}"
        
        api_url = f"{QWEATHER_GEO_URL}/v7/weather/24h"
        if "re.qweatherapi" not in QWEATHER_GEO_URL:
             api_url = "https://devapi.qweather.com/v7/weather/24h"

        response = session.get(
            api_url, 
            params={'location': req_loc, 'lang': 'zh'}, 
            headers={"Authorization": f"Bearer {token}", "Accept-Encoding": "gzip"}, 
            timeout=5
        )
        
        if response.status_code != 200:
            logger.error(f"和风逐小时接口错误: {response.text}")
            return {'code': response.status_code, 'message': '第三方接口异常'}, response.status_code

        res_json = response.json()
        if res_json.get('code') != '200':
             return {'code': 400, 'message': f"和风错误: {res_json.get('code')}"}, 400

        if redis_client:
            redis_client.setex(cache_key, expire_time, json.dumps(res_json))

        return {'code': 200, 'data': res_json}, 200

    except requests.exceptions.Timeout:
        return {'code': 504, 'message': '请求超时'}, 504
    except Exception as e:
        logger.error(f"获取逐小时天气异常: {e}")
        return {'code': 500, 'message': '服务端内部错误'}, 500

# ===================== Token 管理 =====================

def get_valid_qweather_token():
    kid = getattr(settings, 'QWEATHER_KID', None)
    sub = getattr(settings, 'QWEATHER_SUB', None)
    raw_key = getattr(settings, 'QWEATHER_PRIVATE_KEY', None)

    if not all([kid, sub, raw_key]):
        raise ValueError("QWeather configuration is missing")

    cache_key = "qweather:jwt_token"
    if redis_client:
        try:
            token = redis_client.get(cache_key)
            if token: return token.decode('utf-8') if isinstance(token, bytes) else token
        except Exception:
            pass

    try:
        private_key = load_private_key_cached(raw_key)

        now = int(time.time())
        payload = {
            "sub": sub,
            "iat": now - 30,
            "exp": now + 3600
        }
        
        new_token = jwt.encode(
            payload, 
            private_key, 
            algorithm="EdDSA", 
            headers={"alg": "EdDSA", "kid": kid}
        )

        if redis_client:
            redis_client.setex(cache_key, 3000, new_token)

        return new_token

    except Exception as e:
        logger.error(f"JWT Gen Error: {str(e)}")
        raise RuntimeError(f"Failed to generate QWeather Token: {e}")

# ===================== 核心接口 =====================


def is_ratelimited_by_ip(request, limit=50, period=60):
    """
    检查 IP 是否超过频率限制
    :param request: Django request 对象
    :param limit: 周期内允许的最大次数 (20)
    :param period: 时间周期 (60秒)
    """
    # 1. 统一调用独立的 IP 获取工具，保证获取真实公网 IP
    ip = get_client_ip(request)

    # 2. 生成唯一的 Redis Key
    cache_key = f"ratelimit:weather_api:{generate_cache_key('ip', ip)}"

    # 3. 执行 Redis 递增与过期检查
    try:
        current_usage = redis_client.incr(cache_key)
        
        # 4. 如果是该周期的第一次调用，设置过期时间
        if current_usage == 1:
            redis_client.expire(cache_key, period)
            
        # 5. 判断是否超过限制
        if current_usage > limit:
            return True, current_usage
            
        return False, current_usage
    except Exception as e:
        # 如果 Redis 挂了，记录带有具体 IP 的日志，并默认放行保证核心业务可用
        logger.error(f"Rate limit check failed for IP {ip}: {e}")
        return False, 0

def ratelimit_ip(limit=20, period=60):
    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            limited, count = is_ratelimited_by_ip(request, limit, period)
            if limited:
                return JsonResponse({
                    'code': 429,
                    'message': f'请求过于频繁，请在{period}秒后再试',
                    'detail': f'当前频率: {count}/{limit}'
                }, status=429)
            return func(request, *args, **kwargs)
        return wrapper
    return decorator
@csrf_exempt
@verify_signature
@guest_weather_quota(limit=GUEST_WEATHER_DAILY_LIMIT)
def weather_now(request):
    if request.method != 'GET':
        return JsonResponse({'code': 405, 'message': '仅支持 GET 请求'}, status=405)

    location = request.GET.get('location', '').strip()
    if not location:
        return JsonResponse({'code': 400, 'message': '请传入城市ID或名称'}, status=400)
    if is_invalid_first_char(location):
        return JsonResponse({'code': 400, 'message': '城市名称或ID格式不正确', 'data': {}}, status=400)

    weather_cache_key = generate_cache_key('weather_now', location)
    
    # === 并发请求 ===
    # 1. 实时天气 (QWeather - 使用经纬度/城市ID)
    future_weather = GLOBAL_EXECUTOR.submit(fetch_weather_now_qweather, location)
    # 2. 日出日落 (Seniverse)
    future_sun = GLOBAL_EXECUTOR.submit(fetch_sun_data, location)
    # 3. 逐小时天气 (QWeather)
    future_hourly = GLOBAL_EXECUTOR.submit(fetch_hourly_data, location)
    # 4. [新增] 实时空气质量 (QWeather)
    future_aqi = GLOBAL_EXECUTOR.submit(fetch_air_quality, location)

    # === 获取结果 ===
    weather_result, weather_status = future_weather.result()
    sun_result, sun_status = future_sun.result()
    hourly_result, hourly_status = future_hourly.result()
    aqi_result, aqi_status = future_aqi.result() # 获取 AQI 结果

    final_data = {
        'weather': weather_result.get('data'),
        'sun': sun_result.get('data'),
        'hourly': hourly_result.get('data'),
        'air_quality': aqi_result.get('data'), # 新增字段
    }

    final_code = weather_result['code']
    final_message = ''
    
    if final_code == 200:
        final_message = '查询成功'
        errors = []
        if sun_result['code'] != 200: errors.append('日出日落')
        if hourly_result['code'] != 200: errors.append('逐小时预报')
        if aqi_result['code'] != 200: errors.append('空气质量') # 错误提示
        
        if errors:
            final_message += f"（{'、'.join(errors)}数据暂不可用）"
    else:
        final_message = weather_result.get('message', '数据查询失败')

    return JsonResponse({
        'code': final_code,
        'message': final_message,
        'data': final_data
    }, status=weather_status)


def _qweather_api_base_url():
    return QWEATHER_GEO_URL if "re.qweatherapi" in QWEATHER_GEO_URL else "https://devapi.qweather.com"


def _recent_historical_dates():
    today = timezone.localdate()
    return [
        (today - datetime.timedelta(days=offset)).strftime("%Y%m%d")
        for offset in range(1, 11)
    ]


def fetch_weather_history_qweather(location: str, date_value: str, lang="zh", unit="m"):
    """
    获取单日历史天气数据。
    项目接口走 /weather/user/weather/history，上游官方接口走 /v7/historical/weather。
    """
    cache_key = generate_cache_key("weather_history_qweather", f"{location}:{date_value}:{lang}:{unit}")

    if redis_client:
        try:
            cached_data = redis_client.get(cache_key)
            if cached_data:
                return {'code': 200, 'data': json.loads(cached_data)}, 200
        except Exception:
            pass

    try:
        token = get_valid_qweather_token()
        response = session.get(
            f"{_qweather_api_base_url()}/v7/historical/weather",
            params={"location": location, "date": date_value, "lang": lang, "unit": unit},
            headers={"Authorization": f"Bearer {token}", "Accept-Encoding": "gzip"},
            timeout=8
        )

        if response.status_code != 200:
            logger.error(f"和风历史天气接口错误: {response.status_code}, {response.text}")
            return {'code': response.status_code, 'message': '第三方历史天气接口异常'}, response.status_code

        res_json = response.json()
        if res_json.get('code') != '200':
            return {'code': 400, 'message': f"和风错误: {res_json.get('code')}"}, 400

        if redis_client:
            redis_client.setex(cache_key, get_seconds_until_midnight(), json.dumps(res_json, ensure_ascii=False))

        return {'code': 200, 'data': res_json}, 200

    except requests.exceptions.Timeout:
        return {'code': 504, 'message': '历史天气请求超时'}, 504
    except Exception as e:
        logger.error(f"获取历史天气异常: {e}", exc_info=True)
        return {'code': 500, 'message': '服务端内部错误'}, 500


def _air_category_from_aqi(aqi):
    try:
        value = int(float(aqi))
    except (TypeError, ValueError):
        return {'aqi': '--', 'level': '', 'category': '--', 'primary': '--'}

    if value <= 50:
        level, category = '1', '优'
    elif value <= 100:
        level, category = '2', '良'
    elif value <= 150:
        level, category = '3', '轻度污染'
    elif value <= 200:
        level, category = '4', '中度污染'
    elif value <= 300:
        level, category = '5', '重度污染'
    else:
        level, category = '6', '严重污染'

    return {'aqi': str(value), 'level': level, 'category': category, 'primary': '--'}


def _build_air_summary(air_hourly):
    valid_items = []
    for item in air_hourly or []:
        try:
            aqi = int(float(item.get('aqi')))
        except (TypeError, ValueError):
            continue
        valid_items.append((aqi, item))

    if not valid_items:
        return _air_category_from_aqi(None)

    average_aqi = round(sum(aqi for aqi, _ in valid_items) / len(valid_items))
    summary = _air_category_from_aqi(average_aqi)

    primary_items = [
        item.get('primary')
        for _, item in valid_items
        if item.get('primary') and item.get('primary') != 'NA'
    ]
    if primary_items:
        summary['primary'] = max(set(primary_items), key=primary_items.count)

    return summary


def fetch_air_history_qweather(location: str, date_value: str, lang="zh"):
    """
    获取单日历史空气质量数据。
    这是历史天气的补充数据，失败时由调用方降级为空 AQI，不影响天气展示。
    """
    cache_key = generate_cache_key("air_history_qweather_v2", f"{location}:{date_value}:{lang}")

    if redis_client:
        try:
            cached_data = redis_client.get(cache_key)
            if cached_data:
                return {'code': 200, 'data': json.loads(cached_data)}, 200
        except Exception:
            pass

    try:
        token = get_valid_qweather_token()
        response = session.get(
            f"{_qweather_api_base_url()}/v7/historical/air",
            params={"location": location, "date": date_value, "lang": lang},
            headers={"Authorization": f"Bearer {token}", "Accept-Encoding": "gzip"},
            timeout=8
        )

        if response.status_code != 200:
            logger.warning(f"和风历史空气质量接口错误: {response.status_code}, {response.text}")
            return {'code': response.status_code, 'message': '第三方历史空气质量接口异常'}, response.status_code

        res_json = response.json()
        if res_json.get('code') != '200':
            return {'code': 400, 'message': f"和风空气质量错误: {res_json.get('code')}"}, 400

        if redis_client:
            redis_client.setex(cache_key, get_seconds_until_midnight(), json.dumps(res_json, ensure_ascii=False))

        return {'code': 200, 'data': res_json}, 200

    except requests.exceptions.Timeout:
        return {'code': 504, 'message': '历史空气质量请求超时'}, 504
    except Exception as e:
        logger.error(f"获取历史空气质量异常: {e}", exc_info=True)
        return {'code': 500, 'message': '服务端内部错误'}, 500


def fetch_weather_history_with_air(location: str, date_value: str, lang="zh", unit="m"):
    with ThreadPoolExecutor(max_workers=2, thread_name_prefix="HistoryDayWorker") as executor:
        weather_future = executor.submit(fetch_weather_history_qweather, location, date_value, lang, unit)
        air_future = executor.submit(fetch_air_history_qweather, location, date_value, lang)
        weather_result, weather_status = weather_future.result()
        air_result, air_status = air_future.result()

    if weather_result.get('code') != 200:
        return weather_result, weather_status

    raw_weather = weather_result.get('data') or {}
    weather_daily = raw_weather.get('weatherDaily') or {}
    air_ok = air_result.get('code') == 200
    raw_air = air_result.get('data') or {} if air_ok else {}
    air_hourly = raw_air.get('airHourly') or []
    air_summary = _build_air_summary(air_hourly)

    weather_daily['airQuality'] = air_summary
    raw_weather['weatherDaily'] = weather_daily
    raw_weather['airHourly'] = air_hourly
    raw_weather['airSummary'] = air_summary
    raw_weather['airStatus'] = {
        'ok': air_ok,
        'httpStatus': air_status,
        'code': raw_air.get('code') if air_ok else air_result.get('code'),
        'message': '查询成功' if air_ok else air_result.get('message', '历史空气质量查询失败'),
        'sourceApi': '/v7/historical/air'
    }

    return {'code': 200, 'data': raw_weather}, 200


@csrf_exempt
@verify_signature
@guest_weather_quota(limit=GUEST_WEATHER_DAILY_LIMIT)
def weather_history(request):
    """
    历史天气查询接口，结构和 weather_now 保持一致：
    前端 -> 本接口 -> 和风天气 /v7/historical/weather -> 原始数据返回前端处理展示。
    """
    if request.method != 'GET':
        return JsonResponse({'code': 405, 'message': '仅支持 GET 请求'}, status=405)

    location = request.GET.get('location', '').strip()
    lang = request.GET.get('lang', 'zh').strip() or 'zh'
    unit = request.GET.get('unit', 'm').strip() or 'm'

    if not location:
        return JsonResponse({'code': 400, 'message': '请传入城市LocationID'}, status=400)
    if is_invalid_first_char(location) or ":" in location or "," in location:
        return JsonResponse({'code': 400, 'message': '历史天气仅支持城市LocationID', 'data': {}}, status=400)
    if unit not in ('m', 'i'):
        return JsonResponse({'code': 400, 'message': 'unit参数仅支持 m 或 i', 'data': {}}, status=400)

    dates = _recent_historical_dates()
    futures = {
        GLOBAL_EXECUTOR.submit(fetch_weather_history_with_air, location, date_value, lang, unit): date_value
        for date_value in dates
    }

    history_days = []
    errors = []
    air_errors = []
    for future in as_completed(futures):
        date_value = futures[future]
        try:
            result, status = future.result()
        except Exception as e:
            logger.error(f"历史天气批量查询异常({date_value}): {e}", exc_info=True)
            errors.append({'date': date_value, 'code': 500, 'message': '服务端内部错误'})
            continue

        if result.get('code') != 200:
            errors.append({
                'date': date_value,
                'code': result.get('code', status),
                'message': result.get('message', '历史天气查询失败')
            })
            continue

        raw_data = result.get('data') or {}
        air_status = raw_data.get('airStatus') or {}
        if air_status and not air_status.get('ok'):
            air_errors.append({
                'date': date_value,
                'code': air_status.get('code'),
                'httpStatus': air_status.get('httpStatus'),
                'message': air_status.get('message', '历史空气质量查询失败')
            })
        history_days.append({
            'date': date_value,
            'fxLink': raw_data.get('fxLink'),
            'weatherDaily': raw_data.get('weatherDaily') or {},
            'weatherHourly': raw_data.get('weatherHourly') or [],
            'airHourly': raw_data.get('airHourly') or [],
            'airSummary': raw_data.get('airSummary') or _build_air_summary(raw_data.get('airHourly') or []),
            'airStatus': air_status,
            'refer': raw_data.get('refer') or {}
        })

    history_days.sort(key=lambda item: item['date'], reverse=True)

    final_code = 200 if history_days else (errors[0].get('code', 502) if errors else 502)
    final_message = '查询成功'
    if not history_days:
        final_message = errors[0].get('message', '历史天气查询失败') if errors else '历史天气查询失败'
    elif errors:
        final_message = '查询成功（部分日期数据暂不可用）'

    return JsonResponse({
        'code': final_code,
        'message': final_message,
        'data': {
            'source_api': ['/v7/historical/weather', '/v7/historical/air'],
            'location': location,
            'dates': dates,
            'history': history_days,
            'errors': errors,
            'air_errors': air_errors
        }
    }, status=200 if history_days else 502)


@csrf_exempt
@verify_signature 
def location_search(request):
    def silent_success(msg="无结果"):
        return JsonResponse({'code': 200, 'message': msg, 'data': []})

    if request.method != 'GET': return silent_success('仅支持 GET')

    q = normalize_search_keyword(request.GET.get('q', ''))
    if not q or is_invalid_first_char(q): return silent_success("无效关键词")

    cache_key = generate_cache_key('location_search_qweather_v2', q)
    if redis_client:
        try:
            cached = redis_client.get(cache_key)
            if cached:
                return JsonResponse({'code': 200, 'message': '查询成功', 'data': json.loads(cached)})
        except: pass 

    try:
        token = get_valid_qweather_token() 
        headers = {"Authorization": f"Bearer {token}", "Accept-Encoding": "gzip"}
        
        response = session.get(
            f"{QWEATHER_GEO_URL}/geo/v2/city/lookup", 
            params={"location": q, "range": "world", "lang": "zh"}, 
            headers=headers, 
            timeout=5
        )
        
        # [修改] 修复缓存穿透：对于API返回无效的请求，也进行短期缓存
        if response.status_code == 400: 
            if redis_client:
                try: redis_client.setex(cache_key, 600, json.dumps([])) # 缓存空结果 10分钟
                except: pass
            return silent_success("上游无效参数")
            
        if response.status_code != 200:
            logger.error(f"和风API错误: {response.status_code}")
            return JsonResponse({'code': 502, 'message': f'第三方服务异常({response.status_code})'}, status=502)

        res_json = response.json()
        api_status = res_json.get("code")
        
        if api_status == "200":
            data = serialize_location_results(res_json.get("location", []))
            if redis_client:
                try: redis_client.setex(cache_key, 43200, json.dumps(data)) 
                except: pass
            return JsonResponse({'code': 200, 'message': '查询成功', 'data': data})
        
        elif api_status in ["204", "404", "400"]:
            # [修改] 缓存穿透保护：将“无结果”也写入 Redis，但过期时间短一点（如10分钟）
            if redis_client:
                try: redis_client.setex(cache_key, 600, json.dumps([])) 
                except: pass
            return silent_success("无匹配结果")
        else:
            return silent_success(f"API业务码: {api_status}")

    except requests.exceptions.Timeout:
        logger.warning(f"搜索超时: {q}")
        return JsonResponse({'code': 504, 'message': '网络请求超时'}, status=504)
    except requests.exceptions.ConnectionError:
        logger.warning(f"网络连接失败: {q}")
        return JsonResponse({'code': 502, 'message': '网络连接失败，请检查网络'}, status=502)
    except Exception as e:
        logger.error(f"系统内部错误: {str(e)}")
        return JsonResponse({'code': 500, 'message': '服务器内部错误'}, status=500)
    

def fetch_air_quality(location: str):
    """
    获取实时空气质量数据 (格点空气质量)
    API文档: /airquality/v1/current/{latitude}/{longitude}
    """
    expire_time = 600 # 10分钟
    cache_key = generate_cache_key('air_quality_now', location)

    # 1. 读缓存
    if redis_client:
        try:
            cached_data = redis_client.get(cache_key)
            if cached_data:
                return {'code': 200, 'data': json.loads(cached_data)}, 200
        except Exception:
            pass

    # 2. 调用 API
    try:
        token = get_valid_qweather_token()
        
        # --- 位置参数处理 ---
        # 必须拆分出 lat 和 lon，因为该接口路径参数强制要求
        lat, lon = None, None
        if ":" in location:
            parts = location.split(":")
            if len(parts) >= 2 and parts[0] != 'undefined':
                lat = parts[0]
                lon = parts[1]
        
        if not lat or not lon:
             return {'code': 400, 'message': '实时空气质量需提供经纬度坐标'}, 400

        # --- URL 构造 ---
        base_url = QWEATHER_GEO_URL
        if "re.qweatherapi" not in base_url:
             base_url = "https://devapi.qweather.com"

        # [修正点] 直接拼接经纬度到 URL 路径中
        api_url = f"{base_url}/airquality/v1/current/{lat}/{lon}"

        response = session.get(
            api_url, 
            params={'lang': 'zh'}, 
            headers={"Authorization": f"Bearer {token}", "Accept-Encoding": "gzip"}, 
            timeout=5
        )
        
        if response.status_code != 200:
            logger.error(f"空气质量接口错误: {response.text}")
            return {'code': response.status_code, 'message': '空气质量服务异常'}, response.status_code

        res_json = response.json()
        
        # [修正点] 校验逻辑
        # 格点空气质量接口成功时直接返回数据对象，不包含 "code": "200" 字段
        # 因此通过判断是否包含核心数据字段来确认是否成功
        if not res_json.get('indexes') and not res_json.get('pollutants'):
             # 如果既没有 indexes 也没有 pollutants，尝试获取 code 看是否有报错信息
             error_code = res_json.get('code', 'No Data')
             return {'code': 400, 'message': f"AQI数据缺失: {error_code}"}, 400

        # 3. 写缓存
        if redis_client:
            redis_client.setex(cache_key, expire_time, json.dumps(res_json))

        return {'code': 200, 'data': res_json}, 200

    except requests.exceptions.Timeout:
        return {'code': 504, 'message': 'AQI请求超时'}, 504
    except Exception as e:
        logger.error(f"获取空气质量异常: {e}")
        return {'code': 500, 'message': '服务端内部错误'}, 500


def fetch_weather_now_qweather(location: str):
    """
    获取实时天气数据 (和风天气 QWeather)
    API文档: /v7/weather/now
    """
    expire_time = 900  # 缓存 15 分钟 (900秒)
    cache_key = generate_cache_key('weather_now_qweather', location)

    # 1. 读缓存
    if redis_client:
        try:
            cached_data = redis_client.get(cache_key)
            if cached_data:
                return {'code': 200, 'data': json.loads(cached_data)}, 200
        except Exception:
            pass

    # 2. 调用 API
    try:
        token = get_valid_qweather_token()
        
        # --- 位置参数处理 ---
        req_loc = location
        # 如果传入的是 "lat:lon" 格式，将其转换为和风需要的 "lon,lat"
        if ":" in location:
            parts = location.split(":")
            if len(parts) >= 2 and parts[0] != 'undefined':
                req_loc = f"{parts[1]},{parts[0]}"
        
        # --- URL 构造 ---
        api_url = f"{QWEATHER_GEO_URL}/v7/weather/now"
        # 兼容开发版域名
        if "re.qweatherapi" not in QWEATHER_GEO_URL:
             api_url = "https://devapi.qweather.com/v7/weather/now"

        response = session.get(
            api_url, 
            params={'location': req_loc, 'lang': 'zh'}, 
            headers={"Authorization": f"Bearer {token}", "Accept-Encoding": "gzip"}, 
            timeout=5
        )
        
        if response.status_code != 200:
            logger.error(f"和风实时天气接口错误: {response.text}")
            return {'code': response.status_code, 'message': '第三方接口异常'}, response.status_code

        res_json = response.json()
        if res_json.get('code') != '200':
             return {'code': 400, 'message': f"和风错误: {res_json.get('code')}"}, 400

        # 3. 写缓存
        if redis_client:
            redis_client.setex(cache_key, expire_time, json.dumps(res_json))

        return {'code': 200, 'data': res_json}, 200

    except requests.exceptions.Timeout:
        return {'code': 504, 'message': '实时天气请求超时'}, 504
    except Exception as e:
        logger.error(f"获取实时天气异常: {e}")
        return {'code': 500, 'message': '服务端内部错误'}, 500
