"""
Analytics helper functions for tracking QR code scans
"""
import requests
from user_agents import parse


def get_client_ip(request):
    """Get the real IP address of the client"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_location_from_ip(ip_address):
    """Get country and city from IP address using ipapi.co (free tier)"""
    if ip_address in ['127.0.0.1', 'localhost']:
        return 'Local', 'Local'
    
    try:
        response = requests.get(f'https://ipapi.co/{ip_address}/json/', timeout=2)
        if response.status_code == 200:
            data = response.json()
            country = data.get('country_name', 'Unknown')
            city = data.get('city', 'Unknown')
            return country, city
    except:
        pass
    
    return 'Unknown', 'Unknown'


def get_device_info(request):
    """Parse user agent to get device type and browser info"""
    user_agent_string = request.META.get('HTTP_USER_AGENT', '')
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
    
    browser = user_agent.browser.family
    os = user_agent.os.family
    
    return device_type, browser, os


def get_referrer(request):
    """Get the traffic source from HTTP referer"""
    referer = request.META.get('HTTP_REFERER', 'Direct')
    if referer == '':
        referer = 'Direct'
    return referer
