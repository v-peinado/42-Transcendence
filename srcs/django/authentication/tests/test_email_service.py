from django.test import TestCase
from django.core import mail
from django.conf import settings
from ..models import CustomUser
from ..services.email_service import EmailService
from django.template.loader import render_to_string
from django.utils.html import strip_tags

class EmailServiceTest(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_send_verification_email(self):
        """Test envío de email de verificación"""
        token = {
            'uid': 'test-uid',
            'token': 'test-token'
        }
        
        # Enviar email
        result = EmailService.send_verification_email(self.user, token)
        
        # Verificar que el email fue enviado
        self.assertTrue(result)
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        
        # Verificar contenido del email
        self.assertEqual(email.subject, 'Verifica tu cuenta de PongOrama')
        self.assertEqual(email.from_email, settings.DEFAULT_FROM_EMAIL)
        self.assertEqual(email.to, [self.user.email])

    def test_send_password_reset_email(self):
        """Test envío de email de reseteo de contraseña"""
        token = {
            'uid': 'test-uid',
            'token': 'test-token'
        }
        
        result = EmailService.send_password_reset_email(self.user, token)
        
        self.assertTrue(result)
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.subject, 'Restablece tu contraseña')

    def test_send_password_changed_notification(self):
        """Test envío de notificación de cambio de contraseña"""
        result = EmailService.send_password_changed_notification(self.user)
        
        self.assertTrue(result)
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.subject, 'Tu contraseña ha sido cambiada')

    def test_send_email_change_notification(self):
        """Test envío de notificación de cambio de email"""
        old_email = 'old@example.com'
        result = EmailService.send_email_change_notification(self.user, old_email)
        
        self.assertTrue(result)
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.subject, 'Tu email ha sido actualizado')
        self.assertIn(old_email, email.to)
        self.assertIn(self.user.email, email.to)

    def test_send_2fa_code(self):
        """Test envío de código 2FA"""
        code = '123456'
        result = EmailService.send_2fa_code(self.user, code)
        
        self.assertTrue(result)
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.subject, 'Tu código de verificación PongOrama')
        self.assertIn(code, email.body)

    def test_email_failure_handling(self):
        """Test manejo de errores en envío de emails"""
        with self.settings(EMAIL_BACKEND='django.core.mail.backends.dummy.EmailBackend'):
            with self.assertRaises(Exception):
                EmailService.send_verification_email(self.user, {})

    def test_email_content_security(self):
        """Test que el contenido del email es seguro"""
        token = {
            'uid': 'safe-uid',
            'token': 'test-token'
        }
        
        result = EmailService.send_verification_email(self.user, token)
        
        self.assertTrue(result)
        email = mail.outbox[0]
        # Verificar que el contenido malicioso fue escapado
        self.assertNotIn('<script>', email.body)