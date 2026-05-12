import hashlib
import secrets
import time
from django.conf import settings
from django.utils import timezone
import jwt
import json
import datetime
import os
import ipaddress  # 新增：用于IP处理
import uuid       # 新增：用于生成文件名
from functools import wraps  # 新增：用于装饰器

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import IntegrityError
from weather_app.models import User
from .redis_config import *

# -------------------------- 装饰器 (新增：DRY原则核心) --------------------------

def jwt_login_required(roles=None):
    """
    JWT鉴权装饰器
    :param roles: 允许访问的角色列表，例如 ['ADMIN']，为 None 则只验证登录
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # 1. 提取 Token
            auth_header = request.headers.get('Authorization', '')
            if not auth_header.startswith('Bearer '):
                return JsonResponse({'code': 401, 'message': '未提供有效 Token'}, status=401)
            
            token = auth_header.split(' ')[1]
            
            # 2. 验证 Token
            try:
                payload = jwt.decode(
                    token,
                    settings.JWT_SETTINGS['SECRET_KEY'],
                    algorithms=[settings.JWT_SETTINGS['ALGORITHM']]
                )
                if payload.get('token_type', 'access') != 'access':
                    return JsonResponse({'code': 401, 'message': 'Token 类型无效'}, status=401)

                user_id = payload.get('user_id')
                session_jti = payload.get('session_jti')
                active_jti = get_active_session_jti(user_id) if user_id else None
                if not session_jti or not active_jti or session_jti != active_jti:
                    return JsonResponse({
                        'code': 4017,
                        'message': '账号已在其他设备登录，当前会话已切换为游客模式'
                    }, status=401)
                
                # 3. 角色校验
                if roles and payload.get('user_role') not in roles:
                     logger.warning(f"权限不足访问，用户ID: {payload.get('user_id')}")
                     return JsonResponse({'code': 403, 'message': '无权访问'}, status=403)

                # 4. 将用户信息挂载到 request 对象，供视图直接使用
                request.user_payload = payload
                request.user_id = user_id
                request.user_email = payload.get('email')
                request.user_role = payload.get('user_role')
                
                return view_func(request, *args, **kwargs)
                
            except jwt.ExpiredSignatureError:
                return JsonResponse({'code': 4012, 'message': 'Access Token 已过期'}, status=401)
            except jwt.InvalidTokenError:
                return JsonResponse({'code': 401, 'message': 'Token 无效'}, status=401)
            except Exception as e:
                logger.error(f"JWT 鉴权未知错误: {str(e)}")
                return JsonResponse({'code': 500, 'message': '鉴权服务异常'}, status=500)
        return _wrapped_view
    return decorator


# -------------------------- 工具函数 --------------------------

# (保留原逻辑) 生成JWT Token工具函数
def generate_jwt_token(user_id, user_role, email, username, session_jti=None):
    expire_hours = settings.JWT_SETTINGS.get('ACCESS_EXPIRE_MINUTES', 15) / 60
    current_shanghai_time = timezone.now()
    expire_shanghai_time = current_shanghai_time + datetime.timedelta(hours=expire_hours)
    expire_utc_time = expire_shanghai_time.astimezone(datetime.timezone.utc)
    
    payload = {
        'user_id': user_id,
        'user_role': user_role,
        'email': email,
        'username': username,
        'token_type': 'access',
        'exp': expire_utc_time,
        'iat': current_shanghai_time.astimezone(datetime.timezone.utc),
        'jti': hashlib.sha256(f"{user_id}{current_shanghai_time}".encode()).hexdigest()[:32]
    }
    if session_jti:
        payload['session_jti'] = session_jti
    
    token = jwt.encode(
        payload,
        settings.JWT_SETTINGS['SECRET_KEY'],
        algorithm=settings.JWT_SETTINGS['ALGORITHM']
    )
    
    expire_minutes = settings.JWT_SETTINGS.get('ACCESS_EXPIRE_MINUTES', 15)
    expire_text = f"{expire_minutes}分钟"
    return token, int(expire_utc_time.timestamp()), expire_text


def generate_refresh_token(user_id):
    expire_days = settings.JWT_SETTINGS.get('REFRESH_EXPIRE_DAYS', 7)
    current_time = timezone.now()
    expire_time = current_time + datetime.timedelta(days=expire_days)
    expire_utc_time = expire_time.astimezone(datetime.timezone.utc)
    jti = hashlib.sha256(f"refresh:{user_id}:{current_time}:{uuid.uuid4()}".encode()).hexdigest()

    payload = {
        'user_id': user_id,
        'token_type': 'refresh',
        'exp': expire_utc_time,
        'iat': current_time.astimezone(datetime.timezone.utc),
        'jti': jti
    }

    token = jwt.encode(
        payload,
        settings.JWT_SETTINGS['SECRET_KEY'],
        algorithm=settings.JWT_SETTINGS['ALGORITHM']
    )
    return token, jti, int(expire_utc_time.timestamp()), f"{expire_days}天"


def generate_session_sign_key():
    return secrets.token_urlsafe(32)


def store_refresh_token(user_id, jti, expire_at, sign_key=None):
    ttl = max(expire_at - int(time.time()), 1)
    redis_client.setex(f"refresh_token:{jti}", ttl, str(user_id))
    if sign_key:
        redis_client.setex(f"sign_key:session:{jti}", ttl, sign_key)


def _decode_redis_value(value):
    if isinstance(value, bytes):
        return value.decode('utf-8')
    return value


def get_active_session_jti(user_id):
    if not user_id:
        return None
    return _decode_redis_value(redis_client.get(f"user_active_session:{user_id}"))


def set_active_session(user_id, jti, expire_at):
    ttl = max(expire_at - int(time.time()), 1)
    redis_client.setex(f"user_active_session:{user_id}", ttl, jti)


def clear_active_session(user_id, jti=None):
    if not user_id:
        return
    active_jti = get_active_session_jti(user_id)
    if jti is None or active_jti == jti:
        redis_client.delete(f"user_active_session:{user_id}")


def revoke_refresh_token(jti):
    user_id = _decode_redis_value(redis_client.get(f"refresh_token:{jti}"))
    redis_client.delete(f"refresh_token:{jti}")
    redis_client.delete(f"sign_key:session:{jti}")
    clear_active_session(user_id, jti)


def store_guest_sign_key(guest_id, sign_key, expire_at):
    ttl = max(expire_at - int(time.time()), 1)
    redis_client.setex(f"sign_key:guest:{guest_id}", ttl, sign_key)


API_SECRET_KEY = os.getenv("API_SIGN_SECRET", "")
SIGN_EXPIRE_SECONDS = 60


def _get_session_sign_key(request):
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        token = auth_header.split(' ', 1)[1].strip()
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SETTINGS['SECRET_KEY'],
                algorithms=[settings.JWT_SETTINGS['ALGORITHM']],
                options={'verify_exp': True}
            )
            if payload.get('token_type') != 'access':
                return None, "Token 类型无效"
            session_jti = payload.get('session_jti')
            if not session_jti:
                return None, "缺少会话签名标识"
            active_jti = get_active_session_jti(payload.get('user_id'))
            if active_jti != session_jti:
                return None, "账号已在其他设备登录"
            sign_key = redis_client.get(f"sign_key:session:{session_jti}")
            if isinstance(sign_key, bytes):
                sign_key = sign_key.decode('utf-8')
            return sign_key, "验证通过" if sign_key else "会话签名已失效"
        except jwt.ExpiredSignatureError:
            return None, "Access Token 已过期"
        except jwt.InvalidTokenError:
            return None, "Token 无效"

    guest_token = request.headers.get('X-Guest-Token', '').strip()
    if guest_token:
        try:
            payload = jwt.decode(
                guest_token,
                settings.JWT_SETTINGS['SECRET_KEY'],
                algorithms=[settings.JWT_SETTINGS['ALGORITHM']],
                options={'verify_exp': True}
            )
            if payload.get('token_type') != 'guest':
                return None, "游客Token类型无效"
            guest_id = payload.get('guest_id')
            if not guest_id:
                return None, "游客身份无效"
            sign_key = redis_client.get(f"sign_key:guest:{guest_id}")
            if isinstance(sign_key, bytes):
                sign_key = sign_key.decode('utf-8')
            return sign_key, "验证通过" if sign_key else "游客签名已失效"
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            return None, "游客身份无效，请重新获取游客Token"

    return None, "缺少会话签名身份"


def verify_signed_headers(request, params=None, require_session_key=False):
    params = params or {}
    client_sign = request.headers.get('X-Sign')
    timestamp = request.headers.get('X-Timestamp')
    nonce = request.headers.get('X-Nonce')

    if not all([client_sign, timestamp, nonce]):
        return False, "缺少签名参数"

    try:
        req_time = int(timestamp)
        current_time = int(time.time() * 1000)
        if abs(current_time - req_time) > (SIGN_EXPIRE_SECONDS * 1000):
            return False, "请求已过期"
    except ValueError:
        return False, "时间戳格式错误"

    try:
        nonce_key = f"nonce:{nonce}"
        is_new_request = redis_client.set(nonce_key, "1", ex=SIGN_EXPIRE_SECONDS, nx=True)
        if not is_new_request:
            return False, "重复的请求"
    except Exception as e:
        logger.error(f"Redis Error in signature check: {e}")
        return False, "内部校验服务异常"

    filtered_params = {k: v for k, v in params.items() if v != ''}
    sorted_keys = sorted(filtered_params.keys())
    param_str = "&".join(f"{key}={filtered_params[key]}" for key in sorted_keys)
    sign_key = API_SECRET_KEY
    if require_session_key:
        sign_key, key_msg = _get_session_sign_key(request)
        if not sign_key:
            return False, key_msg

    raw_str = f"{param_str}&timestamp={timestamp}&nonce={nonce}&secret={sign_key}"
    server_sign = hashlib.md5(raw_str.encode('utf-8')).hexdigest().upper()

    if client_sign != server_sign:
        return False, "签名验证失败"

    return True, "验证通过"


# (优化版) 获取客户端IP
def get_client_ip(request):
    """获取客户端真实IP地址（使用标准库优化版）"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ips = [ip.strip() for ip in x_forwarded_for.split(',') if ip.strip()]
        for ip_str in ips:
            try:
                # 使用 ipaddress 库判断是否为内网IP
                ip_obj = ipaddress.ip_address(ip_str)
                if not (ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_reserved):
                    return str(ip_obj)
            except ValueError:
                continue
        # 如果过滤后没有公网IP，则返回列表第一个（通常是最近的代理）
        if ips:
            return ips[0]
            
    return request.META.get('REMOTE_ADDR', 'unknown')

