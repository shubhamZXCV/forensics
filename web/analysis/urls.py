from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('request/<int:pk>/', views.request_detail, name='request_detail'),
    path('api/request/<int:pk>/status/', views.request_status_api, name='request_status_api'),
]
