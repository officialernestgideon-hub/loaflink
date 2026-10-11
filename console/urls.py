from django.urls import path
from . import views

app_name = 'console'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('bakeries/', views.bakeries, name='bakeries'),
    path('retailers/', views.retailers, name='retailers'),
    path('notifications/', views.notifications_view, name='notifications'),
]