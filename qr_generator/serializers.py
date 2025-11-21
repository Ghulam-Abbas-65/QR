from rest_framework import serializers
from .models import QRCode, UploadedFile, ScanAnalytics


class UploadedFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UploadedFile
        fields = ['id', 'token', 'original_filename', 'uploaded_at']


class QRCodeSerializer(serializers.ModelSerializer):
    uploaded_file = UploadedFileSerializer(read_only=True)
    scan_count = serializers.SerializerMethodField()
    
    class Meta:
        model = QRCode
        fields = ['id', 'qr_type', 'content', 'qr_image', 'uploaded_file', 'created_at', 'scan_count']
    
    def get_scan_count(self, obj):
        return obj.scans.count()


class URLQRCreateSerializer(serializers.Serializer):
    url = serializers.URLField()


class FileQRCreateSerializer(serializers.Serializer):
    file = serializers.FileField()


class ScanAnalyticsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScanAnalytics
        fields = ['id', 'country', 'city', 'device_type', 'browser', 'operating_system', 'scanned_at']
