from rest_framework import serializers
from .models import QRCode, UploadedFile, ScanAnalytics


class UploadedFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UploadedFile
        fields = ['id', 'token', 'original_filename', 'uploaded_at']


class QRCodeSerializer(serializers.ModelSerializer):
    uploaded_file = UploadedFileSerializer(read_only=True)
    scan_count = serializers.SerializerMethodField()
    qr_image = serializers.SerializerMethodField()
    redirect_url = serializers.SerializerMethodField()
    
    class Meta:
        model = QRCode
        fields = [
            'id', 'qr_type', 'content', 'qr_image', 'uploaded_file', 
            'short_code', 'is_active', 'name', 'redirect_url',
            'created_at', 'updated_at', 'scan_count'
        ]
    
    def get_scan_count(self, obj):
        return obj.scans.count()
    
    def get_qr_image(self, obj):
        request = self.context.get('request')
        if obj.qr_image and request:
            return request.build_absolute_uri(obj.qr_image.url)
        return obj.qr_image.url if obj.qr_image else None
    
    def get_redirect_url(self, obj):
        """Return the redirect URL for dynamic QR codes"""
        if obj.qr_type == 'dynamic' and obj.short_code:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(f'/r/{obj.short_code}/')
        return None


class URLQRCreateSerializer(serializers.Serializer):
    url = serializers.URLField()


class FileQRCreateSerializer(serializers.Serializer):
    file = serializers.FileField()


class ScanAnalyticsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScanAnalytics
        fields = ['id', 'country', 'city', 'device_type', 'browser', 'operating_system', 'scanned_at']
