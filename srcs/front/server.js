const http = require('http');
const fs = require('fs');
const path = require('path');

const server = http.createServer((req, res) => {
    // Manejar favicon.ico silenciosamente
    if (req.url === '/favicon.ico') {
        const faviconPath = './favicon.ico';
        fs.readFile(faviconPath, (error, content) => {
            if (error) {
                res.writeHead(204);
                res.end();
            } else {
                res.writeHead(200, { 'Content-Type': 'image/x-icon' });
                res.end(content);
            }
        });
        return;
    }

    // Solo log de rutas principales
    if (!req.url.includes('.js') && !req.url.includes('.css')) {
        console.log(`Request URL: ${req.url}`);
    }

    // Lista de rutas que deberían servir index.html
    const spaRoutes = ['/', '/game', '/profile', '/404'];
    
    let filePath = '.' + req.url;
    
    // Si es una ruta SPA o no tiene extensión, servir index.html
    if (spaRoutes.includes(req.url) || !path.extname(req.url)) {
        filePath = './index.html';
        res.writeHead(200, { 'Content-Type': 'text/html' });
        fs.createReadStream(filePath).pipe(res);
        return;
    }

    const extname = String(path.extname(filePath)).toLowerCase();
    const mimeTypes = {
        '.html': 'text/html',
        '.js': 'application/javascript; charset=utf-8',  // Modificado
        '.css': 'text/css',
        '.mjs': 'application/javascript; charset=utf-8'  // Modificado
    };

    // Configurar CORS y headers
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

    // Si es un archivo JavaScript
    if (extname === '.js' || extname === '.mjs') {
        res.setHeader('Content-Type', 'application/javascript; charset=utf-8');  // Modificado
    }

    fs.readFile(filePath, (error, content) => {
        if (error) {
            if (error.code === 'ENOENT') {
                // Si no es favicon.ico, loguear el error
                if (!req.url.includes('favicon.ico')) {
                    console.error('File not found:', filePath);
                }
                fs.readFile('./index.html', (error, content) => {
                    if (error) {
                        res.writeHead(500);
                        res.end('Error loading index.html');
                    } else {
                        res.writeHead(200, { 'Content-Type': 'text/html' });
                        res.end(content);
                    }
                });
            } else {
                res.writeHead(500);
                res.end(`Server Error: ${error.code}`);
            }
        } else {
            const contentType = mimeTypes[extname] || 'application/octet-stream';
            res.writeHead(200, { 'Content-Type': contentType });
            res.end(content);
        }
    });
});

server.listen(3000, '0.0.0.0', () => {
    console.log('Server running at http://0.0.0.0:3000/');
});
