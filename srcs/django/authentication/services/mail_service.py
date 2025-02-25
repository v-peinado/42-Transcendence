from django.core.mail import send_mail
from django.core.exceptions import ValidationError
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.html import strip_tags
from authentication.models import CustomUser
from authentication.services.token_service import TokenService
from django.utils.http import urlsafe_base64_decode
import jwt


class EmailVerificationService:
    @staticmethod
    def verify_email(uidb64, token):
        """Verifies user's email to activate account"""
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = CustomUser.objects.get(pk=uid)
            payload = TokenService.decode_jwt_token(token)

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
            TypeError,
            ValueError,
            OverflowError,
            CustomUser.DoesNotExist,
            jwt.InvalidTokenError,
        ):
            raise ValidationError("El enlace de verificación no es válido")
        except Exception as e:
            raise ValidationError(f"Error al verificar email: {str(e)}")

    @staticmethod
    def verify_email_change(uidb64, token):
        """Verifies email change request"""
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = CustomUser.objects.get(pk=uid)
            payload = TokenService.decode_jwt_token(token)

            if not (
                user
                and payload
                and payload["user_id"] == user.id
                and token == user.pending_email_token
            ):
                raise ValueError("Token inválido")

            old_email = user.email
            user.email = user.pending_email
            user.pending_email = None
            user.pending_email_token = None
            user.save()

            MailSendingService.send_email_change_confirmation(user, old_email)
            return user

        except Exception as e:
            raise ValueError(f"Error de verificación: {str(e)}")


class MailSendingService:
    @staticmethod
    def send_verification_email(user, token):
        """Sends verification email"""
        try:
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
            return True
        except Exception as e:
            raise Exception(f"Error al enviar email de verificación: {str(e)}")

    @staticmethod
    def send_welcome_email(user):
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
                [user.email],
                html_message=html_message,
                fail_silently=False,
            )
            return True
        except Exception as e:
            raise Exception(f"Error al enviar notificación: {str(e)}")

    @staticmethod
    def send_email_change_verification(user, verification_data):
        """Send email change verification email"""
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
                f"Error al enviar email de verificación de cambio: {str(e)}"
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
                [old_email],
                html_message=html_message,
                fail_silently=False,
            )
            return True
        except Exception as e:
            raise Exception(
                f"Error al enviar confirmación de cambio de email: {str(e)}"
            )

    @staticmethod
    def send_password_reset_email(user, verification_data):
        """Send password reset email"""
        try:
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
                [user.email],
                html_message=html_message,
                fail_silently=False,
            )
            return True
        except Exception as e:
            raise Exception(f"Error al enviar email de reset: {str(e)}")
