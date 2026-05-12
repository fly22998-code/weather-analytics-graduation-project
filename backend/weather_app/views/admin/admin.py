from django.http import JsonResponse
from django.db.models import Q
from django.db import IntegrityError, transaction
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework import serializers
import requests
import redis
import psutil
import re
import time
import json
import logging
import hashlib
import threading
import platform
from datetime import datetime, timedelta
from ...models import User
from ...permissions import admin_required

# 【修改点1】直接从 redis_config 导入 client 和 生成函数
from ..user.redis_config import redis_client, generate_cache_key

# ================= 配置区域 =================
PROTECTED_EMAILS = ["admin@example.com"]
MEITUAN_API_URL = "https://apimobile.meituan.com/locate/v2/ip/loc"
MEITUAN_API_KEY = "yourAppKey"  # 请替换为真实Key
SERVER_STATUS_KEY = "monitor:server_status_v3"
TRAFFIC_PREFIX = "monitor:traffic"

# 全局正则预编译
PHONE_REGEX = re.compile(r'^1[3-9]\d{9}$')
DATE_REGEX = re.compile(r'^\d{4}-\d{2}-\d{2}$')

logger = logging.getLogger(__name__)

# ================= 工具函数 =================

def read_redis_int(key, default=0):
    value = redis_client.get(key)
    if value is None:
        return default
    if isinstance(value, bytes):
        value = value.decode('utf-8', errors='ignore')
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def traffic_daily_key(date_value, name):
    return f"{TRAFFIC_PREFIX}:{date_value.strftime('%Y%m%d')}:{name}"


def traffic_minute_key(date_value):
    return f"{TRAFFIC_PREFIX}:minute:{date_value.strftime('%Y%m%d%H%M')}"


def decode_redis_value(value):
    return value.decode('utf-8', errors='ignore') if isinstance(value, bytes) else value


def get_unique_visitors(date_value):
    key = traffic_daily_key(date_value, 'visitor_unique')
    try:
        return int(redis_client.pfcount(key))
    except Exception:
        return 0


def build_traffic_day(date_value):
    api_total = read_redis_int(traffic_daily_key(date_value, 'api_total'))
    visit_total = read_redis_int(traffic_daily_key(date_value, 'session_total'))
    api_success = read_redis_int(traffic_daily_key(date_value, 'api_success'))
    api_error = read_redis_int(traffic_daily_key(date_value, 'api_error'))
    success_rate = round((api_success / api_total) * 100, 1) if api_total else 0

    return {
        "date": date_value.strftime('%Y-%m-%d'),
        "api_total": api_total,
        "visit_total": visit_total,
        "unique_visitors": get_unique_visitors(date_value),
        "api_success": api_success,
        "api_error": api_error,
        "success_rate": success_rate
    }


def build_minute_series(minutes=30):
    now = timezone.localtime().replace(second=0, microsecond=0)
    start = now - timedelta(minutes=minutes - 1)
    points = []

    for index in range(minutes):
        current = start + timedelta(minutes=index)
        points.append({
            "time": current.strftime('%H:%M'),
            "count": read_redis_int(traffic_minute_key(current))
        })

    return points


