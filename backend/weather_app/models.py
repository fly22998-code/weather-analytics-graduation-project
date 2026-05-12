from django.db import models
from django.utils import timezone
import datetime
from django.utils.translation import gettext_lazy as _    # 支持多语言（可选）
from django.contrib.auth.hashers import make_password, check_password  # 导入Django内置哈希工具
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator  # 补充导入RegexValidator




class User(models.Model):
    """优化版用户表：修复密码二次加密问题"""
    # 1. 核心登录字段
    email = models.EmailField(
        max_length=100,
        unique=True,
        verbose_name=_("登录邮箱"),
        help_text=_("用户唯一登录账号，不可重复")
    )
    password = models.CharField(
        max_length=255,
        verbose_name=_("加密密码"),
        help_text=_("存储加密后的密码，不存储明文")
    )

    # 2. 基础个人信息
    username = models.CharField(
        max_length=50,
        verbose_name="用户昵称",
        default="默认用户",
        help_text="显示用昵称，可修改，允许重复"
    )
    phone = models.CharField(
        max_length=15,
        null=True,
        blank=True,
        unique=True,
        verbose_name=_("手机号码"),
        help_text=_("可选，用于账号找回、短信通知，需唯一")
    )
    avatar = models.ImageField(
        upload_to="avatar/",
        null=True,
        blank=True,
        verbose_name=_("用户头像"),
        help_text=_("可选，默认使用系统占位图")
    )
    gender = models.CharField(
        max_length=10,
        choices=[
            ("MALE", _("男")),
            ("FEMALE", _("女")),
            ("OTHER", _("其他")),
            ("SECRET", _("保密"))
        ],
        default="SECRET",
        verbose_name=_("性别"),
        help_text=_("默认保密")
    )
    birthday = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("出生日期"),
        help_text=_("可选，用于个性化功能（如生日提醒）")
    )

    # 3. 账号状态与权限
    is_banned = models.BooleanField(
        default=False,
        verbose_name=_("是否被永久封禁"),
        help_text=_("False为正常状态；True时账号被永久封禁，需管理员手动解封")
    )
    ban_reason = models.TextField(
        null=True,
        blank=True,
        verbose_name=_("封禁原因"),
        help_text=_("记录永久封禁的原因，如违反平台规则等")
    )
    ban_time = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("封禁时间"),
        help_text=_("账号被永久封禁时的时间，自动记录")
    )

    is_staff = models.BooleanField(
        default=False,
        verbose_name=_("是否为管理员"),
        help_text=_("True时可登录Django后台管理系统，管理数据")
    )
    user_role = models.CharField(
        max_length=20,
        choices=[
            ("NORMAL", _("普通用户")),
            ("VIP", _("会员用户")),
            ("ADMIN", _("系统管理员"))
        ],
        default="NORMAL",
        verbose_name=_("用户角色"),
        help_text=_("控制功能权限（如普通用户无数据导出权限）")
    )

    # 4. 安全与时间相关
    last_login_ip = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name=_("上次登录IP"),
        help_text=_("记录用户上次登录的IP地址，用于安全审计")
    )
    last_login_time = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("上次登录时间"),
        help_text=_("记录用户上次登录的时间")
    )
    login_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_("累计登录次数"),
        help_text=_("统计用户成功登录的总次数，每次登录自动+1")
    )
    password_reset_time = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("密码最后修改时间"),
        help_text=_("用于提示用户定期修改密码，增强安全性")
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=_("注册时间"),
        help_text=_("用户账号创建时间，自动生成")
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("信息更新时间"),
        help_text=_("用户信息修改时自动更新")
    )

    class Meta:
        verbose_name = _("用户")
        verbose_name_plural = _("用户")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["email"]),
            models.Index(fields=["phone"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["is_banned"]),
            models.Index(fields=["user_role", "is_banned"]),
        ]

    def __str__(self):
        return f"{self.username}（{self.email}）"

    def save(self, *args, **kwargs):
        # 修复核心：仅在密码真正变化且为明文时加密
        if self.pk:  # 存在主键 = 更新操作
            try:
                old_user = User.objects.get(pk=self.pk)
                # 只有当密码被修改，且新密码不是已加密状态时才加密
                if self.password != old_user.password and not self.password.startswith('$'):
                    self.password = make_password(self.password)
                    self.password_reset_time = timezone.now()  # 仅修改密码时更新重置时间
            except User.DoesNotExist:
                pass  # 理论上不会触发，防止意外
        else:  # 新建用户 = 必须加密
            if not self.password.startswith('$'):
                self.password = make_password(self.password)
        
        super().save(*args, **kwargs)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)

    def ban(self, reason: str):
        self.is_banned = True
        self.ban_reason = reason
        self.ban_time = timezone.now()
        self.save(update_fields=['is_banned', 'ban_reason', 'ban_time'])

    def unban(self):
        self.is_banned = False
        self.ban_reason = None
        self.ban_time = None
        self.save(update_fields=['is_banned', 'ban_reason', 'ban_time'])


# -------------------------- 修复：UserVerifyCode 独立定义（不嵌套在任何类内） --------------------------
class UserVerifyCode(models.Model):
    """用户验证码表：用于密码找回、邮箱验证等场景，存储临时验证码"""
    email = models.EmailField(  # 改用EmailField，自动校验邮箱格式
        max_length=100,
        verbose_name="用户邮箱",
        help_text="接收验证码的用户邮箱"
    )
    verify_code = models.CharField(
        max_length=6,
        verbose_name="6位验证码",
        help_text="随机生成的6位数字验证码"
    )
    expire_time = models.DateTimeField(
        verbose_name="过期时间",
        help_text="验证码有效期（默认5分钟）"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="创建时间",
        help_text="验证码生成时间"
    )

    class Meta:
        verbose_name = "用户验证码"
        verbose_name_plural = verbose_name
        indexes = [
            models.Index(fields=["email"]),  # 加速按邮箱查询验证码
            models.Index(fields=["email", "expire_time"]),  # 加速“邮箱+有效期”组合查询
        ]
        # 避免同一邮箱在有效期内有多个验证码
        constraints = [
            models.UniqueConstraint(
                fields=["email"],
                condition=models.Q(expire_time__gt=timezone.now()),
                name="unique_active_verify_code"
            )
        ]

    def __str__(self):
        return f"{self.email} - {self.verify_code}（{self.expire_time.strftime('%Y-%m-%d %H:%M')}过期）"

    # 类方法：生成验证码并创建记录（5分钟过期）
    @classmethod
    def create_code(cls, email, verify_code):
        expire_time = timezone.now() + datetime.timedelta(minutes=5)
        return cls.objects.create(
            email=email,
            verify_code=verify_code,
            expire_time=expire_time
        )

