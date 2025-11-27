import uuid
from django.db import models
from django.db.models import Count, Q
from django.utils import timezone
from django.contrib.auth.models import User


class UploadedFile(models.Model):
    """Store uploaded files with secure random access tokens"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='uploaded_files')
    file = models.FileField(upload_to='uploads/')
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    original_filename = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.original_filename} ({self.token})"
    
    class Meta:
        ordering = ['-uploaded_at']


class QRCode(models.Model):
    """Store generated QR codes"""
    QR_TYPE_CHOICES = [
        ('url', 'URL'),
        ('file', 'File'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='qr_codes')
    qr_type = models.CharField(max_length=10, choices=QR_TYPE_CHOICES)
    content = models.TextField()  # URL or file token
    qr_image = models.ImageField(upload_to='qr_codes/')
    uploaded_file = models.ForeignKey(
        UploadedFile, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name='qr_codes'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.qr_type} - {self.created_at}"
    
    class Meta:
        ordering = ['-created_at']


class ScanAnalytics(models.Model):
    """Track analytics for QR code scans"""
    qr_code = models.ForeignKey(
        QRCode,
        on_delete=models.CASCADE,
        related_name='scans'
    )
    
    # User identification
    ip_address = models.GenericIPAddressField()
    user_identifier = models.CharField(max_length=255)  # Hash of IP + User Agent for unique users
    
    # Location data
    country = models.CharField(max_length=100, default='Unknown')
    city = models.CharField(max_length=100, default='Unknown')
    
    # Device information
    device_type = models.CharField(max_length=50)  # iPhone, Android, Desktop, etc.
    browser = models.CharField(max_length=100, default='Unknown')
    operating_system = models.CharField(max_length=100, default='Unknown')
    
    # Traffic source
    referrer = models.CharField(max_length=500, default='Direct')
    
    # Timestamp
    scanned_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Scan of {self.qr_code} from {self.country} at {self.scanned_at}"
    
    class Meta:
        ordering = ['-scanned_at']
        verbose_name_plural = 'Scan Analytics'
        indexes = [
            models.Index(fields=['qr_code', '-scanned_at']),
            models.Index(fields=['user_identifier']),
        ]
    
    @staticmethod
    def get_stats_for_qr(qr_code, country='', city='', device='', browser=''):
        """Get comprehensive statistics for a QR code with optional filters"""
        scans = ScanAnalytics.objects.filter(qr_code=qr_code)
        
        # Apply filters
        if country:
            scans = scans.filter(country=country)
        if city:
            scans = scans.filter(city=city)
        if device:
            scans = scans.filter(device_type=device)
        if browser:
            scans = scans.filter(browser=browser)
        
        return {
            'total_scans': scans.count(),
            'unique_users': scans.values('user_identifier').distinct().count(),
            'countries': scans.values('country').annotate(count=Count('country')).order_by('-count'),
            'cities': scans.values('city', 'country').annotate(count=Count('city')).order_by('-count'),
            'devices': scans.values('device_type').annotate(count=Count('device_type')).order_by('-count'),
            'browsers': scans.values('browser').annotate(count=Count('browser')).order_by('-count'),
            'hourly_distribution': scans.extra(
                select={'hour': "strftime('%%H', scanned_at)"}
            ).values('hour').annotate(count=Count('id')).order_by('hour'),
            'referrers': scans.values('referrer').annotate(count=Count('referrer')).order_by('-count'),
            'recent_scans': scans[:10],
        }
