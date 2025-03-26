"""
Comprehensive pattern collection for detecting XSS, SQL injection, and hybrid attacks.
This module centralizes all security patterns to simplify maintenance and updates.
"""

# Basic XSS patterns from existing implementation
XSS_PATTERNS = [
    r'<script[\s\S]*?>[\s\S]*?</script>',  # Script tags
    r'<\s*img[^>]*\sonerror\s*=',  # Image onerror
    r'<\s*img[^>]*\ssrc\s*=\s*["\']?\s*javascript:',  # JavaScript in src
    r'javascript\s*:',  # JavaScript protocol
    r'<\s*svg[^>]*\sonload\s*=',  # SVG onload
    r'<\s*iframe',  # iframes
    r'<\s*object',  # object tags
    r'<\s*embed',  # embed tags
    r'<\s*form',  # form tags (potential CSRF)
    r'<\s*base',  # base tags
    r'<\s*link',  # link tags
    r'<\s*meta',  # meta tags
    r'on\w+\s*=\s*["\']?',  # Event handlers (onclick, onload, etc.)
    r'data\s*:(?!image/)',  # Data URIs except safe images
    r'src\s*=\s*["\']?\s*data:',  # Src with data URIs
    r'expression\(.*\)',  # CSS expressions
    r'document\.(?:cookie|write|createelement)',  # DOM manipulation
    r'(?:window|self|this|top|parent|frames)\.',  # Window object references
    r'eval\(.*\)',  # Eval
    r'setInterval\(.*\)',  # Timer functions
    r'setTimeout\(.*\)',
    r'Function\(.*\)',  # Function constructor
    r'alert\(.*\)',  # Alert dialog
    r'confirm\(.*\)',  # Confirm dialog
    r'prompt\(.*\)',  # Prompt dialog
    r'<\s*applet',  # Applet tags
    r'<\s*style',  # Style tags
    r'vbscript\s*:',  # VBScript protocol
    r'moz-binding',  # Mozilla binding
    r'@import',  # CSS import
    r'@charset',  # CSS charset
    r'base64\s*,',  # Base64 encoded data
    r'innerHTML\s*=',  # InnerHTML assignment
    r'outerHTML\s*=',  # OuterHTML assignment
    r'location\s*=',  # Location assignment
    r'location\s*\.\s*href',  # Location href assignment
    r'location\s*\.\s*assign',  # Location assign
    r'location\s*\.\s*replace',  # Location replace
    r'localStorage',  # Local storage access
    r'sessionStorage',  # Session storage access
    r'content\s*=',  # Meta content attribute
    r'charset\s*=',  # Meta charset attribute
    r'xmlns\s*=',  # XML namespace
    r'formaction\s*=',  # Form action attribute
    r'form\s*=\s*',  # Form attribute
    r'input\s*=\s*',  # Input attribute
    r'button\s*=\s*',  # Button attribute
    r'target\s*=\s*',  # Target attribute
    r'frame\s*=\s*',  # Frame attribute
    r'frameset\s*=\s*',  # Frameset attribute
    r'noembed\s*=\s*',  # Noembed attribute
    r'noframes\s*=\s*',  # Noframes attribute
    r'plaintext\s*=\s*',  # Plaintext attribute
    r'template\s*=\s*',  # Template attribute
    r'textarea\s*=\s*',  # Textarea attribute
    r'title\s*=\s*',  # Title attribute
    r'video\s*=\s*',  # Video attribute
    r'audio\s*=\s*',  # Audio attribute
    r'canvas\s*=\s*',  # Canvas attribute
    r'command\s*=\s*',  # Command attribute
    r'datalist\s*=\s*',  # Datalist attribute
    r'details\s*=\s*',  # Details attribute
    r'dialog\s*=\s*',  # Dialog attribute
    r'keygen\s*=\s*',  # Keygen attribute
    r'menu\s*=\s*',  # Menu attribute
    r'menuitem\s*=\s*',  # Menuitem attribute
    r'progress\s*=\s*',  # Progress attribute
    r'ruby\s*=\s*',  # Ruby attribute
    r'summary\s*=\s*',  # Summary attribute
    r'track\s*=\s*',  # Track attribute
    r'wbr\s*=\s*',  # Wbr attribute
]

