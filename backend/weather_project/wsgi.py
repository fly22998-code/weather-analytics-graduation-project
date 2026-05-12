# """
# WSGI config for weather_project project.

# It exposes the WSGI callable as a module-level variable named ``application``.

# For more information on this file, see
# https://docs.djangoproject.com/en/3.2/howto/deployment/wsgi/
# """

# import os

# from django.core.wsgi import get_wsgi_application

# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'weather_project.settings')

# application = get_wsgi_application()

"""
WSGI config for weather_project project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application
import ssl

# 替换为上一步找到的系统根证书路径
os.environ['SSL_CERT_FILE'] = '/etc/ssl/certs/ca-certificates.crt'
# 强制重新加载证书配置
ssl._create_default_https_context = ssl._create_unverified_context  # 临时兼容，后续可移除
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'weather_project.settings')

application = get_wsgi_application()
