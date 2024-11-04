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
### A. Backend (Django)
- [ ] **Configuración del Servidor con Django**:
  - [ ] Instalar Django y configurar un nuevo proyecto.
  - [ ] Definir la estructura de la aplicación Django.
  
- [ ] **Configuración de la Base de Datos (PostgreSQL)**:
  - [ ] Instalar PostgreSQL.
  - [ ] Configurar la conexión de Django a PostgreSQL.
  - [ ] Definir modelos en Django para usuarios y puntuaciones.
  
- [ ] **Implementar la Lógica del Juego**:
  - [ ] Crear vistas y controladores para manejar el estado del juego.
  - [ ] Sincronizar la lógica del juego entre los jugadores a través de Django.

### B. Frontend (Bootstrap)
- [ ] **Desarrollo de la Interfaz de Usuario**:
  - [ ] Usar Bootstrap para crear un diseño responsivo.
  - [ ] Implementar la lógica del juego en JavaScript:
    - [ ] Crear elementos para las palas y la bola.
    - [ ] Manejar el estado del juego usando JavaScript.
    - [ ] Detectar colisiones y actualizar el marcador en tiempo real.
    - [ ] Implementar reinicio del juego.

### C. API
- [ ] **Desarrollar la API para el Juego**:
  - [ ] Definir las rutas de la API en Django.
  - [ ] Documentar la API para facilitar el uso y la integración.

---
