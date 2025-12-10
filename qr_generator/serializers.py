from rest_framework import serializers
from .models import (
    Project, QRCode, UploadedFile, ScanAnalytics,
    QRCustomization, QRAdvancedOptions, QRUTMParameters, QRDeviceRedirects
)


class ProjectSerializer(serializers.ModelSerializer):
    qr_code_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Project
        fields = ['id', 'name', 'description', 'created_at', 'updated_at', 'qr_code_count']
        read_only_fields = ['id', 'created_at', 'updated_at', 'qr_code_count']
    
    def get_qr_code_count(self, obj):
        return obj.qr_codes.count()


class ProjectCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, allow_blank=True)


class UploadedFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UploadedFile
        fields = ['id', 'token', 'original_filename', 'uploaded_at']


class QRCodeSerializer(serializers.ModelSerializer):
    uploaded_file = UploadedFileSerializer(read_only=True)
    project = ProjectSerializer(read_only=True)
    project_id = serializers.IntegerField(write_only=True, required=False)
    scan_count = serializers.SerializerMethodField()
    qr_image = serializers.SerializerMethodField()
    redirect_url = serializers.SerializerMethodField()
    
    class Meta:
        model = QRCode
        fields = [
            'id', 'project', 'project_id', 'qr_type', 'content', 'qr_image', 'uploaded_file', 
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
        """Return the redirect URL for ALL QR codes (for tracking)"""
        if obj.short_code:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(f'/r/{obj.short_code}/')
        return None


class QRCustomizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = QRCustomization
        fields = ["color", "size"]


class QRAdvancedOptionsSerializer(serializers.ModelSerializer):
    class Meta:
        model = QRAdvancedOptions
        fields = ["password_protection", "expiry_date", "use_short_url"]


class QRUTMParametersSerializer(serializers.ModelSerializer):
    class Meta:
        model = QRUTMParameters
        fields = ["utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content"]


class URLQRCreateSerializer(serializers.Serializer):
    project_id = serializers.IntegerField(required=True)
    url = serializers.URLField()
    title = serializers.CharField(max_length=255, required=False, allow_blank=True)
    qr_customization = QRCustomizationSerializer(required=False)
    advanced_options = QRAdvancedOptionsSerializer(required=False)
    utm_parameters = QRUTMParametersSerializer(required=False)


class FileQRCreateSerializer(serializers.Serializer):
    project_id = serializers.IntegerField(required=True)
    file = serializers.FileField()
    title = serializers.CharField(max_length=255, required=False, allow_blank=True)
    qr_customization = QRCustomizationSerializer(required=False)
    advanced_options = QRAdvancedOptionsSerializer(required=False)
    utm_parameters = QRUTMParametersSerializer(required=False)


class QRDeviceRedirectsSerializer(serializers.ModelSerializer):
    class Meta:
        model = QRDeviceRedirects
        fields = ["mobile_url", "desktop_url", "default_url"]


class DynamicQRCreateSerializer(serializers.Serializer):
    project_id = serializers.IntegerField(required=True)
    default_url = serializers.URLField(required=False)
    mobile_url = serializers.URLField(required=False)
    desktop_url = serializers.URLField(required=False)
    title = serializers.CharField(max_length=255, required=False, allow_blank=True)
    qr_customization = QRCustomizationSerializer(required=False)
    advanced_options = QRAdvancedOptionsSerializer(required=False)
    utm_parameters = QRUTMParametersSerializer(required=False)
    
    def validate(self, data):
        """At least one URL must be provided"""
        if not any([data.get('default_url'), data.get('mobile_url'), data.get('desktop_url')]):
            raise serializers.ValidationError("At least one URL (default_url, mobile_url, or desktop_url) must be provided.")
        return data


class ScanAnalyticsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScanAnalytics
        fields = ['id', 'country', 'city', 'device_type', 'browser', 'operating_system', 'scanned_at']


class RecentScanSerializer(serializers.ModelSerializer):
    """Serializer for recent QR scans with project and QR code information"""
    project_name = serializers.SerializerMethodField()
    qr_name = serializers.SerializerMethodField()
    device_name = serializers.SerializerMethodField()
    location = serializers.SerializerMethodField()
    date = serializers.SerializerMethodField()
    time = serializers.SerializerMethodField()
    
    class Meta:
        model = ScanAnalytics
        fields = [
            'id', 'project_name', 'qr_name', 'device_name', 
            'location', 'date', 'time', 'scanned_at'
        ]
    
    def get_project_name(self, obj):
        """Get project name from QR code"""
        return obj.qr_code.project.name if obj.qr_code.project else 'No Project'
    
    def get_qr_name(self, obj):
        """Get QR code name"""
        return obj.qr_code.name if obj.qr_code.name else f"QR {obj.qr_code.id}"
    
    def get_device_name(self, obj):
        """Get device name (capitalize device_type)"""
        return obj.device_type.title() if obj.device_type else 'Unknown'
    
    def get_location(self, obj):
        """Get location as city, country or just country"""
        if obj.city and obj.city != 'Unknown':
            return f"{obj.city}, {obj.country}" if obj.country != 'Unknown' else obj.city
        return obj.country if obj.country != 'Unknown' else 'Unknown'
    
    def get_date(self, obj):
        """Format date as 'Month Day, Year' (e.g., 'May 29, 2017')"""
        return obj.scanned_at.strftime('%B %d, %Y')
    
    def get_time(self, obj):
        """Format time as 'H:MM am/pm' (e.g., '5:45 am')"""
        return obj.scanned_at.strftime('%I:%M %p').lower()
