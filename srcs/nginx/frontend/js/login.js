document.addEventListener("DOMContentLoaded", function() {
  const loginForm = document.getElementById("loginForm");
  const loginButton = document.getElementById("loginButton");
  const loginWith42Button = document.getElementById("loginWith42");
  const errorMessage = document.getElementById("error");

  // Manejador de envío del formulario para login tradicional
  loginForm.addEventListener("submit", async function(event) {
      event.preventDefault(); // Prevenir el envío del formulario

      const username = document.getElementById("username").value;
      const password = document.getElementById("password").value;

      try {
          const response = await fetch('/api/authentication/login/', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ username, password })
          });

          const data = await response.json();

          if (data.status === "success") {
              alert(data.message);
              window.location.href = "/user.html";
          } else if (data.error) {
              errorMessage.style.display = "block";
              errorMessage.textContent = data.error;
          }
      } catch (error) {
          console.error('Error:', error);
          errorMessage.style.display = "block";
          errorMessage.textContent = "An error occurred. Please try again later.";
      }
  });

  // Manejador del botón para login con 42
  loginWith42Button.addEventListener("click", async function() {
      try {
          const response = await fetch('/api/authentication/42/api/42/login/', {
              method: 'GET',
              headers: { 'Content-Type': 'application/json' }
          });

          const data = await response.json();

          if (data.auth_url) {
              // Redirigir al usuario a la URL de autenticación de 42
              window.location.href = data.auth_url;
          } else {
              errorMessage.style.display = "block";
              errorMessage.textContent = "Error al obtener la URL de autenticación";
          }
      } catch (error) {
          console.error('Error:', error);
          errorMessage.style.display = "block";
          errorMessage.textContent = "An error occurred. Please try again later.";
      }
  });
});
