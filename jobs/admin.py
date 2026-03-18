from django.contrib import admin
from .models import JobListing, JobApplication


@admin.register(JobListing)
class JobListingAdmin(admin.ModelAdmin):
    list_display = ('title', 'company', 'category', 'employment_type', 'cdl_requirement', 'pay_display', 'status', 'is_urgent', 'created_at')
    list_filter = ('category', 'employment_type', 'cdl_requirement', 'status', 'is_urgent')
    search_fields = ('title', 'company__company_name', 'description')
    raw_id_fields = ('company', 'city_pool')


@admin.register(JobApplication)
class JobApplicationAdmin(admin.ModelAdmin):
    list_display = ('driver', 'job', 'stage', 'flagged_by_dispatcher', 'interview_time', 'created_at')
    list_filter = ('stage', 'flagged_by_dispatcher')
    search_fields = ('driver__user__first_name', 'driver__user__last_name', 'job__title')
    raw_id_fields = ('job', 'driver')


