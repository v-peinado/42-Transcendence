from authentication.services.token_service import TokenService
from django.utils.http import urlsafe_base64_decode
from django.template.loader import render_to_string
from django.core.exceptions import ValidationError
from .rate_limit_service import RateLimitService
from authentication.models import CustomUser
from django.utils.html import strip_tags
from django.core.mail import send_mail
from django.conf import settings
import logging
import jwt

logger = logging.getLogger(__name__)

class EmailVerificationService:
    @staticmethod
    def verify_email(uidb64, token):
        """Verifies user's email to activate account"""
        try:
            uid = urlsafe_base64_decode(uidb64).decode() # Decode user ID from base64 
            user = CustomUser.objects.get(pk=uid) # Get user by ID from database
            payload = TokenService.decode_jwt_token(token)	# Decode JWT token to get user ID

            if user and payload and payload["user_id"] == user.id:
                user.email_verified = True
                user.is_active = True
                user.email_verification_token = None
                user.save()

                MailSendingService.send_welcome_email(user)
                return user
            else:
                raise ValidationError("Token de verificación inválido")

        except (	
            TypeError,	# if uidb64 is not a valid base64 string
            ValueError,	# if value is not a valid base64 string
            OverflowError,	# if value is too large
            CustomUser.DoesNotExist, # if user does not exist
            jwt.InvalidTokenError,	# if token is invalid
        ):
            raise ValidationError("El enlace de verificación no es válido")
        except Exception as e:
            raise ValidationError(f"Error sending verification email: {str(e)}")

    @staticmethod
    def verify_email_change(uidb64, token):
        """Verifies email change request"""
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = CustomUser.objects.get(pk=uid)
            payload = TokenService.decode_jwt_token(token)

            if not (
                user # Check if user exists
                and payload # Check if payload exists
                and payload["user_id"] == user.id # Check if user ID matches the payload
                and token == user.pending_email_token # Check if token matches the pending email token
            ):
                raise ValueError("Token inválido")

			# Update user email (swapping old email with new email)
            old_email = user.email
            user.email = user.pending_email
            user.pending_email = None
            user.pending_email_token = None
            user.save()

            MailSendingService.send_email_change_confirmation(user, old_email)
            return user

        except Exception as e:
            raise ValueError(f"Error sending email change: {str(e)}")


### Mail sending methods ###

