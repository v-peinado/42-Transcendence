from django.test import TestCase
from ..models import CustomUser
from ..services.two_factor_service import TwoFactorService

class TwoFactorServiceTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!'
        )
        self.user.two_factor_secret = TwoFactorService.generate_2fa_secret()
        self.user.save()

    def test_enable_2fa(self):
        code = TwoFactorService.enable_2fa(self.user)
        self.assertTrue(self.user.two_factor_enabled)
        self.assertIsNotNone(self.user.two_factor_secret)
        self.assertIsNotNone(code)

    def test_verify_2fa_code(self):
        """Test verificación de código 2FA"""
        # Generar código usando el servicio
        code = TwoFactorService.generate_2fa_code(self.user)
        
        # Verificar que el código se guardó correctamente
        self.user.refresh_from_db()
        self.assertEqual(self.user.last_2fa_code, code)
        self.assertIsNotNone(self.user.last_2fa_time)
        
        # Verificar que el código es válido
        self.assertTrue(TwoFactorService.verify_2fa_code(self.user, code))

    def test_disable_2fa(self):
        TwoFactorService.enable_2fa(self.user)
        self.assertTrue(TwoFactorService.disable_2fa(self.user))
        self.assertFalse(self.user.two_factor_enabled)
        self.assertIsNone(self.user.two_factor_secret)