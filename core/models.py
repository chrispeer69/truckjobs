from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_CHOICES = [
        ('driver', 'Driver'),
        ('company', 'Company'),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='driver')

    def is_driver(self):
        return self.role == 'driver'

    def is_company(self):
        return self.role == 'company'

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.role})"


class PasswordResetOTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='otp_codes')
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_valid(self):
        from django.utils import timezone
        import datetime
        return timezone.now() < self.created_at + datetime.timedelta(minutes=15)
