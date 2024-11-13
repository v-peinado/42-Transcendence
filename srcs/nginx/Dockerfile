FROM nginx:alpine

# Copia la configuración personalizada de nginx (si la tienes)
COPY ./nginx.conf /etc/nginx/conf.d/default.conf

# No necesitas usar "COPY ../frontend", ya que ahora el contexto es el directorio raíz del proyecto.
# Montamos el volumen frontend desde docker-compose.yml, por lo que no es necesario copiarlo aquí.

CMD ["nginx", "-g", "daemon off;"]