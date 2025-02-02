import AuthService from '../../services/AuthService.js';
import { getNavbarHTML } from '../../components/Navbar.js';
import { messages } from '../../translations.js';

export function VerifyEmailView(uidb64, token) {
    const app = document.getElementById('app');
    app.textContent = ''; // Limpiar de forma segura

    function createVerificationCard() {
        const container = document.createElement('div');
        container.className = 'hero-section';

        const content = document.createElement('div');
        content.className = 'container';
        
        // Crear estructura usando createElement
        const row = document.createElement('div');
        row.className = 'row justify-content-center';
        
        const col = document.createElement('div');
        col.className = 'col-md-6 col-lg-5';
        
        const card = document.createElement('div');
        card.className = 'card login-card';
        
        const cardBody = document.createElement('div');
        cardBody.className = 'card-body p-5 text-center';

        // Crear SVG de forma segura
        const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        svg.setAttribute('class', 'logo mb-4');
        svg.setAttribute('width', '64');
        svg.setAttribute('height', '64');
        svg.setAttribute('viewBox', '0 0 100 100');
        
        // Añadir elementos SVG de forma segura
        const rect1 = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
        rect1.setAttribute('x', '10');
        rect1.setAttribute('y', '40');
        rect1.setAttribute('width', '10');
        rect1.setAttribute('height', '20');
        rect1.setAttribute('fill', '#fff');
        
        // Crear animación
        const animate1 = document.createElementNS('http://www.w3.org/2000/svg', 'animate');
        animate1.setAttribute('attributeName', 'height');
        animate1.setAttribute('values', '20;40;20');
        animate1.setAttribute('dur', '1s');
        animate1.setAttribute('repeatCount', 'indefinite');
        
        rect1.appendChild(animate1);
        svg.appendChild(rect1);
        
        // Añadir texto
        const title = document.createElement('h3');
        title.className = 'text-light mb-4';
        title.textContent = 'Verificando tu email...';
        
        const subtitle = document.createElement('p');
        subtitle.className = 'text-muted';
        subtitle.textContent = 'Esto solo tomará un momento';

        // Ensamblar todo
        cardBody.appendChild(svg);
        cardBody.appendChild(title);
        cardBody.appendChild(subtitle);
        card.appendChild(cardBody);
        col.appendChild(card);
        row.appendChild(col);
        content.appendChild(row);
        container.appendChild(content);

        return container;
    }

    // Mostrar pantalla de carga inicial
    app.appendChild(createVerificationCard());

    // Manejar la verificación
    AuthService.verifyEmail(uidb64, token)
        .then(async () => {
            const parser = new DOMParser();
            const navbarElement = parser.parseFromString(
                await getNavbarHTML(false), 
                'text/html'
            ).body.firstElementChild;

            app.textContent = ''; // Limpiar de forma segura
            app.appendChild(navbarElement);

            const successCard = createSuccessCard();
            app.appendChild(successCard);

            // Limpiar estado
            localStorage.clear();
            sessionStorage.clear();
        })
        .catch(error => {
            app.textContent = ''; // Limpiar de forma segura
            app.appendChild(createErrorCard(error.message));
        });
}

// Funciones auxiliares para crear las tarjetas de éxito y error
function createSuccessCard() {
    const container = document.createElement('div');
    container.className = 'hero-section';

    const content = document.createElement('div');
    content.className = 'container';
    
    const row = document.createElement('div');
    row.className = 'row justify-content-center';
    
    const col = document.createElement('div');
    col.className = 'col-md-6 col-lg-5';
    
    const card = document.createElement('div');
    card.className = 'verification-message';
    
    const cardBody = document.createElement('div');
    cardBody.className = 'card-body p-5 text-center';

    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('class', 'logo mb-4');
    svg.setAttribute('width', '64');
    svg.setAttribute('height', '64');
    svg.setAttribute('viewBox', '0 0 100 100');
    
    const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
    rect.setAttribute('width', '100');
    rect.setAttribute('height', '100');
    rect.setAttribute('fill', 'none');
    
    const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
    circle.setAttribute('cx', '50');
    circle.setAttribute('cy', '50');
    circle.setAttribute('r', '40');
    circle.setAttribute('fill', 'none');
    circle.setAttribute('stroke', '#0d6efd');
    circle.setAttribute('stroke-width', '8');
    
    const animateCircle = document.createElementNS('http://www.w3.org/2000/svg', 'animate');
    animateCircle.setAttribute('attributeName', 'stroke-dasharray');
    animateCircle.setAttribute('from', '0,251.2');
    animateCircle.setAttribute('to', '251.2,0');
    animateCircle.setAttribute('dur', '1s');
    animateCircle.setAttribute('fill', 'freeze');
    
    circle.appendChild(animateCircle);
    svg.appendChild(rect);
    svg.appendChild(circle);
    
    const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    path.setAttribute('d', 'M30 50 L45 65 L70 35');
    path.setAttribute('stroke', '#0d6efd');
    path.setAttribute('stroke-width', '8');
    path.setAttribute('fill', 'none');
    path.setAttribute('stroke-dasharray', '0,90');
    path.setAttribute('stroke-dashoffset', '0');
    
    const animatePath = document.createElementNS('http://www.w3.org/2000/svg', 'animate');
    animatePath.setAttribute('attributeName', 'stroke-dasharray');
    animatePath.setAttribute('from', '0,90');
    animatePath.setAttribute('to', '90,0');
    animatePath.setAttribute('dur', '0.5s');
    animatePath.setAttribute('fill', 'freeze');
    animatePath.setAttribute('begin', '0.6s');
    
    path.appendChild(animatePath);
    svg.appendChild(path);
    
    const title = document.createElement('h3');
    title.className = 'text-light mb-3';
    title.textContent = messages.AUTH.EMAIL_VERIFICATION.SUCCESS_TITLE;
    
    const message = document.createElement('p');
    message.className = 'text-white fs-6 mb-4';
    message.textContent = messages.AUTH.EMAIL_VERIFICATION.SUCCESS_MESSAGE;
    
    const buttonContainer = document.createElement('div');
    buttonContainer.className = 'd-grid';
    
    const button = document.createElement('a');
    button.setAttribute('href', '/login');
    button.className = 'btn btn-primary btn-lg';
    button.innerHTML = `<i class="fas fa-sign-in-alt me-2"></i>${messages.AUTH.EMAIL_VERIFICATION.SUCCESS_BUTTON}`;
    
    buttonContainer.appendChild(button);
    cardBody.appendChild(svg);
    cardBody.appendChild(title);
    cardBody.appendChild(message);
    cardBody.appendChild(buttonContainer);
    card.appendChild(cardBody);
    col.appendChild(card);
    row.appendChild(col);
    content.appendChild(row);
    container.appendChild(content);

    return container;
}

