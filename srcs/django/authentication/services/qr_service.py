from authentication.services.two_factor_service import TwoFactorService
from authentication.services.rate_limit_service import RateLimitService
from authentication.models import CustomUser
from django.utils import timezone
import logging
import hashlib
import qrcode
import io

logger = logging.getLogger(__name__)

class QRService:
    def __init__(self):
        self._rate_limiter = None

# @property decorator transforms a method into a virtual attribute, allowing you to access it
# as if it were a regular attribute (without parentheses) while still executing code.
# This approach allows us to defer the cost of creating the RateLimitService until it's actually
# required, following the principle of "pay only for what you use".
# We use here because this method utilizes redis, which is an expensive operation in ram.

    @property
    def rate_limiter(self):
        """Property to access RateLimitService instance"""
        if self._rate_limiter is None:
            self._rate_limiter = RateLimitService() # Create RateLimitService instance to combine with QRService (property)
        return self._rate_limiter

    def _generate_username_hash(self, username, timestamp):
        """Generates a unique temporary hash for the username and timestamp
        to encript the QR code (to made it more secure) and store it in Redis"""
        data = f"{username}:{timestamp}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]	# Return first 16 characters of the hash (make it shorter because the QR code has a limit of characters)

    def generate_qr(self, username):
        """Generate QR code for username with 8h validity and max 3 uses"""
        try:
            is_limited, remaining = self.rate_limiter.is_rate_limited(
                username, 'qr_generation')
            if is_limited:
                raise ValueError(f"Demasiados intentos. Intenta de nuevo en {remaining} segundos")

            # Generate unique hash for this session
            timestamp = int(timezone.now().timestamp())	# Get current timestamp
            username_hash = self._generate_username_hash(username, timestamp) # Generate hash
            
            # Store in Redis with 8h TTL and 3 uses limit
            key = f"qr_auth:{username_hash}" # Store username in Redis
            uses_key = f"qr_uses:{username_hash}" # Store uses counter in Redis
            
            # We use pipeline for atomicity and performance
            pipe = self.rate_limiter.redis_client.pipeline()
            pipe.setex(key, 28800, username)  # 8 hours validity
            pipe.setex(uses_key, 28800, 0)    # Counter starts at 0
            pipe.execute() # Execute both commands atomically

            logger.info(f"QR generated for {username} - valid for 8h, max 3 uses")

            # Immediate verification (testing purposes)
            stored_value = self.rate_limiter.redis_client.get(key) # Check if stored correctly
            logger.info(f"QR Redis verification: stored_value={stored_value}")

            # Generate QR string (image buffer)
            qr = qrcode.QRCode(version=1, box_size=10, border=4)
            qr.add_data(username_hash)
            qr.make(fit=True)

			# Generate image with buffer and return it (png)
            img = qr.make_image(fill="black", back_color="white")
            buffer = io.BytesIO()
            img.save(buffer, format="PNG")
            buffer.seek(0)

            return buffer

        except Exception as e:
            logger.error(f"Error generating QR: {str(e)}", exc_info=True)
            raise
        
## Deprecated method (not used anymore) ################
    def validate_qr_data(self, qr_data):
        """Validates QR data and authenticates user"""
        # Disclaimer:
        # This method is deprecated and is not used anymore.
        # It's kept here because we used it in the development phase (port 8000 test frontend, web views)
        # Its here to avoid errors when we deploy the project.
        # Now we use the "two-phase" validation method below.
        try:
            # Validate format and get username
            valid, error, username = self.pre_validate_qr(qr_data)
            if not valid:
                return False, error, None

            # Authenticate user
            valid, user, redirect_url = self.authenticate_qr(username)
            if not valid:
                return False, user, None

            return True, None, redirect_url

        except Exception as e:
            logger.error(f"QR validation error: {str(e)}", exc_info=True)
            return False, f"Error al validar QR: {str(e)}", None
