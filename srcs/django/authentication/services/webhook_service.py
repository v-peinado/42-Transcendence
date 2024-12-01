from django.core.exceptions import ValidationError
from django.conf import settings
import requests
import json
import hmac
import hashlib
from ..models import CustomUser

class WebhookService:
    @staticmethod
    def verify_signature(payload, signature, secret):
        """Verifica la firma del webhook"""
        try:
            expected = hmac.new(
                secret.encode('utf-8'),
                payload.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            return hmac.compare_digest(expected, signature)
        except Exception as e:
            raise ValidationError(f"Error al verificar firma: {str(e)}")

    @staticmethod
    def process_webhook(payload, event_type):
        """Procesa los webhooks recibidos"""
        try:
            if event_type == 'user.updated':
                return WebhookService.handle_user_update(payload)
            elif event_type == 'user.deleted':
                return WebhookService.handle_user_deletion(payload)
            else:
                raise ValidationError(f"Tipo de evento no soportado: {event_type}")
        except Exception as e:
            raise ValidationError(f"Error procesando webhook: {str(e)}")

    @staticmethod
    def handle_user_update(payload):
        """Maneja actualizaciones de usuario desde 42"""
        try:
            user_data = payload.get('user', {})
            fortytwo_id = str(user_data.get('id'))
            
            user = CustomUser.objects.filter(fortytwo_id=fortytwo_id).first()
            if user:
                # Actualizar datos del usuario
                if 'email' in user_data:
                    user.email = user_data['email']
                if 'image_url' in user_data:
                    user.fortytwo_image = user_data['image_url']
                user.save()
                return True
            return False
        except Exception as e:
            raise ValidationError(f"Error al manejar actualización de usuario: {str(e)}")

    @staticmethod
    def handle_user_deletion(payload):
        """Maneja eliminación de usuario desde 42"""
        try:
            user_data = payload.get('user', {})
            fortytwo_id = str(user_data.get('id'))
            
            user = CustomUser.objects.filter(fortytwo_id=fortytwo_id).first()
            if user:
                # Guardar datos importantes antes de anonimizar
                old_username = user.username
                old_email = user.email
                
                # Anonimizar y desactivar usuario
                user.is_active = False
                user.email = f"deleted_{user.id}@deleted.com"
                user.username = f"deleted_user_{user.id}"
                user.fortytwo_image = None
                user.save()
                
                # Retornar información sobre la operación
                return {
                    'status': 'success',
                    'message': f'Usuario {old_username} anonimizado correctamente',
                    'data': {
                        'original_username': old_username,
                        'original_email': old_email,
                        'fortytwo_id': fortytwo_id,
                        'new_username': user.username
                    }
                }
            return {'status': 'not_found', 'message': 'Usuario no encontrado'}
            
        except Exception as e:
            raise ValidationError(f"Error al manejar eliminación de usuario: {str(e)}")

    @staticmethod
    def send_webhook_response(url, data, secret):
        """Envía respuesta a un webhook"""
        try:
            # Crear firma para la respuesta
            payload = json.dumps(data)
            signature = hmac.new(
                secret.encode('utf-8'),
                payload.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            headers = {
                'Content-Type': 'application/json',
                'X-Hub-Signature': f'sha256={signature}'
            }
            
            response = requests.post(url, 
                                  data=payload, 
                                  headers=headers)
            return response.status_code == 200
        except Exception as e:
            raise ValidationError(f"Error al enviar respuesta webhook: {str(e)}")