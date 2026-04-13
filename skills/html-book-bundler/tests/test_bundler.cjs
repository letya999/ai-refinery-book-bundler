const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const testDir = path.join(__dirname, 'test_chapters');
const outputFile = path.join(__dirname, 'test_output.html');
const bundlerPath = path.join(__dirname, '../scripts/bundle.cjs');

// Setup
if (fs.existsSync(testDir)) fs.rmSync(testDir, { recursive: true });
fs.mkdirSync(testDir, { recursive: true });

fs.writeFileSync(path.join(testDir, 'chapter1.html'), `<!DOCTYPE html><html><head><meta charset="utf-8"><title>Test 1</title></head><body><h1>Hello</h1></body></html>`);
fs.writeFileSync(path.join(testDir, 'chapter2.html'), `<!DOCTYPE html><html><head><meta charset="utf-8"><title>Test 2</title></head><body><h1>World</h1></body></html>`);

console.log('Running bundler...');
try {
    execSync(`node "${bundlerPath}" --input "${testDir}" --output "${outputFile}"`, { stdio: 'inherit' });
} catch (e) {
    console.error('Bundler execution failed:', e.message);
    process.exit(1);
}

console.log('Validating output...');
const out = fs.readFileSync(outputFile, 'utf8');

if (!out.includes('Test 1') || !out.includes('Test 2')) {
    console.error('FAIL: Missing titles in output.');
    process.exit(1);
}

// All template placeholders must be replaced
const noUnreplacedPlaceholders = !out.includes('{{');
// Shell must contain the B64 array variable (LOCAL_B64_CHAPTERS was replaced to populate B64)
const hasB64Var = /\bB64\s*=\s*\[/.test(out);
// Titles should appear in the sidebar JSON
const hasTitles = out.includes('Test 1') && out.includes('Test 2');
// CSP must be present
const hasCSP = out.includes('Content-Security-Policy');
if (noUnreplacedPlaceholders && hasB64Var && hasTitles && hasCSP) {
    console.log('PASS: Basic structural checks passed.');
} else {
    console.error(`FAIL: noPlaceholders=${noUnreplacedPlaceholders} hasB64=${hasB64Var} hasTitles=${hasTitles} hasCSP=${hasCSP}`);
    process.exit(1);
}

console.log('All tests passed.');

// Cleanup
fs.rmSync(testDir, { recursive: true });
if (fs.existsSync(outputFile)) fs.rmSync(outputFile);
