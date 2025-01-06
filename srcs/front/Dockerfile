FROM node:20-alpine

WORKDIR /app

RUN apk add --no-cache libc6-compat

# Configurar permisos
RUN mkdir -p /app && chown -R node:node /app

# Copiar solo los archivos necesarios
COPY --chown=node:node index.html ./
COPY --chown=node:node server.js ./
COPY --chown=node:node css/ ./css/
COPY --chown=node:node js/ ./js/

USER node

EXPOSE 3000

CMD ["node", "server.js"]
