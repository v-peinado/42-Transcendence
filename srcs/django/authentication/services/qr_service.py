from authentication.services.two_factor_service import TwoFactorService
import qrcode
import io

class QRService:
    @staticmethod
    def generate_qr(username):
        """Genera imagen QR"""
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(username)
        qr.make(fit=True)
        
        img = qr.make_image(fill='black', back_color='white')
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        
        return buffer

    @staticmethod
    def validate_qr_data(user_or_username):
        """Valida usuario y maneja 2FA"""
        try:
            # Manejar tanto objeto usuario como username
            if isinstance(user_or_username, str):
                from ..models import CustomUser
                user = CustomUser.objects.get(username=user_or_username)
            else:
                user = user_or_username

            if not user:
                return False, 'Usuario no encontrado', None
                
            if not user.email_verified:
                return False, 'Por favor verifica tu email para activar tu cuenta', None
                
            if user.two_factor_enabled:
                code = TwoFactorService.generate_2fa_code(user)
                TwoFactorService.send_2fa_code(user, code)
                return True, 'Código 2FA enviado a tu email', '/verify-2fa/'
                
            return True, None, '/user/'
        except CustomUser.DoesNotExist:
            return False, 'Usuario no encontrado', None
        except Exception as e:
            return False, str(e), None