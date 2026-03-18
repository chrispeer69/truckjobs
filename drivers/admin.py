from django.contrib import admin
from .models import DriverProfile, Credential, DriverReview


@admin.register(DriverProfile)
class DriverProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'cdl_class', 'years_experience', 'city', 'state', 'availability', 'is_active', 'is_identity_verified')
    list_filter = ('cdl_class', 'availability', 'is_active', 'is_identity_verified', 'state')
    search_fields = ('user__first_name', 'user__last_name', 'user__email', 'city')
    raw_id_fields = ('user', 'city_pool')


@admin.register(Credential)
class CredentialAdmin(admin.ModelAdmin):
    list_display = ('driver', 'credential_type', 'status', 'expiry_date', 'days_remaining')
    list_filter = ('credential_type', 'status')
    search_fields = ('driver__user__first_name', 'driver__user__last_name')
    raw_id_fields = ('driver',)


@admin.register(DriverReview)
class DriverReviewAdmin(admin.ModelAdmin):
    list_display = ('driver', 'company', 'overall_average', 'reliability', 'punctuality', 'equipment', 'communication', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('driver__user__first_name', 'driver__user__last_name', 'company__company_name')
    raw_id_fields = ('driver', 'company')
