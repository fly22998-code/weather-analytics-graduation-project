# weather_app/urls.py
from django.urls import path
from .views.user import *
from .views.admin import *


app_name = 'weather_app'

urlpatterns = [
    # -------------------------- 普通用户接口 --------------------------
    # 注册相关
    path('user/register/', user_register, name='user_register'),
    path('user/send-register-code/', send_register_code, name='send_register_code'),
    path('user/check-email/', check_email_exists, name='check_email'),
    # 登录
    path('user/login/', user_login, name='user_login'),
    path('user/refresh/', refresh_access_token, name='refresh_access_token'),
    path('user/logout/', user_logout, name='user_logout'),
    path('user/guest-token/', issue_guest_token, name='issue_guest_token'),
    # 密码找回
    path('user/send-reset-code/', send_verify_code, name='send_reset_code'),
    path('user/verify-code/', verify_code, name='verify_code'),
    path('user/reset-password/', reset_password, name='reset_password'),
    # 天气查询 - 调用具体的视图函数
    path('user/weather/', weather_view, name='weather_view'),
    path('user/weather/history', weather_history, name='weather_history'),
    path('user/weather/history/', weather_history, name='weather_history_slash'),
    path('user/weather/predict', weather_prediction_view, name='weather_prediction'),
    path('user/historical/weather/', historical_weather_view, name='historical_weather_alias'),
    path('user/current/', get_current_user_info, name='get_current_user_info'),
    path('user/save/', save_user_info, name='save_user_info'),
    path('user/upload/avatar/', upload_avatar, name='upload_avatar'),
    path('user/check-username/', check_username, name='check_username'),
    path('user/location/search', location_search, name='location_search'),
    path('user/weather/now',  weather_now, name= 'weather_now'),
    






    # -------------------------- 管理员接口 --------------------------
    # 用户列表接口
    path('admin/users/', user_list, name='admin-user-list'),
    # 单个用户详情接口
    path('admin/users/<int:user_id>/info/', user_detail, name='admin-user-detail'),
    # 用户编辑接口
    path('admin/users/<int:user_id>/edit/', edit_user, name='admin-user-edit'),
    path('admin/users/<int:user_id>/delete/', delete_user, name='admin-user-delete'),
    path('admin/users/batch-delete/', batch_delete_users, name='admin-user-batch-delete'),
    path('admin/users/ip-search/', get_ip_location, name='get_ip_location'),
    path('admin/users/traffic-stats/', get_traffic_stats, name='get_traffic_stats'),
    path('admin/users/server-status/', get_server_status, name='get_server_status'),
]