function createErrorCard(errorMessage) {
    const container = document.createElement('div');
    container.className = 'hero-section';

    const content = document.createElement('div');
    content.className = 'container';
    
    const row = document.createElement('div');
    row.className = 'row justify-content-center';
    
    const col = document.createElement('div');
    col.className = 'col-md-6 col-lg-5';
    
    const card = document.createElement('div');
    card.className = 'card login-card';
    
    const cardBody = document.createElement('div');
    cardBody.className = 'card-body p-5 text-center';

    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('class', 'logo mb-4');
    svg.setAttribute('width', '64');
    svg.setAttribute('height', '64');
    svg.setAttribute('viewBox', '0 0 100 100');
    
    const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
    rect.setAttribute('width', '100');
    rect.setAttribute('height', '100');
    rect.setAttribute('fill', 'none');
    
    const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
    circle.setAttribute('cx', '50');
    circle.setAttribute('cy', '50');
    circle.setAttribute('r', '40');
    circle.setAttribute('fill', 'none');
    circle.setAttribute('stroke', '#dc3545');
    circle.setAttribute('stroke-width', '8');
    
    const animateCircle = document.createElementNS('http://www.w3.org/2000/svg', 'animate');
    animateCircle.setAttribute('attributeName', 'stroke-dasharray');
    animateCircle.setAttribute('from', '0,251.2');
    animateCircle.setAttribute('to', '251.2,0');
    animateCircle.setAttribute('dur', '1s');
    animateCircle.setAttribute('fill', 'freeze');
    
    circle.appendChild(animateCircle);
    svg.appendChild(rect);
    svg.appendChild(circle);
    
    const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    path.setAttribute('d', 'M35 35 L65 65 M65 35 L35 65');
    path.setAttribute('stroke', '#dc3545');
    path.setAttribute('stroke-width', '8');
    path.setAttribute('fill', 'none');
    path.setAttribute('stroke-dasharray', '0,90');
    path.setAttribute('stroke-dashoffset', '0');
    
    const animatePath = document.createElementNS('http://www.w3.org/2000/svg', 'animate');
    animatePath.setAttribute('attributeName', 'stroke-dasharray');
    animatePath.setAttribute('from', '0,90');
    animatePath.setAttribute('to', '90,0');
    animatePath.setAttribute('dur', '0.5s');
    animatePath.setAttribute('fill', 'freeze');
    animatePath.setAttribute('begin', '0.6s');
    
    path.appendChild(animatePath);
    svg.appendChild(path);
    
    const title = document.createElement('h3');
    title.className = 'text-light mb-4';
    title.textContent = 'Error de Verificación';
    
    const alert = document.createElement('div');
    alert.className = 'alert alert-danger bg-danger bg-opacity-25 text-light border-danger mb-4';
    alert.textContent = errorMessage;
    
    const button = document.createElement('a');
    button.setAttribute('href', '/');
    button.setAttribute('data-link', '');
    button.className = 'btn btn-primary btn-lg';
    button.innerHTML = '<i class="fas fa-home me-2"></i>Volver al Inicio';
    
    cardBody.appendChild(svg);
    cardBody.appendChild(title);
    cardBody.appendChild(alert);
    cardBody.appendChild(button);
    card.appendChild(cardBody);
    col.appendChild(card);
    row.appendChild(col);
    content.appendChild(row);
    container.appendChild(content);

    return container;
}
