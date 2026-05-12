from django.http import JsonResponse
import jwt
import re
import hashlib
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from .models import User
from .views import redis_client

TRAFFIC_PREFIX = "monitor:traffic"
TRAFFIC_SESSION_SECONDS = 1800


def _seconds_until_tomorrow():
    now = timezone.localtime()
    tomorrow = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    return max(int((tomorrow - now).total_seconds()), 60)


def _traffic_key(name):
    return f"{TRAFFIC_PREFIX}:{timezone.localtime().strftime('%Y%m%d')}:{name}"


def _normalize_endpoint(request):
    path = (request.path or '').rstrip('/') or '/'
    path = re.sub(r'/\d+(?=/|$)', '/:id', path)
    return f"{request.method.upper()} {path}"


def _get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', 'unknown')


def _get_request_actor(request):
    auth_header = request.META.get('HTTP_AUTHORIZATION', '')
    if auth_header.startswith('Bearer '):
        token = auth_header.split(' ', 1)[1]
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SETTINGS['SECRET_KEY'],
                algorithms=[settings.JWT_SETTINGS['ALGORITHM']],
                options={'verify_exp': False}
            )
            user_id = payload.get('user_id')
            if user_id:
                user_email = payload.get('email') or f"user:{user_id}"
                return f"user:{user_id}", user_email
        except Exception:
            pass
    client_ip = _get_client_ip(request)
    return f"ip:{client_ip}", f"游客/IP:{client_ip}"


def _track_request_traffic(request, response):
    path = request.path or ''
    if not path.startswith('/weather/'):
        return
    if path.startswith('/weather/admin/users/server-status/') or path.startswith('/weather/admin/users/traffic-stats/'):
        return

    expire_seconds = _seconds_until_tomorrow()
    identity, user_label = _get_request_actor(request)
    identity_hash = hashlib.md5(identity.encode('utf-8')).hexdigest()
    visit_session_key = f"{TRAFFIC_PREFIX}:session:{timezone.localtime().strftime('%Y%m%d')}:{identity_hash}"
    minute_key = f"{TRAFFIC_PREFIX}:minute:{timezone.localtime().strftime('%Y%m%d%H%M')}"
    endpoint_key = _traffic_key('endpoints')
    endpoint_error_key = _traffic_key('endpoint_errors')
    endpoint_user_key = _traffic_key('endpoint_users')
    endpoint_user_error_key = _traffic_key('endpoint_user_errors')
    endpoint_field = _normalize_endpoint(request)
    endpoint_user_field = f"{endpoint_field}\x1f{user_label}"
    status_code = getattr(response, 'status_code', 0)
    is_new_visit = bool(redis_client.set(visit_session_key, '1', ex=TRAFFIC_SESSION_SECONDS, nx=True))

    pipe = redis_client.pipeline()
    keys_to_expire = [
        _traffic_key('api_total'),
        _traffic_key('session_total'),
        _traffic_key('visitor_unique'),
        _traffic_key('api_success'),
        _traffic_key('api_error'),
        endpoint_key,
        endpoint_error_key,
        endpoint_user_key,
        endpoint_user_error_key,
        minute_key,
    ]

    pipe.incr(_traffic_key('api_total'))
    if is_new_visit:
        pipe.incr(_traffic_key('session_total'))
    pipe.pfadd(_traffic_key('visitor_unique'), identity)
    pipe.incr(minute_key)
    pipe.hincrby(endpoint_key, endpoint_field, 1)
    pipe.hincrby(endpoint_user_key, endpoint_user_field, 1)

    if 200 <= status_code < 400:
        pipe.incr(_traffic_key('api_success'))
    elif status_code >= 400:
        pipe.incr(_traffic_key('api_error'))
        pipe.hincrby(endpoint_error_key, endpoint_field, 1)
        pipe.hincrby(endpoint_user_error_key, endpoint_user_field, 1)

    for key in keys_to_expire:
        pipe.expire(key, expire_seconds)
    pipe.expire(minute_key, 180)
    pipe.execute()


def _return_with_traffic(request, response):
    try:
        _track_request_traffic(request, response)
    except Exception:
        pass
    return response


class AuthMiddleware:
    """全局认证中间件：修复is_banned判断逻辑 + 排除媒体文件路径"""
    def __init__(self, get_response):
        self.get_response = get_response
        self.exempt_paths = [
            # 原有豁免路径
            '/weather/user/login/',
            '/weather/user/refresh/',
            '/weather/user/logout/',
            '/weather/user/guest-token/',
            '/weather/user/register/',
            '/weather/user/send-reset-code/',
            '/weather/user/verify-code/',
            '/weather/user/reset-password/',
            '/weather/user/check-email/',
            '/weather/user/send-register-code/',
            # 游客模式可访问的公开天气能力
            '/weather/user/weather/',
            '/weather/user/location/search',
            '/weather/user/weather/now',
            # 新增：媒体文件相关路径豁免（关键修改）
            '/upload/avatar/',  # 头像文件存储路径

        ]

    def __call__(self, request):
        # 优化：判断请求路径是否以豁免路径开头（支持子路径匹配）
        path = request.path
        is_exempt = any(path.startswith(exempt_path) for exempt_path in self.exempt_paths)
        
        if is_exempt:
            response = self.get_response(request)
            return _return_with_traffic(request, response)

        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if not auth_header.startswith('Bearer '):
            return _return_with_traffic(request, JsonResponse({
                'code': 4010,
                'message': '未登录，请先登录'
            }, status=401))

        token = auth_header.split(' ')[1]
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SETTINGS['SECRET_KEY'],
                algorithms=[settings.JWT_SETTINGS['ALGORITHM']],
                options={'verify_exp': True}
            )
            user_id = payload['user_id']
            if payload.get('token_type', 'access') != 'access':
                return _return_with_traffic(request, JsonResponse({
                    'code': 4013,
                    'message': '登录状态无效，请重新登录'
                }, status=401))

            cache_key = f"user:banned:{user_id}"
            cached_status = redis_client.get(cache_key)

            # 修正1：cached_status == '1' 才是封禁（1=封禁）
            if cached_status == '1': 
                return _return_with_traffic(request, JsonResponse({
                    'code': 4011,
                    'message': '账号已被封禁，无法使用'
                }, status=401))

            user = User.objects.only('id', 'is_banned').get(id=user_id)
            # 修正2：user.is_banned == 1 才是封禁（1=封禁）
            if user.is_banned == 1:  
                redis_client.setex(cache_key, 600, '1')  # 缓存封禁状态
                return _return_with_traffic(request, JsonResponse({
                    'code': 4011,
                    'message': '账号已被封禁，无法使用'
                }, status=401))

            # 正常状态：缓存未封禁标记（0=未封禁）
            redis_client.setex(cache_key, 600, '0')
            response = self.get_response(request)
            return _return_with_traffic(request, response)

        except jwt.ExpiredSignatureError:
            response = JsonResponse({
                'code': 4012,
                'message': 'Token已过期，请重新登录'
            }, status=401)
            return _return_with_traffic(request, response)
        except (jwt.InvalidTokenError, User.DoesNotExist):
            response = JsonResponse({
                'code': 4013,
                'message': '登录状态无效，请重新登录'
            }, status=401)
            return _return_with_traffic(request, response)
        except Exception as e:
            print(f"认证异常：{str(e)}")
            response = JsonResponse({
                'code': 4014,
                'message': '登录状态异常，请重新登录'
            }, status=401)
            return _return_with_traffic(request, response)
