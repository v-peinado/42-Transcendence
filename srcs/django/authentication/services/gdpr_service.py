from django.core.exceptions import ValidationError
from django.utils import timezone
import logging


logger = logging.getLogger(__name__)

class GDPRService:
    @staticmethod
    def export_user_data(user):
        """Exports all user's personal data in dictionary format"""
        return {
            "personal_info": {
                "username": user.username,
                "email": user.decrypted_email,
                "date_joined": user.date_joined,
                "last_login": user.last_login,
                "is_active": user.is_active,
                "acepted_privacy_policy": True, # This is acepted in the moment of the registration
				"date_of_acceptance": user.date_joined, # This is the date of the registration
                "is_fortytwo_user": user.is_fortytwo_user,
            },
            "security_settings": {
                "two_factor_enabled": user.two_factor_enabled,
                "email_verified": user.email_verified,
            },
        }

    @staticmethod
    def anonymize_user(user):
        """Anonymizes user's personal data"""
        try:
            # Generate anonymous data
            anon_username = f"deleted_user_{user.id}"
            anon_email = f"deleted_{user.id}@deleted.local"
            anon_password = "pbkdf2_sha256$deleted_password"
            
            # Update only existing fields
            user.username = anon_username
            user.email = anon_email
            user.password = anon_password
            user.first_name = "Deleted"
            user.last_name = "User"
            user.profile_image = None
            user.fortytwo_image = None
            user.is_active = False
            user.two_factor_enabled = False
            user.two_factor_secret = None
            user.deleted_at = timezone.now()
            user.fortytwo_id = None
            user.pending_email = None
            user.pending_email_token = None
            
            user.email_hash = None
            
            # Save only the fields that exist in the model
            user.save(update_fields=[
                'email', 'username', 'password', 'first_name', 
                'last_name', 'profile_image', 'fortytwo_image', 
                'is_active', 'two_factor_enabled', 'two_factor_secret', 
                'deleted_at', 'fortytwo_id', 'pending_email', 
                'pending_email_token', 'email_hash'
            ])

            return True
        except Exception as e:
            logger.error(f"Error in anonymize_user: {str(e)}")
            # Raise the error to inform the caller (upper layer of the system)
            raise ValidationError(f"Error anonymizing user: {str(e)}")

    @staticmethod
    def delete_user_data(user):
        """Soft deletes user's account only by anonymizing their data and deactivating the account, (auditoring GDPR purposes)"""
        try:
            GDPRService.anonymize_user(user) # anonymize user data
            return True
        except Exception as e: # Catch all exceptions of the anonymize_user method
            logger.error(f"Error in delete_user_data: {str(e)}")
            
			# If the exception is already a ValidationError, (raised by the anonymize_user method)
            if isinstance(e, ValidationError):
                raise	# Raise the exception to inform the caller (upper layer of the system)
            # If the exception is not a ValidationError, the error is from the delete_user_data method
            else:
                raise ValidationError(f"Error deleting user: {str(e)}")
    	# *This is developed by me, only to understand how raise works in Python and Django


# Important disclaimer! 
# 
# This is only a few parts of the GDPR methods,
# there is more in other parts of the project, because of the complexity of the GDPR rules.
# For example: cleanup_service.py and tasks.py 
# 