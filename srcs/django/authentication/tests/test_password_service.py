# authentication/tests/test_password_service.py

from django.test import TestCase
from django.core.exceptions import ValidationError
from ..models import CustomUser, PreviousPassword
from ..services.password_service import PasswordService

class PasswordServiceTest(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='oldpassword123'
        )
        PreviousPassword.objects.create(
            user=self.user, 
            password=self.user.password
        )

    def test_change_password_success(self):
        """Test cambio de contraseña exitoso"""
        result = PasswordService.change_password(self.user, 'Newpassword123!')
        self.assertTrue(result)
        self.assertTrue(self.user.check_password('Newpassword123!'))
        self.assertEqual(PreviousPassword.objects.filter(user=self.user).count(), 2)

    def test_validate_password_change(self):
        """Test validación completa de cambio de contraseña"""
        # Caso exitoso
        result = PasswordService.validate_password_change(
            self.user,
            'oldpassword123',  # Contraseña actual
            'Newpassword123!',  # Nueva contraseña
            'Newpassword123!'   # Confirmación
        )
        self.assertTrue(result)

        # Contraseña actual incorrecta
        with self.assertRaises(ValidationError):
            PasswordService.validate_password_change(
                self.user,
                'wrongpassword',
                'Newpassword123!',
                'Newpassword123!'
            )

        # Las nuevas contraseñas no coinciden
        with self.assertRaises(ValidationError):
            PasswordService.validate_password_change(
                self.user,
                'oldpassword123',
                'Newpassword123!',
                'DifferentPassword123!'
            )

        # Nueva contraseña demasiado simple
        with self.assertRaises(ValidationError):
            PasswordService.validate_password_change(
                self.user,
                'oldpassword123',
                'password',
                'password'
            )

    def test_previous_password_validation(self):
        """Test que no se pueden reutilizar contraseñas previas"""
        # Crear historial de contraseñas
        passwords = ['Password1!', 'Password2!', 'Password3!']
        
        for password in passwords:
            PasswordService.change_password(self.user, password)

        # Intentar reutilizar la última contraseña
        with self.assertRaises(ValidationError):
            PasswordService.validate_password_change(
                self.user,
                'Password3!',
                'Password3!',
                'Password3!'
            )

        # Intentar reutilizar la primera contraseña del historial
        with self.assertRaises(ValidationError):
            PasswordService.validate_password_change(
                self.user,
                'Password3!',
                'Password1!',
                'Password1!'
            )

    def test_reset_password(self):
        """Test reseteo de contraseña"""
        result = PasswordService.reset_password(self.user, 'ResetPassword123!')
        self.assertTrue(result)
        self.assertTrue(self.user.check_password('ResetPassword123!'))
        self.assertEqual(PreviousPassword.objects.filter(user=self.user).count(), 2)

@staticmethod
def validate_password_change(user, current_password, new_password1, new_password2):
    """Validar cambio de contraseña"""
    try:
        if not user.check_password(current_password):
            raise ValidationError('La contraseña actual es incorrecta')
        # ... resto de validaciones
        return True  # Retornar True si todo está bien
    except ValidationError as e:
        raise e