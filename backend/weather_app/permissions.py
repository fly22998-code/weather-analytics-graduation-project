# permissions.py
from django.http import JsonResponse
from django.conf import settings
import jwt
from functools import wraps
from weather_app.views.user.user_utils import get_active_session_jti

def admin_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return JsonResponse({'status': 'error', 'message': '未提供Token'}, status=401)
        token = auth_header.split(' ')[1]
        
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SETTINGS['SECRET_KEY'],
                algorithms=[settings.JWT_SETTINGS['ALGORITHM']]
            )
            
            if payload.get('user_role') != 'ADMIN':
                return JsonResponse({'status': 'error', 'message': '无管理员权限'}, status=403)

            user_id = payload.get('user_id')
            session_jti = payload.get('session_jti')
            active_jti = get_active_session_jti(user_id) if user_id else None
            if payload.get('token_type', 'access') != 'access' or not session_jti or active_jti != session_jti:
                return JsonResponse({
                    'status': 'error',
                    'code': 4017,
                    'message': '账号已在其他设备登录，当前会话已切换为游客模式'
                }, status=401)
            
            # 将Token中的用户信息绑定到request对象
            request.jwt_payload = payload  # 新增这一行
            return view_func(request, *args, **kwargs)
            
        except jwt.ExpiredSignatureError:
            return JsonResponse({'status': 'error', 'code': 4012, 'message': 'Access Token 已过期'}, status=401)
        except jwt.InvalidTokenError:
            return JsonResponse({'status': 'error', 'message': 'Token无效'}, status=401)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'权限校验失败：{str(e)}'}, status=500)
    return wrapper
