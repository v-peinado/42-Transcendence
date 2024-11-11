## Intentos de Inyección SQL

### 1. Intento de comentario SQL
- **Usuario**: `admin' --`
- **Contraseña**: `cualquier cosa`

**Explicación**: Este intento agrega un comentario SQL (`--`) después del nombre de usuario, lo que hace que el resto de la consulta SQL sea ignorado. Si la aplicación no está protegida, esto podría permitir el acceso sin necesidad de una contraseña válida.

### 2. Intento de OR lógico
- **Usuario**: `' OR '1'='1`
- **Contraseña**: `cualquier cosa`

**Explicación**: Este intento utiliza una condición OR (`' OR '1'='1`) que siempre es verdadera. Si la aplicación no está protegida, esto podría permitir el acceso sin necesidad de una contraseña válida.

### 3. Intento de cierre de consulta
- **Usuario**: `admin') --`
- **Contraseña**: `cualquier cosa`

**Explicación**: Este intento cierra la consulta SQL con un paréntesis (`)`) y luego agrega un comentario (`--`). Si la aplicación no está protegida, esto podría permitir el acceso sin necesidad de una contraseña válida.

### 4. Intento de combinación de consultas
- **Usuario**: `admin'; DROP TABLE users; --`
- **Contraseña**: `cualquier cosa`

**Explicación**: Este intento cierra la consulta SQL con un punto y coma (`;`) y luego intenta ejecutar una segunda consulta que elimina una tabla (`DROP TABLE users`). Si la aplicación no está protegida, esto podría causar daños significativos a la base de datos.

Para más info, este vídeo está genial:

https://www.youtube.com/watch?v=tdtAmH3ZSAI
