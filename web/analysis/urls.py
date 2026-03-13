from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('request/<int:pk>/', views.request_detail, name='request_detail'),
    path('request/<int:pk>/edit/', views.admin_edit_report, name='admin_edit_report'),
    path('request/<int:pk>/approve/', views.admin_approve_report, name='admin_approve_report'),
    path('api/request/<int:pk>/status/', views.request_status_api, name='request_status_api'),
]
