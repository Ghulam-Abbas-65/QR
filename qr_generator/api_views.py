from rest_framework import viewsets, status
from rest_framework.decorators import api_view, action, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.core.files.base import ContentFile
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count, Q
from .models import (
    Project, QRCode, UploadedFile, ScanAnalytics,
    QRCustomization, QRAdvancedOptions, QRUTMParameters, QRDeviceRedirects
)
from .serializers import (
    ProjectSerializer, ProjectCreateSerializer,
    QRCodeSerializer, URLQRCreateSerializer, 
    FileQRCreateSerializer, ScanAnalyticsSerializer, 
    DynamicQRCreateSerializer, RecentScanSerializer
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
        
        # Format numbers (e.g., 20800 -> "20.8k")
        def format_number(num):
            if num >= 1000:
                return f"{num / 1000:.1f}k"
            return str(num)
        
        return Response({
            'total_project': {
                'value': total_projects,
                'label': 'Total Project',
                'change_percent': round(projects_change, 2),
                'is_positive': projects_change >= 0,
                'this_month': projects_this_month,
                'last_month': projects_last_month
            },
            'total_qr_code': {
                'value': total_qr_codes,
                'label': 'Total Qr Code',
                'change_percent': round(qr_codes_change, 2),
                'is_positive': qr_codes_change >= 0,
                'this_month': qr_codes_this_month,
                'last_month': qr_codes_last_month
            },
            'total_scans': {
                'value': total_scans,
                'formatted_value': format_number(total_scans),
                'label': 'Total Scans',
                'change_percent': round(scans_change, 2),
                'is_positive': scans_change >= 0,
                'this_month': scans_this_month,
                'last_month': scans_last_month
            },
            'unique_scans': {
                'value': unique_scans,
                'label': 'Unique Scans',
                'change_percent': round(unique_scans_change, 2),
                'is_positive': unique_scans_change >= 0,
                'this_month': unique_scans_this_month,
                'last_month': unique_scans_last_month
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
