"""
Analytics helper functions for tracking QR code scans
"""
import requests
import logging
from user_agents import parse

logger = logging.getLogger(__name__)


def get_client_ip(request):
    """Get the real IP address of the client"""
    # Check various headers for real IP (important for proxies/load balancers)
    ip_headers = [
        'HTTP_X_REAL_IP',
        'HTTP_X_FORWARDED_FOR',
        'HTTP_CF_CONNECTING_IP',  # Cloudflare
        'HTTP_TRUE_CLIENT_IP',
        'REMOTE_ADDR',
    ]
    
    for header in ip_headers:
        ip = request.META.get(header)
        if ip:
            # X-Forwarded-For can contain multiple IPs, take the first one
            if ',' in ip:
                ip = ip.split(',')[0].strip()
            # Skip private/local IPs if we have more headers to check
            if ip and not ip.startswith(('10.', '172.', '192.168.', '127.')):
                return ip
    
    # Fallback to REMOTE_ADDR
    return request.META.get('REMOTE_ADDR', '0.0.0.0')


def get_location_from_ip(ip_address):
    """Get country and city from IP address using multiple fallback services"""
    # Skip local/private IPs
    if not ip_address or ip_address in ['127.0.0.1', 'localhost', '0.0.0.0']:
        return 'Local', 'Local'
    
    if ip_address.startswith(('10.', '172.', '192.168.')):
        return 'Private Network', 'Private Network'
    
    # Try multiple geolocation services with fallbacks
    services = [
        {
            'url': f'http://ip-api.com/json/{ip_address}?fields=country,city,status',
            'country_key': 'country',
            'city_key': 'city',
            'check_key': 'status',
            'check_value': 'success'
        },
        {
            'url': f'https://ipapi.co/{ip_address}/json/',
            'country_key': 'country_name',
            'city_key': 'city',
            'check_key': None,
            'check_value': None
        },
        {
            'url': f'https://ipwho.is/{ip_address}',
            'country_key': 'country',
            'city_key': 'city',
            'check_key': 'success',
            'check_value': True
        },
    ]
    
    for service in services:
        try:
            response = requests.get(service['url'], timeout=3)
            if response.status_code == 200:
                data = response.json()
                
                # Check if response is valid
                if service['check_key']:
                    if data.get(service['check_key']) != service['check_value']:
                        continue
                
                country = data.get(service['country_key'], 'Unknown')
                city = data.get(service['city_key'], 'Unknown')
                
                if country and country != 'Unknown':
                    logger.info(f"Geolocation success for {ip_address}: {country}, {city}")
                    return country or 'Unknown', city or 'Unknown'
        except Exception as e:
            logger.warning(f"Geolocation service failed: {e}")
            continue
    
    logger.warning(f"All geolocation services failed for IP: {ip_address}")
    return 'Unknown', 'Unknown'


def get_device_info(request):
    """Parse user agent to get device type and browser info"""
    user_agent_string = request.META.get('HTTP_USER_AGENT', '')
    
    if not user_agent_string:
        return 'Unknown', 'Unknown', 'Unknown'
    
    user_agent = parse(user_agent_string)
    
    # Determine device type
    if user_agent.is_mobile:
        if user_agent.os.family == 'iOS':
            device_type = 'iPhone'
        elif user_agent.os.family == 'Android':
            device_type = 'Android'
        else:
            device_type = 'Mobile'
    elif user_agent.is_tablet:
        device_type = 'Tablet'
    elif user_agent.is_pc:
        device_type = 'Desktop'
    else:
        device_type = 'Unknown'
    
    browser = user_agent.browser.family or 'Unknown'
    os = user_agent.os.family or 'Unknown'
    
    return device_type, browser, os


def get_referrer(request):
    """Get the traffic source from HTTP referer"""
    referer = request.META.get('HTTP_REFERER', '')
    if not referer:
        return 'Direct (QR Scan)'
    return referer