def build_endpoint_stats(date_value, limit=20):
    endpoint_key = traffic_daily_key(date_value, 'endpoints')
    endpoint_error_key = traffic_daily_key(date_value, 'endpoint_errors')
    endpoint_user_key = traffic_daily_key(date_value, 'endpoint_users')
    endpoint_user_error_key = traffic_daily_key(date_value, 'endpoint_user_errors')
    try:
        raw_items = redis_client.hgetall(endpoint_key)
    except Exception:
        raw_items = {}
    try:
        raw_error_items = redis_client.hgetall(endpoint_error_key)
    except Exception:
        raw_error_items = {}
    try:
        raw_user_items = redis_client.hgetall(endpoint_user_key)
    except Exception:
        raw_user_items = {}
    try:
        raw_user_error_items = redis_client.hgetall(endpoint_user_error_key)
    except Exception:
        raw_user_error_items = {}

    error_map = {
        decode_redis_value(endpoint): int(decode_redis_value(count) or 0)
        for endpoint, count in raw_error_items.items()
    }
    user_error_map = {
        decode_redis_value(field): int(decode_redis_value(count) or 0)
        for field, count in raw_user_error_items.items()
    }
    endpoint_user_map = {}

    for field, count in raw_user_items.items():
        field_text = decode_redis_value(field)
        if not field_text or '\x1f' not in field_text:
            continue
        endpoint_text, user_label = field_text.split('\x1f', 1)
        total_count = int(decode_redis_value(count) or 0)
        error_count = user_error_map.get(field_text, 0)
        endpoint_user_map.setdefault(endpoint_text, []).append({
            "email": user_label,
            "count": total_count,
            "error_count": error_count,
            "error_rate": round((error_count / total_count) * 100, 1) if total_count else 0
        })

    stats = []
    for endpoint, count in raw_items.items():
        endpoint_text = decode_redis_value(endpoint)
        total_count = int(decode_redis_value(count) or 0)
        error_count = error_map.get(endpoint_text, 0)
        users = endpoint_user_map.get(endpoint_text, [])
        users.sort(key=lambda item: item["count"], reverse=True)
        stats.append({
            "endpoint": endpoint_text,
            "count": total_count,
            "error_count": error_count,
            "error_rate": round((error_count / total_count) * 100, 1) if total_count else 0,
            "users": users[:8]
        })

    stats.sort(key=lambda item: item["count"], reverse=True)
    return stats[:limit]

def format_byte_speed(bytes_per_sec):
    """格式化速率字符串 (匹配前端需求)"""
    if bytes_per_sec < 1024:
        return f"{bytes_per_sec:.2f} B/s"
    elif bytes_per_sec < 1024**2:
        return f"{bytes_per_sec/1024:.2f} KB/s"
    else:
        return f"{bytes_per_sec/1024**2:.2f} MB/s"

def get_ip_location(ip):
    """获取IP归属地 (带缓存优化)"""
    if not ip or ip.strip() in ["", "127.0.0.1", "localhost", "::1", "0.0.0.0"]:
        return "本地"
    
    # 【修改点2】调用 redis_config 中的函数
    # 使用 'monitor:ip_loc' 作为前缀，生成类似 monitor:ip_loc:<md5> 的Key
    cache_key = generate_cache_key('monitor:ip_loc', ip)
    
    cached = redis_client.get(cache_key)
    if cached:
        return cached.decode() if isinstance(cached, bytes) else cached
    
    # 异步或超时控制，防止卡顿
    try:
        params = {"client_source": MEITUAN_API_KEY, "rgeo": "true", "ip": ip}
        resp = requests.get(MEITUAN_API_URL, params=params, timeout=1.5)
        if resp.status_code == 200:
            data = resp.json().get('data', {}).get('rgeo', {})
            loc = ''.join([data.get(k,'') for k in ['province', 'city', 'district'] if data.get(k)])
            if loc:
                redis_client.setex(cache_key, 86400 * 7, loc) # 缓存7天
                return loc
    except:
        pass
    return "未知"

# ================= Serializers =================

