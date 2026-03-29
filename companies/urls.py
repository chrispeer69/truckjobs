from django.urls import path
from . import views

app_name = 'companies'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('job/<int:job_id>/kanban/', views.job_kanban, name='job_kanban'),
    path('job/<int:job_id>/dashboard/', views.job_dashboard, name='job_dashboard'),
    path('job/<int:job_id>/edit/', views.edit_job, name='edit_job'),
    path('job/<int:job_id>/publish/', views.publish_job, name='publish_job'),
    path('job/<int:job_id>/close/', views.close_job, name='close_job'),
    path('<int:company_id>/profile/', views.company_profile_public, name='company_profile_public'),
    path('post/', views.post_job, name='post_job'),
    path('jobs/', views.company_jobs, name='company_jobs'),
    path('application/<int:app_id>/stage/', views.update_stage, name='update_stage'),
    path('driver/<int:driver_id>/documents/', views.view_driver_documents, name='view_driver_documents'),
    path('review/driver/<int:driver_id>/', views.leave_driver_review, name='leave_driver_review'),
]
