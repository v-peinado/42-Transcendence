from django.test import TestCase
from .test_base import BaseTestCase
from ..models import CustomUser, PreviousPassword
from django.core.exceptions import ValidationError

class CustomUserModelTest(TestCase):
    def setUp(self):
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'TestPass123!'
        }
        self.user = CustomUser.objects.create_user(**self.user_data)

    def test_create_user(self):
        self.assertEqual(self.user.username, 'testuser')
        self.assertTrue(self.user.check_password('TestPass123!'))

    def test_create_superuser(self):
        admin_data = {
            'username': 'admin',  # Username diferente
            'email': 'admin@example.com',
            'password': 'TestPass123!'
        }
        admin = CustomUser.objects.create_superuser(**admin_data)
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)

class PreviousPasswordModelTest(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!'
        )

    def test_previous_password_creation(self):
        """Test creación de historial de contraseñas"""
        prev_pass = PreviousPassword.objects.create(
            user=self.user,
            password=self.user.password
        )
        self.assertEqual(prev_pass.user, self.user)
        self.assertEqual(prev_pass.password, self.user.password)