class UserSerializer(serializers.ModelSerializer):
    gender_display = serializers.CharField(source='get_gender_display', read_only=True)
    user_role_display = serializers.CharField(source='get_user_role_display', read_only=True)
    is_banned_display = serializers.SerializerMethodField()
    last_login_location = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'phone', 'gender', 'gender_display',
            'user_role', 'user_role_display', 'is_banned', 'is_banned_display',
            'ban_reason', 'birthday', 'last_login_ip', 'last_login_time',
            'login_count', 'created_at', 'password_reset_time', 'ban_time',
            'last_login_location'
        ]
        read_only_fields = ['id', 'email', 'created_at']

    def get_is_banned_display(self, obj):
        return "已封禁" if obj.is_banned else "正常"

    def get_last_login_location(self, obj):
        return get_ip_location(obj.last_login_ip)

    def validate_phone(self, value):
        if value and not PHONE_REGEX.match(value):
            raise serializers.ValidationError("手机号格式不正确")
        return value

    def validate(self, data):
        user = self.instance
        request = self.context.get('request')
        current_admin = request.jwt_payload
        
        # 保护账号逻辑
        if user and user.email in PROTECTED_EMAILS:
            if current_admin.get('email') not in PROTECTED_EMAILS:
                raise serializers.ValidationError("无权修改受保护的系统账号")
        
        # 封禁逻辑
        if data.get('is_banned'):
            if not data.get('ban_reason') and not (user and user.ban_reason):
                 raise serializers.ValidationError({"ban_reason": "封禁必须填写原因"})
        
        return data


class UserListSerializer(serializers.ModelSerializer):
    user_role_display = serializers.CharField(source='get_user_role_display', read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'email', 'phone', 'user_role', 'user_role_display',
            'is_banned', 'last_login_ip', 'last_login_time',
            'login_count', 'created_at'
        ]

# ================= 用户管理 Views =================

@api_view(['GET'])
@admin_required
def user_list(request):
    """用户列表"""
    page = max(int(request.GET.get('page', 1)), 1)
    page_size = min(max(int(request.GET.get('page_size', 10)), 1), 100)
    search = request.GET.get('search', '').strip()
    role = request.GET.get('role', '')
    is_banned = request.GET.get('is_banned', '')

    queryset = User.objects.only(
        'id', 'email', 'phone', 'user_role', 'is_banned',
        'last_login_ip', 'last_login_time', 'login_count', 'created_at',
        'username'
    ).order_by('id')

    if search:
        queryset = queryset.filter(
            Q(email__icontains=search) | 
            Q(username__icontains=search) | 
            Q(phone__icontains=search)
        )
    if role:
        queryset = queryset.filter(user_role=role)
    if is_banned:
        queryset = queryset.filter(is_banned=is_banned.lower() == 'true')

    total = queryset.count()
    users = queryset[(page - 1) * page_size : page * page_size]
    serializer = UserListSerializer(users, many=True)
    
    return JsonResponse({
        "status": "success",
        "total": total,
        "page": page,
        "page_size": page_size,
        "data": serializer.data
    })

@api_view(['GET'])
@admin_required
def user_detail(request, user_id):
    user = get_object_or_404(User, id=user_id)
    serializer = UserSerializer(user)
    return JsonResponse({"status": "success", "data": serializer.data})

@api_view(['PUT'])
@admin_required
def edit_user(request, user_id):
    """编辑用户 (安全事务版)"""
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return JsonResponse({"status": "error", "message": "用户不存在"}, status=404)

    data = request.data.copy()
    # 安全清理
    for field in ['password', 'email', 'id', 'created_at']:
        data.pop(field, None)
    if not data.get('username'): data.pop('username', None)

    serializer = UserSerializer(user, data=data, partial=True, context={'request': request})

    if serializer.is_valid():
        try:
            with transaction.atomic():
                # 处理封禁状态副作用
                if 'is_banned' in serializer.validated_data:
                    is_banned = serializer.validated_data['is_banned']
                    if is_banned:
                        user.ban(serializer.validated_data.get('ban_reason', user.ban_reason))
                    else:
                        user.unban()
                    redis_client.setex(f"user:banned:{user.id}", 600, '1' if is_banned else '0')
                
                serializer.save()

            # 【修改点3】清理缓存时加上明确的业务前缀
            # 因为 redis_config 去掉了 'weather:'，这里我们手动指定 'user:info' 等前缀
            redis_client.delete(
                generate_cache_key('user:info', user.email),
                generate_cache_key('user:login', user.email)
            )
            return JsonResponse({"status": "success", "message": "更新成功", "data": serializer.data})

        except IntegrityError as e:
            msg = "数据冲突"
            if "phone" in str(e): msg = "手机号已被使用"
            if "username" in str(e): msg = "用户名已被使用"
            return JsonResponse({"status": "error", "message": msg}, status=400)
    
    return JsonResponse({"status": "error", "message": list(serializer.errors.values())[0][0]}, status=400)

