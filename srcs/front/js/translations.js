export const messages = {
    AUTH: {
        EMAIL_VERIFICATION: {
            TITLE: "¡Casi listo!",
            MESSAGE: "Te hemos enviado un correo para verificar tu cuenta",
            SUBMESSAGE: "Por favor, revisa tu bandeja de entrada y sigue las instrucciones",
            BUTTON: "Volver al login",
            SUCCESS_TITLE: "¡Verificación exitosa!",
            SUCCESS_MESSAGE: "Tu cuenta ha sido verificada correctamente",
            SUCCESS_BUTTON: "Iniciar sesión"
        },
        TWO_FACTOR: {
            TITLE: "Verificación en dos pasos",
            MESSAGE: "Te hemos enviado un código a tu email",
            BUTTON: "Verificar"
        },
        RATE_LIMIT: {
            TITLE: "Usuario bloqueado",
            MESSAGES: {
                login: "Por seguridad, hemos bloqueado temporalmente tus intentos de inicio de sesión. Podrás intentarlo nuevamente en {time}.",
                two_factor: "Por razones de seguridad, tu cuenta ha sido bloqueada temporalmente. Podrás intentarlo de nuevo en {time}.",
                password_reset: "Has enviado demasiadas solicitudes de restablecimiento de contraseña. Por favor, espera {time}.",
                email_verification: "Has solicitado demasiadas verificaciones de email. Inténtalo de nuevo en {time}.",
                qr_generation: "Has generado demasiados códigos QR. Por favor, espera {time} antes de generar otro.",
                qr_validation: "Has realizado demasiados intentos de validación QR. Por favor, espera {time} antes de intentarlo de nuevo.",
                qr_uses: "Has alcanzado el límite máximo de 3 usos para este QR. Genera uno nuevo.",
                qr_expired: "El código QR ha expirado (válido por 8 horas). Por favor, genera uno nuevo.",
                email_send: "Has realizado demasiados intentos de envío de códigos. Por favor, espera {time} antes de solicitar otro código."
            }
        },
        ERRORS: {
            LOGIN_FAILED: '¡Vaya! No pudimos conectar con 42',
            INVALID_CREDENTIALS: 'Usuario o contraseña incorrectos',
            EMAIL_NOT_VERIFIED: 'Por favor verifica tu email para activar tu cuenta',
            NO_SESSION: 'No hay sesión activa',
            PRIVACY_POLICY: 'Debes aceptar la política de privacidad',
            RATE_LIMIT: "Has excedido el número máximo de intentos",
            INVALID_2FA_CODE: 'El código de verificación introducido no es correcto',
            DEFAULT: 'Ha ocurrido un error inesperado'
        }
    }
};
