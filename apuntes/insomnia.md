# Guía Práctica para Probar la API con Insomnia

## Paso 1: Crear un Nuevo Usuario

1. **Abrir Insomnia**:
   - Si no tienes Insomnia instalado, puedes descargarlo desde [insomnia.rest/download](https://insomnia.rest/download).

2. **Crear una Nueva Petición**:
   - Haz clic en el botón morado `Create` en la esquina superior izquierda.
   - Selecciona `Request` (o `Nueva Petición` si está en español).
   - Ponle un nombre como "Crear Usuario" y selecciona el método `POST`.

3. **Configurar la Petición**:
   - En la barra de dirección, escribe: `http://localhost:8000/api/register/`.
   - Ve a la pestaña `Body`, selecciona `JSON` y copia el siguiente contenido:
   ```json
   {
       "username": "nuevousuario",
       "email": "usuario@ejemplo.com",
       "password1": "tucontraseña",
       "password2": "tucontraseña"
   }
   ```
 - Modifica los datos por los que quieras usar.

4. **Enviar la Petición**:
   - Haz clic en el botón `Send` (o `Enviar`).
   - Si todo va bien, verás un mensaje de éxito. Si algo falla, el mensaje te dirá qué corregir.

## Paso 2: Hacer Login con tu Usuario

1. **Crear otra Petición Nueva**:
   - Sigue el mismo proceso: botón `Create` → `Request`.
   - Nombra esta petición como "Login" y selecciona el método `POST`.

2. **Configurar la Petición**:
   - En la barra de dirección, escribe: `http://localhost:8000/api/login/`.
   - Ve a la pestaña `Body`, selecciona `JSON` y copia el siguiente contenido:
   ```json
   {
       "username": "nuevousuario",
       "password1": "tucontraseña"
   }
   ```
   - Usa el mismo username y contraseña que pusiste en el registro.

3. **Enviar la Petición**:
   - Haz clic en `Send`.
   - Si las credenciales son correctas, recibirás un mensaje de login exitoso.


### RESUMEN: 

### 1. Registro de Usuario
- **Método**: POST
- **URL**: `http://localhost:8000/api/register/`
- **Headers**: 
  - Content-Type: application/json
- **Body** (JSON):

{
    "username": "nuevousuario",
    "email": "usuario@ejemplo.com",
    "password1": "tucontraseña",
    "password2": "tucontraseña"
}

### 2. Login de Usuario
- **Método**: POST
- **URL**: `http://localhost:8000/api/login/`
- **Headers**: 
  - Content-Type: application/json
- **Body** (JSON):

{
    "username": "tuusuario",
    "password1": "tucontraseña"
}

