from django.http import JsonResponse
from django.db import IntegrityError
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.utils import timezone
from django.core.mail import send_mail
import random
import hashlib
import time
from django.db.models import F
import json
from django.core.cache import cache
import re   
from django_ratelimit.decorators import ratelimit
from django.views.decorators.http import require_GET
from threading import Thread
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
import logging

# 引入你的模型和工具
from weather_app.models import User
from .redis_config import redis_client, generate_cache_key
from .user_utils import * # 假设 verify_sign, get_client_ip, generate_jwt_token 在这里

# ================= 配置常量 (业务隔离) =================
# 定义不同的前缀，防止业务混淆（修复串用漏洞）
PREFIX_REGISTER_CODE = "reg_code"    # 注册验证码
PREFIX_REGISTER_TOKEN = "reg_token"  # 注册通过令牌
PREFIX_RESET_CODE = "reset_code"     # 重置密码验证码
PREFIX_RESET_TOKEN = "reset_token"   # 重置密码令牌
PREFIX_EMAIL_CHECK = "email_check"   # 邮箱状态缓存

logger = logging.getLogger(__name__)
REFRESH_TOKEN_COOKIE_NAME = "weather_refresh_token"

# ================= 辅助函数 =================

def _decode_redis_text(value, default=""):
    """统一处理 Redis 返回的 bytes/str，减少重复分支判断。"""
    if value is None:
        return default
    return value.decode() if isinstance(value, bytes) else value


def _get_login_fail_status(attempts_key):
    """合并获取失败次数和锁定剩余时间，减少 Redis 往返。"""
    try:
        pipe = redis_client.pipeline()
        pipe.get(attempts_key)
        pipe.ttl(attempts_key)
        raw_count, ttl = pipe.execute()
        failed_count = int(_decode_redis_text(raw_count, "0"))
        return failed_count, max(ttl or 0, 0)
    except Exception:
        return 0, 0


def _incr_with_initial_expire(key, timeout):
    """计数并仅在新 key 时设置过期时间，避免重复 expire 写入。"""
    pipe = redis_client.pipeline()
    pipe.incr(key)
    pipe.ttl(key)
    current_count, ttl = pipe.execute()
    if ttl == -1:
        redis_client.expire(key, timeout)
    return current_count


def _get_register_send_limits(send_limit_key, ip_limit_key):
    """批量获取注册验证码发送频率计数。"""
    try:
        pipe = redis_client.pipeline()
        pipe.get(send_limit_key)
        pipe.get(ip_limit_key)
        send_count, ip_send_count = pipe.execute()
        return int(_decode_redis_text(send_count, "0")), int(_decode_redis_text(ip_send_count, "0"))
    except Exception:
        return 0, 0


def _cache_registered_email(email_status_key):
    redis_client.setex(email_status_key, 300, json.dumps({'code': 1001, 'message': '该邮箱已注册'}))


def _set_refresh_cookie(response, refresh_token, expire_at):
    max_age = max(int(expire_at) - int(time.time()), 1)
    response.set_cookie(
        REFRESH_TOKEN_COOKIE_NAME,
        refresh_token,
        max_age=max_age,
        httponly=True,
        secure=not settings.DEBUG,
        samesite='Lax',
        path='/'
    )
    return response


def _delete_refresh_cookie(response):
    response.delete_cookie(
        REFRESH_TOKEN_COOKIE_NAME,
        path='/',
        samesite='Lax'
    )
    return response


def _get_refresh_cookie_payload(request):
    refresh_token = request.COOKIES.get(REFRESH_TOKEN_COOKIE_NAME, '').strip()
    if not refresh_token:
        return None
    try:
        payload = jwt.decode(
            refresh_token,
            settings.JWT_SETTINGS['SECRET_KEY'],
            algorithms=[settings.JWT_SETTINGS['ALGORITHM']],
            options={'verify_exp': False}
        )
        return payload if payload.get('token_type') == 'refresh' else None
    except jwt.InvalidTokenError:
        return None

