from django.test import TestCase, Client
from django.urls import reverse
from django.core import mail
from ..models import CustomUser

class WebViewsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = CustomUser.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!'
        )
        self.user.email_verified = True
        self.user.save()

    def test_home_view(self):
        """Test vista de inicio"""
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'authentication/home.html')

    def test_register_view(self):
        """Test vista de registro"""
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'authentication/register.html')

        # Test registro con email de 42
        data = {
            'username': 'newuser',
            'email': 'test@student.42madrid.com',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!'
        }
        response = self.client.post(reverse('register'), data)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(CustomUser.objects.filter(email=data['email']).exists())

    def test_verify_email(self):
        """Test verificación de email"""
        # Crear usuario no verificado
        user = CustomUser.objects.create_user(
            username='unverified',
            email='unverified@example.com',
            password='TestPass123!',
            is_active=False,
            email_verified=False
        )
        
        # Simular verificación de email
        response = self.client.get(reverse('verify_email', kwargs={
            'uidb64': 'test-uid',
            'token': 'test-token'
        }))
        
        self.assertEqual(response.status_code, 302)  # Redirección