class MailSendingService:
    @staticmethod
    def _check_email_rate_limit(user_id):
        """Helper method to check email sending rate limits"""
        rate_limiter = RateLimitService()
        is_limited, remaining_time = rate_limiter.is_rate_limited(user_id, 'email_send')
        
        if is_limited:
            logger.warning(f"Rate limit exceeded for user {user_id} on email sending")
            raise ValidationError(f"Demasiados emails enviados. Por favor, espera {remaining_time} segundos.")
    
    @staticmethod
    def send_verification_email(user, token):
        """Sends verification email"""
        try:
            MailSendingService._check_email_rate_limit(user.id)
            
            subject = "Verifica tu cuenta de PongOrama"
            context = {
                "user": user,
                "domain": settings.SITE_URL,
                "uid": token["uid"],
                "token": token["token"],
                "email": user.decrypted_email,
            }
            html_message = render_to_string(
                "authentication/email_verification.html", context
            )
            plain_message = strip_tags(html_message)

            send_mail(
                subject,
                plain_message,
                settings.DEFAULT_FROM_EMAIL,
                [user.decrypted_email],  
                html_message=html_message,
                fail_silently=False,
            )
            # Reset rate limit after sending email successfully
            rate_limiter = RateLimitService()
            rate_limiter.reset_limit(user.id, 'email_send')
            return True
        except ValidationError as e:
            # Re-raise the validation exception (rate limit)
            raise e
        except Exception as e:
            raise Exception(f"Error sending verification email: {str(e)}")

    @staticmethod
    def send_welcome_email(user):
        """Send welcome email to new user"""
        try:
            subject = "¡Bienvenido a PongOrama!"
            context = {
                "user": user,
                "email": user.decrypted_email,  
            }
            html_message = render_to_string("authentication/welcome_email.html", context)
            plain_message = strip_tags(html_message)

            send_mail(
                subject,
                plain_message,
                settings.DEFAULT_FROM_EMAIL,
                [user.decrypted_email],  
                html_message=html_message,
                fail_silently=False,
            )
            return True 
        except Exception as e:
            raise Exception(f"Error sending welcome email: {str(e)}")

    @staticmethod
    def send_password_changed_notification(user, is_reset=False):
        """Password change notification"""
        try:
            subject = "Tu contraseña ha sido cambiada"
            context = {"user": user, "reset": is_reset}
            html_message = render_to_string(
                "authentication/password_changed_email.html", context
            )
            plain_message = strip_tags(html_message)

            send_mail(
                subject,
                plain_message,
                settings.DEFAULT_FROM_EMAIL,
                [user.decrypted_email],
                html_message=html_message,
                fail_silently=False,
            )
            return True
        except Exception as e:
            raise Exception(f"Error sending password change notification: {str(e)}")

    @staticmethod
    def send_email_change_verification(user, verification_data):
        """Send email change verification email"""
        # The token expended in this method has a expiration time protection too
        # but it´s implemented in ProfileService.handle_email_change method that calls this method
        # see srcs/django/authentication/services/profile_service.py for more details
        try:
            subject = "Confirma tu nuevo email"

            verification_url = f"{settings.SITE_URL}/verify-email-change/{verification_data['uid']}/{verification_data['token']}/"

            context = {
                "user": user,
                "new_email": verification_data["new_email"],
                "verification_url": verification_url,
            }

            html_message = render_to_string(
                "authentication/email_change_verification.html", context
            )
            plain_message = strip_tags(html_message)

            send_mail(
                subject,
                plain_message,
                settings.DEFAULT_FROM_EMAIL,
                [verification_data["new_email"]],
                html_message=html_message,
                fail_silently=False,
            )
            return True
        except Exception as e:
            raise Exception(
                f"Error sending email change verification email: {str(e)}"
            )

    @staticmethod
    def send_email_change_confirmation(user, old_email):
        """Send email change confirmation email"""
        try:
            subject = "Tu email ha sido actualizado"
            context = {"user": user, "old_email": old_email, "new_email": user.email}
            html_message = render_to_string(
                "authentication/email_change_confirmation.html", context
            )
            plain_message = strip_tags(html_message)

            send_mail(
                subject,
                plain_message,
                settings.DEFAULT_FROM_EMAIL,
                [user.decrypted_email],
                html_message=html_message,
                fail_silently=False,
            )
            return True
        except Exception as e:
            raise Exception(
                f"Error sending email change confirmation email: {str(e)}"
            )

    @staticmethod
    def send_password_reset_email(user, verification_data):
        """Send password reset email"""
        try:
            MailSendingService._check_email_rate_limit(user.id)
            
            subject = "Resetear contraseña de PongOrama"
            context = {
                "user": user,
                "verification_url": f"{settings.SITE_URL}/reset/{verification_data['uid']}/{verification_data['token']}/",
            }

            html_message = render_to_string(
                "authentication/password_reset_email.html", context
            )
            plain_message = strip_tags(html_message)

            send_mail(
                subject,
                plain_message,
                settings.DEFAULT_FROM_EMAIL,
                [user.decrypted_email],
                html_message=html_message,
                fail_silently=False,
            )
            
            # Reset rate limit after sending email successfully
            rate_limiter = RateLimitService()
            rate_limiter.reset_limit(user.id, 'email_send')
            return True
        except ValidationError as e:
            # Re-raise the validation exception (rate limit)
            raise e
        except Exception as e:
            raise Exception(f"Error sending password reset email: {str(e)}")

    @staticmethod
    def send_inactivity_warning(user, remaining_days=0, time_unit='days', connection=None):
        """ Notifies users that their account will be deleted in the specified time period."""
        try:
            subject = "Your account will be deleted due to inactivity"
            context = {
                "user": user,
                "days_remaining": remaining_days,
                "time_unit": time_unit,
                "login_url": f"{settings.FRONTEND_URL}/login"
            }
            
            html_message = render_to_string('authentication/inactivity_warning_email.html', context)
            plain_message = strip_tags(html_message)
            
            send_mail(
                subject,
                plain_message,
                settings.DEFAULT_FROM_EMAIL,
                [user.decrypted_email],
                html_message=html_message,
                fail_silently=False,
                connection=connection,
            )
            
            logger.info(f"Inactivity email sent to {user.username}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending inactivity email to {user.username}: {str(e)}")
            raise Exception(f"Error sending inactivity email: {str(e)}")
