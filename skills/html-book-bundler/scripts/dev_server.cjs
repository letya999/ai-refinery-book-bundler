const http = require('http');
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const args = process.argv.slice(2);
const inputDir = args[args.indexOf('--input') + 1] || './chapters';
const outputFile = args[args.indexOf('--output') + 1] || './preview.html';
const bundlerPath = path.join(__dirname, 'bundle.cjs');

let port = args.includes('--port') ? parseInt(args[args.indexOf('--port') + 1]) : 3000;
let clients = [];

function rebuild() {
    console.log('Rebuilding book...');
    try {
        execSync(`node "${bundlerPath}" --input "${inputDir}" --output "${outputFile}"`, { stdio: 'inherit' });
        console.log('Rebuild successful. Notifying clients...');
        clients.forEach(res => res.write('data: reload\n\n'));
    } catch (e) {
        console.error('Rebuild failed:', e.message);
    }
}

const server = http.createServer((req, res) => {
    if (req.url === '/') {
        if (!fs.existsSync(outputFile)) rebuild();
        if (fs.existsSync(outputFile)) {
            let content = fs.readFileSync(outputFile, 'utf8');
            const devInjected = '<script>window.BOOK_DEV_MODE = true;</script>';
            content = content.replace('</head>', devInjected + '</head>');
            res.writeHead(200, { 'Content-Type': 'text/html' });
            res.end(content);
        } else {
            res.writeHead(500);
            res.end('Failed to build output file.');
        }
    } else if (req.url === '/events') {
        res.writeHead(200, {
            'Content-Type': 'text/event-stream',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive'
        });
        clients.push(res);
        req.on('close', () => {
            clients = clients.filter(c => c !== res);
        });
    } else {
        res.writeHead(404);
        res.end('Not found');
    }
});

function startServer(p) {
    server.listen(p)
        .on('error', (err) => {
            if (err.code === 'EADDRINUSE') {
                if (args.includes('--port')) {
                    console.error(`Error: Port ${p} is already in use.`);
                    process.exit(1);
                } else {
                    console.log(`Port ${p} is busy, trying ${p + 1}...`);
                    startServer(p + 1);
                }
            } else {
                console.error(err);
            }
        })
        .on('listening', () => {
            console.log(`\n🚀 Dev Server started on http://localhost:${p}`);
            console.log(`💡 Tip: Use --port <number> to change port.`);
            console.log(`Watching ${inputDir} for changes...`);
            
            if (fs.existsSync(inputDir)) {
                let timeout;
                const WATCH_EXT = ['.html', '.css', '.js', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp'];
                fs.watch(inputDir, { recursive: true }, (eventType, filename) => {
                    if (filename) {
                        const ext = path.extname(filename).toLowerCase();
                        if (WATCH_EXT.includes(ext)) {
                            clearTimeout(timeout);
                            timeout = setTimeout(() => {
                                console.log(`Change detected in ${filename}.`);
                                rebuild();
                            }, 150);
                        }
                    }
                });
            } else {
                console.error(`Input directory not found: ${inputDir}.`);
            }
            rebuild();
        });
}

startServer(port);
