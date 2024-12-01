from django.test import TestCase
from django.conf import settings
from unittest.mock import patch
from ..models import CustomUser
from ..services.webhook_service import WebhookService
import json
import hmac
import hashlib

class WebhookServiceTest(TestCase):
    def setUp(self):
        self.webhook_secret = 'test_secret'
        self.test_payload = {
            'event': 'user.updated',
            'user': {'id': '12345'}
        }
        self.user = CustomUser.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!',
            fortytwo_id='12345'
        )

    def test_verify_signature(self):
        """Test verificación de firma del webhook"""
        payload = json.dumps(self.test_payload)
        signature = hmac.new(
            self.webhook_secret.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        # Test firma válida
        self.assertTrue(
            WebhookService.verify_signature(payload, signature, self.webhook_secret)
        )

        # Test firma inválida
        invalid_signature = "invalid_signature"
        self.assertFalse(
            WebhookService.verify_signature(payload, invalid_signature, self.webhook_secret)
        )

    def test_handle_user_update(self):
        """Test manejo de actualización de usuario"""
        payload = {
            'user': {
                'id': '12345',
                'email': 'new@example.com',
                'image_url': 'new_image_url'
            }
        }

        result = WebhookService.handle_user_update(payload)
        self.assertTrue(result)

        # Verificar que el usuario fue actualizado
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'new@example.com')
        self.assertEqual(self.user.fortytwo_image, 'new_image_url')

    def test_handle_user_deletion(self):
        """Test manejo de eliminación de usuario"""
        payload = {'user': {'id': '12345'}}
        
        result = WebhookService.handle_user_deletion(payload)
        self.assertTrue(result)

        # Verificar que el usuario fue anonimizado
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)
        self.assertTrue(self.user.username.startswith('deleted_user_'))
        self.assertTrue(self.user.email.startswith('deleted_'))
        self.assertIsNone(self.user.fortytwo_image)

    @patch('requests.post')
    def test_send_webhook_response(self, mock_post):
        """Test envío de respuesta webhook"""
        mock_post.return_value.status_code = 200
        url = 'https://test.com/webhook'
        data = {'status': 'success'}
        
        result = WebhookService.send_webhook_response(url, data, self.webhook_secret)
        self.assertTrue(result)
        
        # Verificar que se llamó a requests.post con los parámetros correctos
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        self.assertEqual(call_args[0][0], url)
        self.assertIn('X-Hub-Signature', call_args[1]['headers'])