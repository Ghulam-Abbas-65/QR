from django.contrib import admin
from .models import UploadedFile, QRCode, ScanAnalytics


@admin.register(UploadedFile)
class UploadedFileAdmin(admin.ModelAdmin):
    list_display = ['original_filename', 'token', 'uploaded_at']
    readonly_fields = ['token', 'uploaded_at']
    search_fields = ['original_filename', 'token']


@admin.register(QRCode)
class QRCodeAdmin(admin.ModelAdmin):
    list_display = ['qr_type', 'content', 'created_at', 'total_scans']
    list_filter = ['qr_type', 'created_at']
    readonly_fields = ['created_at']
    search_fields = ['content']
    
    def total_scans(self, obj):
        return obj.scans.count()
    total_scans.short_description = 'Total Scans'


@admin.register(ScanAnalytics)
class ScanAnalyticsAdmin(admin.ModelAdmin):
    list_display = ['qr_code', 'country', 'city', 'device_type', 'scanned_at']
    list_filter = ['device_type', 'country', 'scanned_at']
    readonly_fields = ['scanned_at']
    search_fields = ['country', 'city', 'ip_address']
    date_hierarchy = 'scanned_at'
