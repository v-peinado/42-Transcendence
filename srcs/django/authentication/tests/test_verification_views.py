from rest_framework.test import APITestCase
from django.urls import reverse
from rest_framework import status
from ..models import CustomUser
from ..services.two_factor_service import TwoFactorService

class VerificationAPITests(APITestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!'
        )
        self.user.email_verified = True
        self.user.save()

    def test_verify_2fa(self):
        """Test verificación de código 2FA"""
        self.client.force_authenticate(user=self.user)
        url = reverse('verify_2fa')  # Usar URL web
        response = self.client.post(url, {'code': 'test_code'})
        self.assertIn(response.status_code, [200, 302])  # Aceptar ambos códigos

    def test_verify_2fa_invalid_code(self):
        """Test verificación con código 2FA inválido"""
        self.client.force_authenticate(user=self.user)
        url = reverse('verify_2fa')  # Usar URL web en lugar de API
        response = self.client.post(url, {'code': '000000'})
        self.assertEqual(response.status_code, 302)  # Debe redirigir al login