import { loadHTML } from '/js/utils/htmlLoader.js';

export async function getNavbarHTML(isAuthenticated = false, userInfo = null) {
    const navbarHtml = await loadHTML(
        isAuthenticated ? '/views/components/NavbarAuthenticated.html' : '/views/components/NavbarUnauthorized.html'
    );
    
    if (isAuthenticated && userInfo) {
        const parser = new DOMParser();
        const doc = parser.parseFromString(navbarHtml, 'text/html');
        
        // Actualizar imagen y nombre de usuario
        const profileImage = userInfo?.profile_image || 
                           userInfo?.fortytwo_image || 
                           `https://api.dicebear.com/7.x/avataaars/svg?seed=${userInfo?.username}`;

        doc.querySelectorAll('#nav-profile-image, #nav-profile-image-large').forEach(img => {
            img.src = profileImage;
            img.onerror = () => img.src = `https://api.dicebear.com/7.x/avataaars/svg?seed=${userInfo?.username}`;
        });

        doc.querySelectorAll('#nav-username, #nav-username-large').forEach(el => {
            el.textContent = userInfo.username;
        });

        return doc.body.firstElementChild.outerHTML;
    }

    return navbarHtml;
}
