const http = require('http');
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const PORT = 3000;
const args = process.argv.slice(2);
const inputDir = args[args.indexOf('--input') + 1] || './chapters';
const outputFile = args[args.indexOf('--output') + 1] || './preview.html';
const bundlerPath = path.join(__dirname, 'bundle.cjs');

function rebuild() {
    console.log('Rebuilding book...');
    try {
        execSync(`node "${bundlerPath}" --input "${inputDir}" --output "${outputFile}"`, { stdio: 'inherit' });
        console.log('Rebuild successful.');
    } catch (e) {
        console.error('Rebuild failed:', e.message);
    }
}

const server = http.createServer((req, res) => {
    if (req.url === '/') {
        if (!fs.existsSync(outputFile)) rebuild();
        if (fs.existsSync(outputFile)) {
            res.writeHead(200, { 'Content-Type': 'text/html' });
            res.end(fs.readFileSync(outputFile));
        } else {
            res.writeHead(500);
            res.end('Failed to build output file.');
        }
    } else {
        res.writeHead(404);
        res.end('Not found');
    }
});

console.log(`Starting dev server on http://localhost:${PORT}`);
console.log(`Watching ${inputDir} for changes...`);

if (fs.existsSync(inputDir)) {
    fs.watch(inputDir, { recursive: true }, (eventType, filename) => {
        if (filename && filename.endsWith('.html')) {
            console.log(`Change detected in ${filename}.`);
            rebuild();
        }
    });
} else {
    console.error(`Input directory not found: ${inputDir}. Please create it or pass --input <dir>`);
}

rebuild();
server.listen(PORT);
