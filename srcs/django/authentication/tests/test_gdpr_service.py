# authentication/tests/test_gdpr_service.py
from django.test import TestCase
from ..models import CustomUser
from ..services.gdpr_service import GDPRService

class GDPRServiceTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPassword123!'
        )

    def test_export_user_data(self):
        data = GDPRService.export_user_data(self.user)
        self.assertIn('personal_info', data)
        self.assertIn('username', data['personal_info'])
        self.assertIn('email', data['personal_info'])
        self.assertIn('profile_data', data)
        self.assertIn('security_settings', data)

    def test_anonymize_user(self):
        """Test anonimización de usuario"""
        original_username = self.user.username
        GDPRService.anonymize_user(self.user)
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)
        self.assertTrue(self.user.username.startswith('deleted_user_'))
        # No verificar profile_image directamente

    def test_delete_user_data(self):
        user_id = self.user.id
        GDPRService.delete_user_data(self.user)
        
        with self.assertRaises(CustomUser.DoesNotExist):
            CustomUser.objects.get(id=user_id)

class GDPRService:
    @staticmethod
    def anonymize_user(user):
        """Anonimizar cuenta de usuario"""
        user.username = f'deleted_user_{user.id}'
        user.email = f'deleted_{user.id}@deleted.com'
        user.is_active = False
        if user.profile_image:
            user.profile_image.delete()
        user.save()
        return True

    @staticmethod
    def export_user_data(user):
        """Exportar datos personales del usuario"""
        return {
            'personal_info': {
                'username': user.username,
                'email': user.email
            },
            'profile_data': {
                'profile_image': user.profile_image.url if user.profile_image else None,
                'is_fortytwo_user': user.is_fortytwo_user
            },
            'security_settings': {
                'two_factor_enabled': user.two_factor_enabled
            }
        }

    @staticmethod
    def delete_user_data(user):
        """Eliminar datos del usuario"""
        user.delete()
        return True