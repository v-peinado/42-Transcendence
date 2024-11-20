document.getElementById("registerForm").addEventListener("submit", function(event) {
    event.preventDefault(); // Prevenir el envío del formulario
  
    const username = document.getElementById("username").value;
    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;
    const confirmPassword = document.getElementById("confirmPassword").value;
    const errorMessage = document.getElementById("error");

    // Verificar si los campos están vacíos
    if (!username || !email || !password || !confirmPassword) {
        errorMessage.style.display = "block";
        errorMessage.textContent = "Please fill in all fields.";
    } else if (password !== confirmPassword) {
        errorMessage.style.display = "block";
        errorMessage.textContent = "Passwords do not match.";
    } else {
        errorMessage.style.display = "none";

        // Enviar los datos al servidor (API de registro)
        fetch('/api/authentication/register/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                username: username,
                email: email,
                password1: password,
                password2: confirmPassword  // Enviar confirmación de contraseña
            })
        })
        .then(response => response.json())  // Procesar la respuesta JSON
        .then(data => {
            if (data.status == "success") {
                // Registro exitoso
                alert(data.message);
                window.location.href = '/index.html';  // Redirigir al login
            } else if (data.error) {
                // Mostrar mensaje de error si ocurre un problema
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