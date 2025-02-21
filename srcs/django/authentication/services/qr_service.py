from authentication.models import CustomUser
from authentication.services.two_factor_service import TwoFactorService
from authentication.services.token_service import TokenService
from authentication.services.rate_limit_service import RateLimitService
import qrcode
import io
import json
from django.utils import timezone
import logging
import hashlib

logger = logging.getLogger(__name__)

class QRService:
    def __init__(self):
        self._token_service = None
        self._rate_limiter = None

    @property
    def token_service(self):
        if self._token_service is None:
            self._token_service = TokenService()
        return self._token_service

    @property
    def rate_limiter(self):
        if self._rate_limiter is None:
            self._rate_limiter = RateLimitService()
        return self._rate_limiter

    def _generate_username_hash(self, username, timestamp):
        """Genera un hash temporal único para el username"""
        data = f"{username}:{timestamp}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]

    def generate_qr(self, username):
        """Generate QR code for username"""
        try:
            is_limited, remaining = self.rate_limiter.is_rate_limited(
                username, 'qr_generation'
            )
            if is_limited:
                raise ValueError(f"Demasiados intentos. Intenta de nuevo en {remaining} segundos")

            # Generar hash único para esta sesión
            timestamp = int(timezone.now().timestamp())
            username_hash = self._generate_username_hash(username, timestamp)
            
            # Almacenar en Redis con TTL explícito (5 minutos)
            key = f"qr_auth:{username_hash}"
            success = self.rate_limiter.redis_client.setex(
                key, 
                300,  # 5 minutos de validez
                username
            )
            logger.info(f"QR Redis storage: key={key}, success={success}, username={username}")

            # Verificación inmediata
            stored_value = self.rate_limiter.redis_client.get(key)
            logger.info(f"QR Redis verification: stored_value={stored_value}")

            # Generar QR
            qr = qrcode.QRCode(version=1, box_size=10, border=4)
            qr.add_data(username_hash)
            qr.make(fit=True)

            img = qr.make_image(fill="black", back_color="white")
            buffer = io.BytesIO()
            img.save(buffer, format="PNG")
            buffer.seek(0)

            return buffer

        except Exception as e:
            logger.error(f"Error generating QR: {str(e)}", exc_info=True)
            raise

    def validate_qr_data(self, qr_data):
        """Validates QR data and handles 2FA"""
        try:
            # Primera fase: validar formato y obtener username
            valid, error, username = self.pre_validate_qr(qr_data)
            if not valid:
                return False, error, None

            # Segunda fase: autenticar usuario
            valid, user, redirect_url = self.authenticate_qr(username)
            if not valid:
                return False, user, None

            return True, None, redirect_url

        except Exception as e:
            logger.error(f"QR validation error: {str(e)}", exc_info=True)
            return False, f"Error al validar QR: {str(e)}", None

    def pre_validate_qr(self, qr_data):
        """Primera fase: validar formato y obtener username"""
        try:
            # Validar formato del hash
            hash_code = self._validate_hash_format(qr_data)
            if not hash_code:
                return False, "Datos QR inválidos", None

            # Obtener username de Redis
            key = f"qr_auth:{hash_code}"
            stored_username = self.rate_limiter.redis_client.get(key)
            if not stored_username:
                logger.error(f"No username found for hash {hash_code}")
                return False, "Código QR expirado o inválido", None

            # Decodificar username
            username = stored_username.decode('utf-8') if isinstance(stored_username, bytes) else stored_username
            logger.info(f"QR pre-validation: hash={hash_code}, username={username}")
            
            return True, None, username

        except Exception as e:
            logger.error(f"QR pre-validation error: {str(e)}")
            return False, str(e), None

    def authenticate_qr(self, username):
        """Segunda fase: autenticar usuario"""
        try:
            # Verificar rate limit
            is_limited, remaining = self.rate_limiter.is_rate_limited(
                username, 'qr_validation'
            )
            if is_limited:
                return False, f"Demasiados intentos. Intenta en {remaining} segundos", None

            # Obtener y validar usuario
            try:
                user = CustomUser.objects.get(username=username)
            except CustomUser.DoesNotExist:
                logger.error(f"User not found: {username}")
                return False, "Usuario no encontrado", None

            if not user.email_verified:
                return False, "Por favor verifica tu email primero", None

            # Manejar 2FA si está habilitado
            if user.two_factor_enabled:
                code = TwoFactorService.generate_2fa_code(user)
                TwoFactorService.send_2fa_code(user, code)
                return True, user, "/verify-2fa/"

            # Eliminación del QR después de autenticación exitosa
            key = f"qr_auth:{self._current_hash}"
            self.rate_limiter.redis_client.delete(key)
            logger.info(f"QR code deleted for user {username}")
            
            return True, user, "/"

        except Exception as e:
            logger.error(f"QR authentication error: {str(e)}", exc_info=True)
            return False, str(e), None

    def _validate_hash_format(self, qr_data):
        """Valida el formato del hash QR"""
        try:
            if isinstance(qr_data, str):
                hash_code = qr_data.strip()
            elif isinstance(qr_data, dict):
                hash_code = qr_data.get('username', '').strip()
            else:
                logger.error(f"Invalid QR data format: {type(qr_data)}")
                return None

            if not hash_code or not hash_code.isalnum() or len(hash_code) != 16:
                logger.error(f"Invalid hash format: {hash_code}")
                return None
            
            self._current_hash = hash_code
            return hash_code
        except Exception as e:
            logger.error(f"Hash validation error: {str(e)}")
            return None
