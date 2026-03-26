from django.urls import path
from . import views

app_name = 'drivers'

urlpatterns = [
    path('profile/', views.driver_profile, name='profile'),
    path('<int:driver_id>/profile/', views.driver_profile_public, name='driver_profile_public'),
    path('apply/<int:job_id>/', views.quick_apply, name='quick_apply'),
    path('review/company/<int:company_id>/', views.leave_company_review, name='leave_company_review'),
]
