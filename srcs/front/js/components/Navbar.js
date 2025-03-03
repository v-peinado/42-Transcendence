import { loadHTML } from '../utils/htmlLoader.js';

export async function getNavbarHTML(isAuthenticated = false, userInfo = null, isProfile = false) {
    // Determinar qué navbar cargar
    const templatePath = isProfile ? '/views/components/NavbarProfile.html' :
                        window.location.pathname === '/chat' ? '/views/components/NavbarChat.html' :
                        isAuthenticated ? '/views/components/NavbarAuthenticated.html' :
                        '/views/components/NavbarUnauthorized.html';
    
    const navbarHtml = await loadHTML(templatePath);
    
    if (!isAuthenticated) {
        return navbarHtml;
    }

    const parser = new DOMParser();
    const doc = parser.parseFromString(navbarHtml, 'text/html');
    const navbar = doc.body.firstElementChild;

    // Obtener la ruta actual y limpiarla
    const currentPath = window.location.pathname.replace(/\/$/, '');
    
    // Eliminar los elementos del nav que coincidan con la ruta actual
    const navLinks = navbar.querySelectorAll('.nav-link[href]');
    navLinks.forEach(link => {
        const href = link.getAttribute('href').replace(/\/$/, '');
        if (href === currentPath) {
            const navItem = link.closest('.nav-item');
            if (navItem) {
                navItem.remove();
            }
        }
    });

    // Actualizar userInfo después de modificar la estructura
    if (userInfo) {
        const profileImage = userInfo?.profile_image || 
            userInfo?.fortytwo_image || 
            `https://api.dicebear.com/7.x/avataaars/svg?seed=${encodeURIComponent(userInfo.username)}`;

        const imgElements = navbar.querySelectorAll('#nav-profile-image, #nav-profile-image-large');
        const usernameElements = navbar.querySelectorAll('#nav-username, #nav-username-large');
        
        imgElements.forEach(img => {
            img.src = profileImage;
            img.onerror = () => {
                img.src = `https://api.dicebear.com/7.x/avataaars/svg?seed=${encodeURIComponent(userInfo.username)}`;
            };
        });
        
        usernameElements.forEach(el => {
            if (el) el.textContent = userInfo.username;
        });
    }

    return navbar.outerHTML;
}
