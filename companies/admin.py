from django.contrib import admin
from .models import CompanyProfile


@admin.register(CompanyProfile)
class CompanyProfileAdmin(admin.ModelAdmin):
    list_display = ('company_name', 'company_type', 'city', 'state', 'contact_name', 'active_job_count')
    list_filter = ('company_type', 'state')
    search_fields = ('company_name', 'contact_name', 'user__email')
    raw_id_fields = ('user', 'city_pool')
