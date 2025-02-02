import { loadHTML } from '/js/utils/htmlLoader.js';

export async function getNavbarHTML(isAuthenticated = false, userInfo = null) {
    // Cargar el template HTML apropiado
    const templatePath = isAuthenticated ? 
        '/views/components/NavbarAuthenticated.html' : 
        '/views/components/NavbarUnauthorized.html';
    
    const navbarHtml = await loadHTML(templatePath);
    
    if (!isAuthenticated) {
        return navbarHtml;
    }

    const parser = new DOMParser();
    const doc = parser.parseFromString(navbarHtml, 'text/html');
    const navbar = doc.body.firstElementChild;

    if (userInfo) {
        const profileImage = userInfo?.profile_image || 
            userInfo?.fortytwo_image || 
            `https://api.dicebear.com/7.x/avataaars/svg?seed=${encodeURIComponent(userInfo.username)}`;

        // Actualizar imágenes de perfil
        ['nav-profile-image', 'nav-profile-image-large'].forEach(id => {
            const img = navbar.querySelector(`#${id}`);
            if (img) {
                img.setAttribute('src', profileImage);
                img.onerror = () => {
                    img.setAttribute('src', 
                        `https://api.dicebear.com/7.x/avataaars/svg?seed=${encodeURIComponent(userInfo.username)}`
                    );
                };
            }
        });

        // Actualizar nombres de usuario
        ['nav-username', 'nav-username-large'].forEach(id => {
            const el = navbar.querySelector(`#${id}`);
            if (el) {
                el.textContent = userInfo.username;
            }
        });
    }

    return navbar.outerHTML;
}
