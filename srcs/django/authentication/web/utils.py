import jwt
from datetime import datetime, timedelta
from django.conf import settings

def generate_jwt_token(user, expiration_minutes=15):
    """
    Genera un token JWT para el usuario
    """
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
    """
    Decodifica un token JWT
    """
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