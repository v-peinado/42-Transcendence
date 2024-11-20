// Verifica si la respuesta contiene el status success
if (document.body.textContent.includes('"status":"success"')) {
    // Redirige al usuario a user.html
    window.location.href = '/user.html';
}