def _record_login_failure(user_key, ip_key):
    """
    辅助函数：原子性记录失败次数 (Pipeline优化版)
    """
    LOCK_TIME = 300  # 锁定 5 分钟
    
    try:
        pipe = redis_client.pipeline()
        pipe.incr(user_key)
        pipe.incr(ip_key)
        pipe.ttl(user_key)
        pipe.ttl(ip_key)
        current_fails, _, user_ttl, ip_ttl = pipe.execute()

        if user_ttl == -1 or current_fails == 5:
            redis_client.expire(user_key, LOCK_TIME)
        if ip_ttl == -1:
            redis_client.expire(ip_key, LOCK_TIME)
    except Exception as e:
        logger.error(f"Redis写入失败: {e}")
        current_fails = 1 # 兜底
        
    return current_fails

# ================= 业务接口 =================

# -------------------------- 1. 注册专用发送验证码 --------------------------
@csrf_exempt
def send_register_code(request):
    if request.method != "POST":
        return JsonResponse({"code": 400, "message": "请用POST请求"})
    
    try:
        data = json.loads(request.body)
        
        email = data.get("email", "").strip().lower()

        # 签名验证
        verify_result, verify_msg = verify_signed_headers(request, {"email": email})
        if not verify_result:
            return JsonResponse({"code": 403, "message": verify_msg})

        if not email:
            return JsonResponse({"code": 400, "message": "邮箱不能为空"})
        
        # 生成Redis相关键
        email_status_key = generate_cache_key(PREFIX_EMAIL_CHECK, email)
        code_cache_key = generate_cache_key(PREFIX_REGISTER_CODE, email) # 【安全】使用注册专用前缀
        send_limit_key = generate_cache_key('send_limit', email)
        ip_limit_key = generate_cache_key('ip_limit', request.META.get('REMOTE_ADDR', 'unknown'))
        
        # 1. 频率限制
        send_count, ip_send_count = _get_register_send_limits(send_limit_key, ip_limit_key)
        
        if send_count >= 5 or ip_send_count >= 10:
            return JsonResponse({"code": 429, "message": "验证码发送过于频繁，请10分钟后再试"})
        
        # 2. 检查邮箱状态 (缓存 + 数据库)
        cached_status = redis_client.get(email_status_key)
        if cached_status:
            status_data = json.loads(_decode_redis_text(cached_status))
            if status_data.get('code') == 1001:
                return JsonResponse({"code": 410, "message": "该邮箱已注册"})
        
        if User.objects.filter(email=email).exists():
            # 更新缓存
            _cache_registered_email(email_status_key)
            return JsonResponse({"code": 410, "message": "该邮箱已注册"})
        
        # 3. 生成验证码
        verify_code = str(random.randint(100000, 999999))
        redis_client.setex(code_cache_key, 60, verify_code)  # 1分钟有效
        
        # 调试日志
        print(f"[注册] Email: {email}, Code: {verify_code}")
        
        # 4. 更新限制计数
        _incr_with_initial_expire(send_limit_key, 600)
        _incr_with_initial_expire(ip_limit_key, 600)
        
        # 5. 异步发送邮件
        def send_email_task():
            try:
                send_mail(
                    subject="账号注册验证码",
                    message=f"您好！您的注册验证码是：{verify_code}\n有效期1分钟，如非本人操作请忽略。",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                    fail_silently=False,
                )
            except Exception as e:
                logger.error(f"邮件发送失败: {e}")
                redis_client.delete(code_cache_key) # 发送失败回滚
        
        Thread(target=send_email_task).start()
        
        return JsonResponse({"code": 200, "message": "验证码已发送"})
    
    except Exception as e:
        logger.error(f"发送接口异常: {e}")
        return JsonResponse({"code": 500, "message": "服务器内部错误"}, status=500)


# -------------------------- 2. 找回密码专用发送验证码 --------------------------
@csrf_exempt
def send_verify_code(request):
    """找回密码验证码发送接口"""
    if request.method != "POST":
        return JsonResponse({"code": 400, "message": "请用POST请求"})
    
    try:
        data = json.loads(request.body)
        email = data.get("email", "").strip().lower()

        verify_result, verify_msg = verify_signed_headers(request, {"email": email})
        if not verify_result:
            return JsonResponse({"code": 403, "message": verify_msg})

        if not email:
            return JsonResponse({"code": 400, "message": "邮箱不能为空"})
        
        # 检查邮箱是否存在 (找回密码的前提)
        if not User.objects.filter(email=email).exists():
            return JsonResponse({"code": 404, "message": "该邮箱未注册"})
        
        verify_code = str(random.randint(100000, 999999))
        
        # 【安全】使用重置密码专用前缀
        code_cache_key = generate_cache_key(PREFIX_RESET_CODE, email) 
        
        redis_client.setex(code_cache_key, 60, verify_code)
        
        # 发送邮件
        def send_reset_email():
            try:
                send_mail(
                    subject="密码找回验证码",
                    message=f"您好！您的密码找回验证码是：{verify_code}\n有效期1分钟。",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                    fail_silently=False,
                )
            except Exception as e:
                logger.error(f"重置邮件发送失败: {e}")
                redis_client.delete(code_cache_key)

        Thread(target=send_reset_email).start()
        print(f"[重置] Email: {email}, Code: {verify_code}")

        return JsonResponse({"code": 200, "message": "验证码已发送"})
        
    except Exception as e:
        logger.error(f"接口异常: {e}")
        return JsonResponse({"code": 500, "message": "服务器内部错误"}, status=500)


