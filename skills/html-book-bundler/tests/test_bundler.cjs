'use strict';
const fs   = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const testDir    = path.join(__dirname, 'test_chapters');
const outputFile = path.join(__dirname, 'test_output.html');
const bundler    = path.join(__dirname, '../scripts/bundle.cjs');

let passed = 0;
let failed = 0;

function assert(condition, label) {
  if (condition) {
    console.log(`  PASS: ${label}`);
    passed++;
  } else {
    console.error(`  FAIL: ${label}`);
    failed++;
  }
}

// ── Setup: create test chapters ─────────────────────────────────────────────
if (fs.existsSync(testDir)) fs.rmSync(testDir, { recursive: true });
fs.mkdirSync(testDir, { recursive: true });

// 12 chapters to test numeric sort (verifies chapter10 sorts after chapter9)
for (let i = 1; i <= 12; i++) {
  fs.writeFileSync(
    path.join(testDir, `chapter${i}.html`),
    `<!DOCTYPE html><html><head><meta charset="utf-8"><title>Test Chapter ${i}</title></head>` +
    `<body><h1>Chapter ${i}</h1><p>Content of chapter number ${i} with some text.</p></body></html>`
  );
}

// ── Test 1: Basic build ──────────────────────────────────────────────────────
console.log('\n[Test 1] Basic build with --title and --lang en');
try {
  execSync(
    `node "${bundler}" --input "${testDir}" --output "${outputFile}" --title "Test Book" --lang en`,
    { stdio: 'inherit' }
  );
  assert(fs.existsSync(outputFile), 'Output file created');
} catch (e) {
  console.error('Bundler execution failed:', e.message);
  failed++;
}

const out = fs.existsSync(outputFile) ? fs.readFileSync(outputFile, 'utf8') : '';

// ── Test 2: Template placeholders resolved ───────────────────────────────────
console.log('\n[Test 2] Template placeholder resolution');
assert(!out.includes('{{'), 'No unreplaced {{...}} placeholders');
assert(out.includes('Test Book'), 'Book title appears in output');

// ── Test 3: srcdoc architecture ──────────────────────────────────────────────
console.log('\n[Test 3] srcdoc chapter architecture');
assert(/\bCHAPTERS\s*=\s*\[/.test(out), 'CHAPTERS array present');
assert(!out.includes('URL.createObjectURL'), 'No Blob URL usage (srcdoc replaces it)');
assert(out.includes('srcdoc'), 'srcdoc assignment present in shell JS');

// ── Test 4: Security ─────────────────────────────────────────────────────────
console.log('\n[Test 4] Security features');
assert(out.includes('Content-Security-Policy'), 'CSP meta tag present');
assert(out.includes('sandbox='), 'iframe sandbox attribute present');

// ── Test 5: i18n (English) ───────────────────────────────────────────────────
console.log('\n[Test 5] i18n (English lang)');
assert(out.includes('Chapter'), 'English "Chapter" label present');
assert(!out.includes('Загрузка'), 'Russian "Loading" string absent (English mode)');

// ── Test 6: Chapter titles in output ─────────────────────────────────────────
console.log('\n[Test 6] Chapter titles');
assert(out.includes('Test Chapter 1'),  'Chapter 1 title present');
assert(out.includes('Test Chapter 12'), 'Chapter 12 title present (12 chapters test)');

// ── Test 7: Numeric sort (chapter10 must come after chapter9) ────────────────
console.log('\n[Test 7] Numeric chapter sort');
const idx9  = out.indexOf('Test Chapter 9');
const idx10 = out.indexOf('Test Chapter 10');
assert(idx9 !== -1 && idx10 !== -1 && idx10 > idx9, 'Chapter 10 sorted after Chapter 9 (numeric sort)');

// ── Test 8: Search index ─────────────────────────────────────────────────────
console.log('\n[Test 8] Search index');
assert(/\bSIDX\s*=\s*\{/.test(out), 'SIDX search index present');

// ── Test 9: --help flag ──────────────────────────────────────────────────────
console.log('\n[Test 9] --help flag');
try {
  const help = execSync(`node "${bundler}" --help`, { encoding: 'utf8' });
  assert(help.includes('--input') && help.includes('--output'), '--help shows usage');
} catch (e) {
  // Exit code 0 expected from --help
  assert(false, '--help exits cleanly');
}

// ── Test 10: Missing args exits with error ────────────────────────────────────
console.log('\n[Test 10] Missing required args');
try {
  execSync(`node "${bundler}" --input "${testDir}"`, { stdio: 'pipe' });
  assert(false, 'Should have exited with error when --output missing');
} catch (e) {
  assert(e.status !== 0, 'Exits with non-zero code when --output missing');
}

// ── Test 11: prefers-reduced-motion ──────────────────────────────────────────
console.log('\n[Test 11] Accessibility');
assert(out.includes('prefers-reduced-motion'), 'prefers-reduced-motion media query present');

// ── Summary ──────────────────────────────────────────────────────────────────
console.log(`\n${'─'.repeat(40)}`);
console.log(`Results: ${passed} passed, ${failed} failed`);

// Cleanup
fs.rmSync(testDir, { recursive: true });
if (fs.existsSync(outputFile)) fs.rmSync(outputFile);

if (failed > 0) {
  console.error('Some tests FAILED.');
  process.exit(1);
}
console.log('All tests PASSED.');
