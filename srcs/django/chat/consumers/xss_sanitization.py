"""
XSS sanitization module containing detection patterns and neutralization rules,
with additional functionality to display code as literal text without modifying the frontend.
"""
import re
import html
from .xss_patterns import XSS_PATTERNS

# Improved patterns for XSS detection with obfuscation
TAG_PATTERNS = [
    # HTML script tags with variations
    (r'<\s*script', '&lt;script'),
    (r'<\s*/\s*script', '&lt;/script'),
    
    # HTML tags for embedded content (existing patterns)
    (r'<img', '&lt;img'),
    (r'<iframe', '&lt;iframe'),
    (r'<object', '&lt;object'),
    (r'<embed', '&lt;embed'),
    (r'<svg', '&lt;svg'),
    (r'<form', '&lt;form'),
    (r'</form', '&lt;/form'),
    (r'<base', '&lt;base'),
    (r'<link', '&lt;link'),
    (r'<meta', '&lt;meta'),
    (r'<applet', '&lt;applet'),
    (r'<style', '&lt;style'),
    (r'</style', '&lt;/style'),
    
    # Other potentially dangerous tags (existing patterns)
    (r'<plaintext', '&lt;plaintext'),
    (r'<template', '&lt;template'),
    (r'<textarea', '&lt;textarea'),
    (r'<canvas', '&lt;canvas'),
    (r'<noembed', '&lt;noembed'),
    (r'<noframes', '&lt;noframes'),
    (r'<frameset', '&lt;frameset'),
    (r'<keygen', '&lt;keygen'),
    (r'<details', '&lt;details'),
    (r'<dialog', '&lt;dialog'),
    (r'<menu', '&lt;menu'),
    (r'<menuitem', '&lt;menuitem'),
    (r'<summary', '&lt;summary'),
    (r'<track', '&lt;track'),
    (r'<datalist', '&lt;datalist'),
    (r'<ruby', '&lt;ruby'),
    (r'<wbr', '&lt;wbr'),
    
    # Additional patterns to detect obfuscation techniques
    (r'<[^>]*data-[^>]*=', '&lt;data-attribute'),
    (r'<[^>]*javascript:', '&lt;javascript-attribute'),
    (r'<[^>]*&#', '&lt;encoded-attribute'),
    (r'<[^>]*\\u00', '&lt;unicode-attribute'),
    (r'<[^>]*\\x', '&lt;hex-attribute'),
]

ATTRIBUTE_PATTERNS = [
    # Events with obfuscation detection
    (r'([\s"\'])\s*on\s*(\w+)\s*(\s*=)', r'\1on-\2\3'),
    (r'([\s"\'])\s*On\s*(\w+)\s*(\s*=)', r'\1on-\2\3'),  # Variant with initial capital
    (r'([\s"\'])\s*ON\s*(\w+)\s*(\s*=)', r'\1on-\2\3'),  # Variant with all caps
    
    # Dangerous src attributes with obfuscation detection
    (r'(src\s*=\s*["\']?\s*)j\s*a\s*v\s*a\s*s\s*c\s*r\s*i\s*p\s*t\s*:', r'\1javascript&#58;'),
    (r'(src\s*=\s*["\']?\s*)d\s*a\s*t\s*a\s*:', r'\1data&#58;'),
    (r'(src\s*=\s*["\']?\s*)(&#x6A;|&#106;|\\x6A|\\u006A)(&#x61;|&#97;|\\x61|\\u0061)(&#x76;|&#118;|\\x76|\\u0076)(&#x61;|&#97;|\\x61|\\u0061)' + 
      r'(&#x73;|&#115;|\\x73|\\u0073)(&#x63;|&#99;|\\x63|\\u0063)(&#x72;|&#114;|\\x72|\\u0072)(&#x69;|&#105;|\\x69|\\u0069)' + 
      r'(&#x70;|&#112;|\\x70|\\u0070)(&#x74;|&#116;|\\x74|\\u0074)(&#x3A;|&#58;|\\x3A|\\u003A)', r'\1javascript&#58;'),
    
    # Other dangerous attributes (existing patterns)
    (r'(formaction\s*=)', r'formaction-disabled='),
    (r'(xmlns\s*=)', r'xmlns-disabled='),
    (r'(content\s*=)', r'content-disabled='),
    (r'(charset\s*=)', r'charset-disabled='),
    (r'(form\s*=\s*)', r'form-disabled='),
    (r'(input\s*=\s*)', r'input-disabled='),
    (r'(button\s*=\s*)', r'button-disabled='),
    (r'(target\s*=\s*)', r'target-disabled='),
    (r'(frame\s*=\s*)', r'frame-disabled='),
    (r'(title\s*=\s*)', r'title-disabled='),
    (r'(video\s*=\s*)', r'video-disabled='),
    (r'(audio\s*=\s*)', r'audio-disabled='),
    (r'(command\s*=\s*)', r'command-disabled='),
    (r'(progress\s*=\s*)', r'progress-disabled='),
]

