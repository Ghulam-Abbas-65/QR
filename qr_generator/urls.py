from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('generate/url/', views.generate_url_qr, name='generate_url_qr'),
    path('generate/file/', views.generate_file_qr, name='generate_file_qr'),
    path('result/<int:qr_id>/', views.qr_result, name='qr_result'),
    path('analytics/<int:qr_id>/', views.analytics_dashboard, name='analytics_dashboard'),
    path('check-analytics/', views.check_analytics, name='check_analytics'),
    path('download-qr/<int:qr_id>/<str:format>/', views.download_qr, name='download_qr'),
    path('r/<str:short_code>/', views.dynamic_redirect, name='dynamic_redirect'),
    path('<uuid:token>/', views.download_file, name='download_file'),
]
