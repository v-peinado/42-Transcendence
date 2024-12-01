from django.test import TestCase, Client
from django.urls import reverse
from ..models import CustomUser
from django.core import mail

class ViewsTest(TestCase):
    def setUp(self):
        """Configuración inicial para los tests"""
        self.client = Client()
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'TestPass123!'
        }
        self.user = CustomUser.objects.create_user(**self.user_data)
        self.user.email_verified = True
        self.user.save()

    def test_home_view(self):
        """Test vista de inicio"""
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'authentication/home.html')

    def test_login_view(self):
        """Test vista de login"""
        # Test GET
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'authentication/login.html')

        # Test POST exitoso
        response = self.client.post(reverse('login'), self.user_data)
        self.assertRedirects(response, reverse('user'))

    def test_register_view(self):
        """Test vista de registro"""
        response = self.client.post(reverse('register'), {
            'username': 'newuser',
            'email': 'new@example.com',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!',
            'privacy_policy': True  
        })
        self.assertRedirects(response, reverse('login'))

    def test_edit_profile_view(self):
        """Test vista de edición de perfil"""
        self.client.login(**self.user_data)
        response = self.client.get(reverse('edit_profile'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'authentication/edit_profile.html')

    def test_verify_2fa_view(self):
        """Test vista de verificación 2FA"""
        # Configurar sesión para 2FA
        session = self.client.session
        session['pending_user_id'] = self.user.id
        session['user_authenticated'] = True
        session.save()

        response = self.client.get(reverse('verify_2fa'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'authentication/verify_2fa.html')