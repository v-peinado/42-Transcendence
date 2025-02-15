from django.core.exceptions import ValidationError

class GDPRService:
    @staticmethod
    def export_user_data(user):
        """Exporta todos los datos personales del usuario en formato diccionario"""
        return {
            'personal_info': {
                'username': user.username,
                'email': user.email,
                'date_joined': user.date_joined,
                'last_login': user.last_login,
                'is_active': user.is_active,
                'is_fortytwo_user': user.is_fortytwo_user,
                'fortytwo_id': user.fortytwo_id if user.is_fortytwo_user else None,
            },
            'profile_data': {
                'profile_image': user.profile_image.url if user.profile_image else None,
                'fortytwo_image': user.fortytwo_image if user.is_fortytwo_user else None,
            },
            'security_settings': {
                'two_factor_enabled': user.two_factor_enabled,
                'email_verified': user.email_verified,
            }
        }

    @staticmethod
    def anonymize_user(user):
        """Anonimiza los datos personales del usuario"""
        try:
            # Generar identificadores anónimos
            anon_username = f"deleted_user_{user.id}"
            anon_email = f"deleted_{user.id}@anonymous.com"

            # Actualizar campos con datos anónimos
            user.username = anon_username
            user.email = anon_email
            user.first_name = "Deleted"
            user.last_name = "User"
            user.profile_image = None
            user.fortytwo_image = None
            user.is_active = False
            user.two_factor_enabled = False
            user.two_factor_secret = None
            user.save()

            return True
        except Exception as e:
            raise ValidationError(f"Error al anonimizar usuario: {str(e)}")

    @staticmethod
    def delete_user_data(user):
        """Elimina permanentemente la cuenta del usuario"""
        try:
            # Primero anonimizamos
            GDPRService.anonymize_user(user)
            # Luego eliminamos
            user.delete()
            return True
        except Exception as e:
            raise ValidationError(f"Error al eliminar usuario: {str(e)}")