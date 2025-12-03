import random
import string
from typing import List

def generate_id(length: int = 8) -> str:
    """Generate random ID"""
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

def truncate_text(text: str, max_length: int = 500) -> str:
    """Truncate text to max length"""
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."

def format_bytes(bytes_value: int) -> str:
    """Format bytes to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.2f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.2f} PB"

def classify_target(target: str) -> str:
    """Classify target type"""
    import re
    
    # IP address pattern
    ip_pattern = r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$'
    
    # Domain pattern
    domain_pattern = r'^([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}$'
    
    # URL pattern
    url_pattern = r'^https?://'
    
    if re.match(ip_pattern, target):
        return "ip"
    elif re.match(url_pattern, target):
        return "url"
    elif re.match(domain_pattern, target):
        return "domain"
    elif '/' in target:
        return "path"
    else:
        return "unknown"
