from django.urls import path, include
from . import api_views

urlpatterns = [
    # Authentication endpoints
    path('auth/', include('qr_generator.auth_urls')),
    
    # Dashboard endpoint
    path('dashboard/overview/', api_views.dashboard_overview_api, name='api_dashboard_overview'),
    path('dashboard/recent-scans/', api_views.recent_scans_api, name='api_recent_scans'),
    
    # Project management endpoints
    path('projects/', api_views.list_projects_api, name='api_projects_list'),
    path('projects/create/', api_views.create_project_api, name='api_project_create'),
    path('projects/<int:project_id>/', api_views.get_project_api, name='api_project_detail'),
    path('projects/<int:project_id>/update/', api_views.update_project_api, name='api_project_update'),
    path('projects/<int:project_id>/delete/', api_views.delete_project_api, name='api_project_delete'),
    
    # QR code endpoints (require authentication)
    path('qr-codes/', api_views.qr_code_list_api, name='api_qr_list'),
    path('qr-codes/<int:qr_id>/', api_views.qr_code_detail_api, name='api_qr_detail'),
    path('qr-codes/<int:qr_id>/analytics/', api_views.analytics_api, name='api_analytics'),
    path('qr-codes/<int:qr_id>/update/', api_views.update_dynamic_qr_api, name='api_update_dynamic'),
    path('generate/url/', api_views.generate_url_qr_api, name='api_generate_url'),
    path('generate/file/', api_views.generate_file_qr_api, name='api_generate_file'),
    path('generate/dynamic/', api_views.generate_dynamic_qr_api, name='api_generate_dynamic'),
    path('generate/dynamic-file/', api_views.generate_dynamic_file_qr_api, name='api_generate_dynamic_file'),
]