# -------------------------- 3. 统一验证码校验接口 --------------------------
@csrf_exempt
def verify_code(request):
    """
    通用验证接口
    参数: email, code, type ('register' | 'reset')
    """
    if request.method != "POST":
        return JsonResponse({"code": 400, "message": "请用POST请求"})
    
    try:
        data = json.loads(request.body)
        email = data.get("email", "").strip().lower()
        code = data.get("code", "").strip()
        # 【关键】前端必须传递场景类型，默认 register
        action_type = data.get("type", "register") 
    except json.JSONDecodeError:
        return JsonResponse({"code": 400, "message": "数据格式错误"})
    
    if not email or not code:
        return JsonResponse({"code": 400, "message": "参数不完整"})
    
    # 根据场景选择不同的前缀
    if action_type == "reset":
        code_prefix = PREFIX_RESET_CODE
        token_prefix = PREFIX_RESET_TOKEN
    else:
        code_prefix = PREFIX_REGISTER_CODE
        token_prefix = PREFIX_REGISTER_TOKEN
        
    code_key = generate_cache_key(code_prefix, email)
    token_key = generate_cache_key(token_prefix, email)
    
    try:
        cached_code = redis_client.get(code_key)
        
        if _decode_redis_text(cached_code) == code:
            # 验证通过
            verify_token = hashlib.sha256(f"{email}{timezone.now()}".encode()).hexdigest()
            pipe = redis_client.pipeline()
            pipe.delete(code_key) # 防止验证码二次使用
            pipe.setex(token_key, 300, verify_token) # 5分钟有效
            pipe.execute()
            
            return JsonResponse({
                "code": 200, 
                "message": "验证通过",
                "data": {"verify_token": verify_token} 
            })
        else:
            return JsonResponse({"code": 400, "message": "验证码错误或已过期"})
            
    except Exception as e:
        logger.error(f"验证异常: {e}")
        return JsonResponse({"code": 500, "message": "验证失败"}, status=500)


# -------------------------- 4. 用户注册接口 --------------------------
@csrf_exempt
def user_register(request):
    if request.method != 'POST':
        return JsonResponse({'code': 400, 'message': '仅支持POST请求'}, status=400)
    
    try:
        data = json.loads(request.body)
        email = data.get('email', '').strip().lower()
        password = data.get('password', '').strip()
        verify_token = data.get('verify_token', '').strip()
    except Exception:
        return JsonResponse({'code': 400, 'message': '数据格式错误'}, status=400)
    
    # 验证令牌 (使用注册专用前缀)
    token_key = generate_cache_key(PREFIX_REGISTER_TOKEN, email)
    cached_token = redis_client.get(token_key)
    
    if not verify_token or _decode_redis_text(cached_token) != verify_token:
        return JsonResponse({'code': 403, 'message': '验证已过期，请重新验证邮箱'}, status=403)
    
    # 密码强度校验
    if len(password) < 8 or not (any(c.isalpha() for c in password) and any(c.isdigit() for c in password)):
        return JsonResponse({'code': 400, 'message': '密码需8位以上且包含字母和数字'}, status=400)
    
    try:
        # 再次检查邮箱 (双重保险)
        if User.objects.filter(email=email).exists():
            return JsonResponse({'code': 409, 'message': '该邮箱已被注册'}, status=409)
            
        # 创建用户
        user = User(email=email, password=password) # 确保Model里的save方法处理了密码加密
        user.save()
        
        # 注册成功后，销毁令牌，防止重放
        email_status_key = generate_cache_key(PREFIX_EMAIL_CHECK, email)
        pipe = redis_client.pipeline()
        pipe.delete(token_key)
        pipe.setex(email_status_key, 300, json.dumps({'code': 1001, 'message': '该邮箱已注册'}))
        pipe.execute()
        
        return JsonResponse({'code': 200, 'message': '注册成功', 'data': {'email': email}})
    
    except IntegrityError:
        return JsonResponse({'code': 409, 'message': '该邮箱已被注册'}, status=409)
    except Exception as e:
        logger.error(f"注册失败: {e}")
        return JsonResponse({'code': 500, 'message': '注册失败'}, status=500)


