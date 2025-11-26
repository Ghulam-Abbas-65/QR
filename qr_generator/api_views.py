from rest_framework import viewsets, status
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.core.files.base import ContentFile
from .models import QRCode, UploadedFile, ScanAnalytics
from .serializers import (
    QRCodeSerializer, URLQRCreateSerializer, 
    FileQRCreateSerializer, ScanAnalyticsSerializer
)
from .views import create_qr_code


@api_view(['POST'])
def generate_url_qr_api(request):
    """API endpoint to generate QR code from URL"""
    serializer = URLQRCreateSerializer(data=request.data)
    
    if serializer.is_valid():
        url = serializer.validated_data['url']
        
        # Generate QR code
        qr_image = create_qr_code(url)
        
        # Save to database
        qr_code = QRCode.objects.create(
            qr_type='url',
            content=url,
        )
        qr_code.qr_image.save(
            f'qr_{qr_code.id}.png',
            ContentFile(qr_image),
            save=True
        )
        
        return Response(
            QRCodeSerializer(qr_code, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def generate_file_qr_api(request):
    """API endpoint to generate QR code from uploaded file"""
    serializer = FileQRCreateSerializer(data=request.data)
    
    if serializer.is_valid():
        uploaded_file = request.FILES['file']
        
        # Save the uploaded file with secure token
        file_obj = UploadedFile.objects.create(
            file=uploaded_file,
            original_filename=uploaded_file.name
        )
        
        # Create secure download URL using token
        download_url = request.build_absolute_uri(
            reverse('download_file', kwargs={'token': file_obj.token})
        )
        
        # Generate QR code with the secure URL
        qr_image = create_qr_code(download_url)
        
        # Save QR code to database
        qr_code = QRCode.objects.create(
            qr_type='file',
            content=download_url,
            uploaded_file=file_obj
        )
        qr_code.qr_image.save(
            f'qr_{qr_code.id}.png',
            ContentFile(qr_image),
            save=True
        )
        
        return Response(
            QRCodeSerializer(qr_code, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def qr_code_detail_api(request, qr_id):
    """Get QR code details"""
    qr_code = get_object_or_404(QRCode, id=qr_id)
    return Response(QRCodeSerializer(qr_code, context={'request': request}).data)


@api_view(['GET'])
def qr_code_list_api(request):
    """List all QR codes with optional search"""
    search = request.GET.get('search', '')
    
    if search:
        from django.db.models import Q
        qr_codes = QRCode.objects.filter(
            Q(id__icontains=search) |
            Q(content__icontains=search) |
            Q(uploaded_file__original_filename__icontains=search)
        ).select_related('uploaded_file').order_by('-created_at')[:20]
    else:
        qr_codes = QRCode.objects.filter(qr_type='file').select_related('uploaded_file').order_by('-created_at')[:10]
    
    return Response(QRCodeSerializer(qr_codes, many=True, context={'request': request}).data)


@api_view(['GET'])
def analytics_api(request, qr_id):
    """Get analytics for a QR code with optional filters"""
    try:
        qr_code = get_object_or_404(QRCode, id=qr_id)
        
        # Get filter parameters
        country = request.GET.get('country', '')
        city = request.GET.get('city', '')
        device = request.GET.get('device', '')
        browser = request.GET.get('browser', '')
        
        # Get filtered stats
        stats = ScanAnalytics.get_stats_for_qr(qr_code, country, city, device, browser)
        
        # Get filter options
        all_scans = ScanAnalytics.objects.filter(qr_code=qr_code)
        filter_options = {
            'countries': list(all_scans.values_list('country', flat=True).distinct().order_by('country')),
            'cities': list(all_scans.values_list('city', flat=True).distinct().order_by('city')),
            'devices': list(all_scans.values_list('device_type', flat=True).distinct().order_by('device_type')),
            'browsers': list(all_scans.values_list('browser', flat=True).distinct().order_by('browser')),
        }
        
        # Convert QuerySets to lists for JSON serialization
        stats['countries'] = list(stats['countries'])
        stats['cities'] = list(stats['cities'])
        stats['devices'] = list(stats['devices'])
        stats['browsers'] = list(stats['browsers'])
        stats['hourly_distribution'] = list(stats['hourly_distribution'])
        stats['referrers'] = list(stats['referrers'])
        stats['recent_scans'] = ScanAnalyticsSerializer(stats['recent_scans'], many=True).data
        
        return Response({
            'qr_code': QRCodeSerializer(qr_code, context={'request': request}).data,
            'stats': stats,
            'filter_options': filter_options,
        })
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
