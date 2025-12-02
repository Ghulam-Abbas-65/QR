import qrcode
import hashlib
from io import BytesIO
from django.shortcuts import render, redirect, get_object_or_404
from django.core.files.base import ContentFile
from django.http import FileResponse, Http404
from django.urls import reverse
from django.contrib import messages
from django.db.models import Q
from .models import UploadedFile, QRCode, ScanAnalytics
from .forms import URLQRForm, FileQRForm
from .analytics import get_client_ip, get_location_from_ip, get_device_info, get_referrer


def home(request):
    """Home page with both forms"""
    url_form = URLQRForm()
    file_form = FileQRForm()
    
    context = {
        'url_form': url_form,
        'file_form': file_form,
    }
    return render(request, 'qr_generator/home.html', context)


def generate_url_qr(request):
    """Generate QR code from URL"""
    if request.method == 'POST':
        form = URLQRForm(request.POST)
        if form.is_valid():
            url = form.cleaned_data['url']
            
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
            
            return redirect('qr_result', qr_id=qr_code.id)
    
    return redirect('home')


def generate_file_qr(request):
    """Generate QR code from uploaded file"""
    if request.method == 'POST':
        form = FileQRForm(request.POST, request.FILES)
        if form.is_valid():
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
            
            return redirect('qr_result', qr_id=qr_code.id)
    
    return redirect('home')


def qr_result(request, qr_id):
    """Display generated QR code with analytics"""
    qr_code = get_object_or_404(QRCode, id=qr_id)
    
    # Get analytics stats
    stats = ScanAnalytics.get_stats_for_qr(qr_code)
    
    context = {
        'qr_code': qr_code,
        'stats': stats,
    }
    return render(request, 'qr_generator/result.html', context)


def download_file(request, token):
    """Download file using secure token"""
    uploaded_file = get_object_or_404(UploadedFile, token=token)
    
    # Note: Tracking is now done in dynamic_redirect view
    # This endpoint is called after redirect, so no duplicate tracking
    
    try:
        return FileResponse(
            uploaded_file.file.open('rb'),
            as_attachment=True,
            filename=uploaded_file.original_filename
        )
    except FileNotFoundError:
        raise Http404("File not found")


def dynamic_redirect(request, short_code):
    """Redirect ANY QR code to its destination and track scan"""
    qr_code = get_object_or_404(QRCode, short_code=short_code)
    
    # Check if QR code is active (for dynamic QR codes)
    if qr_code.qr_type == 'dynamic' and not qr_code.is_active:
        raise Http404("This QR code is no longer active")
    
    # Track the scan for ALL QR types
    track_scan(request, qr_code)
    
    # For file QR codes, redirect to download
    if qr_code.qr_type == 'file' and qr_code.uploaded_file:
        return redirect('download_file', token=qr_code.uploaded_file.token)
    
    # For URL and dynamic QR codes, redirect to content
    return redirect(qr_code.content)


def track_scan(request, qr_code):
    """Track analytics for QR code scan"""
    # Get client information
    ip_address = get_client_ip(request)
    device_type, browser, os = get_device_info(request)
    country, city = get_location_from_ip(ip_address)
    referrer = get_referrer(request)
    
    # Create unique user identifier (hash of IP + User Agent)
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    user_identifier = hashlib.md5(f"{ip_address}{user_agent}".encode()).hexdigest()
    
    # Save analytics
    ScanAnalytics.objects.create(
        qr_code=qr_code,
        ip_address=ip_address,
        user_identifier=user_identifier,
        country=country,
        city=city,
        device_type=device_type,
        browser=browser,
        operating_system=os,
        referrer=referrer
    )