# Detailed XSS patterns with replacement values, the replacement not used in this module
# but can be used in other applications for sanitization or future enhancements
# These are used both for detection and sanitization
TAG_PATTERNS = [
    # HTML script tags with variations
    (r'<\s*script', '&lt;script'),
    (r'<\s*/\s*script', '&lt;/script'),
    
    # HTML tags for embedded content
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
    
    # Other potentially dangerous tags
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
    
    # Other dangerous attributes
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
    
    # Dangerous CSS
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

# Patterns to detect advanced XSS attacks
ADVANCED_XSS_PATTERNS = [
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

# SQL injection patterns
SQL_PATTERNS = [
    # Basic SQL injection patterns
    r"(\s|\')*(OR|AND)(\s|\')*(\'|\")?\s*\d+\s*=\s*\d+\s*(\'|\")?",  # OR 1=1, AND 1=1
    r"(\s|\')*(OR|AND)(\s|\')*(\'|\")?\s*\d+\s*=\s*\d+\s*(\-\-|\#)",  # OR 1=1--, AND 1=1#
    r"(\s|\')*(OR|AND)(\s|\')*(\'|\")?\s*\d+\s*>\s*\d+\s*(\'|\")?",   # OR 1>0, AND 1>0
    r"(\s|\')*(OR|AND)(\s|\')*(\'|\")?\s*\'[^\']*\'\s*=\s*\'[^\']*\'",  # OR 'a'='a'
    r"(\s|\')*(OR|AND)(\s|\')*(\'|\")?\s*\"[^\"]*\"\s*=\s*\"[^\"]*\"",  # OR "a"="a"
    
    # UNION-based SQL injection
    r"(\s|\')+(UNION)(\s|\')+(ALL|SELECT)",  # UNION ALL, UNION SELECT
    r"(\s|\')+(UNION)(\s|\')+(SELECT)(\s|\')[^\']*(FROM)",  # UNION SELECT * FROM
    
    # Error-based SQL injection
    r"(CONVERT\s*\([^\)]*\(SELECT)",  # CONVERT(SELECT...)
    r"(UPDATEXML\s*\([^\)]*\(SELECT)",  # UPDATEXML(SELECT...)
    r"(EXTRACTVALUE\s*\([^\)]*\(SELECT)",  # EXTRACTVALUE(SELECT...)
    
    # Stacked queries
    r";\s*(SELECT|INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|TRUNCATE)",  # ;SELECT, ;DROP, etc
    
    # Time-based blind SQL injection
    r"(SLEEP\s*\(\s*\d+\s*\))",  # SLEEP(10)
    r"(BENCHMARK\s*\(\s*\d+\s*,\s*[^\)]+\))",  # BENCHMARK(1000000,MD5('A'))
    r"(PG_SLEEP\s*\(\s*\d+\s*\))",  # PG_SLEEP(10)
    r"(WAITFOR\s+DELAY\s+\'\d{2}:\d{2}:\d{2}\')",  # WAITFOR DELAY '00:00:10'
    
    # Comments to bypass filters
    r"/\*(!|\*)*\*/",  # /**/, /*!*/, /*abcd*/
    r"(\-\-|\#).*",  # -- comment, # comment
    
    # Obfuscation techniques
    r"(\%\d+|\&\#\d+;)",  # %27, &#39;
    r"(CHAR\s*\(\s*\d+(\s*,\s*\d+)*\s*\))",  # CHAR(49, 50, 51)
    r"(CONCAT\s*\([^\)]+\))",  # CONCAT('a', 'b')
    r"(CONCAT_WS\s*\([^\)]+\))",  # CONCAT_WS('a', 'b', 'c')
    
    # Database specific functions often used in SQL injection
    r"(VERSION\s*\(\s*\))",  # VERSION()
    r"(DATABASE\s*\(\s*\))",  # DATABASE()
    r"(USER\s*\(\s*\))",  # USER()
    r"(CURRENT_USER\s*\(\s*\))",  # CURRENT_USER()
    r"(SYSTEM_USER\s*\(\s*\))",  # SYSTEM_USER()
    r"(SESSION_USER\s*\(\s*\))",  # SESSION_USER()
    r"(@@hostname)",  # @@hostname
    r"(@@version)",  # @@version
    r"(@@datadir)",  # @@datadir
    
    # Data extraction
    r"(LOAD_FILE\s*\([^\)]+\))",  # LOAD_FILE('/etc/passwd')
    r"(LOAD\s+DATA\s+INFILE)",  # LOAD DATA INFILE
    r"(INTO\s+OUTFILE)",  # INTO OUTFILE
    r"(INTO\s+DUMPFILE)",  # INTO DUMPFILE
]

# SQL keywords that could indicate SQL injection in combination
SQL_KEYWORDS = [
    # SELECT query components
    r"(\s|\')+(SELECT)(\s|\')+",  # SELECT
    r"(\s|\')+(FROM)(\s|\')+",  # FROM
    r"(\s|\')+(WHERE)(\s|\')+",  # WHERE
    r"(\s|\')+(GROUP\s+BY)(\s|\')+",  # GROUP BY
    r"(\s|\')+(HAVING)(\s|\')+",  # HAVING
    r"(\s|\')+(ORDER\s+BY)(\s|\')+",  # ORDER BY
    r"(\s|\')+(LIMIT)(\s|\')+",  # LIMIT
    
    # Data modification
    r"(\s|\')+(INSERT\s+INTO)(\s|\')+",  # INSERT INTO
    r"(\s|\')+(UPDATE)(\s|\')+",  # UPDATE
    r"(\s|\')+(DELETE\s+FROM)(\s|\')+",  # DELETE FROM
    r"(\s|\')+(TRUNCATE\s+TABLE)(\s|\')+",  # TRUNCATE TABLE
    
    # Database modification
    r"(\s|\')+(CREATE\s+TABLE)(\s|\')+",  # CREATE TABLE
    r"(\s|\')+(ALTER\s+TABLE)(\s|\')+",  # ALTER TABLE
    r"(\s|\')+(DROP\s+TABLE)(\s|\')+",  # DROP TABLE
    r"(\s|\')+(CREATE\s+DATABASE)(\s|\')+",  # CREATE DATABASE
    r"(\s|\')+(DROP\s+DATABASE)(\s|\')+",  # DROP DATABASE
    
    # Transactions
    r"(\s|\')+(BEGIN)(\s|\')+",  # BEGIN
    r"(\s|\')+(COMMIT)(\s|\')+",  # COMMIT
    r"(\s|\')+(ROLLBACK)(\s|\')+",  # ROLLBACK
    
    # Conditional statements
    r"(\s|\')+(CASE)(\s|\')+",  # CASE
    r"(\s|\')+(WHEN)(\s|\')+",  # WHEN
    r"(\s|\')+(THEN)(\s|\')+",  # THEN
    r"(\s|\')+(ELSE)(\s|\')+",  # ELSE
    r"(\s|\')+(END)(\s|\')+",  # END
]

# Advanced SQL injection techniques
ADVANCED_SQL_PATTERNS = [
    # Case variation
    r"(?i)(SeL[eE][cC][tT])",  # SeLeCt, SELECT, select, etc.
    r"(?i)(Un[iI][oO][nN])",  # UnIoN, UNION, union, etc.
    
    # Space replacement
    r"(SELECT|UNION|INSERT|UPDATE|DELETE|DROP|ALTER)[\s\+\%0-9A-Fa-f]+",  # SELECT%20, SELECT+, SELECT/**/, etc.
    
    # SQL string operations for bypassing WAF
    r"(SUBSTRING|SUBSTR|MID)\([^\)]+\)",  # SUBSTR(table_name,1,1)
    r"(ASCII|CHAR|CHR|ORD)\([^\)]+\)",  # ASCII('A')
    
    # Alternative logic tricks
    r"(XOR|DIV|RLIKE)",  # XOR, DIV, RLIKE operators
    
    # Blind SQL injection
    r"(IF|IFNULL|NULLIF)\([^\)]+\)",  # IF(1=1,1,0)
    r"(CASE\s+WHEN[^\)]+END)",  # CASE WHEN 1=1 THEN 1 ELSE 0 END
]

# Hybrid attacks patterns that combine XSS and SQL injection techniques
HYBRID_ATTACK_PATTERNS = [
    # HTML that generates or manipulates SQL
    r"<[^>]*>[^<]*(?:SELECT|INSERT|UPDATE|DELETE|DROP|ALTER)[^<]*</[^>]*>",  # HTML containing SQL commands
    
    # Script tags with SQL content
    r"<\s*script[^>]*>[^<]*(?:SELECT|INSERT|UPDATE|DELETE|DROP|ALTER)[^<]*</\s*script\s*>",
    
    # SQL inside event handlers
    r"on\w+\s*=\s*[\"'][^\"']*(?:SELECT|INSERT|UPDATE|DELETE|DROP|ALTER)[^\"']*[\"']",
    
    # HTML entities encoding SQL
    r"&#\d+;[^<]*(?:SELECT|INSERT|UPDATE|DELETE|DROP|ALTER)",
    
    # SQL comments with HTML
    r"--[^<]*<[^>]*>",  # SQL comment followed by HTML
    
    # JavaScript that builds SQL queries
    r"(?:var|let|const)\s+\w+\s*=\s*[\"'][^\"']*(?:SELECT|INSERT|UPDATE|DELETE|DROP|ALTER)[^\"']*[\"']",
    
    # Script using DOM to send SQL
    r"document\s*\.\s*(?:write|createElement)[^;]*(?:SELECT|INSERT|UPDATE|DELETE|DROP|ALTER)",
    
    # Script using fetch/ajax to send SQL
    r"(?:fetch|ajax|XMLHttpRequest)[^;]*[\"'][^\"']*(?:SELECT|INSERT|UPDATE|DELETE|DROP|ALTER)[^\"']*[\"']",
    
    # HTML attribute with SQL inside
    r"<[^>]*\s+(?:src|href|action|data)\s*=\s*[\"'][^\"']*(?:SELECT|INSERT|UPDATE|DELETE|DROP|ALTER)[^\"']*[\"'][^>]*>",
    
    # SQL with embedded XSS payload
    r"(?:SELECT|INSERT|UPDATE).*?['\"][^'\"]*<script[^>]*>[^<]*</script>[^'\"]*['\"]",
    
    # Encoded script tags with SQL
    r"(?:%3C|\&lt;)script(?:%3E|\&gt;)[^<]*(?:SELECT|INSERT|UPDATE|DELETE|DROP|ALTER)",
    
    # XSS using SQL syntax for obfuscation
    r"<[^>]*\s+on\w+\s*=\s*[\"'].*?(?:--|#|/\*).*?[\"'][^>]*>",
]

# Comprehensive patterns for all malicious code detection
# the _ variable is used to ignore the replacement values, _ is a common convention for unused variables
# example: (r'<\s*script', '&lt;script') -> (r'<\s*script', '_'), we can iignore the replacement value because we are only interested in the pattern
ALL_MALICIOUS_PATTERNS = (XSS_PATTERNS + 
                          [pattern for pattern, _ in TAG_PATTERNS] + 
                          [pattern for pattern, _ in ATTRIBUTE_PATTERNS] + 
                          [pattern for pattern, _ in SCRIPT_PATTERNS] + 
                          [pattern for pattern, _ in ADVANCED_XSS_PATTERNS] + 
                          SQL_PATTERNS + 
                          ADVANCED_SQL_PATTERNS + 
                          HYBRID_ATTACK_PATTERNS)

# Export all pattern sets for flexible usage, when use "from xss_patterns import *"
__all__ = [
    'XSS_PATTERNS',
    'TAG_PATTERNS',
    'ATTRIBUTE_PATTERNS',
    'SCRIPT_PATTERNS',
    'ADVANCED_XSS_PATTERNS',
    'SQL_PATTERNS', 
    'SQL_KEYWORDS', 
    'ADVANCED_SQL_PATTERNS',
    'HYBRID_ATTACK_PATTERNS',
    'ALL_MALICIOUS_PATTERNS'
]