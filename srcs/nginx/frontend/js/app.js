document.getElementById("loginForm").addEventListener("submit", function(event) {
    event.preventDefault(); // Prevenir el envío del formulario
  
    const username = document.getElementById("username").value;
    const password = document.getElementById("password").value;
    const errorMessage = document.getElementById("error");

    // Verificar si los campos están vacíos
    if (!username || !password) {
      errorMessage.style.display = "block";
      errorMessage.textContent = "Please fill in both fields.";
    } else {
      errorMessage.style.display = "none";

      // Enviar los datos al servidor (API de login)
      fetch('/api/login/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          username: username,
          password1: password
        })
      })
      .then(response => response.json())  // Procesar la respuesta JSON
      .then(data => {
        if (data.message) {
          // Si el login es exitoso
          alert(data.message);
          // Redirigir o hacer algo después del login exitoso
        } else if (data.error) {
          // Si hay un error (usuario no encontrado o contraseña incorrecta)
          errorMessage.style.display = "block";
          errorMessage.textContent = data.error;
        }
      })
      .catch(error => {
        // Manejar errores de red o problemas con la solicitud
        console.error('Error:', error);
        errorMessage.style.display = "block";
        errorMessage.textContent = "An error occurred. Please try again later.";
      });
    }
});

  