# (保留原逻辑) ImageFieldFile序列化
def get_avatar_url(avatar_field):
    import urllib.parse
    if not avatar_field or avatar_field is None:
        return ''
    if hasattr(avatar_field, 'url'):
        return urllib.parse.quote(avatar_field.url, safe=':/')
    return urllib.parse.quote(str(avatar_field), safe=':/')


# -------------------------- 视图函数 (业务逻辑) --------------------------

@csrf_exempt
@jwt_login_required(roles=['ADMIN']) # 直接使用装饰器鉴权
def admin_dashboard(request):
    """管理员看板接口"""
    # 鉴权逻辑已被装饰器接管，直接写业务
    return JsonResponse({
        'code': 200,
        'message': '管理员数据加载成功',
        'data': {'stats': '管理员专用数据'}
    })


@csrf_exempt
@jwt_login_required() # 通用登录鉴权
def get_current_user_info(request):
    """获取当前用户信息接口"""
    if request.method != 'GET':
        return JsonResponse({'code': 405, 'message': '仅支持 GET 请求'}, status=405)
    
    # 直接使用装饰器挂载的 email
    user_email = request.user_email
    
    try:
        user = User.objects.get(email=user_email)
        
        user_data = {
            'email': user.email,
            'username': user.username,
            'role': user.role if hasattr(user, 'role') else request.user_role,
            'avatar': get_avatar_url(user.avatar) if hasattr(user, 'avatar') else '',
            'phone': user.phone if hasattr(user, 'phone') and user.phone else '',
            'gender': user.gender if hasattr(user, 'gender') and user.gender else '',
            'birthday': user.birthday if hasattr(user, 'birthday') and user.birthday else ''
        }
        
        return JsonResponse({
            'code': 200, 
            'message': '获取用户信息成功', 
            'data': user_data
        })
        
    except User.DoesNotExist:
        return JsonResponse({'code': 404, 'message': '用户不存在'}, status=404)
    except Exception as db_err:
        logger.error(f"查询用户信息数据库错误：{str(db_err)}")
        return JsonResponse({'code': 500, 'message': '查询用户信息失败'}, status=500)

