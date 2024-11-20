document.addEventListener("DOMContentLoaded", async () => {
    let userData = JSON.parse(localStorage.getItem('user'));

    if (!userData) {
        try {
            // Hacer la solicitud GET a la API para obtener los datos del usuario
            const response = await fetch('/api/authentication/42/api/42/callback/', {
                method: 'GET',
                headers: { 'Content-Type': 'application/json' }
            });

            if (!response.ok) {
                throw new Error('Error al obtener los datos de usuario.');
            }

            const data = await response.json();

            if (data.message === "Login successfull") {
                // Guardar los datos del usuario en localStorage
                userData = data.user;
                localStorage.setItem('user', JSON.stringify(userData));
            } else {
                // Redirigir al login si no hay datos válidos
                window.location.href = "/login.html";
                return;
            }
        } catch (error) {
            console.error('Error:', error);
            window.location.href = "/login.html";
            return;
        }
    }

    // Mostrar el nombre de usuario
    document.getElementById('usernameDisplay').textContent = userData.username;

    // Opcional: Si deseas mostrar el email o imagen de perfil, añade esos elementos en el HTML
    // y actualízalos aquí
    // document.getElementById('emailDisplay').textContent = userData.email;
    // const profileImage = document.getElementById('profileImage');
    // profileImage.src = userData.profile_image;
    // profileImage.style.display = 'block';
});
