import { loadHTML } from '/js/utils/htmlLoader.js';

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

    if (userInfo) {
        const profileImage = userInfo?.profile_image || 
            userInfo?.fortytwo_image || 
            `https://api.dicebear.com/7.x/avataaars/svg?seed=${encodeURIComponent(userInfo.username)}`;

        // Actualizar imágenes y username
        const imgElement = navbar.querySelector('#nav-profile-image');
        const usernameElement = navbar.querySelector('#nav-username');
        
        if (imgElement) {
            imgElement.src = profileImage;
            imgElement.onerror = () => {
                imgElement.src = `https://api.dicebear.com/7.x/avataaars/svg?seed=${encodeURIComponent(userInfo.username)}`;
            };
        }
        
        if (usernameElement) {
            usernameElement.textContent = userInfo.username;
        }
    }

    return navbar.outerHTML;
}
