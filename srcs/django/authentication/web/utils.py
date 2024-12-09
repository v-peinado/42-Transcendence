import jwt
from datetime import datetime, timedelta
from django.conf import settings
import pyotp
from django.utils import timezone
from django.core.mail import send_mail
from django.template.loader import render_to_string
import random

def generate_2fa_code(user):									#para los logins de dos factores
    """Genera un código 2FA usando JWT"""
    
    code = str(random.randint(100000, 999999))					#generar un código aleatorio de 6 dígitos
    
    payload = {
        'user_id': user.id,
        'code': code,
        'exp': datetime.utcnow() + timedelta(seconds=60),
        'iat': datetime.utcnow(),
        'type': '2fa'
    }
    token = jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    
    user.last_2fa_code = code									#guardar el código en el usuario
    user.last_2fa_time = timezone.now()							#guardar la fecha y hora de emisión
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

def verify_2fa_code(user, provided_code):
    """Verifica el código 2FA"""

    if not user.last_2fa_time or \
       timezone.now() - user.last_2fa_time > timedelta(seconds=60):
        return False											#si el código ha expirado (más de 60 segundos)
    
    return user.last_2fa_code == provided_code					#comparar el código proporcionado con el código guardado en el usuario