def create_qr_code(data):
    """Helper function to generate QR code image"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to bytes
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    return buffer.getvalue()



def analytics_dashboard(request, qr_id):
    """Display detailed analytics dashboard with filtering"""
    qr_code = get_object_or_404(QRCode, id=qr_id)
    
    # Get filter parameters
    country_filter = request.GET.get('country', '')
    city_filter = request.GET.get('city', '')
    device_filter = request.GET.get('device', '')
    browser_filter = request.GET.get('browser', '')
    
    # Get filtered stats
    stats = ScanAnalytics.get_stats_for_qr(
        qr_code, 
        country=country_filter,
        city=city_filter,
        device=device_filter,
        browser=browser_filter
    )
    
    # Get all unique values for filter dropdowns
    all_scans = ScanAnalytics.objects.filter(qr_code=qr_code)
    filter_options = {
        'countries': all_scans.values_list('country', flat=True).distinct().order_by('country'),
        'cities': all_scans.values_list('city', flat=True).distinct().order_by('city'),
        'devices': all_scans.values_list('device_type', flat=True).distinct().order_by('device_type'),
        'browsers': all_scans.values_list('browser', flat=True).distinct().order_by('browser'),
    }
    
    context = {
        'qr_code': qr_code,
        'stats': stats,
        'filter_options': filter_options,
        'active_filters': {
            'country': country_filter,
            'city': city_filter,
            'device': device_filter,
            'browser': browser_filter,
        }
    }
    return render(request, 'qr_generator/analytics.html', context)



def check_analytics(request):
    """Search and view analytics for QR codes"""
    search_query = request.GET.get('search', '')
    qr_codes = None
    
    if search_query:
        # Search by QR ID, filename, or content
        qr_codes = QRCode.objects.filter(
            Q(id__icontains=search_query) |
            Q(content__icontains=search_query) |
            Q(uploaded_file__original_filename__icontains=search_query)
        ).select_related('uploaded_file').order_by('-created_at')[:20]
    else:
        # Show recent QR codes
        qr_codes = QRCode.objects.filter(qr_type='file').select_related('uploaded_file').order_by('-created_at')[:10]
    
    context = {
        'qr_codes': qr_codes,
        'search_query': search_query,
    }
    return render(request, 'qr_generator/check_analytics.html', context)



def download_qr(request, qr_id, format):
    """Download QR code in different formats"""
    from PIL import Image
    import io
    from django.http import HttpResponse
    
    qr_code = get_object_or_404(QRCode, id=qr_id)
    
    # Open the original QR code image
    img = Image.open(qr_code.qr_image.path)
    
    # Convert to RGB if needed (for JPEG)
    if format.lower() in ['jpg', 'jpeg'] and img.mode != 'RGB':
        img = img.convert('RGB')
    
    # Handle SVG separately
    if format.lower() == 'svg':
        import qrcode.image.svg
        qr = qrcode.QRCode(
            image_factory=qrcode.image.svg.SvgPathImage,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_code.content)
        qr.make(fit=True)
        
        buffer = io.BytesIO()
        img_svg = qr.make_image(fill_color="black", back_color="white")
        img_svg.save(buffer)
        
        response = HttpResponse(buffer.getvalue(), content_type='image/svg+xml')
        response['Content-Disposition'] = f'attachment; filename="qr_code_{qr_id}.svg"'
        return response
    
    # For raster formats
    buffer = io.BytesIO()
    
    # Map format names to PIL format names
    format_map = {
        'jpg': 'JPEG',
        'jpeg': 'JPEG',
        'png': 'PNG',
        'webp': 'WEBP',
        'bmp': 'BMP',
    }
    
    pil_format = format_map.get(format.lower(), 'PNG')
    img.save(buffer, format=pil_format)
    buffer.seek(0)
    
    content_types = {
        'png': 'image/png',
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'webp': 'image/webp',
        'bmp': 'image/bmp',
    }
    
    response = HttpResponse(buffer.getvalue(), content_type=content_types.get(format.lower(), 'image/png'))
    response['Content-Disposition'] = f'attachment; filename="qr_code_{qr_id}.{format.lower()}"'
    return response
