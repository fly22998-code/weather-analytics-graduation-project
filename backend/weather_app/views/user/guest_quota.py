import uuid
import datetime
from functools import wraps

import jwt
from django.conf import settings
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from weather_app.models import User
from .redis_config import generate_cache_key, redis_client, logger
from .user_utils import (
    generate_session_sign_key,
    get_active_session_jti,
    get_client_ip,
    store_guest_sign_key,
    verify_signed_headers,
)


GUEST_WEATHER_DAILY_LIMIT = 10
GUEST_IP_DAILY_LIMIT = 200
GUEST_TOKEN_EXPIRE_DAYS = 30
GUEST_TOKEN_HEADER = 'X-Guest-Token'


def _seconds_until_midnight():
    now = timezone.now()
    tomorrow = (now + datetime.timedelta(days=1)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    return int(max((tomorrow - now).total_seconds(), 300))


def get_optional_authenticated_user(request):
    """Return a valid logged-in user, otherwise None so the request is a guest."""
    auth_header = request.META.get('HTTP_AUTHORIZATION', '')
    if not auth_header.startswith('Bearer '):
        return None

    token = auth_header.split(' ', 1)[1].strip()
    if not token:
        return None

    try:
        payload = jwt.decode(
            token,
            settings.JWT_SETTINGS['SECRET_KEY'],
            algorithms=[settings.JWT_SETTINGS['ALGORITHM']],
            options={'verify_exp': True}
        )
        user_id = payload.get('user_id')
        session_jti = payload.get('session_jti')
        if not user_id:
            return None
        if payload.get('token_type', 'access') != 'access':
            return None
        if not session_jti or get_active_session_jti(user_id) != session_jti:
            raise ValueError('SESSION_REPLACED')

        user = User.objects.only('id', 'is_banned').get(id=user_id)
        return None if user.is_banned == 1 else user
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, User.DoesNotExist):
        return None
    except Exception as e:
        logger.warning(f"Optional auth check failed: {e}")
        return None


def _decode_guest_token(token):
    if not token:
        return None

    try:
        payload = jwt.decode(
            token,
            settings.JWT_SETTINGS['SECRET_KEY'],
            algorithms=[settings.JWT_SETTINGS['ALGORITHM']],
            options={'verify_exp': True}
        )
        if payload.get('token_type') != 'guest':
            return None
        return payload.get('guest_id')
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None


def _issue_guest_token():
    now = timezone.now()
    expire_at = now + datetime.timedelta(days=GUEST_TOKEN_EXPIRE_DAYS)
    guest_id = uuid.uuid4().hex
    sign_key = generate_session_sign_key()
    token = jwt.encode(
        {
            'token_type': 'guest',
            'guest_id': guest_id,
            'iat': int(now.timestamp()),
            'exp': int(expire_at.timestamp())
        },
        settings.JWT_SETTINGS['SECRET_KEY'],
        algorithm=settings.JWT_SETTINGS['ALGORITHM']
    )
    store_guest_sign_key(guest_id, sign_key, int(expire_at.timestamp()))
    return guest_id, token, sign_key


def _get_guest_identity(request):
    token = request.headers.get(GUEST_TOKEN_HEADER, '').strip()
    guest_id = _decode_guest_token(token)
    if guest_id:
        return guest_id, token
    return None, None


def _build_guest_quota_headers(used, limit):
    return {
        'X-Guest-Quota-Limit': str(limit),
        'X-Guest-Quota-Used': str(min(used, limit)),
        'X-Guest-Quota-Remaining': str(max(limit - used, 0))
    }


def _attach_headers(response, headers):
    for key, value in headers.items():
        response[key] = value
    return response


@csrf_exempt
def issue_guest_token(request):
    if request.method != 'POST':
        return JsonResponse({'code': 405, 'message': '仅支持POST请求'}, status=405)

    verify_result, verify_msg = verify_signed_headers(request)
    if not verify_result:
        return JsonResponse({'code': 403, 'message': verify_msg}, status=403)

    _guest_id, guest_token, sign_key = _issue_guest_token()
    response = JsonResponse({
        'code': 200,
        'message': '游客Token签发成功',
        'data': {
            'guest_token': guest_token,
            'sign_key': sign_key
        }
    })
    response[GUEST_TOKEN_HEADER] = guest_token
    return response


def guest_weather_quota(limit=GUEST_WEATHER_DAILY_LIMIT, ip_limit=GUEST_IP_DAILY_LIMIT):
    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            try:
                authenticated_user = get_optional_authenticated_user(request)
            except ValueError as exc:
                if str(exc) == 'SESSION_REPLACED':
                    return JsonResponse({
                        'code': 4017,
                        'message': '账号已在其他设备登录，当前会话已切换为游客模式'
                    }, status=401)
                authenticated_user = None

            if authenticated_user:
                return func(request, *args, **kwargs)

            ip = get_client_ip(request)
            guest_id, guest_token = _get_guest_identity(request)
            if not guest_id or not guest_token:
                return JsonResponse({
                    'code': 4016,
                    'message': '游客身份无效，请重新获取游客Token'
                }, status=401)

            today = timezone.localdate().isoformat()
            ttl = _seconds_until_midnight()
            guest_key = f"guest_quota:weather:{today}:{generate_cache_key('guest', guest_id)}"
            ip_key = f"guest_quota:weather_ip:{today}:{generate_cache_key('ip', ip)}"

            try:
                guest_count = redis_client.incr(guest_key)
                ip_count = redis_client.incr(ip_key)
                if guest_count == 1:
                    redis_client.expire(guest_key, ttl)
                if ip_count == 1:
                    redis_client.expire(ip_key, ttl)
            except Exception as e:
                logger.error(f"Guest weather quota check failed for IP {ip}: {e}")
                return func(request, *args, **kwargs)

            headers = _build_guest_quota_headers(guest_count, limit)

            if ip_count > ip_limit:
                response = JsonResponse({
                    'code': 429,
                    'message': '游客请求过于频繁，请登录后继续使用。',
                    'detail': f'今日当前网络游客请求次数: {ip_count}/{ip_limit}'
                }, status=429)
                return _attach_headers(response, headers)

            if guest_count > limit:
                response = JsonResponse({
                    'code': 429,
                    'message': '游客今日查询次数已用完，登录后可继续查询。',
                    'detail': f'今日游客查询次数: {guest_count}/{limit}',
                    'limit': limit,
                    'used': min(guest_count, limit),
                    'remaining': 0
                }, status=429)
                return _attach_headers(response, headers)

            response = func(request, *args, **kwargs)
            return _attach_headers(response, headers)
        return wrapper
    return decorator
