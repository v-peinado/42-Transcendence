class AuthGDPR {
    static async getGDPRSettings() {
        try {
            // Obtener política de privacidad
			const response = await fetch('/api/gdpr/settings/', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                credentials: 'include'
            });
			return await response.json();
		} catch (error) {
			console.error('Error getting GDPR settings:', error);
			return { status: 'error', message: error.message };
		}
	}

    static async updateGDPRSettings(settings) {
        try {
			const response = await fetch('/api/gdpr/settings/', {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json',
					'X-CSRFToken': this.getCSRFToken()
				},
				body: JSON.stringify(settings),
				credentials: 'include'
			});
			return await response.json();
		} catch (error) {
			console.error('Error updating GDPR settings:', error);
			return { status: 'error', message: error.message };
		}
	}

	static async downloadUserData() {
		try {
			// Mostrar indicador de proceso
			console.log('Iniciando descarga de datos GDPR...');

			// Hacer una solicitud directa al endpoint de descarga para obtener el blob
			const response = await fetch('/api/gdpr/export-data/download/', {
				method: 'GET',
				headers: {
					'X-CSRFToken': this.getCSRFToken()
				},
				credentials: 'include'
			});

			// Verificar si la respuesta es correcta
			if (!response.ok) {
				const errorData = await response.json();
				throw new Error(errorData.message || 'Error en la descarga de datos');
			}

			// Comprobar el tipo de contenido - si es JSON pero con un mensaje de error
			const contentType = response.headers.get('content-type');
			if (contentType && contentType.includes('application/json')) {
				// Intentar analizar como JSON para ver si hay un mensaje de error
				const jsonData = await response.json();
				if (jsonData.status === 'error') {
					throw new Error(jsonData.message || 'Error al obtener los datos');
				}

				// Si llegamos aquí, los datos son JSON válidos y no contienen error
				// Convertir los datos JSON a un blob y descargar
				const blob = new Blob([JSON.stringify(jsonData, null, 2)], { type: 'application/json' });
				const username = localStorage.getItem('username') || 'user';
				// Usar la referencia de clase estática en lugar de this
				AuthGDPR.downloadBlob(blob, `user_data_${username}.json`);
				return { status: 'success', message: 'Datos descargados correctamente' };
			}

			// Si no es JSON o no contiene error, obtener como blob y descargar
			const blob = await response.blob();
			const username = localStorage.getItem('username') || 'user';
			// Usar la referencia de clase estática en lugar de this
			AuthGDPR.downloadBlob(blob, `user_data_${username}.json`);

			return { status: 'success', message: 'Datos descargados correctamente' };
		} catch (error) {
			console.error('Error downloading user data:', error);
			return { status: 'error', message: error.message };
		}
	}

	static downloadBlob(blob, filename) {
		// Crear un URL para el blob
		const url = window.URL.createObjectURL(blob);

		// Crear un elemento <a> para la descarga
		const a = document.createElement('a');
		a.href = url;
		a.download = filename;

		// Añadir al documento, hacer click y luego eliminar
		document.body.appendChild(a);
		a.click();

		// Limpiar después de un momento
		setTimeout(() => {
			document.body.removeChild(a);
			window.URL.revokeObjectURL(url);
		}, 100);
	}

	static getCSRFToken() {
		const cookieValue = document.cookie
			.split('; ')
			.find(row => row.startsWith('csrftoken='))
			?.split('=')[1];
		return cookieValue || '';
	}

    static async deleteAccount(password = null) {
        try {
            const response = await fetch('/api/profile/delete-account/', {  // Corregir la ruta
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({ confirm_password: password }),
                credentials: 'include'
            });

            if (!response.ok) {
                const contentType = response.headers.get('content-type');
                if (contentType && contentType.includes('application/json')) {
                    const data = await response.json();
                    throw new Error(data.message || 'Error al eliminar la cuenta');
                } else {
                    throw new Error('Error de servidor al eliminar la cuenta');
                }
            }

            const data = await response.json();
            return { status: 'success', ...data };  // Asegurar que siempre devolvemos un objeto con status
        } catch (error) {
            console.error('Error en deleteAccount:', error);
            throw error;
        }
    }

    static getDefaultGDPRPolicy() {
        return {
            data_collection: [
                "Nombre de usuario y correo electrónico para identificación",
                "Datos de inicio de sesión y actividad de la cuenta",
                "Imagen de perfil (opcional)",
                "Información de autenticación de dos factores (si está activada)",
                "Datos de integración con 42 (si aplica)"
            ],
            data_usage: [
                "Autenticación y gestión de tu cuenta",
                "Comunicaciones importantes sobre tu cuenta y seguridad",
                "Mejora de nuestros servicios y experiencia de usuario",
                "Cumplimiento de obligaciones legales y regulatorias"
            ],
            user_rights: [
                "Derecho de acceso: Puedes descargar todos tus datos personales",
                "Derecho al olvido: Puedes solicitar la eliminación de tu cuenta",
                "Derecho de rectificación: Puedes modificar tus datos personales",
                "Derecho de portabilidad: Puedes exportar tus datos en formato JSON",
                "Derecho de oposición: Puedes desactivar funcionalidades opcionales"
            ],
            security_measures: [
                "Encriptación de datos sensibles",
                "Autenticación de dos factores opcional",
                "Anonimización de datos en caso de eliminación de cuenta",
                "Auditoría de accesos y cambios en datos personales",
                "Almacenamiento seguro de contraseñas mediante hash"
            ],
            data_retention: [
                "Tus datos se mantienen mientras tu cuenta esté activa",
                "Al eliminar tu cuenta, tus datos son anonimizados",
                "Mantenemos logs anonimizados por razones de seguridad",
                "Los backups se eliminan según política de retención"
            ]
        };
    }
}

export { AuthGDPR };
