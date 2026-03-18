from django.db import models
import json


class JobListing(models.Model):
    CATEGORY_CHOICES = [
        ('tow_truck', 'Tow Truck'),
        ('box_truck', 'Box Truck'),
        ('dispatcher', 'Dispatcher'),
        ('shop', 'Shop / Mechanic'),
    ]
    EMPLOYMENT_CHOICES = [
        ('full_time', 'Full Time'),
        ('part_time', 'Part Time'),
        ('contract', '1099 / Contract'),
        ('temp', 'Temporary'),
    ]
    CDL_CHOICES = [
        ('cdl_a', 'CDL-A Required'),
        ('cdl_b', 'CDL-B Required'),
        ('no_cdl', 'No CDL Required'),
        ('cdl_preferred', 'CDL Preferred'),
    ]
    PAY_TYPE_CHOICES = [
        ('hourly', 'Per Hour'),
        ('per_mile', 'Per Mile'),
        ('salary', 'Salary'),
        ('per_load', 'Per Load'),
    ]
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('filled', 'Filled'),
        ('draft', 'Draft'),
    ]

    company = models.ForeignKey('companies.CompanyProfile', on_delete=models.CASCADE, related_name='job_listings')
    city_pool = models.ForeignKey('pools.CityPool', on_delete=models.SET_NULL, null=True, blank=True)
    title = models.CharField(max_length=200)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='tow_truck')
    employment_type = models.CharField(max_length=20, choices=EMPLOYMENT_CHOICES, default='full_time')
    cdl_requirement = models.CharField(max_length=20, choices=CDL_CHOICES, default='no_cdl')
    experience_years = models.PositiveIntegerField(default=0)
    pay_min = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    pay_max = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    pay_type = models.CharField(max_length=10, choices=PAY_TYPE_CHOICES, default='hourly')
    description = models.TextField(blank=True)
    benefits = models.TextField(blank=True, help_text='JSON list of benefits')
    is_urgent = models.BooleanField(default=False)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_urgent', '-created_at']

    def __str__(self):
        return f"{self.title} at {self.company}"

    @property
    def pay_display(self):
        if self.pay_min and self.pay_max:
            if self.pay_type == 'hourly':
                return f"${self.pay_min:.0f}–${self.pay_max:.0f}/hr"
            elif self.pay_type == 'salary':
                return f"${self.pay_min:,.0f}–${self.pay_max:,.0f}/yr"
            elif self.pay_type == 'per_mile':
                return f"${self.pay_min:.2f}–${self.pay_max:.2f}/mi"
            elif self.pay_type == 'per_load':
                return f"${self.pay_min:.0f}–${self.pay_max:.0f}/load"
        elif self.pay_min:
            if self.pay_type == 'hourly':
                return f"${self.pay_min:.0f}/hr+"
            return f"${self.pay_min:,.0f}+"
        return "Pay DOE"

    @property
    def benefits_list(self):
        if self.benefits:
            try:
                return json.loads(self.benefits)
            except (json.JSONDecodeError, TypeError):
                return []
        return []

    @property
    def matched_drivers_count(self):
        if self.city_pool:
            return self.city_pool.driverprofile_set.filter(is_active=True).count()
        return 0

    @property
    def application_count(self):
        return self.applications.count()

    def time_since_posted(self):
        from django.utils import timezone
        delta = timezone.now() - self.created_at
        if delta.days > 0:
            return f"{delta.days}d ago"
        hours = delta.seconds // 3600
        if hours > 0:
            return f"{hours}h ago"
        return "Just now"


class JobApplication(models.Model):
    STAGE_CHOICES = [
        ('applied', 'Applied'),
        ('reviewed', 'Reviewed'),
        ('interview', 'Interview'),
        ('hired', 'Hired'),
    ]

    job = models.ForeignKey(JobListing, on_delete=models.CASCADE, related_name='applications')
    driver = models.ForeignKey('drivers.DriverProfile', on_delete=models.CASCADE, related_name='applications')
    stage = models.CharField(max_length=10, choices=STAGE_CHOICES, default='applied')
    flagged_by_dispatcher = models.BooleanField(default=False)
    interview_time = models.DateTimeField(null=True, blank=True)
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['job', 'driver']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.driver} → {self.job} [{self.stage}]"
