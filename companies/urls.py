from django.urls import path
from . import views

app_name = 'companies'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('post/', views.post_job, name='post_job'),
    path('jobs/', views.company_jobs, name='company_jobs'),
    path('application/<int:app_id>/stage/', views.update_stage, name='update_stage'),
]