@csrf_exempt
@jwt_login_required()
def save_user_info(request):
    """保存用户信息接口 (逻辑优化版)"""
    try:
        request_data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'code': 400, 'message': '请求体格式错误，需为JSON'}, status=400)
    
    validation_errors = []
    
    # 1. 基础字段清洗与验证
    # 用户名
    username = request_data.get('username', '').strip() if request_data.get('username') else ''
    if 'username' in request_data and (len(username) < 2 or len(username) > 20):
        validation_errors.append('用户名长度需在2-20个字符之间')

    # 性别
    gender = request_data.get('gender', '').strip().upper() if request_data.get('gender') else ''
    if 'gender' in request_data and gender not in ['MALE', 'FEMALE', 'OTHER', 'SECRET', '']:
        validation_errors.append('性别值无效')

    # 生日
    birthday = request_data.get('birthday', '').strip() if request_data.get('birthday') else None
    if birthday:
        try:
            datetime.datetime.strptime(birthday, '%Y-%m-%d')
        except ValueError:
            validation_errors.append('生日格式无效，需为YYYY-MM-DD')

    # 手机号 (含唯一性校验预处理)
    phone = request_data.get('phone', '').strip() if request_data.get('phone') else ''
    if 'phone' in request_data:
        if phone and (not phone.isdigit() or len(phone) != 11):
            validation_errors.append('手机号需为11位数字')
        elif phone:
            # 唯一性检查
            if User.objects.filter(phone=phone).exclude(id=request.user_id).exists():
                validation_errors.append('该手机号已被其他用户绑定')

    if validation_errors:
        return JsonResponse({'code': 400, 'message': '参数验证失败', 'errors': validation_errors}, status=400)

    # 2. 数据库更新
    try:
        user = User.objects.get(id=request.user_id) # 直接用ID查更稳
        
        # 动态更新存在的字段
        if 'username' in request_data:
            user.username = username
        if 'gender' in request_data:
            user.gender = gender
        if 'birthday' in request_data:
            user.birthday = birthday # None or valid date string
        if 'phone' in request_data:
            # 核心修复：空值设为None避免唯一键冲突
            user.phone = phone if phone else None

        user.save()
        logger.info(f"用户信息更新成功，用户ID: {request.user_id}, IP: {get_client_ip(request)}")
        
        # 3. 构造返回数据
        updated_user_data = {
            'email': user.email,
            'username': user.username,
            'role': user.user_role if hasattr(user, 'user_role') else request.user_role,
            'avatar': get_avatar_url(user.avatar) if hasattr(user, 'avatar') else '',
            'phone': user.phone if hasattr(user, 'phone') else '',
            'gender': user.gender if hasattr(user, 'gender') else '',
            'birthday': user.birthday if (user.birthday and hasattr(user, 'birthday')) else ''
        }
        
        return JsonResponse({'code': 200, 'message': '用户信息保存成功', 'data': updated_user_data})
        
    except User.DoesNotExist:
        return JsonResponse({'code': 404, 'message': '该用户不存在'}, status=404)
    except IntegrityError as e:
        # 双重保险，防止并发时的唯一性冲突
        if 'phone' in str(e):
            return JsonResponse({'code': 400, 'message': '该手机号已被其他用户绑定'}, status=400)
        logger.error(f"数据库完整性错误: {e}")
        return JsonResponse({'code': 500, 'message': '保存失败，数据冲突'}, status=500)
    except Exception as e:
        logger.error(f"保存用户信息未知错误: {str(e)}")
        return JsonResponse({'code': 500, 'message': '服务器内部错误'}, status=500)


