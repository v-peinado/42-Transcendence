import jwt
from datetime import datetime, timedelta
from django.conf import settings
import pyotp
from django.utils import timezone
from django.core.mail import send_mail
from django.template.loader import render_to_string

def generate_jwt_token(user, expiration_minutes=15):
    """Genera un token JWT para el usuario"""
    payload = {
        'user_id': user.id,
        'exp': datetime.utcnow() + timedelta(minutes=expiration_minutes),
        'iat': datetime.utcnow()
    }
    token = jwt.encode(
        payload, 
        settings.JWT_SECRET_KEY, 
        algorithm=settings.JWT_ALGORITHM
    )
    return token

def decode_jwt_token(token):
    """Decodifica un token JWT"""
    try:
        payload = jwt.decode(
            token, 
            settings.JWT_SECRET_KEY, 
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def generate_2fa_code(user):
    """Genera un código 2FA temporal"""
    if not user.two_factor_secret:
        user.two_factor_secret = pyotp.random_base32()
        user.save()
    
    totp = pyotp.TOTP(user.two_factor_secret)
    code = totp.now()
    
    user.last_2fa_code = code
    user.last_2fa_time = timezone.now()
    user.save()
    
    return code

def send_2fa_code(user, code):
    """Envía el código 2FA por email"""
    subject = 'Tu código de verificación PongOrama'
    message = render_to_string('authentication/2fa_email.html', {
        'user': user,
        'code': code
    })
    
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
        html_message=message
    )

def verify_2fa_code(user, code):
    """Verifica si el código 2FA es válido"""
    if not user.last_2fa_code or not user.last_2fa_time:
        return False
        
    time_diff = timezone.now() - user.last_2fa_time
    if time_diff.total_seconds() > 300:  # 5 minutos
        return False
        
    return user.last_2fa_code == code