# -------------------------- 5. 重置密码接口 --------------------------
@csrf_exempt
def reset_password(request):
    if request.method != "POST":
        return JsonResponse({"code": 400, "message": "请用POST请求"})
    
    try:
        data = json.loads(request.body)
        email = data.get("email", "").strip()
        new_password = data.get("new_password", "").strip()
        verify_token = data.get("verify_token", "").strip()
    except Exception:
        return JsonResponse({"code": 400, "message": "数据格式错误"})
    
    # 验证令牌 (使用重置专用前缀)
    token_key = generate_cache_key(PREFIX_RESET_TOKEN, email)
    cached_token = redis_client.get(token_key)
    
    if not verify_token or _decode_redis_text(cached_token) != verify_token:
        return JsonResponse({"code": 403, "message": "验证失效，请重新获取验证码"}, status=403)
    
    # 密码强度校验
    if len(new_password) < 8 or not (any(c.isalpha() for c in new_password) and any(c.isdigit() for c in new_password)):
         return JsonResponse({"code": 400, "message": "密码需8位以上且包含字母和数字"})

    try:
        user = User.objects.get(email=email)
        user.password = new_password 
        user.save()
        
        # 成功后销毁令牌
        redis_client.delete(token_key)
        
        return JsonResponse({"code": 200, "message": "密码重置成功，请登录"})
    except User.DoesNotExist:
        return JsonResponse({"code": 404, "message": "用户不存在"})
    except Exception as e:
        logger.error(f"重置失败: {e}")
        return JsonResponse({"code": 500, "message": "服务器内部错误"}, status=500)


