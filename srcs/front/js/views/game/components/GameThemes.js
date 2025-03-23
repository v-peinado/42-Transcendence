export const GameThemes = {
    classic: {
        name: 'Clásico',
        ball: {
            color: '#FFFFFF',
            size: 10,
            trail: false
        },
        paddles: {
            color: '#FFFFFF',
            width: 10,
            height: 100,
            effects: false
        },
        field: {
            background: 'rgba(16, 19, 34, 0.95)',
            lineColor: 'rgba(255, 255, 255, 0.1)',
            lineDash: [10, 10]
        }
    },

    neon: {
        name: 'Neón',
        ball: {
            color: '#00ff00',
            size: 10,
            trail: true,
            glow: '0 0 10px #00ff00'
        },
        paddles: {
            color: '#ff00ff',
            width: 10,
            height: 100,
            effects: true,
            glow: '0 0 15px #ff00ff'
        },
        field: {
            background: 'rgba(0, 0, 0, 0.95)',
            lineColor: 'rgba(0, 255, 255, 0.2)',
            lineDash: [10, 10],
            glow: true
        }
    },

    retro: {
        name: 'Retro',
        ball: {
            color: '#ffcc00',
            size: 12,
            trail: false,
            pixelated: true
        },
        paddles: {
            color: '#ff6b6b',
            width: 12,
            height: 100,
            effects: false,
            pixelated: true
        },
        field: {
            background: '#111111',
            lineColor: '#333333',
            lineDash: [8, 8],
            gridEffect: true
        }
    },

    cyberpunk: {
        name: 'Cyberpunk',
        ball: {
            color: '#ff00ff',
            size: 10,
            trail: true,
            glow: '0 0 15px #ff00ff'
        },
        paddles: {
            color: '#00ffff',
            width: 10,
            height: 100,
            effects: true,
            glow: '0 0 20px #00ffff'
        },
        field: {
            background: '#000000',
            lineColor: '#ff00ff',
            lineDash: [5, 15],
            glow: true
        }
    },

    matrix: {
        name: 'Matrix',
        ball: {
            color: '#00ff00',
            size: 8,
            trail: true,
            glow: '0 0 10px #00ff00'
        },
        paddles: {
            color: '#003300',
            width: 8,
            height: 100,
            effects: true,
            glow: '0 0 15pxrgb(66, 180, 66)'
        },
        field: {
            background: '#000000',
            lineColor: '#003300',
            lineDash: [1, 10],
            digitalRain: true
        }
    },

    outrun: {
        name: 'Outrun',
        ball: {
            color: '#ffd319',  // Amarillo brillante
            size: 10,
            trail: true,
            glow: '0 0 15px #ffd319'
        },
        paddles: {
            color: '#411e5c',
            width: 10,
            height: 100,
            effects: true,
            glow: '0 0 20pxrgb(128, 39, 70)'
        },
        field: {
            background: 'linear-gradient(180deg, #411e5c 0%, #ff2975 100%)',  // Degradado sunset característico
            lineColor: '#ffd319',  // Línea central amarilla
            lineDash: [15, 5],
            glow: true,
            sunsetGrid: true  // Nuevo efecto específico
        }
    },

    cosmic: {
        name: 'Galactic',  // Cambio de nombre para reflejar mejor el tema
        ball: {
            color: '#7b2ff7',  // Morado espacial
            size: 10,
            trail: true,
            glow: '0 0 15px #7b2ff7',
            pulsar: true  // Nuevo efecto de pulso
        },
        paddles: {
            color: '#00eaff',  // Azul espacial brillante
            width: 10,
            height: 100,
            effects: true,
            glow: '0 0 20px #00eaff'
        },
        field: {
            background: '#0a001a',  // Azul muy oscuro casi negro
            lineColor: 'rgba(123, 47, 247, 0.5)',  // Línea central morada transparente
            lineDash: [0],  // Línea sólida
            glow: true,
            nebulaEffect: true  // Nuevo efecto de nebulosa
        }
    },

    synthwave: {
        name: 'Synthwave',
        ball: {
            color: '#ff2d95',
            size: 10,
            trail: true,
            glow: '0 0 15px #ff2d95'
        },
        paddles: {
            color: '#2de2e6',
            width: 10,
            height: 100,
            effects: true,
            glow: '0 0 20px #2de2e6'
        },
        field: {
            background: '#240b36',
            lineColor: '#ff2d95',
            lineDash: [10, 10],
            glow: true,
            gridEffect: true
        }
    }
};

export const defaultTheme = GameThemes.classic;

export const validateTheme = (theme) => {
    return {
        ball: {
            color: theme.ball?.color || defaultTheme.ball.color,
            size: Math.min(Math.max(theme.ball?.size || defaultTheme.ball.size, 8), 15),
            trail: theme.ball?.trail || false
        },
        paddles: {
            color: theme.paddles?.color || defaultTheme.paddles.color,
            width: Math.min(Math.max(theme.paddles?.width || defaultTheme.paddles.width, 8), 12),
            height: Math.min(Math.max(theme.paddles?.height || defaultTheme.paddles.height, 60), 120),
            effects: theme.paddles?.effects || false
        },
        field: {
            background: theme.field?.background || defaultTheme.field.background,
            lineColor: theme.field?.lineColor || defaultTheme.field.lineColor,
            lineDash: theme.field?.lineDash || defaultTheme.field.lineDash
        }
    };
};

export function getThemeIcon(theme) {
    const icons = {
        classic: 'fa-circle',
        neon: 'fa-bolt',
        retro: 'fa-gamepad',
        cyberpunk: 'fa-microchip',
        matrix: 'fa-terminal',
        outrun: 'fa-car',
        cosmic: 'fa-stars',
        synthwave: 'fa-wave-square'
    };
    return icons[theme] || 'fa-circle';
}
