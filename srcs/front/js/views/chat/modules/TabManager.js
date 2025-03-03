export class TabManager {
    constructor(tabsContainer, onTabChange) {
        this.tabsContainer = tabsContainer;
        this.onTabChange = onTabChange;
        this.initializeEventListeners();
    }

    initializeEventListeners() {
        this.tabsContainer.addEventListener('click', (e) => {
            if (e.target.matches('[data-tab]')) {
                this.switchTab(e.target.getAttribute('data-tab'));
            }
        });
    }

    switchTab(targetTab) {
        // Actualizar botones
        this.tabsContainer.querySelectorAll('.btn').forEach(btn => {
            btn.classList.toggle('active', btn.getAttribute('data-tab') === targetTab);
        });

        // Actualizar contenedores
        const containers = document.querySelectorAll('.tab-content');
        containers.forEach(container => {
            const isActive = container.id === `${targetTab}-container`;
            container.classList.toggle('active', isActive);
            if (isActive) {
                container.style.opacity = '0';
                setTimeout(() => {
                    container.style.opacity = '1';
                }, 50);
            }
        });

        // Llamar al callback si existe
        if (this.onTabChange) {
            this.onTabChange(targetTab);
        }
    }
}