SCRIPT_PATTERNS = [
    # Protocols with obfuscation detection
    (r'j\s*a\s*v\s*a\s*s\s*c\s*r\s*i\s*p\s*t\s*:', 'javascript&#58;'),
    (r'v\s*b\s*s\s*c\s*r\s*i\s*p\s*t\s*:', 'vbscript&#58;'),
    (r'd\s*a\s*t\s*a\s*:', 'data&#58;'),
    
    # Dangerous CSS (existing patterns)
    (r'expression\s*\(', 'expression&#40;'),
    (r'@\s*import', '@imp&#111;rt'),
    (r'@\s*charset', '@chars&#101;t'),
    (r'moz\s*-\s*binding', 'm&#111;z-binding'),
    
    # DOM manipulation with obfuscation detection
    (r'innerHTML\s*=', 'innerHTML&#61;'),
    (r'outerHTML\s*=', 'outerHTML&#61;'),
    (r'document\s*\.\s*cookie', 'document&#46;cookie'),
    (r'document\s*\.\s*write', 'document&#46;write'),
    (r'document\s*\.\s*createelement', 'document&#46;createelement'),
    
    # Dangerous JavaScript functions with obfuscation detection
    (r'eval\s*\(', 'eval&#40;'),
    (r'Function\s*\(', 'Function&#40;'),
    (r'setTimeout\s*\(', 'setTimeout&#40;'),
    (r'setInterval\s*\(', 'setInterval&#40;'),
    (r'alert\s*\(', 'alert&#40;'),
    (r'confirm\s*\(', 'confirm&#40;'),
    (r'prompt\s*\(', 'prompt&#40;'),
    
    # Global object references with obfuscation detection
    (r'window\s*\.\s*', 'window&#46;'),
    (r'self\s*\.\s*', 'self&#46;'),
    (r'this\s*\.\s*', 'this&#46;'),
    (r'top\s*\.\s*', 'top&#46;'),
    (r'parent\s*\.\s*', 'parent&#46;'),
    (r'frames\s*\.\s*', 'frames&#46;'),
    
    # Location and storage with obfuscation detection
    (r'location\s*=', 'location&#61;'),
    (r'location\s*\.\s*href', 'location&#46;href'),
    (r'location\s*\.\s*assign', 'location&#46;assign'),
    (r'location\s*\.\s*replace', 'location&#46;replace'),
    (r'localStorage\s*\.\s*', 'localStorage&#46;'),
    (r'sessionStorage\s*\.\s*', 'sessionStorage&#46;'),
    
    # Base64 data
    (r'base64\s*,', 'base64&#44;'),
    
    # Additional protection against advanced obfuscation techniques
    (r'fromCharCode', 'fromCharCode-disabled'),
    (r'String\.fromCodePoint', 'fromCodePoint-disabled'),
    (r'(\d+\s*,\s*){5,}', 'suspicious-char-codes'),  # Long sequences of character codes
    (r'atob\s*\(', 'atob&#40;'),  # Base64 decoding
]

