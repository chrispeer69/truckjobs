from django.contrib import admin
from .models import CityPool


@admin.register(CityPool)
class CityPoolAdmin(admin.ModelAdmin):
    list_display = ('name', 'state', 'is_active', 'driver_count', 'company_count', 'open_job_count')
    list_filter = ('state', 'is_active')
    search_fields = ('name',)
