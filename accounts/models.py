from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.validators import RegexValidator


# Shared phone validator
phone_validator = RegexValidator(
    regex=r'^\+?[0-9]{7,15}$',
    message='Enter a valid phone number (7–15 digits, optional + prefix).'
)


# ============================================================
# USER MANAGER
# ============================================================
class UserManager(BaseUserManager):
    """Manager for phone-based User model."""

    def create_user(self, phone, password=None, **extra_fields):
        if not phone:
            raise ValueError('Phone number is required.')
        user = self.model(phone=phone, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, phone, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'admin')
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        return self.create_user(phone, password, **extra_fields)


# ============================================================
# USER
# ============================================================
class User(AbstractBaseUser, PermissionsMixin):
    """
    Central auth model. Uses phone as login field.
    Role determines what the user can access after login.
    """

    ROLE_CHOICES = [
        ('admin', 'Platform Admin'),
        ('bakery', 'Bakery'),
        ('retailer', 'Retailer'),
    ]

    phone = models.CharField(
        max_length=20,
        unique=True,
        validators=[phone_validator],
        help_text='Login phone number, e.g. +2348012345678'
    )
    full_name = models.CharField(max_length=120, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='retailer')

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    # OTP fields (used in Stage 3)
    otp_code = models.CharField(max_length=6, blank=True)
    otp_created_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.phone} ({self.get_role_display()})'
