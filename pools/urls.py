from django.urls import path
from . import views

app_name = 'pools'

urlpatterns = [
    path('', views.pool_list, name='list'),
]
