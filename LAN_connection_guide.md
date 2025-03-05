# Guía de conexión en red LAN

## Para el servidor (host)

1. Asegúrate de conocer tu dirección IP en la red local:
   ```bash
   ifconfig   # En macOS/Linux
   ipconfig   # En Windows
   ```

2. Actualiza los certificados con tu IP:
   ```bash
   cd /Users/miguel/Desktop/transcendence_42/srcs/ssl
   chmod +x update_certs.sh
   ./update_certs.sh 192.168.1.144  # Reemplaza con tu IP actual
   ```

3. Reinicia los contenedores:
   ```bash
   cd /Users/miguel/Desktop/transcendence_42
   docker-compose down
   docker-compose up -d
   ```

4. Verifica que todo esté funcionando correctamente accediendo a:
   ```
   https://192.168.1.144:8445
   ```

## Para los clientes (otros ordenadores)

1. Asegúrate de estar en la misma red que el servidor.

2. Abre un navegador web y accede a:
   ```
   https://192.168.1.144:8445  # Reemplaza con la IP del servidor
   ```

3. Aparecerá una advertencia de certificado no confiable. Esto es normal porque estamos usando un certificado autofirmado. Haz click en "Avanzado" y luego en "Proceder a [IP] (no seguro)".

4. Ahora podrás usar la aplicación normalmente.

## Solución de problemas

- **No puedo conectarme al servidor**: Asegúrate de que ambos equipos están en la misma red y que no hay un firewall bloqueando la conexión.
  
- **Error de certificado**: Es normal ver una advertencia de seguridad, ya que estamos usando un certificado autofirmado para una IP local.

- **La aplicación no funciona correctamente**: Verifica que todas las URLs en la configuración usan la IP del servidor en lugar de "localhost".