# Patterns to detect advanced attacks
ADVANCED_PATTERNS = [
    # Unicode obfuscation
    (r'\\u00[0-9a-f]{2}', 'unicode-sequence'),
    # Hex obfuscation
    (r'\\x[0-9a-f]{2}', 'hex-sequence'),
    # HTML entity obfuscation
    (r'&#x[0-9a-f]{2};', 'html-hex-entity'),
    (r'&#\d{2,3};', 'html-decimal-entity'),
    # Multi-layer obfuscation
    (r'eval\s*\(\s*atob\s*\(', 'eval-atob-sequence'),
    # Protocol obfuscation with Unicode
    (r'\\u006A\\u0061\\u0076\\u0061\\u0073\\u0063\\u0072\\u0069\\u0070\\u0074', 'javascript-unicode'),
]

import re
import html
from .xss_patterns import XSS_PATTERNS

def detect_xss(text):
    """
    Detects possible XSS attacks in a text, using all available patterns.
    
    Args:
        text (str): Text to analyze
        
    Returns:
        bool: True if an XSS attack is detected
    """
    if text is None:
        return False
    
    # 1. Check with imported XSS_PATTERNS
    for pattern in XSS_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    
    # 2. Check with detailed patterns defined in this module
    
    # Tag patterns
    for pattern, _ in TAG_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    
    # Attribute patterns
    for pattern, _ in ATTRIBUTE_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    
    # Script patterns
    for pattern, _ in SCRIPT_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    
    # Advanced patterns
    for pattern, _ in ADVANCED_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    
    return False

def render_code_safely(text, add_warning_prefix=False):
    """
    Prepares potentially malicious code to be displayed as text
    using a completely invisible textarea that blends with normal text.
    
    Args:
        text (str): The text to sanitize
        add_warning_prefix (bool): Whether to add a warning prefix
        
    Returns:
        str: Sanitized text that preserves the visual appearance
    """
    if text is None:
        return None
    
    # Check if already processed
    if is_already_processed(text):
        return text
    
    # Check if potentially dangerous
    is_dangerous = detect_xss(text)
    
    if not is_dangerous:
        # If not dangerous, return without modifications
        return text
    
    # Add warning prefix if needed
    prefix = "⚠️ " if add_warning_prefix else ""
    full_text = prefix + text
    
    # Use readonly textarea with completely invisible styling
    # This makes it look exactly like normal text with no visual difference
    result = f'''<textarea readonly style="width:100%;height:auto;overflow:hidden;resize:none;background:transparent;border:none;padding:0;margin:0;font-family:inherit;font-size:inherit;color:inherit;line-height:inherit;display:inline;outline:none;box-shadow:none;appearance:none;">{full_text}</textarea>'''
    
    return result

def is_already_processed(text):
    """
    Verifies if the text has already been processed with any of the
    supported safety mechanisms.
    
    Args:
        text (str): Text to verify
        
    Returns:
        bool: True if already processed
    """
    if not text:
        return False
    
    # Check for the new pre/code format
    if text.startswith('<pre style=') and '</code>' in text and text.endswith('</pre>'):
        return True
    
    # Check for old textarea format (for backwards compatibility)
    if text.startswith('<textarea') and text.endswith('</textarea>'):
        return True
    
    # Very old backwards compatibility
    if text.startswith('<xmp ') and text.endswith('</xmp>'):
        return True
    
    return False

def neutralize_xss(text, add_warning_prefix=True):
    """
    Compatibility function. Redirects to render_code_safely.
    """
    return render_code_safely(text, add_warning_prefix)

def is_already_sanitized(text):
    """
    Compatibility function. Redirects to is_already_processed.
    """
    return is_already_processed(text)