@api_view(['DELETE'])
@admin_required
def delete_user(request, user_id):
    if request.jwt_payload.get('email') not in PROTECTED_EMAILS:
        return JsonResponse({"status": "error", "message": "无权操作"}, status=403)
    
    user = get_object_or_404(User, id=user_id)
    if user.email in PROTECTED_EMAILS:
        return JsonResponse({"status": "error", "message": "无法删除保护账号"}, status=403)

    user.delete()
    # 清理缓存
    redis_client.delete(generate_cache_key('user:info', user.email))
    return JsonResponse({"status": "success", "message": "删除成功"})

@api_view(['DELETE'])
@admin_required
def batch_delete_users(request):
    if request.jwt_payload.get('email') not in PROTECTED_EMAILS:
        return JsonResponse({"status": "error", "message": "无权操作"}, status=403)
    
    ids = request.data.get('ids', [])
    if not ids: return JsonResponse({"status": "error", "message": "参数无效"}, status=400)

    # 排除保护账号和自己
    exclude_emails = PROTECTED_EMAILS + [request.jwt_payload.get('email')]
    
    with transaction.atomic():
        qs = User.objects.filter(id__in=ids).exclude(email__in=exclude_emails)
        # 注意：Django的delete()不会自动触发单个对象的信号，
        # 如果需要严格清理所有缓存，建议先查出Email再删除，或者依赖缓存自然过期。
        deleted_count, _ = qs.delete()
        
    return JsonResponse({"status": "success", "message": f"删除 {deleted_count} 人"})

# ================= 服务器监控 (核心修复) =================

