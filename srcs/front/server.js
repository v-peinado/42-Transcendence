const http = require('http');
const fs = require('fs');
const path = require('path');

const server = http.createServer((req, res) => {
    if (!req.url.startsWith('/api')) {
        let filePath = '.' + req.url;
        
        if (filePath === './' || !path.extname(filePath)) {
            filePath = './index.html';
        }

        fs.readFile(filePath, (err, content) => {
            if (err) {
                fs.readFile('./index.html', (err, content) => {
                    if (err) {
                        res.writeHead(500);
                        res.end('Error loading index.html');
                        return;
                    }
                    res.writeHead(200, { 'Content-Type': 'text/html' });
                    res.end(content);
                });
                return;
            }
            
            // Determinar el tipo de contenido basado en la extensión
            const ext = path.extname(filePath);
            const contentType = {
                '.html': 'text/html',
                '.js': 'text/javascript',
                '.css': 'text/css',
                '.json': 'application/json',
                '.svg': 'image/svg+xml'
            }[ext] || 'text/plain';

            res.writeHead(200, { 'Content-Type': contentType });
            res.end(content);
        });
    }
});