@csrf_exempt
@jwt_login_required()
def upload_avatar(request):
    """头像上传接口 (内存与文件名优化版)"""
    if request.method != 'POST':
        return JsonResponse({'code': 405, 'message': '仅支持POST请求'}, status=405)
    
    if 'avatar' not in request.FILES:
        return JsonResponse({'code': 400, 'message': '未上传头像文件'}, status=400)
    
    avatar_file = request.FILES['avatar']
    
    # 验证文件
    allowed_types = ['image/jpeg', 'image/png']
    if avatar_file.content_type not in allowed_types:
        return JsonResponse({'code': 400, 'message': '仅支持JPG/PNG格式图片'}, status=400)
    
    if avatar_file.size > 2 * 1024 * 1024:
        return JsonResponse({'code': 400, 'message': '图片大小不能超过2MB'}, status=400)
    
    try:
        user = User.objects.get(id=request.user_id)
        
        # 1. 记录旧头像路径用于后续删除
        old_avatar_path = user.avatar.path if (user.avatar and hasattr(user.avatar, 'path')) else None
        
        # 2. 生成标准化文件名 (user_ID_UUID.ext)
        file_ext = os.path.splitext(avatar_file.name)[1].lower()
        if file_ext not in ['.jpg', '.jpeg', '.png']:
            file_ext = '.png'
            
        new_filename = f"user_{user.id}_{uuid.uuid4().hex[:8]}{file_ext}"
        
        # 3. 核心优化：直接修改文件对象名称，无需内存重组
        avatar_file.name = new_filename
        user.avatar = avatar_file
        user.save() # Django 会自动处理保存逻辑
        
        # 4. 安全删除旧文件 (只有在保存成功后才删除)
        if old_avatar_path and os.path.exists(old_avatar_path):
            try:
                # 简单防卫：确保删除的是头像目录下的文件
                if 'avatar' in old_avatar_path: 
                    os.remove(old_avatar_path)
            except Exception as e:
                logger.warning(f"旧头像删除失败 (不影响主流程): {e}")

        return JsonResponse({
            'code': 200, 
            'message': '头像上传成功',
            'data': {
                'avatar_path': user.avatar.url,
                'avatar_name': user.avatar.name
            }
        })
            
    except User.DoesNotExist:
        return JsonResponse({'code': 404, 'message': '用户不存在'}, status=404)
    except Exception as e:
        logger.error(f"头像上传错误：{str(e)}")
        return JsonResponse({'code': 500, 'message': f'服务器错误：{str(e)}'}, status=500)


@csrf_exempt
@jwt_login_required()
def check_username(request):
    """验证昵称重复接口"""
    if request.method != 'POST':
        return JsonResponse({'code': 405, 'message': '仅支持POST请求'}, status=405)
    
    try:
        request_data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'code': 400, 'message': '请求体格式错误'}, status=400)
    
    username = request_data.get('username', '').strip()
    if not username:
        return JsonResponse({'code': 400, 'message': '昵称不能为空'}, status=400)
    
    if len(username) < 2 or len(username) > 20:
        return JsonResponse({'code': 400, 'message': '昵称长度需在2-20个字符之间'}, status=400)
    
    try:
        # 使用装饰器中的 user_id 排除自身
        duplicate_exists = User.objects.filter(username=username).exclude(id=request.user_id).exists()
        
        if duplicate_exists:
            return JsonResponse({'code': 200, 'message': '该昵称已被占用', 'data': False})
        else:
            return JsonResponse({'code': 200, 'message': '昵称可用', 'data': True})
            
    except Exception as e:
        logger.error(f"验证昵称出错: {str(e)}")
        return JsonResponse({'code': 500, 'message': '验证服务异常'}, status=500)

