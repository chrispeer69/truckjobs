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
