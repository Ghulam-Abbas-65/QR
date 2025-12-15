from rest_framework import viewsets, status
from rest_framework.decorators import api_view, action, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.core.files.base import ContentFile
from django.utils import timezone
from datetime import timedelta, datetime
from django.db.models import Count, Q, Max
from .models import (
    Project, QRCode, UploadedFile, ScanAnalytics,
    QRCustomization, QRAdvancedOptions, QRUTMParameters, QRDeviceRedirects
)
from .serializers import (
    ProjectSerializer, ProjectCreateSerializer,
    QRCodeSerializer, URLQRCreateSerializer, 
    FileQRCreateSerializer, ScanAnalyticsSerializer, 
    DynamicQRCreateSerializer, RecentScanSerializer,
    TopPerformingQRSerializer
)
from .views import create_qr_code


# ==================== PROJECT MANAGEMENT APIs ====================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_project_api(request):
    """Create a new project"""
    if not request.user.is_active:
        return Response({
            'error': 'Email verification required.',
            'requires_verification': True
        }, status=status.HTTP_403_FORBIDDEN)
    
    serializer = ProjectCreateSerializer(data=request.data)
    if serializer.is_valid():
        name = serializer.validated_data['name']
        description = serializer.validated_data.get('description', '')
        
        # Check if project with same name already exists for this user
        if Project.objects.filter(user=request.user, name=name).exists():
            return Response({
                'error': 'A project with this name already exists.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        project = Project.objects.create(
            user=request.user,
            name=name,
            description=description
        )
        
        return Response(
            ProjectSerializer(project).data,
            status=status.HTTP_201_CREATED
        )
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_projects_api(request):
    """List all projects for the authenticated user"""
    projects = Project.objects.filter(user=request.user).order_by('-created_at')
    return Response(
        ProjectSerializer(projects, many=True).data,
        status=status.HTTP_200_OK
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_project_api(request, project_id):
    """Get project details"""
    project = get_object_or_404(Project, id=project_id, user=request.user)
    return Response(
        ProjectSerializer(project).data,
        status=status.HTTP_200_OK
    )


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_project_api(request, project_id):
    """Update project"""
    project = get_object_or_404(Project, id=project_id, user=request.user)
    
    name = request.data.get('name')
    description = request.data.get('description')
    
    if name:
        # Check if another project with same name exists
        if Project.objects.filter(user=request.user, name=name).exclude(id=project_id).exists():
            return Response({
                'error': 'A project with this name already exists.'
            }, status=status.HTTP_400_BAD_REQUEST)
        project.name = name
    
    if description is not None:
        project.description = description
    
    project.save()
    
    return Response(
        ProjectSerializer(project).data,
        status=status.HTTP_200_OK
    )


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_project_api(request, project_id):
    """Delete project (and all its QR codes)"""
    project = get_object_or_404(Project, id=project_id, user=request.user)
    project.delete()
    
    return Response({
        'message': 'Project deleted successfully'
    }, status=status.HTTP_200_OK)


# ==================== QR CODE GENERATION APIs ====================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_url_qr_api(request):
    """API endpoint to generate QR code from URL with customization, advanced options, and UTM parameters"""
    # Check if user is verified (active)
    if not request.user.is_active:
        return Response({
            'error': 'Email verification required. Please verify your email address before generating QR codes.',
            'requires_verification': True,
            'user_email': request.user.email
        }, status=status.HTTP_403_FORBIDDEN)
    
    serializer = URLQRCreateSerializer(data=request.data)
    
    if serializer.is_valid():
        project_id = serializer.validated_data['project_id']
        url = serializer.validated_data['url']
        title = serializer.validated_data.get('title', '')
        customization_data = serializer.validated_data.get('qr_customization', None)
        advanced_data = serializer.validated_data.get('advanced_options', None)
        utm_data = serializer.validated_data.get('utm_parameters', None)
        
        # Verify project belongs to user
        try:
            project = Project.objects.get(id=project_id, user=request.user)
        except Project.DoesNotExist:
            return Response({
                'error': 'Project not found or you do not have permission to access it.'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Build final URL with UTM parameters if present
        final_url = url
        if utm_data:
            from urllib.parse import urlencode
            params = {
                k: v for k, v in {
                    'utm_source': utm_data.get('utm_source'),
                    'utm_medium': utm_data.get('utm_medium'),
                    'utm_campaign': utm_data.get('utm_campaign'),
                    'utm_term': utm_data.get('utm_term'),
                    'utm_content': utm_data.get('utm_content'),
                }.items() if v
            }
            if params:
                final_url += ('&' if '?' in final_url else '?') + urlencode(params)
        
        # Save to database first (to get short_code)
        qr_code = QRCode.objects.create(
            user=request.user,
            project=project,
            qr_type='url',
            content=final_url,
            name=title if title else '',
        )
        
        # Create related objects if provided
        if customization_data:
            QRCustomization.objects.create(qr=qr_code, **customization_data)
        
        if advanced_data:
            QRAdvancedOptions.objects.create(qr=qr_code, **advanced_data)
        
        if utm_data:
            QRUTMParameters.objects.create(qr=qr_code, **utm_data)
        
        # Generate redirect URL for tracking
        redirect_url = request.build_absolute_uri(
            reverse('dynamic_redirect', kwargs={'short_code': qr_code.short_code})
        )
        
        # Generate QR code with customization options pointing to tracking redirect URL
        qr_image = create_qr_code(redirect_url, qr_code)
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
@permission_classes([IsAuthenticated])
def generate_file_qr_api(request):
    """API endpoint to generate QR code from uploaded file with customization, advanced options, and UTM parameters"""
    # Check if user is verified (active)
    if not request.user.is_active:
        return Response({
            'error': 'Email verification required. Please verify your email address before generating QR codes.',
            'requires_verification': True,
            'user_email': request.user.email
        }, status=status.HTTP_403_FORBIDDEN)
    
    serializer = FileQRCreateSerializer(data=request.data)
    
    if serializer.is_valid():
        project_id = serializer.validated_data['project_id']
        uploaded_file = request.FILES['file']
        title = serializer.validated_data.get('title', '')
        customization_data = serializer.validated_data.get('qr_customization', None)
        advanced_data = serializer.validated_data.get('advanced_options', None)
        utm_data = serializer.validated_data.get('utm_parameters', None)
        
        # Verify project belongs to user
        try:
            project = Project.objects.get(id=project_id, user=request.user)
        except Project.DoesNotExist:
            return Response({
                'error': 'Project not found or you do not have permission to access it.'
            }, status=status.HTTP_404_NOT_FOUND)
        
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
        
        # Build final URL with UTM parameters if present
        final_url = download_url
        if utm_data:
            from urllib.parse import urlencode
            params = {
                k: v for k, v in {
                    'utm_source': utm_data.get('utm_source'),
                    'utm_medium': utm_data.get('utm_medium'),
                    'utm_campaign': utm_data.get('utm_campaign'),
                    'utm_term': utm_data.get('utm_term'),
                    'utm_content': utm_data.get('utm_content'),
                }.items() if v
            }
            if params:
                final_url += ('&' if '?' in final_url else '?') + urlencode(params)
        
        # Save QR code to database first (to get short_code)
        qr_code = QRCode.objects.create(
            user=request.user,
            project=project,
            qr_type='file',
            content=final_url,
            name=title if title else '',
            uploaded_file=file_obj
        )
        
        # Create related objects if provided
        if customization_data:
            QRCustomization.objects.create(qr=qr_code, **customization_data)
        
        if advanced_data:
            QRAdvancedOptions.objects.create(qr=qr_code, **advanced_data)
        
        if utm_data:
            QRUTMParameters.objects.create(qr=qr_code, **utm_data)
        
        # Generate redirect URL for tracking
        redirect_url = request.build_absolute_uri(
            reverse('dynamic_redirect', kwargs={'short_code': qr_code.short_code})
        )
        
        # Generate QR code with customization options
        qr_image = create_qr_code(redirect_url, qr_code)
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
@permission_classes([IsAuthenticated])
def generate_dynamic_qr_api(request):
    """API endpoint to generate dynamic QR code with device-based redirects, customization, advanced options, and UTM parameters"""
    # Check if user is verified (active)
    if not request.user.is_active:
        return Response({
            'error': 'Email verification required. Please verify your email address before generating QR codes.',
            'requires_verification': True,
            'user_email': request.user.email
        }, status=status.HTTP_403_FORBIDDEN)
    
    serializer = DynamicQRCreateSerializer(data=request.data)
    
    if serializer.is_valid():
        project_id = serializer.validated_data['project_id']
        title = serializer.validated_data.get('title', '')
        default_url = serializer.validated_data.get('default_url', '')
        mobile_url = serializer.validated_data.get('mobile_url', '')
        desktop_url = serializer.validated_data.get('desktop_url', '')
        customization_data = serializer.validated_data.get('qr_customization', None)
        advanced_data = serializer.validated_data.get('advanced_options', None)
        utm_data = serializer.validated_data.get('utm_parameters', None)
        device_redirects_data = {
            'default_url': default_url,
            'mobile_url': mobile_url,
            'desktop_url': desktop_url
        }
        
        # Verify project belongs to user
        try:
            project = Project.objects.get(id=project_id, user=request.user)
        except Project.DoesNotExist:
            return Response({
                'error': 'Project not found or you do not have permission to access it.'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Use default_url as content if provided, otherwise use mobile_url or desktop_url
        content_url = default_url or mobile_url or desktop_url
        
        # Create dynamic QR code (short_code is auto-generated in model save)
        qr_code = QRCode.objects.create(
            user=request.user,
            project=project,
            qr_type='dynamic',
            content=content_url,  # Store default URL as content
            name=title if title else '',
        )
        
        # Create related objects if provided
        if customization_data:
            QRCustomization.objects.create(qr=qr_code, **customization_data)
        
        if advanced_data:
            QRAdvancedOptions.objects.create(qr=qr_code, **advanced_data)
        
        if utm_data:
            QRUTMParameters.objects.create(qr=qr_code, **utm_data)
        
        # Create device redirects if any URL is provided
        if any([default_url, mobile_url, desktop_url]):
            QRDeviceRedirects.objects.create(qr=qr_code, **device_redirects_data)
        
        # Generate redirect URL for tracking (points to dynamic_redirect view)
        redirect_url = request.build_absolute_uri(
            reverse('dynamic_redirect', kwargs={'short_code': qr_code.short_code})
        )
        
        # Generate QR code with customization options
        qr_image = create_qr_code(redirect_url, qr_code)
        qr_code.qr_image.save(
            f'qr_dynamic_{qr_code.id}.png',
            ContentFile(qr_image),
            save=True
        )
        
        return Response(
            QRCodeSerializer(qr_code, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_dynamic_file_qr_api(request):
    """API endpoint to generate dynamic QR code for file"""
    if not request.user.is_active:
        return Response({
            'error': 'Email verification required.',
            'requires_verification': True
        }, status=status.HTTP_403_FORBIDDEN)
    
    project_id = request.data.get('project_id')
    if not project_id:
        return Response({'error': 'project_id is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Verify project belongs to user
    try:
        project = Project.objects.get(id=project_id, user=request.user)
    except Project.DoesNotExist:
        return Response({
            'error': 'Project not found or you do not have permission to access it.'
        }, status=status.HTTP_404_NOT_FOUND)
    
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
        project=project,
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


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_overview_api(request):
    """Get dashboard overview statistics for the authenticated user"""
    try:
        user = request.user
        now = timezone.now()
        
        # Calculate current month start (1st day of current month)
        current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Calculate last month start and end
        if current_month_start.month == 1:
            last_month_start = current_month_start.replace(year=current_month_start.year - 1, month=12)
        else:
            last_month_start = current_month_start.replace(month=current_month_start.month - 1)
        
        last_month_end = current_month_start - timedelta(seconds=1)
        
        # Get all projects for the user
        user_projects = Project.objects.filter(user=user)
        total_projects = user_projects.count()
        
        # Get all QR codes for the user
        user_qr_codes = QRCode.objects.filter(user=user)
        
        # Total QR Codes - cumulative total
        total_qr_codes = user_qr_codes.count()
        
        # Projects created this month vs last month
        projects_this_month = user_projects.filter(
            created_at__gte=current_month_start
        ).count()
        projects_last_month = user_projects.filter(
            created_at__gte=last_month_start,
            created_at__lte=last_month_end
        ).count()
        
        # Calculate percentage change for projects
        if projects_last_month > 0:
            projects_change = ((projects_this_month - projects_last_month) / projects_last_month) * 100
        else:
            projects_change = 100 if projects_this_month > 0 else 0
        
        # New QR codes created this month vs last month
        qr_codes_this_month = user_qr_codes.filter(
            created_at__gte=current_month_start
        ).count()
        qr_codes_last_month = user_qr_codes.filter(
            created_at__gte=last_month_start,
            created_at__lte=last_month_end
        ).count()
        
        # Calculate percentage change for QR codes
        if qr_codes_last_month > 0:
            qr_codes_change = ((qr_codes_this_month - qr_codes_last_month) / qr_codes_last_month) * 100
        else:
            qr_codes_change = 100 if qr_codes_this_month > 0 else 0
        
        # Get all scans for user's QR codes
        user_scan_ids = user_qr_codes.values_list('id', flat=True)
        all_scans = ScanAnalytics.objects.filter(qr_code_id__in=user_scan_ids)
        
        # Total Scans - cumulative total
        total_scans = all_scans.count()
        
        # Scans this month vs last month
        scans_this_month = all_scans.filter(
            scanned_at__gte=current_month_start
        ).count()
        scans_last_month = all_scans.filter(
            scanned_at__gte=last_month_start,
            scanned_at__lte=last_month_end
        ).count()
        
        # Calculate percentage change for scans
        if scans_last_month > 0:
            scans_change = ((scans_this_month - scans_last_month) / scans_last_month) * 100
        else:
            scans_change = 100 if scans_this_month > 0 else 0
        
        # Unique Scans (Unique Users) - cumulative total
        unique_scans = all_scans.values('user_identifier').distinct().count()
        
        # Unique scans this month vs last month
        unique_scans_this_month = all_scans.filter(
            scanned_at__gte=current_month_start
        ).values('user_identifier').distinct().count()
        unique_scans_last_month = all_scans.filter(
            scanned_at__gte=last_month_start,
            scanned_at__lte=last_month_end
        ).values('user_identifier').distinct().count()
        
        # Calculate percentage change for unique scans
        if unique_scans_last_month > 0:
            unique_scans_change = ((unique_scans_this_month - unique_scans_last_month) / unique_scans_last_month) * 100
        else:
            unique_scans_change = 100 if unique_scans_this_month > 0 else 0
        
        # Scans Today
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        scans_today = all_scans.filter(scanned_at__gte=today_start).count()
        
        # Scans on same day last month
        # Calculate the same day in last month
        try:
            last_month_same_day = last_month_start.replace(day=now.day)
        except ValueError:
            # Handle case where current day doesn't exist in last month (e.g., Jan 31 -> Feb doesn't have 31st)
            # Use the last day of last month
            if last_month_start.month == 12:
                last_day = 31
            elif last_month_start.month in [4, 6, 9, 11]:
                last_day = 30
            elif last_month_start.month == 2:
                # Check for leap year
                if (last_month_start.year % 4 == 0 and last_month_start.year % 100 != 0) or (last_month_start.year % 400 == 0):
                    last_day = 29
                else:
                    last_day = 28
            else:
                last_day = 31
            last_month_same_day = last_month_start.replace(day=last_day)
        
        last_month_same_day_start = last_month_same_day.replace(hour=0, minute=0, second=0, microsecond=0)
        last_month_same_day_end = last_month_same_day.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        scans_today_last_month = all_scans.filter(
            scanned_at__gte=last_month_same_day_start,
            scanned_at__lte=last_month_same_day_end
        ).count()
        
        # Calculate percentage change for scans today
        if scans_today_last_month > 0:
            scans_today_change = ((scans_today - scans_today_last_month) / scans_today_last_month) * 100
        else:
            scans_today_change = 100 if scans_today > 0 else 0
        
        # Average Daily Scans (for current month)
        days_in_current_month = (now - current_month_start).days + 1
        avg_daily_this_month = scans_this_month / days_in_current_month if days_in_current_month > 0 else 0
        
        # Average Daily Scans (for last month)
        days_in_last_month = (last_month_end - last_month_start).days + 1
        scans_last_month_total = all_scans.filter(
            scanned_at__gte=last_month_start,
            scanned_at__lte=last_month_end
        ).count()
        avg_daily_last_month = scans_last_month_total / days_in_last_month if days_in_last_month > 0 else 0
        
        # Calculate percentage change for avg daily
        if avg_daily_last_month > 0:
            avg_daily_change = ((avg_daily_this_month - avg_daily_last_month) / avg_daily_last_month) * 100
        else:
            avg_daily_change = 100 if avg_daily_this_month > 0 else 0
        
        # Format numbers (e.g., 20800 -> "20.8k")
        def format_number(num):
            if num >= 1000:
                return f"{num / 1000:.1f}k"
            return str(num)
        
        return Response({
            'total_scans': {
                'value': total_scans,
                'formatted_value': format_number(total_scans),
                'label': 'Total Scans',
                'change_percent': round(scans_change, 2),
                'is_positive': scans_change >= 0,
                'this_month': scans_this_month,
                'last_month': scans_last_month
            },
            'unique_scanners': {
                'value': unique_scans,
                'label': 'Unique Scanners',
                'change_percent': round(unique_scans_change, 2),
                'is_positive': unique_scans_change >= 0,
                'this_month': unique_scans_this_month,
                'last_month': unique_scans_last_month
            },
            'scans_today': {
                'value': scans_today,
                'label': 'Scans Today',
                'change_percent': round(scans_today_change, 2),
                'is_positive': scans_today_change >= 0,
                'today': scans_today,
                'last_month_same_day': scans_today_last_month
            },
            'avg_daily': {
                'value': round(avg_daily_this_month, 0),
                'label': 'Avg. Daily',
                'change_percent': round(avg_daily_change, 2),
                'is_positive': avg_daily_change >= 0,
                'this_month': round(avg_daily_this_month, 2),
                'last_month': round(avg_daily_last_month, 2)
            },
            'period': {
                'current_month': current_month_start.strftime('%B %Y'),
                'last_month': last_month_start.strftime('%B %Y')
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def recent_scans_api(request):
    """Get recent QR code scans with project and QR code information"""
    try:
        user = request.user
        
        # Get limit from query parameter (default 20, max 100)
        limit = int(request.GET.get('limit', 20))
        limit = min(limit, 100)  # Cap at 100
        
        # Get project filter if provided
        project_id = request.GET.get('project_id', None)
        
        # Get all QR codes for the user
        user_qr_codes = QRCode.objects.filter(user=user)
        
        # Filter by project if provided
        if project_id:
            try:
                project = Project.objects.get(id=project_id, user=user)
                user_qr_codes = user_qr_codes.filter(project=project)
            except Project.DoesNotExist:
                return Response({
                    'error': 'Project not found or you do not have permission to access it.'
                }, status=status.HTTP_404_NOT_FOUND)
        
        # Get all scan IDs for user's QR codes
        user_qr_ids = user_qr_codes.values_list('id', flat=True)
        
        # Get recent scans with related data
        recent_scans = ScanAnalytics.objects.filter(
            qr_code_id__in=user_qr_ids
        ).select_related(
            'qr_code', 'qr_code__project'
        ).order_by('-scanned_at')[:limit]
        
        # Serialize the data
        serializer = RecentScanSerializer(recent_scans, many=True)
        
        return Response({
            'count': len(serializer.data),
            'results': serializer.data
        }, status=status.HTTP_200_OK)
        
    except ValueError:
        return Response({
            'error': 'Invalid limit parameter. Must be a number.'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def top_performing_qr_api(request):
    """Get top performing QR codes sorted by scan count"""
    try:
        user = request.user
        
        # Get limit from query parameter (default 10, max 50)
        limit = int(request.GET.get('limit', 10))
        limit = min(limit, 50)  # Cap at 50
        
        # Get project filter if provided
        project_id = request.GET.get('project_id', None)
        
        # Get sort parameter (default: 'total_scans')
        sort_by = request.GET.get('sort_by', 'total_scans')  # total_scans, unique_scans, last_scan
        
        # Get date range filter if provided
        start_date = request.GET.get('start_date', None)
        end_date = request.GET.get('end_date', None)
        
        # Get all QR codes for the user
        user_qr_codes = QRCode.objects.filter(user=user)
        
        # Filter by project if provided
        if project_id:
            try:
                project = Project.objects.get(id=project_id, user=user)
                user_qr_codes = user_qr_codes.filter(project=project)
            except Project.DoesNotExist:
                return Response({
                    'error': 'Project not found or you do not have permission to access it.'
                }, status=status.HTTP_404_NOT_FOUND)
        
        # Get QR codes with scan counts
        qr_codes_with_scans = user_qr_codes.annotate(
            total_scans_count=Count('scans'),
            unique_scans_count=Count('scans__user_identifier', distinct=True)
        ).select_related('project')
        
        # Filter by date range if provided
        if start_date or end_date:
            from django.utils.dateparse import parse_date
            if start_date:
                start = parse_date(start_date)
                if start:
                    qr_codes_with_scans = qr_codes_with_scans.filter(
                        scans__scanned_at__gte=timezone.make_aware(
                            datetime.combine(start, datetime.min.time())
                        )
                    )
            if end_date:
                end = parse_date(end_date)
                if end:
                    qr_codes_with_scans = qr_codes_with_scans.filter(
                        scans__scanned_at__lte=timezone.make_aware(
                            datetime.combine(end, datetime.max.time())
                        )
                    )
        
        # Sort by the specified field
        if sort_by == 'unique_scans':
            qr_codes_with_scans = qr_codes_with_scans.order_by('-unique_scans_count', '-total_scans_count', '-created_at')
        elif sort_by == 'last_scan':
            # Get QR codes with their last scan date using Max aggregation
            qr_codes_with_scans = qr_codes_with_scans.annotate(
                last_scan_date=Max('scans__scanned_at')
            ).order_by('-last_scan_date', '-created_at')
        else:
            # Default: sort by total_scans
            qr_codes_with_scans = qr_codes_with_scans.order_by('-total_scans_count', '-created_at')
        
        # Get top QR codes
        top_qr_codes = list(qr_codes_with_scans[:limit])
        
        # Serialize the data
        serializer = TopPerformingQRSerializer(top_qr_codes, many=True, context={'request': request})
        
        return Response({
            'count': len(serializer.data),
            'sort_by': sort_by,
            'results': serializer.data
        }, status=status.HTTP_200_OK)
        
    except ValueError:
        return Response({
            'error': 'Invalid parameter. Check limit, start_date, or end_date format.'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def scan_trends_daily_api(request):
    """Get daily scan trends for the authenticated user's QR codes"""
    try:
        user = request.user
        
        # Get project filter if provided
        project_id = request.GET.get('project_id', None)
        
        # Get date range (default: last 30 days)
        days = int(request.GET.get('days', 30))
        days = min(days, 365)  # Cap at 1 year
        
        # Calculate date range
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        # Get all QR codes for the user
        user_qr_codes = QRCode.objects.filter(user=user)
        
        # Filter by project if provided
        if project_id:
            try:
                project = Project.objects.get(id=project_id, user=user)
                user_qr_codes = user_qr_codes.filter(project=project)
            except Project.DoesNotExist:
                return Response({
                    'error': 'Project not found or you do not have permission to access it.'
                }, status=status.HTTP_404_NOT_FOUND)
        
        # Get all scan IDs for user's QR codes
        user_qr_ids = user_qr_codes.values_list('id', flat=True)
        
        # Get scans in date range, grouped by day
        scans = ScanAnalytics.objects.filter(
            qr_code_id__in=user_qr_ids,
            scanned_at__gte=start_date,
            scanned_at__lte=end_date
        )
        
        # Group by day using SQLite date function
        daily_scans = scans.extra(
            select={'date': "DATE(scanned_at)"}
        ).values('date').annotate(
            count=Count('id')
        ).order_by('date')
        
        # Format data for chart
        data = []
        for item in daily_scans:
            # Parse date and format
            date_obj = datetime.strptime(item['date'], '%Y-%m-%d')
            data.append({
                'date': item['date'],
                'label': date_obj.strftime('%b %d'),  # "Jan 15"
                'scans': item['count']
            })
        
        return Response({
            'timeframe': 'daily',
            'days': days,
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
            'data': data
        }, status=status.HTTP_200_OK)
        
    except ValueError:
        return Response({
            'error': 'Invalid days parameter. Must be a number.'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def scan_trends_weekly_api(request):
    """Get weekly scan trends for the authenticated user's QR codes"""
    try:
        user = request.user
        
        # Get project filter if provided
        project_id = request.GET.get('project_id', None)
        
        # Get number of weeks (default: last 12 weeks)
        weeks = int(request.GET.get('weeks', 12))
        weeks = min(weeks, 52)  # Cap at 1 year
        
        # Calculate date range
        end_date = timezone.now()
        start_date = end_date - timedelta(weeks=weeks)
        
        # Get all QR codes for the user
        user_qr_codes = QRCode.objects.filter(user=user)
        
        # Filter by project if provided
        if project_id:
            try:
                project = Project.objects.get(id=project_id, user=user)
                user_qr_codes = user_qr_codes.filter(project=project)
            except Project.DoesNotExist:
                return Response({
                    'error': 'Project not found or you do not have permission to access it.'
                }, status=status.HTTP_404_NOT_FOUND)
        
        # Get all scan IDs for user's QR codes
        user_qr_ids = user_qr_codes.values_list('id', flat=True)
        
        # Get scans in date range
        scans = ScanAnalytics.objects.filter(
            qr_code_id__in=user_qr_ids,
            scanned_at__gte=start_date,
            scanned_at__lte=end_date
        )
        
        # Group by week using SQLite date functions
        # Calculate week start (Monday) for each scan
        weekly_scans = scans.extra(
            select={
                'week_start': "DATE(scanned_at, '-' || ((strftime('%w', scanned_at) + 6) % 7) || ' days')"
            }
        ).values('week_start').annotate(
            count=Count('id')
        ).order_by('week_start')
        
        # Format data for chart
        data = []
        for item in weekly_scans:
            # Parse date and format
            date_obj = datetime.strptime(item['week_start'], '%Y-%m-%d')
            # Get week number and year
            week_num = date_obj.isocalendar()[1]
            data.append({
                'date': item['week_start'],
                'label': f"Week {week_num}, {date_obj.strftime('%Y')}",  # "Week 15, 2024"
                'scans': item['count']
            })
        
        return Response({
            'timeframe': 'weekly',
            'weeks': weeks,
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
            'data': data
        }, status=status.HTTP_200_OK)
        
    except ValueError:
        return Response({
            'error': 'Invalid weeks parameter. Must be a number.'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def scan_trends_annually_api(request):
    """Get annual scan trends (monthly) for the authenticated user's QR codes"""
    try:
        user = request.user
        
        # Get project filter if provided
        project_id = request.GET.get('project_id', None)
        
        # Get year (default: current year)
        year = int(request.GET.get('year', timezone.now().year))
        
        # Calculate date range for the year
        start_date = timezone.make_aware(datetime(year, 1, 1))
        end_date = timezone.make_aware(datetime(year, 12, 31, 23, 59, 59))
        
        # Get all QR codes for the user
        user_qr_codes = QRCode.objects.filter(user=user)
        
        # Filter by project if provided
        if project_id:
            try:
                project = Project.objects.get(id=project_id, user=user)
                user_qr_codes = user_qr_codes.filter(project=project)
            except Project.DoesNotExist:
                return Response({
                    'error': 'Project not found or you do not have permission to access it.'
                }, status=status.HTTP_404_NOT_FOUND)
        
        # Get all scan IDs for user's QR codes
        user_qr_ids = user_qr_codes.values_list('id', flat=True)
        
        # Get scans in date range, grouped by month
        scans = ScanAnalytics.objects.filter(
            qr_code_id__in=user_qr_ids,
            scanned_at__gte=start_date,
            scanned_at__lte=end_date
        )
        
        # Group by month using SQLite date function
        monthly_scans = scans.extra(
            select={'month': "strftime('%Y-%m', scanned_at)"}
        ).values('month').annotate(
            count=Count('id')
        ).order_by('month')
        
        # Create a complete list of all 12 months
        month_names = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
        data_dict = {}
        
        # Populate with actual data
        for item in monthly_scans:
            month_num = int(item['month'].split('-')[1])
            data_dict[month_num] = {
                'month': month_num,
                'month_name': month_names[month_num - 1],
                'date': item['month'],
                'scans': item['count']
            }
        
        # Fill in missing months with 0
        data = []
        for month_num in range(1, 13):
            if month_num in data_dict:
                data.append(data_dict[month_num])
            else:
                data.append({
                    'month': month_num,
                    'month_name': month_names[month_num - 1],
                    'date': f"{year}-{month_num:02d}",
                    'scans': 0
                })
        
        return Response({
            'timeframe': 'annually',
            'year': year,
            'data': data
        }, status=status.HTTP_200_OK)
        
    except ValueError:
        return Response({
            'error': 'Invalid year parameter. Must be a number.'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def geography_analytics_api(request):
    """Get geography analytics for the authenticated user's QR codes"""
    try:
        user = request.user
        now = timezone.now()
        
        # Calculate current month start (1st day of current month)
        current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Calculate last month start and end
        if current_month_start.month == 1:
            last_month_start = current_month_start.replace(year=current_month_start.year - 1, month=12)
        else:
            last_month_start = current_month_start.replace(month=current_month_start.month - 1)
        
        last_month_end = current_month_start - timedelta(seconds=1)
        
        # Get all QR codes for the user
        user_qr_codes = QRCode.objects.filter(user=user)
        user_qr_ids = user_qr_codes.values_list('id', flat=True)
        
        # Get all scans for user's QR codes
        all_scans = ScanAnalytics.objects.filter(qr_code_id__in=user_qr_ids)
        
        # Get scans for current month
        scans_this_month = all_scans.filter(scanned_at__gte=current_month_start)
        
        # Get scans for last month
        scans_last_month = all_scans.filter(
            scanned_at__gte=last_month_start,
            scanned_at__lte=last_month_end
        )
        
        # 1. Countries Reached - unique countries (excluding 'Unknown')
        countries_this_month = scans_this_month.exclude(country='Unknown').values('country').distinct().count()
        countries_last_month = scans_last_month.exclude(country='Unknown').values('country').distinct().count()
        
        # Calculate percentage change for countries reached
        if countries_last_month > 0:
            countries_change = ((countries_this_month - countries_last_month) / countries_last_month) * 100
        else:
            countries_change = 100 if countries_this_month > 0 else 0
        
        # 2. Top Country - country with most scans
        top_country_data = scans_this_month.exclude(country='Unknown').values('country').annotate(
            count=Count('id')
        ).order_by('-count').first()
        
        top_country = top_country_data['country'] if top_country_data else 'Unknown'
        top_country_scans = top_country_data['count'] if top_country_data else 0
        
        # Get top country from last month for comparison
        top_country_last_month_data = scans_last_month.exclude(country='Unknown').values('country').annotate(
            count=Count('id')
        ).order_by('-count').first()
        
        top_country_last_month = top_country_last_month_data['country'] if top_country_last_month_data else 'Unknown'
        top_country_scans_last_month = top_country_last_month_data['count'] if top_country_last_month_data else 0
        
        # 3. Top Country Scan Count (e.g., "Japan Scan")
        # Calculate percentage change for top country scans
        if top_country_scans_last_month > 0:
            top_country_scan_change = ((top_country_scans - top_country_scans_last_month) / top_country_scans_last_month) * 100
        else:
            top_country_scan_change = 100 if top_country_scans > 0 else 0
        
        # 4. Top Country Share - percentage of total scans from top country
        total_scans_this_month = scans_this_month.count()
        top_country_share_this_month = (top_country_scans / total_scans_this_month * 100) if total_scans_this_month > 0 else 0
        
        total_scans_last_month = scans_last_month.count()
        top_country_share_last_month = (top_country_scans_last_month / total_scans_last_month * 100) if total_scans_last_month > 0 else 0
        
        # Calculate percentage change for top country share
        if top_country_share_last_month > 0:
            top_country_share_change = ((top_country_share_this_month - top_country_share_last_month) / top_country_share_last_month) * 100
        else:
            top_country_share_change = 100 if top_country_share_this_month > 0 else 0
        
        return Response({
            'countries_reached': {
                'value': countries_this_month,
                'label': 'Countries Reached',
                'change_percent': round(countries_change, 2),
                'is_positive': countries_change >= 0,
                'this_month': countries_this_month,
                'last_month': countries_last_month
            },
            'top_country_scan': {
                'value': top_country_scans,
                'label': f'{top_country} Scan',
                'change_percent': round(top_country_scan_change, 2),
                'is_positive': top_country_scan_change >= 0,
                'this_month': top_country_scans,
                'last_month': top_country_scans_last_month,
                'country': top_country
            },
            'top_country_share': {
                'value': round(top_country_share_this_month, 0),
                'formatted_value': f'{round(top_country_share_this_month, 0)}%',
                'label': f'{top_country} Share',
                'change_percent': round(top_country_share_change, 2),
                'is_positive': top_country_share_change >= 0,
                'this_month': round(top_country_share_this_month, 2),
                'last_month': round(top_country_share_last_month, 2),
                'country': top_country
            },
            'top_country': {
                'value': top_country,
                'label': 'Top Country',
                'this_month': top_country,
                'last_month': top_country_last_month
            },
            'period': {
                'current_month': current_month_start.strftime('%B %Y'),
                'last_month': last_month_start.strftime('%B %Y')
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def scans_by_countries_api(request):
    """Get scan counts by countries with timeframe filtering"""
    try:
        user = request.user
        
        # Get timeframe parameter (daily, weekly, annually)
        timeframe = request.GET.get('timeframe', 'annually').lower()
        
        # Get project filter if provided
        project_id = request.GET.get('project_id', None)
        
        # Get limit (default: all, max: 50)
        limit = request.GET.get('limit', None)
        if limit:
            limit = int(limit)
            limit = min(limit, 50)
        
        # Get all QR codes for the user
        user_qr_codes = QRCode.objects.filter(user=user)
        
        # Filter by project if provided
        if project_id:
            try:
                project = Project.objects.get(id=project_id, user=user)
                user_qr_codes = user_qr_codes.filter(project=project)
            except Project.DoesNotExist:
                return Response({
                    'error': 'Project not found or you do not have permission to access it.'
                }, status=status.HTTP_404_NOT_FOUND)
        
        # Get all scan IDs for user's QR codes
        user_qr_ids = user_qr_codes.values_list('id', flat=True)
        
        # Get scans based on timeframe
        now = timezone.now()
        scans = ScanAnalytics.objects.filter(qr_code_id__in=user_qr_ids)
        
        if timeframe == 'daily':
            # Last 30 days
            start_date = now - timedelta(days=30)
            scans = scans.filter(scanned_at__gte=start_date)
        elif timeframe == 'weekly':
            # Last 12 weeks
            start_date = now - timedelta(weeks=12)
            scans = scans.filter(scanned_at__gte=start_date)
        elif timeframe == 'annually':
            # Current year
            year_start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            scans = scans.filter(scanned_at__gte=year_start)
        
        # Group by country and count scans
        country_scans = scans.exclude(country='Unknown').values('country').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Apply limit if provided
        if limit:
            country_scans = country_scans[:limit]
        
        # Country name to code mapping (common countries)
        country_code_map = {
            'United States': 'USA',
            'United States of America': 'USA',
            'USA': 'USA',
            'Canada': 'CAN',
            'United Kingdom': 'GBR',
            'Great Britain': 'GBR',
            'UK': 'GBR',
            'Pakistan': 'PAK',
            'India': 'IND',
            'Saudi Arabia': 'SAU',
            'Russia': 'RUS',
            'Russian Federation': 'RUS',
            'France': 'FRA',
            'Japan': 'JPN',
            'Australia': 'AUS',
            'Mexico': 'MEX',
            'Germany': 'DEU',
            'China': 'CHN',
            'Brazil': 'BRA',
            'Italy': 'ITA',
            'Spain': 'ESP',
            'South Korea': 'KOR',
            'Netherlands': 'NLD',
            'Sweden': 'SWE',
            'Norway': 'NOR',
            'Denmark': 'DNK',
            'Finland': 'FIN',
            'Poland': 'POL',
            'Turkey': 'TUR',
            'Indonesia': 'IDN',
            'Thailand': 'THA',
            'Singapore': 'SGP',
            'Malaysia': 'MYS',
            'Philippines': 'PHL',
            'Vietnam': 'VNM',
            'South Africa': 'ZAF',
            'Egypt': 'EGY',
            'UAE': 'ARE',
            'United Arab Emirates': 'ARE',
            'Qatar': 'QAT',
            'Kuwait': 'KWT',
            'Bangladesh': 'BGD',
            'Sri Lanka': 'LKA',
            'Nepal': 'NPL',
            'Afghanistan': 'AFG',
            'Iran': 'IRN',
            'Iraq': 'IRQ',
            'Israel': 'ISR',
            'Jordan': 'JOR',
            'Lebanon': 'LBN',
            'Oman': 'OMN',
            'Yemen': 'YEM',
            'Argentina': 'ARG',
            'Chile': 'CHL',
            'Colombia': 'COL',
            'Peru': 'PER',
            'Venezuela': 'VEN',
            'New Zealand': 'NZL',
            'Ireland': 'IRL',
            'Belgium': 'BEL',
            'Switzerland': 'CHE',
            'Austria': 'AUT',
            'Portugal': 'PRT',
            'Greece': 'GRC',
            'Czech Republic': 'CZE',
            'Romania': 'ROU',
            'Hungary': 'HUN',
            'Ukraine': 'UKR',
            'Belarus': 'BLR',
            'Kazakhstan': 'KAZ',
            'Uzbekistan': 'UZB',
        }
        
        # Format data for chart
        data = []
        for item in country_scans:
            country_name = item['country']
            country_code = country_code_map.get(country_name, country_name[:3].upper() if len(country_name) >= 3 else country_name.upper())
            
            data.append({
                'country': country_name,
                'country_code': country_code,
                'scans': item['count'],
                'formatted_scans': f"{item['count']:,}"  # Format with commas
            })
        
        return Response({
            'timeframe': timeframe,
            'count': len(data),
            'data': data
        }, status=status.HTTP_200_OK)
        
    except ValueError:
        return Response({
            'error': 'Invalid limit parameter. Must be a number.'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def country_performance_details_api(request):
    """Get detailed country performance metrics with scans, unique scanners, percentage, and growth"""
    try:
        user = request.user
        now = timezone.now()
        
        # Calculate current month start (1st day of current month)
        current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Calculate last month start and end
        if current_month_start.month == 1:
            last_month_start = current_month_start.replace(year=current_month_start.year - 1, month=12)
        else:
            last_month_start = current_month_start.replace(month=current_month_start.month - 1)
        
        last_month_end = current_month_start - timedelta(seconds=1)
        
        # Get project filter if provided
        project_id = request.GET.get('project_id', None)
        
        # Get limit (default: all, max: 100)
        limit = request.GET.get('limit', None)
        if limit:
            limit = int(limit)
            limit = min(limit, 100)
        
        # Get all QR codes for the user
        user_qr_codes = QRCode.objects.filter(user=user)
        
        # Filter by project if provided
        if project_id:
            try:
                project = Project.objects.get(id=project_id, user=user)
                user_qr_codes = user_qr_codes.filter(project=project)
            except Project.DoesNotExist:
                return Response({
                    'error': 'Project not found or you do not have permission to access it.'
                }, status=status.HTTP_404_NOT_FOUND)
        
        # Get all scan IDs for user's QR codes
        user_qr_ids = user_qr_codes.values_list('id', flat=True)
        
        # Get all scans for user's QR codes
        all_scans = ScanAnalytics.objects.filter(qr_code_id__in=user_qr_ids)
        
        # Get scans for current month
        scans_this_month = all_scans.filter(scanned_at__gte=current_month_start)
        
        # Get scans for last month
        scans_last_month = all_scans.filter(
            scanned_at__gte=last_month_start,
            scanned_at__lte=last_month_end
        )
        
        # Total scans this month (for percentage calculation)
        total_scans_this_month = scans_this_month.count()
        
        # Get country performance for current month
        country_performance_this_month = scans_this_month.exclude(country='Unknown').values('country').annotate(
            scans=Count('id'),
            unique_scanners=Count('user_identifier', distinct=True)
        ).order_by('-scans')
        
        # Get country performance for last month
        country_performance_last_month = scans_last_month.exclude(country='Unknown').values('country').annotate(
            scans=Count('id')
        )
        
        # Create a dictionary for last month data for quick lookup
        last_month_dict = {item['country']: item['scans'] for item in country_performance_last_month}
        
        # Format data for table
        data = []
        for item in country_performance_this_month:
            country = item['country']
            scans = item['scans']
            unique_scanners = item['unique_scanners']
            
            # Calculate percentage of total
            percentage_of_total = (scans / total_scans_this_month * 100) if total_scans_this_month > 0 else 0
            
            # Get last month scans for growth calculation
            last_month_scans = last_month_dict.get(country, 0)
            
            # Calculate growth percentage
            if last_month_scans > 0:
                growth = ((scans - last_month_scans) / last_month_scans) * 100
            else:
                growth = 100 if scans > 0 else 0
            
            data.append({
                'country': country,
                'scans': scans,
                'unique_scanners': unique_scanners,
                'percentage_of_total': round(percentage_of_total, 1),
                'formatted_percentage': f'{round(percentage_of_total, 1)}%',
                'growth': round(growth, 1),
                'formatted_growth': f'{round(growth, 1)}%',
                'is_positive': growth >= 0,
                'last_month_scans': last_month_scans
            })
        
        # Apply limit if provided
        if limit:
            data = data[:limit]
        
        return Response({
            'count': len(data),
            'total_scans_this_month': total_scans_this_month,
            'period': {
                'current_month': current_month_start.strftime('%B %Y'),
                'last_month': last_month_start.strftime('%B %Y')
            },
            'data': data
        }, status=status.HTTP_200_OK)
        
    except ValueError:
        return Response({
            'error': 'Invalid limit parameter. Must be a number.'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def devices_analytics_api(request):
    """Get device analytics with Mobile, Desktop, Tablet percentages and growth"""
    try:
        user = request.user
        now = timezone.now()
        
        # Calculate current month start (1st day of current month)
        current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Calculate last month start and end
        if current_month_start.month == 1:
            last_month_start = current_month_start.replace(year=current_month_start.year - 1, month=12)
        else:
            last_month_start = current_month_start.replace(month=current_month_start.month - 1)
        
        last_month_end = current_month_start - timedelta(seconds=1)
        
        # Get project filter if provided
        project_id = request.GET.get('project_id', None)
        
        # Get all QR codes for the user
        user_qr_codes = QRCode.objects.filter(user=user)
        
        # Filter by project if provided
        if project_id:
            try:
                project = Project.objects.get(id=project_id, user=user)
                user_qr_codes = user_qr_codes.filter(project=project)
            except Project.DoesNotExist:
                return Response({
                    'error': 'Project not found or you do not have permission to access it.'
                }, status=status.HTTP_404_NOT_FOUND)
        
        # Get all scan IDs for user's QR codes
        user_qr_ids = user_qr_codes.values_list('id', flat=True)
        
        # Get all scans for user's QR codes
        all_scans = ScanAnalytics.objects.filter(qr_code_id__in=user_qr_ids)
        
        # Get scans for current month
        scans_this_month = all_scans.filter(scanned_at__gte=current_month_start)
        
        # Get scans for last month
        scans_last_month = all_scans.filter(
            scanned_at__gte=last_month_start,
            scanned_at__lte=last_month_end
        )
        
        # Total scans for percentage calculation
        total_scans_this_month = scans_this_month.count()
        total_scans_last_month = scans_last_month.count()
        
        # Define device categories
        mobile_devices = ['iPhone', 'Android', 'Mobile']
        desktop_devices = ['Desktop']
        tablet_devices = ['Tablet']
        
        # Helper function to categorize device
        def categorize_device(device_type):
            if device_type in mobile_devices:
                return 'Mobile'
            elif device_type in desktop_devices:
                return 'Desktop'
            elif device_type in tablet_devices:
                return 'Tablet'
            else:
                return 'Other'
        
        # Get device counts for current month
        device_counts_this_month = {}
        for scan in scans_this_month:
            category = categorize_device(scan.device_type)
            device_counts_this_month[category] = device_counts_this_month.get(category, 0) + 1
        
        # Get device counts for last month
        device_counts_last_month = {}
        for scan in scans_last_month:
            category = categorize_device(scan.device_type)
            device_counts_last_month[category] = device_counts_last_month.get(category, 0) + 1
        
        # Calculate percentages and growth for each device category
        devices_data = []
        
        for device_category in ['Mobile', 'Desktop', 'Tablet']:
            scans_this = device_counts_this_month.get(device_category, 0)
            scans_last = device_counts_last_month.get(device_category, 0)
            
            # Calculate percentage
            percentage = (scans_this / total_scans_this_month * 100) if total_scans_this_month > 0 else 0
            
            # Calculate growth
            if scans_last > 0:
                growth = ((scans_this - scans_last) / scans_last) * 100
            else:
                growth = 100 if scans_this > 0 else 0
            
            devices_data.append({
                'device': device_category,
                'percentage': round(percentage, 0),
                'formatted_percentage': f'{round(percentage, 0)}%',
                'scans': scans_this,
                'growth': round(growth, 1),
                'formatted_growth': f'{round(growth, 1)}%',
                'is_positive': growth >= 0,
                'last_month_scans': scans_last
            })
        
        # Find top performance device (highest percentage)
        top_device = max(devices_data, key=lambda x: x['percentage'])
        
        return Response({
            'mobile': {
                'value': next((d['percentage'] for d in devices_data if d['device'] == 'Mobile'), 0),
                'formatted_value': next((d['formatted_percentage'] for d in devices_data if d['device'] == 'Mobile'), '0%'),
                'label': 'Mobile',
                'change_percent': next((d['growth'] for d in devices_data if d['device'] == 'Mobile'), 0),
                'is_positive': next((d['is_positive'] for d in devices_data if d['device'] == 'Mobile'), True),
                'scans': next((d['scans'] for d in devices_data if d['device'] == 'Mobile'), 0),
                'last_month_scans': next((d['last_month_scans'] for d in devices_data if d['device'] == 'Mobile'), 0)
            },
            'desktop': {
                'value': next((d['percentage'] for d in devices_data if d['device'] == 'Desktop'), 0),
                'formatted_value': next((d['formatted_percentage'] for d in devices_data if d['device'] == 'Desktop'), '0%'),
                'label': 'Desktop',
                'change_percent': next((d['growth'] for d in devices_data if d['device'] == 'Desktop'), 0),
                'is_positive': next((d['is_positive'] for d in devices_data if d['device'] == 'Desktop'), True),
                'scans': next((d['scans'] for d in devices_data if d['device'] == 'Desktop'), 0),
                'last_month_scans': next((d['last_month_scans'] for d in devices_data if d['device'] == 'Desktop'), 0)
            },
            'tablet': {
                'value': next((d['percentage'] for d in devices_data if d['device'] == 'Tablet'), 0),
                'formatted_value': next((d['formatted_percentage'] for d in devices_data if d['device'] == 'Tablet'), '0%'),
                'label': 'Tablet',
                'change_percent': next((d['growth'] for d in devices_data if d['device'] == 'Tablet'), 0),
                'is_positive': next((d['is_positive'] for d in devices_data if d['device'] == 'Tablet'), True),
                'scans': next((d['scans'] for d in devices_data if d['device'] == 'Tablet'), 0),
                'last_month_scans': next((d['last_month_scans'] for d in devices_data if d['device'] == 'Tablet'), 0)
            },
            'top_performance_device': {
                'value': top_device['device'],
                'label': 'Top Performance Device',
                'percentage': top_device['percentage'],
                'formatted_percentage': top_device['formatted_percentage']
            },
            'period': {
                'current_month': current_month_start.strftime('%B %Y'),
                'last_month': last_month_start.strftime('%B %Y')
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def device_type_distribution_api(request):
    """Get device type distribution with timeframe filtering (Daily, Weekly, Annually)"""
    try:
        user = request.user
        
        # Get timeframe parameter (daily, weekly, annually)
        timeframe = request.GET.get('timeframe', 'annually').lower()
        
        # Get project filter if provided
        project_id = request.GET.get('project_id', None)
        
        # Get all QR codes for the user
        user_qr_codes = QRCode.objects.filter(user=user)
        
        # Filter by project if provided
        if project_id:
            try:
                project = Project.objects.get(id=project_id, user=user)
                user_qr_codes = user_qr_codes.filter(project=project)
            except Project.DoesNotExist:
                return Response({
                    'error': 'Project not found or you do not have permission to access it.'
                }, status=status.HTTP_404_NOT_FOUND)
        
        # Get all scan IDs for user's QR codes
        user_qr_ids = user_qr_codes.values_list('id', flat=True)
        
        # Get scans based on timeframe
        now = timezone.now()
        scans = ScanAnalytics.objects.filter(qr_code_id__in=user_qr_ids)
        
        if timeframe == 'daily':
            # Last 30 days
            start_date = now - timedelta(days=30)
            scans = scans.filter(scanned_at__gte=start_date)
        elif timeframe == 'weekly':
            # Last 12 weeks
            start_date = now - timedelta(weeks=12)
            scans = scans.filter(scanned_at__gte=start_date)
        elif timeframe == 'annually':
            # Current year
            year_start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            scans = scans.filter(scanned_at__gte=year_start)
        
        # Define device categories
        mobile_devices = ['iPhone', 'Android', 'Mobile']
        desktop_devices = ['Desktop']
        tablet_devices = ['Tablet']
        
        # Helper function to categorize device
        def categorize_device(device_type):
            if device_type in mobile_devices:
                return 'Mobile'
            elif device_type in desktop_devices:
                return 'Desktop'
            elif device_type in tablet_devices:
                return 'Tablet'
            else:
                return 'Other'
        
        # Group by device category and count scans
        device_counts = {}
        for scan in scans:
            category = categorize_device(scan.device_type)
            if category != 'Other':  # Exclude 'Other' category
                device_counts[category] = device_counts.get(category, 0) + 1
        
        # Format data for chart (sorted by scan count, highest first)
        data = []
        for device_category in ['Mobile', 'Desktop', 'Tablet']:
            count = device_counts.get(device_category, 0)
            data.append({
                'device_type': device_category,
                'scans': count,
                'formatted_scans': f"{count:,}"  # Format with commas
            })
        
        # Sort by scans (highest to lowest)
        data.sort(key=lambda x: x['scans'], reverse=True)
        
        return Response({
            'timeframe': timeframe,
            'count': len(data),
            'data': data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def utm_performance_api(request):
    """Get UTM performance metrics: Active Campaigns, UTM Scans, Avg. Conversion, Top Source"""
    try:
        user = request.user
        now = timezone.now()
        
        # Calculate current month start (1st day of current month)
        current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Calculate last month start and end
        if current_month_start.month == 1:
            last_month_start = current_month_start.replace(year=current_month_start.year - 1, month=12)
        else:
            last_month_start = current_month_start.replace(month=current_month_start.month - 1)
        
        last_month_end = current_month_start - timedelta(seconds=1)
        
        # Get project filter if provided
        project_id = request.GET.get('project_id', None)
        
        # Get all QR codes for the user
        user_qr_codes = QRCode.objects.filter(user=user)
        
        # Filter by project if provided
        if project_id:
            try:
                project = Project.objects.get(id=project_id, user=user)
                user_qr_codes = user_qr_codes.filter(project=project)
            except Project.DoesNotExist:
                return Response({
                    'error': 'Project not found or you do not have permission to access it.'
                }, status=status.HTTP_404_NOT_FOUND)
        
        # Get all QR codes with UTM parameters
        qr_codes_with_utm = user_qr_codes.filter(utm__isnull=False)
        qr_codes_with_utm_ids = qr_codes_with_utm.values_list('id', flat=True)
        
        # Get all scan IDs for user's QR codes
        user_qr_ids = user_qr_codes.values_list('id', flat=True)
        
        # Get all scans for user's QR codes
        all_scans = ScanAnalytics.objects.filter(qr_code_id__in=user_qr_ids)
        
        # Get scans for current month
        scans_this_month = all_scans.filter(scanned_at__gte=current_month_start)
        
        # Get scans for last month
        scans_last_month = all_scans.filter(
            scanned_at__gte=last_month_start,
            scanned_at__lte=last_month_end
        )
        
        # Get UTM scans (scans from QR codes with UTM parameters)
        utm_scans_this_month = scans_this_month.filter(qr_code_id__in=qr_codes_with_utm_ids)
        utm_scans_last_month = scans_last_month.filter(qr_code_id__in=qr_codes_with_utm_ids)
        
        # 1. Active Campaigns - unique campaigns with scans this month
        # Get QR codes with UTM that have scans this month
        qr_codes_with_utm_scans_this_month = utm_scans_this_month.values_list('qr_code_id', flat=True).distinct()
        active_campaigns_this_month = QRUTMParameters.objects.filter(
            qr__user=user,
            qr__id__in=qr_codes_with_utm_scans_this_month,
            utm_campaign__isnull=False
        ).exclude(utm_campaign='').values('utm_campaign').distinct().count()
        
        # Get QR codes with UTM that have scans last month
        qr_codes_with_utm_scans_last_month = utm_scans_last_month.values_list('qr_code_id', flat=True).distinct()
        active_campaigns_last_month = QRUTMParameters.objects.filter(
            qr__user=user,
            qr__id__in=qr_codes_with_utm_scans_last_month,
            utm_campaign__isnull=False
        ).exclude(utm_campaign='').values('utm_campaign').distinct().count()
        
        # Calculate percentage change for active campaigns
        if active_campaigns_last_month > 0:
            active_campaigns_change = ((active_campaigns_this_month - active_campaigns_last_month) / active_campaigns_last_month) * 100
        else:
            active_campaigns_change = 100 if active_campaigns_this_month > 0 else 0
        
        # 2. UTM Scans - total scans from QR codes with UTM parameters
        utm_scans_count_this_month = utm_scans_this_month.count()
        utm_scans_count_last_month = utm_scans_last_month.count()
        
        # Calculate percentage change for UTM scans
        if utm_scans_count_last_month > 0:
            utm_scans_change = ((utm_scans_count_this_month - utm_scans_count_last_month) / utm_scans_count_last_month) * 100
        else:
            utm_scans_change = 100 if utm_scans_count_this_month > 0 else 0
        
        # 3. Avg. Conversion - percentage of total scans that are UTM scans
        total_scans_this_month = scans_this_month.count()
        avg_conversion_this_month = (utm_scans_count_this_month / total_scans_this_month * 100) if total_scans_this_month > 0 else 0
        
        total_scans_last_month = scans_last_month.count()
        avg_conversion_last_month = (utm_scans_count_last_month / total_scans_last_month * 100) if total_scans_last_month > 0 else 0
        
        # Calculate percentage change for avg conversion
        if avg_conversion_last_month > 0:
            avg_conversion_change = ((avg_conversion_this_month - avg_conversion_last_month) / avg_conversion_last_month) * 100
        else:
            avg_conversion_change = 100 if avg_conversion_this_month > 0 else 0
        
        # 4. Top Source - utm_source with most scans
        top_source_data = QRUTMParameters.objects.filter(
            qr__user=user,
            qr__id__in=qr_codes_with_utm_ids,
            utm_source__isnull=False
        ).exclude(utm_source='').annotate(
            scan_count=Count('qr__scans', filter=Q(qr__scans__scanned_at__gte=current_month_start))
        ).order_by('-scan_count').first()
        
        top_source = top_source_data.utm_source if top_source_data and top_source_data.utm_source else 'N/A'
        
        return Response({
            'active_campaigns': {
                'value': active_campaigns_this_month,
                'label': 'Active Campaigns',
                'change_percent': round(active_campaigns_change, 2),
                'is_positive': active_campaigns_change >= 0,
                'this_month': active_campaigns_this_month,
                'last_month': active_campaigns_last_month
            },
            'utm_scans': {
                'value': utm_scans_count_this_month,
                'label': 'UTM Scans',
                'change_percent': round(utm_scans_change, 2),
                'is_positive': utm_scans_change >= 0,
                'this_month': utm_scans_count_this_month,
                'last_month': utm_scans_count_last_month
            },
            'avg_conversion': {
                'value': round(avg_conversion_this_month, 1),
                'formatted_value': f'{round(avg_conversion_this_month, 1)}%',
                'label': 'Avg. Conversion',
                'change_percent': round(avg_conversion_change, 2),
                'is_positive': avg_conversion_change >= 0,
                'this_month': round(avg_conversion_this_month, 2),
                'last_month': round(avg_conversion_last_month, 2)
            },
            'top_source': {
                'value': top_source,
                'label': 'Top Source'
            },
            'period': {
                'current_month': current_month_start.strftime('%B %Y'),
                'last_month': last_month_start.strftime('%B %Y')
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
