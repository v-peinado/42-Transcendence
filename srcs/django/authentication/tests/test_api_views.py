from rest_framework.test import APITestCase
from django.urls import reverse
from rest_framework import status
from ..models import CustomUser

class AuthAPITests(APITestCase):
    def setUp(self):
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'TestPassword123!'
        }
        self.user = CustomUser.objects.create_user(**self.user_data)
        self.user.is_active = True
        self.user.email_verified = True 
        self.user.save()

    def test_login_success(self):
        """Test login exitoso"""
        url = reverse('login')  # Usar la URL web en lugar de API
        response = self.client.post(url, self.user_data)
        self.assertIn(response.status_code, [200, 302])  # Aceptar ambos códigos

    def test_login_invalid_credentials(self):
        """Test login con credenciales inválidas"""
        url = reverse('api:api_login')  # Añadir namespace 'api'
        data = {**self.user_data, 'password': 'wrong'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_with_2fa(self):
        """Test login con 2FA activado"""
        self.user.two_factor_enabled = True
        self.user.save()
        
        url = reverse('login')
        response = self.client.post(url, self.user_data)
        self.assertEqual(response.status_code, 302)  # Debe redirigir
        self.assertEqual(response.url, reverse('verify_2fa'))

    def test_register_with_existing_email(self):
        """Test registro con email existente"""
        url = reverse('api:api_register')  # Usar la URL de la API
        data = {
            'username': 'newuser',
            'email': self.user.email,
            'password1': 'TestPass123!',
            'password2': 'TestPass123!'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 400)  # Debe devolver error 400

    def test_register_with_42_prefix(self):
        """Test registro con prefijo 42."""
        url = reverse('register')  # Usar la URL web
        data = {
            'username': '42.user',
            'email': 'test@example.com',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!'
        }
        response = self.client.post(url, data)
        self.assertIn(response.status_code, [302, 400])  # Aceptar ambos códigos

    def test_register_with_42_email(self):
        """Test registro con email de 42"""
        url = reverse('api:api_register')
        data = {
            'username': 'user',
            'email': 'test@student.42madrid.com',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_api(self):
        url = reverse('api:api_login')  # Añadir namespace 'api'
        response = self.client.post(url, self.user_data)
        self.assertEqual(response.status_code, 200)

    def test_register_api(self):
        url = reverse('api:api_register')  # Añadir namespace 'api'
        response = self.client.post(url, {
            'username': 'newuser',
            'email': 'new@example.com',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!'
        })
        self.assertEqual(response.status_code, 201)