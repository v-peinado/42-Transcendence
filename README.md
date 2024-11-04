# transcendence-primera-fase-

Para acceder a la página "hola mundo":

-Acceder desde la misma máquina local: 
	-> http://localhost:8000

-Para acceder desde otra máquina de la misma red (o si la levantamos en la máquina virtual y queremos acceder desde la máquina host)
	-> sustituir "localhost" por la ip privada de la máquina que hace de servidor.

# Checklist

## 1. Estructura Inicial del Proyecto
- [X] Crear el repositorio en Git.
- [ ] Definir la estructura de carpetas:
  - [ ] `backend/` para la lógica del servidor y API.
  - [ ] `frontend/` para la interfaz de usuario.
  - [ ] `assets/` para imágenes, sonidos, etc.
  - [X] `README.md` para la documentación del proyecto.

---

## 2. Parte Obligatoria
### A. Frontend
- [ ] **Implementación de Pong Básico**:
  - [ ] Diseñar la interfaz de usuario con HTML y CSS.
  - [ ] Programar la lógica del juego en JavaScript puro:
    - [ ] Inicializar el juego.
    - [ ] Manejar el movimiento de las palas.
    - [ ] Detectar colisiones entre la bola y las palas.
    - [ ] Actualizar el marcador en tiempo real.
    - [ ] Implementar reinicio del juego.

### B. Backend
- [ ] **Configuración del Servidor**:
  - [ ] Configurar un servidor básico usando Node.js y Express.
  - [ ] **Configurar la Base de Datos**:
    - [ ] Elegir un sistema de base de datos.
    - [ ] Definir el esquema de la base de datos para almacenar usuarios y puntuaciones.
    - [ ] Implementar la conexión a la base de datos.
  
- [ ] **Implementar la Lógica del Juego**:
  - [ ] Manejar el estado del juego.
  - [ ] Sincronizar la lógica del juego entre jugadores.

### C. API
- [ ] **Desarrollar la API para el Juego**:
  - [ ] Definir las rutas de la API:
    - [ ] `POST /game/start` - Inicializa el juego.
    - [ ] `POST /game/move` - Envía el movimiento de los jugadores.
    - [ ] `GET /game/state` - Devuelve el estado actual del juego.
    - [ ] `POST /scores` - Guarda las puntuaciones en la base de datos.
    - [ ] `GET /scores` - Obtiene las puntuaciones para mostrar en la interfaz.
  - [ ] Documentar la API para facilitar el uso y la integración.

---
