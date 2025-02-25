from django.test import TestCase
from django.utils import timezone
from django.conf import settings
from authentication.models import CustomUser
from authentication.services.gdpr_service import GDPRService
from datetime import timedelta
from unittest.mock import patch

class GDPRInactivityTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.user.email_verified = True
        self.user.is_active = True
        self.user.save()

    def test_inactivity_detection(self):
        # Simular último login hace más tiempo que el umbral
        with patch('django.utils.timezone.now') as mock_now:
            # Configurar tiempo actual
            current_time = timezone.now()
            mock_now.return_value = current_time

            # Simular último login hace más del tiempo de inactividad
            self.user.last_login = current_time - timedelta(seconds=settings.INACTIVITY_THRESHOLD + 1)
            self.user.save()

            # Ejecutar limpieza
            GDPRService.cleanup_inactive_users()

            # Verificar que el usuario fue notificado
            user_updated = CustomUser.objects.get(id=self.user.id)
            self.assertTrue(user_updated.inactivity_notified)

    def test_user_deletion_after_warning(self):
        with patch('django.utils.timezone.now') as mock_now:
            current_time = timezone.now()
            mock_now.return_value = current_time

            # Simular usuario ya notificado hace más del tiempo de warning
            self.user.last_login = current_time - timedelta(seconds=settings.INACTIVITY_THRESHOLD + 1)
            self.user.inactivity_notified = True
            self.user.inactivity_notification_date = current_time - timedelta(seconds=settings.INACTIVITY_WARNING + 1)
            self.user.save()

            # Ejecutar limpieza
            GDPRService.cleanup_inactive_users()

            # Verificar que el usuario fue eliminado
            self.assertFalse(CustomUser.objects.filter(id=self.user.id).exists())

    @patch('authentication.services.mail_service.MailSendingService.send_inactivity_warning')
    def test_warning_email_sent(self, mock_send_warning):
        with patch('django.utils.timezone.now') as mock_now:
            current_time = timezone.now()
            mock_now.return_value = current_time

            # Simular usuario cerca del umbral de inactividad
            self.user.last_login = current_time - timedelta(
                seconds=settings.INACTIVITY_THRESHOLD - settings.INACTIVITY_WARNING + 1
            )
            self.user.save()

            # Ejecutar limpieza
            GDPRService.cleanup_inactive_users()

            # Verificar que se envió el email
            mock_send_warning.assert_called_once_with(self.user)
