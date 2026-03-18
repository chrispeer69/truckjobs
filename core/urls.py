from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/driver/', views.register_driver, name='register_driver'),
    path('register/company/', views.register_company, name='register_company'),
]
