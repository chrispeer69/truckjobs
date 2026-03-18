from django.db import models
from django.conf import settings


class CompanyProfile(models.Model):
    TYPE_CHOICES = [
        ('towing', 'Towing'),
        ('freight', 'Freight / Box Truck'),
        ('both', 'Both'),
    ]
    CONTACT_CHOICES = [
        ('email', 'Email'),
        ('phone', 'Phone'),
        ('text', 'Text Message'),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='company_profile')
    company_name = models.CharField(max_length=200)
    company_type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='both')
    city_pool = models.ForeignKey('pools.CityPool', on_delete=models.SET_NULL, null=True, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=2, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    years_in_operation = models.PositiveIntegerField(default=0)
    contact_name = models.CharField(max_length=100, blank=True)
    contact_method = models.CharField(max_length=10, choices=CONTACT_CHOICES, default='email')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.company_name

    @property
    def initials(self):
        words = self.company_name.split()
        return ''.join(w[0] for w in words[:3]).upper()

    @property
    def active_job_count(self):
        return self.job_listings.filter(status='active').count()

    @property
    def total_applicants(self):
        from jobs.models import JobApplication
        return JobApplication.objects.filter(job__company=self).count()

    @property
    def interviews_this_week(self):
        from jobs.models import JobApplication
        from django.utils import timezone
        from datetime import timedelta
        week_ago = timezone.now() - timedelta(days=7)
        return JobApplication.objects.filter(
            job__company=self,
            stage='interview',
            updated_at__gte=week_ago
        ).count()

class CredentialAccessRequest(models.Model):
    dispatcher = models.ForeignKey(CompanyProfile, on_delete=models.CASCADE, related_name='access_requests')
    driver = models.ForeignKey('drivers.DriverProfile', on_delete=models.CASCADE, related_name='access_requests_received')
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ], default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.dispatcher.company_name} -> {self.driver.user.get_full_name()} ({self.status})"
