import re

def sanitize_path(path):
    invalid_chars_pattern = r'[<>:"/\\|?*\x00-\x1F\x7F]'
    
    sanitized = re.sub(invalid_chars_pattern, '_', path)
    sanitized = sanitized.encode('ascii', 'ignore').decode('ascii')
    sanitized = sanitized.replace(" ", "_").replace(".", "_").lower()
    
    return sanitized