# -------------------------- 6. 用户登录接口 --------------------------
@csrf_exempt
def user_login(request):
    if request.method != 'POST':
        return JsonResponse({'code': 405, 'message': '仅支持POST请求'}, status=405)

    client_ip = get_client_ip(request)

    # --- IP 限流 ---
    ip_rate_key = f"login_ip_limit:{client_ip}"
    try:
        current_rate = _incr_with_initial_expire(ip_rate_key, 300)
    except Exception:
        current_rate = 1 

    if current_rate > 30:
        return JsonResponse({'code': 429, 'message': '请求过于频繁，请稍后再试'}, status=429)

    # --- 参数解析 ---
    try:
        data = json.loads(request.body)
        email = data.get('email', '').strip().lower()
        password = data.get('password', '').strip()
        force_login = bool(data.get('force_login'))
    except Exception:
        return JsonResponse({'code': 400, 'message': '数据格式错误'}, status=400)

    # --- 锁定检查 ---
    attempts_key = f"login_fail_count:{email}"
    ip_attempts_key = f"login_fail_ip:{client_ip}"

    failed_count, ttl = _get_login_fail_status(attempts_key)

    if failed_count >= 5:
        wait_minutes = (ttl // 60) + 1
        return JsonResponse({'code': 403, 'message': f'账号锁定中，请 {wait_minutes} 分钟后再试'}, status=403)

    # --- 查库与校验 ---
    try:
        user = User.objects.only('id', 'password', 'is_banned', 'email', 'user_role', 'username').get(email=email)
    except User.DoesNotExist:
        _record_login_failure(attempts_key, ip_attempts_key)
        return JsonResponse({'code': 401, 'message': '邮箱或密码错误'}, status=401)

    if user.is_banned:
        return JsonResponse({'code': 403, 'message': '账号已禁用'}, status=403)

    if not user.check_password(password):
        current_fails = _record_login_failure(attempts_key, ip_attempts_key)
        remaining = 5 - current_fails
        if remaining > 0:
            return JsonResponse({'code': 401, 'message': f'密码错误，剩 {remaining} 次机会'}, status=401)
        else:
            return JsonResponse({'code': 403, 'message': '错误次数过多，账号锁定 5 分钟'}, status=403)

    active_jti = get_active_session_jti(user.id)
    active_session_exists = bool(active_jti and redis_client.exists(f"refresh_token:{active_jti}"))
    current_cookie_payload = _get_refresh_cookie_payload(request)
    current_cookie_jti = current_cookie_payload.get('jti') if current_cookie_payload else None
    is_current_browser_session = bool(
        active_session_exists
        and current_cookie_jti == active_jti
        and str(current_cookie_payload.get('user_id')) == str(user.id)
    )

    if active_jti and not active_session_exists:
        clear_active_session(user.id, active_jti)
        active_jti = None

    if active_session_exists and not is_current_browser_session and not force_login:
        return JsonResponse({
            'code': 4091,
            'message': '该账号已在其他设备登录，继续登录会使其他设备退出。是否继续？'
        }, status=409)

    # --- 登录成功 ---
    try:
        pipe = redis_client.pipeline()
        pipe.delete(attempts_key)
        pipe.delete(ip_attempts_key)
        pipe.execute()

        User.objects.filter(id=user.id).update(
            last_login_time=timezone.now(),
            last_login_ip=client_ip,
            login_count=F('login_count') + 1
        )

        if active_jti:
            revoke_refresh_token(active_jti)
        
        refresh_token, refresh_jti, refresh_expire_at, refresh_expire_text = generate_refresh_token(user.id)
        sign_key = generate_session_sign_key()
        store_refresh_token(user.id, refresh_jti, refresh_expire_at, sign_key)
        set_active_session(user.id, refresh_jti, refresh_expire_at)
        token, expire_at, expire_text = generate_jwt_token(
            user.id, user.user_role, user.email, user.username, refresh_jti
        )

        response = JsonResponse({
            'code': 200,
            'message': '登录成功',
            'data': {
                'token': token,
                'access_token': token,
                'email': user.email,
                'expire_at': expire_at,
                'expire_text': expire_text,
                'refresh_expire_at': refresh_expire_at,
                'refresh_expire_text': refresh_expire_text,
                'sign_key': sign_key,
            }
        })
        return _set_refresh_cookie(response, refresh_token, refresh_expire_at)
    except Exception as e:
        logger.error(f"登录处理失败: {e}")
        return JsonResponse({'code': 500, 'message': '系统错误'}, status=500)


@csrf_exempt
def refresh_access_token(request):
    if request.method != 'POST':
        return JsonResponse({'code': 405, 'message': '仅支持POST请求'}, status=405)

    refresh_token = request.COOKIES.get(REFRESH_TOKEN_COOKIE_NAME, '').strip()
    if not refresh_token:
        try:
            data = json.loads(request.body or '{}')
            refresh_token = data.get('refresh_token', '').strip()
        except Exception:
            return JsonResponse({'code': 400, 'message': '数据格式错误'}, status=400)

    if not refresh_token:
        return JsonResponse({'code': 4015, 'message': '登录已过期，请重新登录'}, status=401)

    try:
        payload = jwt.decode(
            refresh_token,
            settings.JWT_SETTINGS['SECRET_KEY'],
            algorithms=[settings.JWT_SETTINGS['ALGORITHM']],
            options={'verify_exp': True}
        )
        if payload.get('token_type') != 'refresh':
            return JsonResponse({'code': 4015, 'message': '登录已过期，请重新登录'}, status=401)

        user_id = payload.get('user_id')
        jti = payload.get('jti')
        if not user_id or not jti:
            return JsonResponse({'code': 4015, 'message': '登录已过期，请重新登录'}, status=401)

        session_user_id = redis_client.get(f"refresh_token:{jti}")
        if session_user_id is None:
            return JsonResponse({'code': 4015, 'message': '登录已过期，请重新登录'}, status=401)

        if isinstance(session_user_id, bytes):
            session_user_id = session_user_id.decode('utf-8')
        if str(session_user_id) != str(user_id):
            revoke_refresh_token(jti)
            return JsonResponse({'code': 4015, 'message': '登录已过期，请重新登录'}, status=401)

        active_jti = get_active_session_jti(user_id)
        if active_jti != jti:
            revoke_refresh_token(jti)
            return JsonResponse({
                'code': 4017,
                'message': '账号已在其他设备登录，当前会话已切换为游客模式'
            }, status=401)

        user = User.objects.only('id', 'email', 'username', 'user_role', 'is_banned').get(id=user_id)
        if user.is_banned:
            revoke_refresh_token(jti)
            return JsonResponse({'code': 4011, 'message': '账号已被封禁，无法使用'}, status=401)

        sign_key = generate_session_sign_key()
        redis_client.setex(f"sign_key:session:{jti}", max(payload.get('exp', 0) - int(time.time()), 1), sign_key)

        token, expire_at, expire_text = generate_jwt_token(
            user.id, user.user_role, user.email, user.username, jti
        )
        response = JsonResponse({
            'code': 200,
            'message': '刷新成功',
            'data': {
                'token': token,
                'access_token': token,
                'expire_at': expire_at,
                'expire_text': expire_text,
                'email': user.email,
                'sign_key': sign_key,
            }
        })
        return _set_refresh_cookie(response, refresh_token, payload.get('exp', int(time.time()) + 1))
    except jwt.ExpiredSignatureError:
        return JsonResponse({'code': 4015, 'message': '登录已过期，请重新登录'}, status=401)
    except (jwt.InvalidTokenError, User.DoesNotExist):
        return JsonResponse({'code': 4015, 'message': '登录已过期，请重新登录'}, status=401)
    except Exception as e:
        logger.error(f"刷新Token失败: {e}")
        return JsonResponse({'code': 500, 'message': '系统错误'}, status=500)


@csrf_exempt
def user_logout(request):
    if request.method != 'POST':
        return JsonResponse({'code': 405, 'message': '仅支持POST请求'}, status=405)

    revoked = False
    refresh_token = request.COOKIES.get(REFRESH_TOKEN_COOKIE_NAME, '').strip()
    if not refresh_token:
        try:
            data = json.loads(request.body or '{}')
            refresh_token = data.get('refresh_token', '').strip()
        except Exception:
            refresh_token = ''

    if refresh_token:
        try:
            payload = jwt.decode(
                refresh_token,
                settings.JWT_SETTINGS['SECRET_KEY'],
                algorithms=[settings.JWT_SETTINGS['ALGORITHM']],
                options={'verify_exp': False}
            )
            if payload.get('token_type') == 'refresh' and payload.get('jti'):
                revoke_refresh_token(payload['jti'])
                revoked = True
        except jwt.InvalidTokenError:
            pass
        except Exception as e:
            logger.warning(f"登出撤销Refresh Token失败: {e}")

    if not revoked:
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            try:
                access_payload = jwt.decode(
                    auth_header.split(' ', 1)[1].strip(),
                    settings.JWT_SETTINGS['SECRET_KEY'],
                    algorithms=[settings.JWT_SETTINGS['ALGORITHM']],
                    options={'verify_exp': False}
                )
                if access_payload.get('token_type') == 'access':
                    session_jti = access_payload.get('session_jti')
                    user_id = access_payload.get('user_id')
                    if session_jti:
                        revoke_refresh_token(session_jti)
                    elif user_id:
                        clear_active_session(user_id)
            except jwt.InvalidTokenError:
                pass
            except Exception as e:
                logger.warning(f"登出撤销Access会话失败: {e}")

    response = JsonResponse({'code': 200, 'message': '已退出登录'})
    return _delete_refresh_cookie(response)


# -------------------------- 7. 邮箱状态检查 --------------------------
@require_GET
@ratelimit(key='ip', rate='10/m', block=False)
def check_email_exists(request):
    if getattr(request, 'limited', False):
        return JsonResponse({'code': 429, 'message': '请求过于频繁'}, status=429)

    email = request.GET.get('email', '').strip().lower()
    if not email:
        return JsonResponse({'code': 400, 'message': '邮箱不能为空'})

    # 缓存查询
    cache_key = generate_cache_key(PREFIX_EMAIL_CHECK, email)
    try:
        cached_result = redis_client.get(cache_key)
        if cached_result:
            return JsonResponse(json.loads(_decode_redis_text(cached_result)))
    except Exception:
        pass

    # 数据库查询
    is_exists = User.objects.filter(email=email).exists()
    result_data = {
        'code': 1001 if is_exists else 200,
        'message': '该邮箱已注册' if is_exists else '邮箱未注册'
    }

    # 写入缓存
    try:
        timeout = 300 if is_exists else 30
        redis_client.setex(cache_key, timeout, json.dumps(result_data))
    except Exception:
        pass

    return JsonResponse(result_data)
