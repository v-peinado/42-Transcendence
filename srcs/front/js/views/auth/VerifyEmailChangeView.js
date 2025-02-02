import AuthService from '../../services/AuthService.js';
import { loadHTML } from '../../utils/htmlLoader.js';

export async function VerifyEmailChangeView(uid, token) {
    const app = document.getElementById('app');
    app.textContent = ''; // Limpiar de forma segura

    // Crear la estructura base
    async function createVerifyingView() {
        const parser = new DOMParser();
        const html = await loadHTML('/views/auth/email/VerifyingEmailChange.html');
        return parser.parseFromString(html, 'text/html').body.firstElementChild;
    }

    function createResultView(success, message) {
        const container = document.createElement('div');
        container.className = 'hero-section';

        const content = document.createElement('div');
        content.className = 'container';
        
        const row = document.createElement('div');
        row.className = 'row justify-content-center';
        
        const col = document.createElement('div');
        col.className = 'col-md-6 text-center';

        // Crear SVG resultado
        const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        svg.setAttribute('class', 'logo mb-4');
        svg.setAttribute('width', '64');
        svg.setAttribute('height', '64');
        svg.setAttribute('viewBox', '0 0 100 100');

        if (success) {
            // SVG de éxito
            createSuccessSVG(svg);
        } else {
            // SVG de error
            createErrorSVG(svg);
        }

        // Crear contenido
        const title = document.createElement('h3');
        title.className = 'text-light mb-4';
        title.textContent = success ? '¡Email Actualizado!' : 'Error al verificar email';

        const alert = document.createElement('div');
        alert.className = `alert alert-${success ? 'success' : 'danger'}`;
        alert.textContent = message;

        const button = document.createElement('a');
        button.href = '/profile';
        button.setAttribute('data-link', '');
        button.className = 'btn btn-primary';
        button.textContent = 'Ir a mi perfil';

        // Ensamblar
        col.appendChild(svg);
        col.appendChild(title);
        col.appendChild(alert);
        col.appendChild(button);
        row.appendChild(col);
        content.appendChild(row);
        container.appendChild(content);

        return container;
    }

    // Mostrar vista de carga
    app.appendChild(await createVerifyingView());

    // Manejar la verificación
    try {
        const result = await AuthService.verifyEmailChange(uid, token);
        app.textContent = ''; // Limpiar
        app.appendChild(createResultView(true, result.message));
    } catch (error) {
        app.textContent = ''; // Limpiar
        app.appendChild(createResultView(false, error.message));
    }
}

// Funciones auxiliares para crear SVGs
function createSuccessSVG(svg) {
    const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
    circle.setAttribute('cx', '50');
    circle.setAttribute('cy', '50');
    circle.setAttribute('r', '40');
    circle.setAttribute('stroke', '#198754');
    circle.setAttribute('stroke-width', '8');
    circle.setAttribute('fill', 'none');

    const check = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    check.setAttribute('d', 'M30 50 L45 65 L70 35');
    check.setAttribute('stroke', '#198754');
    check.setAttribute('stroke-width', '8');
    check.setAttribute('fill', 'none');

    svg.appendChild(circle);
    svg.appendChild(check);
}

function createErrorSVG(svg) {
    const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
    circle.setAttribute('cx', '50');
    circle.setAttribute('cy', '50');
    circle.setAttribute('r', '40');
    circle.setAttribute('stroke', '#dc3545');
    circle.setAttribute('stroke-width', '8');
    circle.setAttribute('fill', 'none');

    const cross = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    cross.setAttribute('d', 'M35 35 L65 65 M65 35 L35 65');
    cross.setAttribute('stroke', '#dc3545');
    cross.setAttribute('stroke-width', '8');
    cross.setAttribute('fill', 'none');

    svg.appendChild(circle);
    svg.appendChild(cross);
}
