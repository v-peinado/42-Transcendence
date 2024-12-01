from django.test import TestCase, Client
from django.core.exceptions import ValidationError
from unittest.mock import patch, MagicMock
from ..services.oauth_service import OAuth42Service
from ..models import CustomUser

class OAuth42ServiceTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.mock_user_info = {
            'id': '12345',
            'login': 'test42user',
            'email': 'test42@student.42madrid.com',
            'image_url': 'https://example.com/image.jpg'
        }

    @patch('requests.post')
    def test_get_access_token(self, mock_post):
        """Test obtención de token de acceso"""
        # Configurar mock
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'access_token': 'test_token'}
        mock_post.return_value = mock_response

        # Ejecutar test
        token = OAuth42Service.get_access_token('test_code')
        
        # Verificar resultado
        self.assertEqual(token, 'test_token')
        mock_post.assert_called_once()

    @patch('requests.get')
    def test_get_user_info(self, mock_get):
        """Test obtención de información de usuario"""
        # Configurar mock
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.mock_user_info
        mock_get.return_value = mock_response

        # Ejecutar test
        user_info = OAuth42Service.get_user_info('test_token')
        
        # Verificar resultado
        self.assertEqual(user_info, self.mock_user_info)
        mock_get.assert_called_once()

    def test_create_or_update_user(self):
        """Test creación y actualización de usuario"""
        # Probar creación de usuario nuevo
        user, created = OAuth42Service.create_or_update_user(self.mock_user_info)
        
        self.assertTrue(created)
        self.assertEqual(user.username, '42.test42user')
        self.assertEqual(user.email, self.mock_user_info['email'])
        self.assertEqual(user.fortytwo_id, self.mock_user_info['id'])
        self.assertTrue(user.is_fortytwo_user)
        self.assertTrue(user.is_active)
        self.assertTrue(user.email_verified)

        # Probar actualización de usuario existente
        new_info = self.mock_user_info.copy()
        new_info['image_url'] = 'https://example.com/new_image.jpg'
        
        updated_user, created = OAuth42Service.create_or_update_user(new_info)
        
        self.assertFalse(created)
        self.assertEqual(updated_user.fortytwo_image, new_info['image_url'])

    @patch.object(OAuth42Service, 'get_access_token')
    @patch.object(OAuth42Service, 'get_user_info')
    @patch.object(OAuth42Service, 'create_or_update_user')
    def test_process_oauth_callback(self, mock_create, mock_get_info, mock_get_token):
        """Test proceso completo de callback OAuth"""
        # Configurar mocks
        mock_get_token.return_value = 'test_token'
        mock_get_info.return_value = self.mock_user_info
        mock_create.return_value = (MagicMock(), True)

        # Ejecutar test
        user, created = OAuth42Service.process_oauth_callback('test_code')
        
        # Verificar que se llamaron todos los métodos necesarios
        mock_get_token.assert_called_once_with('test_code')
        mock_get_info.assert_called_once_with('test_token')
        mock_create.assert_called_once_with(self.mock_user_info)