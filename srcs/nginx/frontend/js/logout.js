document.addEventListener("DOMContentLoaded", function() {
    // Seleccionar el botón de logout
    const logoutButton = document.getElementById("logoutButton");
  
    // Función para obtener el token CSRF de las cookies
    function getCookie(name) {
      let cookieValue = null;
      if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
          const cookie = cookies[i].trim();
          if (cookie.substring(0, name.length + 1) === (name + '=')) {
            cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
            break;
          }
        }
      }
      return cookieValue;
    }
  
    // Agregar un event listener para el click en el botón
    logoutButton.addEventListener("click", function() {
      // Obtener el token CSRF
      const csrfToken = getCookie('csrftoken');
  
      // Llamar a la API de logout
      fetch('/api/authentication/logout/', {
        method: 'POST',  // Usamos POST para cerrar sesión
        headers: {
          'Content-Type': 'application/json',  // Especificamos que enviamos JSON
          'X-CSRFToken': csrfToken,  // Enviar el token CSRF en el encabezado
        },
        credentials: 'same-origin'  // Enviar cookies de sesión
      })
      .then(response => response.json())  // Procesamos la respuesta JSON
      .then(data => {
        if (data.status === "success") {
          alert(data.message);
          window.location.href = '/login.html';  // O la página de login que prefieras
        } else {
          console.error("Logout failed:", data.error);
          alert("Logout failed. Please try again.");
        }
      })
      .catch(error => {
        console.error('Error during logout:', error);
        alert("An error occurred. Please try again.");
      });
    });
  });
  

