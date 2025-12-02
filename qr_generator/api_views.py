from rest_framework import viewsets, status
from rest_framework.decorators import api_view, action, permission_classes
from rest_framework.permissions import AllowAny
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
        
        # Save to database first (to get short_code)
        qr_code = QRCode.objects.create(
            user=request.user,
            qr_type='url',
            content=url,
        )
        
        # Generate redirect URL for tracking
        redirect_url = request.build_absolute_uri(
            reverse('dynamic_redirect', kwargs={'short_code': qr_code.short_code})
        )
        
        # Generate QR code pointing to redirect URL
        qr_image = create_qr_code(redirect_url)
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
            user=request.user,
            file=uploaded_file,
            original_filename=uploaded_file.name
        )
        
        # Create secure download URL using token
        download_url = request.build_absolute_uri(
            reverse('download_file', kwargs={'token': file_obj.token})
        )
        
        # Save QR code to database first (to get short_code)
        qr_code = QRCode.objects.create(
            user=request.user,
            qr_type='file',
            content=download_url,
            uploaded_file=file_obj
        )
        
        # Generate redirect URL for tracking
        redirect_url = request.build_absolute_uri(
            reverse('dynamic_redirect', kwargs={'short_code': qr_code.short_code})
        )
        
        # Generate QR code pointing to redirect URL
        qr_image = create_qr_code(redirect_url)
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
    qr_code = get_object_or_404(QRCode, id=qr_id, user=request.user)
    return Response(QRCodeSerializer(qr_code, context={'request': request}).data)


@api_view(['GET'])
def qr_code_list_api(request):
    """List all QR codes with optional search"""
    search = request.GET.get('search', '')
    
    if search:
        from django.db.models import Q
        qr_codes = QRCode.objects.filter(
            user=request.user
        ).filter(
            Q(id__icontains=search) |
            Q(content__icontains=search) |
            Q(name__icontains=search) |
            Q(uploaded_file__original_filename__icontains=search)
        ).select_related('uploaded_file').order_by('-created_at')[:20]
    else:
        qr_codes = QRCode.objects.filter(
            user=request.user
        ).select_related('uploaded_file').order_by('-created_at')[:20]
    
    return Response(QRCodeSerializer(qr_codes, many=True, context={'request': request}).data)


@api_view(['POST'])
def generate_dynamic_qr_api(request):
    """API endpoint to generate dynamic QR code for URL"""
    url = request.data.get('url', '')
    name = request.data.get('name', '')
    
    if not url:
        return Response({'error': 'URL is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Validate URL format
    if not url.startswith(('http://', 'https://')):
        return Response({'error': 'Invalid URL format'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Create dynamic QR code (short_code is auto-generated in model save)
    qr_code = QRCode.objects.create(
        user=request.user,
        qr_type='dynamic',
        content=url,
        name=name,
    )
    
    # Generate redirect URL
    redirect_url = request.build_absolute_uri(
        reverse('dynamic_redirect', kwargs={'short_code': qr_code.short_code})
    )
    
    # Generate QR code image pointing to redirect URL
    qr_image = create_qr_code(redirect_url)
    qr_code.qr_image.save(
        f'qr_dynamic_{qr_code.id}.png',
        ContentFile(qr_image),
        save=True
    )
    
    return Response(
        QRCodeSerializer(qr_code, context={'request': request}).data,
        status=status.HTTP_201_CREATED
    )


@api_view(['POST'])
def generate_dynamic_file_qr_api(request):
    """API endpoint to generate dynamic QR code for file"""
    if 'file' not in request.FILES:
        return Response({'error': 'File is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    uploaded_file = request.FILES['file']
    name = request.data.get('name', '')
    
    # Save the uploaded file
    file_obj = UploadedFile.objects.create(
        user=request.user,
        file=uploaded_file,
        original_filename=uploaded_file.name
    )
    
    # Create download URL
    download_url = request.build_absolute_uri(
        reverse('download_file', kwargs={'token': file_obj.token})
    )
    
    # Create dynamic QR code
    qr_code = QRCode.objects.create(
        user=request.user,
        qr_type='dynamic',
        content=download_url,
        name=name,
        uploaded_file=file_obj,
    )
    
    # Generate redirect URL
    redirect_url = request.build_absolute_uri(
        reverse('dynamic_redirect', kwargs={'short_code': qr_code.short_code})
    )
    
    # Generate QR code image
    qr_image = create_qr_code(redirect_url)
    qr_code.qr_image.save(
        f'qr_dynamic_{qr_code.id}.png',
        ContentFile(qr_image),
        save=True
    )
    
    return Response(
        QRCodeSerializer(qr_code, context={'request': request}).data,
        status=status.HTTP_201_CREATED
    )


@api_view(['PUT', 'POST'])
def update_dynamic_qr_api(request, qr_id):
    """Update dynamic QR code destination (URL or File)"""
    qr_code = get_object_or_404(QRCode, id=qr_id, user=request.user, qr_type='dynamic')
    
    url = request.data.get('url')
    name = request.data.get('name')
    is_active = request.data.get('is_active')
    
    # Handle URL update
    if url:
        if not url.startswith(('http://', 'https://')):
            return Response({'error': 'Invalid URL format'}, status=status.HTTP_400_BAD_REQUEST)
        qr_code.content = url
        qr_code.uploaded_file = None  # Clear file reference if switching to URL
    
    # Handle file replacement
    if 'file' in request.FILES:
        uploaded_file = request.FILES['file']
        
        # Create new file
        file_obj = UploadedFile.objects.create(
            user=request.user,
            file=uploaded_file,
            original_filename=uploaded_file.name
        )
        
        # Update QR code to point to new file
        download_url = request.build_absolute_uri(
            reverse('download_file', kwargs={'token': file_obj.token})
        )
        qr_code.content = download_url
        qr_code.uploaded_file = file_obj
    
    if name is not None:
        qr_code.name = name
    
    if is_active is not None:
        qr_code.is_active = is_active
    
    qr_code.save()
    
    return Response({
        'message': 'QR code updated successfully',
        'qr_code': QRCodeSerializer(qr_code, context={'request': request}).data
    })


@api_view(['GET'])
def analytics_api(request, qr_id):
    """Get analytics for a QR code with optional filters"""
    try:
        qr_code = get_object_or_404(QRCode, id=qr_id, user=request.user)
        
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
