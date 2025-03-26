"""
Unified security sanitization module for XSS and SQL injection protection,
with functionality to display potentially malicious code as literal text.
"""
import re
import html
from .xss_patterns import (
    XSS_PATTERNS, 
    TAG_PATTERNS, 
    ATTRIBUTE_PATTERNS, 
    SCRIPT_PATTERNS,
    ADVANCED_XSS_PATTERNS,
    SQL_PATTERNS, 
    SQL_KEYWORDS, 
    ADVANCED_SQL_PATTERNS,
    HYBRID_ATTACK_PATTERNS,
    ALL_MALICIOUS_PATTERNS
)

def detect_malicious_code(text):
    """
    Unified detector for any type of malicious code (XSS, SQL, or hybrid attacks).
    
    Args:
        text (str): Text to analyze
        
    Returns:
        bool: True if any type of malicious attack is detected
    """
    if text is None:
        return False
    
    # First try the combined patterns for efficiency
    for pattern in ALL_MALICIOUS_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    
    # Fallback to more specific checks if needed
    return False

def detect_xss(text):
    """
    Detects possible XSS attacks in a text.
    
    Args:
        text (str): Text to analyze
        
    Returns:
        bool: True if an XSS attack is detected
    """
    if text is None:
        return False
    
    # Check imported XSS_PATTERNS
    for pattern in XSS_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    
    # Check TAG_PATTERNS
    for pattern, _ in TAG_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    
    # Check ATTRIBUTE_PATTERNS
    for pattern, _ in ATTRIBUTE_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    
    # Check SCRIPT_PATTERNS
    for pattern, _ in SCRIPT_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    
    # Check ADVANCED_XSS_PATTERNS
    for pattern, _ in ADVANCED_XSS_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    
    return False

def detect_sql_injection(text):
    """
    Detects possible SQL injection attacks in text.
    
    Args:
        text (str): Text to analyze
        
    Returns:
        bool: True if an SQL injection attack is detected
    """
    if text is None:
        return False
    
    # Convert to lowercase for case-insensitive matching
    text_lower = text.lower()
    
    # Check SQL_PATTERNS
    for pattern in SQL_PATTERNS:
        if re.search(pattern, text_lower, re.IGNORECASE):
            return True
    
    # Check ADVANCED_SQL_PATTERNS
    for pattern in ADVANCED_SQL_PATTERNS:
        if re.search(pattern, text_lower, re.IGNORECASE):
            return True
    
    # Check for multiple SQL keywords
    keyword_count = 0
    for pattern in SQL_KEYWORDS:
        if re.search(pattern, text_lower, re.IGNORECASE):
            keyword_count += 1
            if keyword_count >= 3:
                return True
    
    return False

def detect_hybrid_attacks(text):
    """
    Detects hybrid attacks that combine XSS and SQL injection techniques.
    
    Args:
        text (str): Text to analyze
        
    Returns:
        bool: True if a hybrid attack is detected
    """
    if text is None:
        return False
    
    # Check HYBRID_ATTACK_PATTERNS
    for pattern in HYBRID_ATTACK_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    
    # Check if text contains both XSS and SQL patterns
    has_xss = detect_xss(text)
    has_sql = detect_sql_injection(text)
    
    return has_xss and has_sql

def render_code_safely(text, add_warning_prefix=False):
    """
    Prepares potentially malicious code (XSS, SQL, or hybrid attacks) to be displayed as text
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
    
    # Check if potentially dangerous using the unified detector
    is_dangerous = detect_malicious_code(text)
    
    if not is_dangerous:
        # If not dangerous, return without modifications
        return text
    
    # Add warning prefix if needed
    prefix = "⚠️ " if add_warning_prefix else ""
    full_text = prefix + text
    
    # Use readonly textarea with completely invisible styling
    # This makes it look exactly like normal text with no visual difference
    result = f'''<textarea readonly style="width:100%;height:auto;overflow:hidden;resize:none;background:transparent;border:none;padding:0;margin:0;font-family:inherit;font-size:inherit;color:inherit;line-height:inherit;display:inline;outline:none;box-shadow:none;appearance:none;">{html.escape(full_text)}</textarea>'''
    
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
    
    # Check for textarea format
    if text.startswith('<textarea') and text.endswith('</textarea>'):
        return True
    
    # Very old backwards compatibility
    if text.startswith('<xmp ') and text.endswith('</xmp>'):
        return True
    
    return False

# Compatibility functions - helps follow the "program to an interface, not an implementation" principle
def neutralize_xss(text, add_warning_prefix=True):
    """
    Compatibility function. Redirects to render_code_safely.
    
    "Program to an interface, not an implementation."
    When implementations change, code that depends only on the interface
    remains unaffected, promoting flexibility and reducing the ripple effects of modifications.
    """
    return render_code_safely(text, add_warning_prefix)

def neutralize_sql_injection(text, add_warning_prefix=True):
    """
    Compatibility function. Redirects to render_code_safely.
    For backward compatibility and following the principle of
    "programming to an interface, not an implementation."
    """
    return render_code_safely(text, add_warning_prefix)

def is_already_sanitized(text):
    """
    Compatibility function. Redirects to is_already_processed.
    """
    return is_already_processed(text)