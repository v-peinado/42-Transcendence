from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from ..services.auth_service import AuthenticationService
from ..services.token_service import TokenService
from ..models import CustomUser
from unittest.mock import patch

class AuthServiceTests(TestCase):
    def setUp(self):
        self.test_user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'TestPass123!'
        }
        self.user = CustomUser.objects.create_user(
            username='existinguser',
            email='existing@example.com',
            password='ExistingPass123!'
        )

    def test_register_user_success(self):
        """Test registro exitoso de usuario"""
        user = AuthenticationService.register_user(
            self.test_user_data['username'],
            self.test_user_data['email'],
            self.test_user_data['password']
        )
        
        self.assertIsInstance(user, CustomUser)
        self.assertEqual(user.username, self.test_user_data['username'].lower())
        self.assertEqual(user.email, self.test_user_data['email'].lower())
        self.assertFalse(user.is_active)  # Usuario inactivo hasta verificar email

    def test_register_duplicate_username(self):
        """Test que no se pueden registrar usernames duplicados"""
        with self.assertRaises(ValidationError):
            AuthenticationService.register_user(
                'existinguser',
                'new@example.com',
                'NewPass123!'
            )

    def test_register_duplicate_email(self):
        """Test que no se pueden registrar emails duplicados"""
        with self.assertRaises(ValidationError):
            AuthenticationService.register_user(
                'newuser',
                'existing@example.com',
                'NewPass123!'
            )

    def test_register_invalid_42_email(self):
        """Test que no se pueden usar emails de 42"""
        with self.assertRaises(ValidationError):
            AuthenticationService.register_user(
                'newuser',
                'test@student.42madrid.com',
                'TestPass123!'
            )

    def test_authenticate_user_success(self):
        """Test autenticación exitosa"""
        user = AuthenticationService.authenticate_user(
            'existinguser',
            'ExistingPass123!'
        )
        self.assertIsInstance(user, CustomUser)
        self.assertEqual(user.username, 'existinguser')

    def test_authenticate_user_wrong_password(self):
        """Test autenticación con contraseña incorrecta"""
        with self.assertRaises(ValidationError):
            AuthenticationService.authenticate_user(
                'existinguser',
                'WrongPass123!'
            )

    def test_authenticate_user_not_found(self):
        """Test autenticación con usuario no existente"""
        with self.assertRaises(ValidationError):
            AuthenticationService.authenticate_user(
                'nonexistentuser',
                'TestPass123!'
            )

    @patch('authentication.services.email_service.EmailService.send_verification_email')
    def test_verify_email(self, mock_send_email):
        """Test verificación de email"""
        # Usuario no verificado
        user = CustomUser.objects.create_user(
            username='unverified',
            email='unverified@example.com',
            password='TestPass123!',
            is_active=False,
            email_verified=False
        )
        
        result = AuthenticationService.verify_email(user, 'test_token')
        
        self.assertTrue(result)
        self.assertTrue(user.email_verified)
        self.assertTrue(user.is_active)

    def test_verify_email(self):
        """Test verificación de email"""
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = TokenService.generate_verification_token(self.user)
        result = AuthenticationService.verify_email(uid, token['token'])
        self.assertTrue(result)

    @staticmethod
    def authenticate_user(username, password):
        """Autenticar usuario"""
        try:
            user = authenticate(username=username, password=password)
            if not user:
                raise ValidationError("Credenciales inválidas")
            return user
        except Exception as e:
            raise ValidationError(f"Error en autenticación: {str(e)}")