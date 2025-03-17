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