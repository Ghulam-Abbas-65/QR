from django.urls import path
from . import api_views

urlpatterns = [
    path('qr-codes/', api_views.qr_code_list_api, name='api_qr_list'),
    path('qr-codes/<int:qr_id>/', api_views.qr_code_detail_api, name='api_qr_detail'),
    path('qr-codes/<int:qr_id>/analytics/', api_views.analytics_api, name='api_analytics'),
    path('generate/url/', api_views.generate_url_qr_api, name='api_generate_url'),
    path('generate/file/', api_views.generate_file_qr_api, name='api_generate_file'),
]
