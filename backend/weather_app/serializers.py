from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from .models import User

class UserSerializer(serializers.ModelSerializer):
    """用户信息序列化器"""
    # 只读字段
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)
    last_login_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)
    password_reset_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)
    ban_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)
    
    # 状态显示转换
    is_banned_display = serializers.CharField(source='get_is_banned_display', read_only=True)
    gender_display = serializers.CharField(source='get_gender_display', read_only=True)
    user_role_display = serializers.CharField(source='get_user_role_display', read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'phone', 'gender', 'gender_display',
            'is_banned', 'is_banned_display', 'user_role', 'user_role_display',
            'last_login_ip', 'login_count', 'created_at', 'password',
            'ban_reason', 'ban_time', 'last_login_time', 'password_reset_time'
        ]
        extra_kwargs = {
            'password': {'write_only': True, 'required': False}
        }

    def create(self, validated_data):
        # 处理密码加密
        if 'password' in validated_data:
            validated_data['password'] = make_password(validated_data['password'])
        return super().create(validated_data)

    def update(self, instance, validated_data):
        # 处理密码更新
        if 'password' in validated_data:
            validated_data['password'] = make_password(validated_data['password'])
        return super().update(instance, validated_data)

    def validate_email(self, value):
        """验证邮箱唯一性（更新时排除自身）"""
        instance = getattr(self, 'instance', None)
        if User.objects.filter(email=value).exclude(pk=getattr(instance, 'pk', None)).exists():
            raise serializers.ValidationError("该邮箱已被使用")
        return value

    def validate_phone(self, value):
        """验证手机号唯一性（允许为空）"""
        if not value:
            return value
        instance = getattr(self, 'instance', None)
        if User.objects.filter(phone=value).exclude(pk=getattr(instance, 'pk', None)).exists():
            raise serializers.ValidationError("该手机号已被使用")
        return value