def collect_server_metrics():
    """
    后台采集任务 - 核心监控逻辑 (已修复磁盘分区显示)
    """
    try:
        # 1. 采样 (阻塞1秒)
        io_start = psutil.disk_io_counters()
        net_start = psutil.net_io_counters()
        time.sleep(1)
        io_end = psutil.disk_io_counters()
        net_end = psutil.net_io_counters()
        
        # 2. 基础数据
        mem = psutil.virtual_memory()
        cpu_percent = psutil.cpu_percent(interval=None)
        
        # 3. 速率计算
        read_speed = io_end.read_bytes - io_start.read_bytes
        write_speed = io_end.write_bytes - io_start.write_bytes
        sent_speed = net_end.bytes_sent - net_start.bytes_sent
        recv_speed = net_end.bytes_recv - net_start.bytes_recv

        # 4. 【新增】磁盘分区遍历逻辑
        partitions_data = []
        try:
            for part in psutil.disk_partitions(all=False):
                # 过滤掉 snap 等虚拟设备 (根据需要调整)
                if 'cdrom' in part.opts or part.device == '':
                    continue
                # Windows/Linux 兼容性处理
                if 'loop' in part.device: 
                    continue
                    
                try:
                    usage = psutil.disk_usage(part.mountpoint)
                    partitions_data.append({
                        "device": part.device,
                        "mountpoint": part.mountpoint,
                        "fstype": part.fstype,
                        "total": usage.total,
                        "used": usage.used,
                        "free": usage.free,
                        "percent": usage.percent
                    })
                except PermissionError:
                    continue
        except Exception as e:
            logger.error(f"磁盘分区获取失败: {e}")

        # 5. 系统信息
        try:
            uptime = time.time() - psutil.boot_time()
            m, s = divmod(uptime, 60)
            h, m = divmod(m, 60)
            d, h = divmod(h, 24)
            uptime_str = f"{int(d)}天 {int(h)}小时 {int(m)}分"
        except:
            uptime_str = "未知"

        # 6. 构建数据
        data = {
            "cpu": {
                "usage_percent": cpu_percent,
                "cores_logical": psutil.cpu_count(),
                "cores_physical": psutil.cpu_count(logical=False),
                "frequency_current": psutil.cpu_freq().current if psutil.cpu_freq() else 0,
                "load_avg": psutil.getloadavg() if hasattr(psutil, "getloadavg") else [0,0,0]
            },
            "memory": {
                "used_percent": mem.percent,
                "used": mem.used,          
                "total": mem.total,        
                "available": mem.available 
            },
            "disk": {
                # 这一行是关键：把分区列表加回去
                "partitions": partitions_data, 
                
                "read_speed": format_byte_speed(read_speed),
                "write_speed": format_byte_speed(write_speed),
                "total_read_bytes": io_end.read_bytes,
                "total_write_bytes": io_end.write_bytes,
                "read_count_per_sec": io_end.read_count - io_start.read_count,
                "write_count_per_sec": io_end.write_count - io_start.write_count,
                "utilization_percent": 0
            },
            "network": {
                "sent_speed": format_byte_speed(sent_speed),
                "recv_speed": format_byte_speed(recv_speed),
                "bytes_sent": net_end.bytes_sent,
                "bytes_recv": net_end.bytes_recv,
                "packets_sent": net_end.packets_sent,
                "packets_recv": net_end.packets_recv,
                "errin": net_end.errin,
                "errout": net_end.errout
            },
            "system": {
                "os_name": platform.system(),
                "os_version": platform.version(),
                "hostname": platform.node(),
                "uptime": uptime_str,
                "process_count": len(psutil.pids()),
                "python_version": platform.python_version(),
                "current_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        }
        
        redis_client.setex(SERVER_STATUS_KEY, 5, json.dumps(data))
        
    except Exception as e:
        logger.error(f"监控采集异常: {e}")

def start_background_monitor():
    """启动后台监控线程"""
    def _run():
        while True:
            collect_server_metrics()
            # collect 内部已有 sleep(1)，此处无需长 sleep
            
    t = threading.Thread(target=_run, daemon=True)
    t.start()

# 自动启动监控 (根据需要取消注释，或在 apps.py ready() 中调用)
start_background_monitor() 

@api_view(['GET'])
@admin_required
def get_traffic_stats(request):
    """后台流量统计：接口调用、访问次数、独立访客和近分钟趋势"""
    try:
        days = int(request.GET.get('days', 7))
    except (TypeError, ValueError):
        days = 7
    days = min(max(days, 1), 30)

    today_date = timezone.localdate()
    daily = [
        build_traffic_day(today_date - timedelta(days=offset))
        for offset in range(days)
    ]

    today = daily[0] if daily else build_traffic_day(today_date)
    minute_series = build_minute_series(30)
    endpoint_stats = build_endpoint_stats(today_date)

    return JsonResponse({
        "status": "success",
        "data": {
            "today": today,
            "daily": daily,
            "minute_series": minute_series,
            "endpoint_stats": endpoint_stats,
            "updated_at": timezone.localtime().strftime('%Y-%m-%d %H:%M:%S')
        }
    })


@api_view(['GET'])
@admin_required
def get_server_status(request):
    """
    状态获取接口 (无阻塞)
    """
    # 1. 读缓存
    cached = redis_client.get(SERVER_STATUS_KEY)
    if cached:
        return JsonResponse({"status": "success", "data": json.loads(cached)})

    # 2. 无缓存时降级 (返回静态数据，不等待速率计算)
    return JsonResponse({
        "status": "success", 
        "data": {
            "cpu": {"usage_percent": 0}, 
            "memory": {"used": 0, "total": 0},
            "system": {"uptime": "初始化中..."}
        }
    })

