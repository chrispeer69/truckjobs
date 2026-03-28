from django.db import models
from django.conf import settings


class DriverProfile(models.Model):
    AVAILABILITY_CHOICES = [
        ('actively_hunting', 'Actively Hunting'),
        ('employed_open', 'Employed but Open'),
        ('not_looking', 'Not Looking'),
    ]
    CDL_CHOICES = [
        ('cdl_a', 'CDL-A'),
        ('cdl_b', 'CDL-B'),
        ('no_cdl', 'No CDL'),
    ]
    SHIFT_CHOICES = [
        ('day', 'Day Shift'),
        ('night', 'Night Shift'),
        ('rotating', 'Rotating'),
        ('flexible', 'Flexible'),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='driver_profile')
    city_pool = models.ForeignKey('pools.CityPool', on_delete=models.SET_NULL, null=True, blank=True)
    cdl_class = models.CharField(max_length=10, choices=CDL_CHOICES, default='no_cdl')
    years_experience = models.PositiveIntegerField(default=0)
    specialties = models.CharField(max_length=255, blank=True, help_text='Comma-separated: flatbed,rollback,heavy-duty')
    availability = models.CharField(max_length=20, choices=AVAILABILITY_CHOICES, default='actively_hunting')
    min_pay_hourly = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    preferred_shift = models.CharField(max_length=10, choices=SHIFT_CHOICES, default='flexible')
    willing_relocate = models.BooleanField(default=False)
    bio = models.TextField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=2, blank=True)
    last_employer = models.CharField(max_length=200, blank=True)
    equipment_experience = models.CharField(max_length=255, blank=True)

    is_identity_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    # SMS / Alert preferences
    sms_profile_views = models.BooleanField(default=True)
    sms_interview_req = models.BooleanField(default=True)
    sms_private_offer = models.BooleanField(default=True)
    sms_job_match = models.BooleanField(default=True)
    alert_cdl_expiry = models.BooleanField(default=True)
    alert_dot_expiry = models.BooleanField(default=True)
    alert_mvr_annual = models.BooleanField(default=True)
    alert_wreckmaster = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.get_full_name()} — {self.get_cdl_class_display()}"

    @property
    def initials(self):
        fn = self.user.first_name
        ln = self.user.last_name
        return f"{fn[0]}{ln[0]}".upper() if fn and ln else self.user.username[:2].upper()

    @property
    def specialty_list(self):
        return [s.strip() for s in self.specialties.split(',') if s.strip()] if self.specialties else []

    @property
    def avg_rating(self):
        reviews = self.reviews.all()
        if not reviews:
            return 0
        total = sum(r.overall_average for r in reviews)
        return round(total / len(reviews), 1)

    @property
    def review_count(self):
        return self.reviews.count()

    @property
    def credential_completeness(self):
        total_types = 6  # cdl, dot, mvr, drug_test, wreckmaster, hazmat
        filled = self.credentials.exclude(status='missing').count()
        return int((filled / total_types) * 100) if total_types else 0

    @property
    def companies_viewed_count(self):
        return 0  # MVP placeholder

    @property
    def applications_count(self):
        return self.applications.count()

    @property
    def interviews_count(self):
        return self.applications.filter(stage='interview').count()


class Credential(models.Model):
    TYPE_CHOICES = [
        ('cdl', 'CDL'),
        ('dot_medical', 'DOT Medical Card'),
        ('mvr', 'MVR (Motor Vehicle Record)'),
        ('drug_test', 'Drug Test'),
        ('wreckmaster', 'WreckMaster Certification'),
        ('hazmat', 'Hazmat Endorsement'),
        ('other', 'Other'),
    ]
    STATUS_CHOICES = [
        ('verified', 'Verified'),
        ('pending', 'Pending Review'),
        ('expired', 'Expired'),
        ('missing', 'Not Uploaded'),
    ]

    driver = models.ForeignKey(DriverProfile, on_delete=models.CASCADE, related_name='credentials')
    credential_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='missing')
    file = models.FileField(upload_to='credentials/', null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)

    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['driver', 'credential_type']

    def __str__(self):
        return f"{self.driver} — {self.get_credential_type_display()} ({self.status})"

    @property
    def days_remaining(self):
        if self.expiry_date:
            from django.utils import timezone
            delta = self.expiry_date - timezone.now().date()
            return delta.days
        return None

    @property
    def urgency(self):
        days = self.days_remaining
        if days is None:
            return 'none'
        if days < 30:
            return 'urgent'
        if days < 60:
            return 'warning'
        return 'good'


class DriverReview(models.Model):
    driver = models.ForeignKey(DriverProfile, on_delete=models.CASCADE, related_name='reviews')
    company = models.ForeignKey('companies.CompanyProfile', on_delete=models.CASCADE, related_name='reviews_given')
    reliability = models.PositiveSmallIntegerField(default=5)
    punctuality = models.PositiveSmallIntegerField(default=5)
    equipment = models.PositiveSmallIntegerField(default=5)
    communication = models.PositiveSmallIntegerField(default=5)
    comment = models.TextField(blank=True)
    employed_from = models.DateField(null=True, blank=True)
    employed_to = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review of {self.driver} by {self.company} — {self.overall_average}★"

    @property
    def overall_average(self):
        return round((self.reliability + self.punctuality + self.equipment + self.communication) / 4, 1)

class DriverDocument(models.Model):
    driver = models.ForeignKey(DriverProfile, on_delete=models.CASCADE, related_name='documents')
    file = models.FileField(upload_to='driver_documents/')
    name = models.CharField(max_length=255)
    is_verified = models.BooleanField(default=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} ({self.driver.user.get_full_name()})"
