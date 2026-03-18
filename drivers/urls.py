from django.urls import path
from . import views

app_name = 'drivers'

urlpatterns = [
    path('profile/', views.driver_profile, name='profile'),
    path('apply/<int:job_id>/', views.quick_apply, name='quick_apply'),
]