############################################################

    def pre_validate_qr(self, qr_data):
        """QR login user (First phase: validate format and get username)"""
        try:
            hash_code = self._validate_hash_format(qr_data) # Validate QR hash format
            if not hash_code:
                return False, "El formato del código QR no es válido", None

            key = f"qr_auth:{hash_code}" # Check if QR exists
            stored_username = self.rate_limiter.redis_client.get(key) # Get username from Redis
            
            if not stored_username:
                # Check if expired or never existed
                if self.rate_limiter.redis_client.exists(f"qr_uses:{hash_code}"):
                    return False, "Este código QR ha expirado (válido por 8 horas)", None
                return False, "Este código QR no es válido o nunca ha existido", None

			# Decode username from bytes to string
            username = stored_username.decode('utf-8') if isinstance(stored_username, bytes) else stored_username
            
            # Get current uses for message
            uses = int(self.rate_limiter.redis_client.get(f"qr_uses:{hash_code}") or 0)
            remaining_uses = 3 - uses	# Remaining uses (3 max)
            
            logger.info(f"QR pre-validation: hash={hash_code}, username={username}, remaining_uses={remaining_uses}")
            return True, None, username

        except Exception as e:
            logger.error(f"QR pre-validation error: {str(e)}")
            return False, f"Error al validar el QR: {str(e)}", None

    def authenticate_qr(self, username):
        """QR login user (Second phase: authenticate user)"""
        try:
            # Combine QR existence and usage checks
            auth_key = f"qr_auth:{self._current_hash}"	# Get username from Redis
            uses_key = f"qr_uses:{self._current_hash}"	# Get uses from Redis (counter)
            
            pipe = self.rate_limiter.redis_client.pipeline() # Use pipeline to combine commands for atomicity and performance
            pipe.exists(auth_key) # Check if QR exists
            pipe.get(uses_key)   # Get uses counter
            exists, uses = pipe.execute() # Execute both commands atomically
            
            if not exists or uses is None:
                return False, "El código QR ha expirado (válido por 8 horas)", None
                
            uses = int(uses) # Convert to integer
            
            if uses >= 3:
                self._cleanup_qr_keys(auth_key, uses_key)
                return False, "Has alcanzado el límite máximo de 3 usos para este QR", None

            # Increment uses counter and get remaining uses in one operation
            new_uses = self.rate_limiter.redis_client.incr(uses_key)
            remaining_uses = 3 - new_uses

            # Remaining validations
            is_limited, remaining = self.rate_limiter.is_rate_limited(
                username, 'qr_validation'
            )
            if is_limited:
                return False, f"Demasiados intentos. Espera {remaining} segundos antes de intentar de nuevo", None

            try:
                user = CustomUser.objects.get(username=username)
            except CustomUser.DoesNotExist:
                logger.error(f"User not found: {username}")
                return False, "Usuario no encontrado", None

            if not user.email_verified:
                return False, "Este usuario aún no ha verificado su email", None

            # Handle 2FA
            if user.two_factor_enabled:
                code = TwoFactorService.generate_2fa_code(user)
                TwoFactorService.send_2fa_code(user, code)
                return True, user, "/verify-2fa/"

            # Clean up if it's the last use
            if new_uses >= 3:
                self._cleanup_qr_keys(auth_key, uses_key)
            
            return True, user, "/" # Redirect to home

        except Exception as e:
            logger.error(f"QR authentication error: {str(e)}", exc_info=True)
            return False, f"Error interno: {str(e)}", None

    def _cleanup_qr_keys(self, auth_key, uses_key):
        """Helper method to clean up QR keys in redis"""
        pipe = self.rate_limiter.redis_client.pipeline() # Pipeline to combine commands for atomicity and performance
        pipe.delete(auth_key)	# Delete both keys
        pipe.delete(uses_key)	
        pipe.execute()	# Execute both commands atomically
        logger.info(f"QR keys cleaned up: {auth_key}, {uses_key}")

    def _validate_hash_format(self, qr_data):
        """Validates QR hash format"""
        try:
            if isinstance(qr_data, str):	# Check if QR data is a string
                hash_code = qr_data.strip()	# Remove leading/trailing whitespaces
            elif isinstance(qr_data, dict):	# Check if QR data is a dictionary (key and value)
                hash_code = qr_data.get('username', '').strip()	# Get username key
            else:
                logger.error(f"Invalid QR data format: {type(qr_data)}")
                return None

            if not hash_code or not hash_code.isalnum() or len(hash_code) != 16:
                logger.error(f"Invalid hash format: {hash_code}")
                return None
            
            self._current_hash = hash_code # Store hash for later use (authenticate_qr)
            return hash_code # Return hash
        except Exception as e:
            logger.error(f"Hash validation error: {str(e)}")
            return None
