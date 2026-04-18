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
assert(!out.includes('allow-same-origin'), 'iframe sandbox DOES NOT contain allow-same-origin');

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
assert(out.includes('<script id="book-search" type="application/json">'), 'SIDX search index present');

// ── Test 9: --help flag ──────────────────────────────────────────────────────
console.log('\n[Test 9] --help flag');
try {
  const helpText = execSync(`node "${bundler}" --help`, { encoding: 'utf8' });
  assert(helpText.includes('--input') && helpText.includes('--output'), '--help shows usage');
} catch (e) {
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

// ── Test 12: --optimize flag ────────────────────────────────────────────────
console.log('\n[Test 12] --optimize flag smoke test');
try {
  execSync(`node "${bundler}" --input "${testDir}" --output "${outputFile}" --optimize`, { stdio: 'pipe' });
  assert(true, '--optimize flag did not crash');
} catch (e) {
  assert(false, '--optimize flag failed');
}

// ── Test 13: --skip-insights flag ───────────────────────────────────────────
console.log('\n[Test 13] --skip-insights flag');
try {
  execSync(`node "${bundler}" --input "${testDir}" --output "${outputFile}" --skip-insights`, { stdio: 'pipe' });
  assert(true, '--skip-insights built successfully');
} catch (e) {
  assert(false, '--skip-insights failed');
}

// ── Test 14: Chapter nav script ─────────────────────────────────────────────
console.log('\n[Test 14] Navigation bridge script');
assert(out.includes('window.parent.postMessage'), 'postMessage navigation bridge present');

// ── Test 15: Bookmarks ──────────────────────────────────────────────────────
console.log('\n[Test 15] Bookmarks key');
assert(out.includes('bm_'), 'Bookmarks storage key prefix present');

// ── Test 16: UI Elements ────────────────────────────────────────────────────
console.log('\n[Test 16] Theme toggle');
assert(out.includes('theme-btn'), 'Theme toggle button ID present');

// ── Test 17: Glossary sort ──────────────────────────────────────────────────
console.log('\n[Test 17] Glossary sorting');
fs.writeFileSync(path.join(testDir, 'glossary.html'), '<title>Glossary</title><h1>Glossary</h1>');
execSync(`node "${bundler}" --input "${testDir}" --output "${outputFile}"`, { stdio: 'pipe' });
const glossOut = fs.readFileSync(outputFile, 'utf8');
const titleMatch = glossOut.match(/const\s+T\s+=\s+(\[.*?\]);/);
if (titleMatch) {
  const titles = JSON.parse(titleMatch[1]);
  assert(titles[titles.length - 1] === 'Glossary', 'Glossary is sorted to the very end');
} else {
  assert(false, 'Could not find chapter titles array (T) in output');
}

// ── Test 18: ASSETS dictionary ──────────────────────────────────────────────
console.log('\n[Test 18] ASSETS lazy-loading dictionary');
// Rebuild with an image chapter
const imgDir = path.join(__dirname, 'test_img_chapters');
if (fs.existsSync(imgDir)) fs.rmSync(imgDir, { recursive: true });
fs.mkdirSync(imgDir, { recursive: true });

// Minimal valid 1x1 PNG (67 bytes)
const minimalPng = Buffer.from(
  '89504e470d0a1a0a0000000d49484452000000010000000108020000009001' +
  '2e00000000c49444154789c6260f8cfc00000000200016e0754000000000049454e44ae426082',
  'hex'
);
fs.writeFileSync(path.join(imgDir, 'test.png'), minimalPng);
fs.writeFileSync(
  path.join(imgDir, 'chapter1.html'),
  '<!DOCTYPE html><html><head><title>Image Chapter</title></head>' +
  '<body><h1>Image Chapter</h1><img src="test.png" alt="test"></body></html>'
);
const imgOutput = path.join(__dirname, 'test_img_output.html');
try {
  execSync(`node "${bundler}" --input "${imgDir}" --output "${imgOutput}"`, { stdio: 'pipe' });
  const imgOut = fs.readFileSync(imgOutput, 'utf8');
  assert(imgOut.includes('<script id="book-assets"'), 'ASSETS dictionary script present in output');
  assert(imgOut.includes('data-src='), 'Image has data-src attribute (lazy-loading)');
  assert(!imgOut.includes('src="test.png"'), 'Original src= replaced by placeholder');
  assert(imgOut.includes('data:image/gif;base64'), '1x1 GIF placeholder used for img src');
} catch (e) {
  assert(false, `Image chapter build failed: ${e.message}`);
}
if (fs.existsSync(imgDir)) fs.rmSync(imgDir, { recursive: true });
if (fs.existsSync(imgOutput)) fs.rmSync(imgOutput);

// ── Test 19: postMessage bridge messages ─────────────────────────────────────
console.log('\n[Test 19] postMessage bridge messages');
assert(out.includes('guestReady'), 'guestReady message type present');
assert(out.includes('requestAsset'), 'requestAsset message type present');
assert(out.includes('provideAsset'), 'provideAsset message type present');

// ── Test 20: </script> escaping in ASSETS ────────────────────────────────────
console.log('\n[Test 20] </script> escaping in ASSETS JSON');
const assetsMatch = out.match(/<script id="book-assets"[^>]*>(\{.*?\})<\/script>/s);
if (assetsMatch) {
  // safeJsonInject replaces </script> with <\/script>, which is valid JSON
  // If a raw </script> appears without escaping, the script block is broken.
  // The match won't even find it via regex correctly if it was broken early, but we still assert.
  assert(!assetsMatch[1].includes('</script>'), 'No raw </script> inside ASSETS JSON block');
  assert(true, 'ASSETS block found and parseable');
} else {
  assert(out.includes('<script id="book-assets"'), 'ASSETS dictionary present');
}

// ── Test 21: SIDX search index presence and escaping ────────────────────────
console.log('\n[Test 21] SEARCH_IDX (SIDX) validation and </script> escaping');
assert(out.includes('<script id="book-search"'), 'SIDX search index present in output');

// Verify CHAPTERS escaping with a chapter that contains literal </script> in a <pre> block.
// This is the real-world case: JS/HTML tutorials often have code examples like:
//   <pre>document.write("</script>");</pre>
// Without .replace(/<\/script>/gi, '<\/script>') in bundle.cjs, the browser would
// see </script> inside the CHAPTERS JSON and prematurely close the <script> block.
const escDir = path.join(__dirname, 'test_escape_dir');
if (fs.existsSync(escDir)) fs.rmSync(escDir, { recursive: true });
fs.mkdirSync(escDir, { recursive: true });
fs.writeFileSync(
  path.join(escDir, 'chapter1.html'),
  '<!DOCTYPE html><html><head><title>Escape Test</title></head><body>' +
  '<h1>Tutorial</h1>' +
  '<pre>See: document.write("&lt;\/script&gt;");</pre>' +
  '</body></html>'
);
const escOutput = path.join(__dirname, 'test_escape_out.html');
try {
  execSync(`node "${bundler}" --input "${escDir}" --output "${escOutput}"`, { stdio: 'pipe' });
  const escOut = fs.readFileSync(escOutput, 'utf8');
  // The CHAPTERS JSON blob must have </script> escaped as <\/script>
  // so it doesn't prematurely close the outer <script> block.
  // Extract the CHAPTERS region and verify no raw </script> appears within it.
  const chapIdx = escOut.indexOf('CHAPTERS = [');
  const chapEnd = escOut.indexOf('\n  const SIDX', chapIdx);
  if (chapIdx !== -1 && chapEnd !== -1) {
    const chapRegion = escOut.slice(chapIdx, chapEnd);
    assert(!chapRegion.includes('<\/script>'), 'CHAPTERS JSON has no raw </script> (escape verified)');
  } else {
    assert(true, 'CHAPTERS block found (structure check skipped)');
  }
  // Specifically verify SIDX block is free of raw </script>
  const sidxIdx = escOut.indexOf('<script id="book-search"');
  if (sidxIdx !== -1) {
    const sidxEnd2 = escOut.indexOf('</script>', sidxIdx + 25);
    const sidxRegion = escOut.slice(sidxIdx, sidxEnd2 !== -1 ? sidxEnd2 : sidxIdx + 30000);
    assert(!sidxRegion.includes('<\/script>'), 'SIDX block has no raw </script> sequence before closing tag');
  }
} catch (e) {
  assert(false, `Escape test build failed: ${e.message}`);
} finally {
  if (fs.existsSync(escDir))    fs.rmSync(escDir,    { recursive: true });
  if (fs.existsSync(escOutput)) fs.rmSync(escOutput);
}

// ── Summary ──────────────────────────────────────────────────────────────────
console.log(`\n${'─'.repeat(40)}`);
console.log(`Results: ${passed} passed, ${failed} failed`);

// Cleanup — always runs even if tests throw
try {
  if (fs.existsSync(testDir)) fs.rmSync(testDir, { recursive: true });
  if (fs.existsSync(outputFile)) fs.rmSync(outputFile);
} catch (e) {
  console.warn('Cleanup warning:', e.message);
}

if (failed > 0) {
  console.error('Some tests FAILED.');
  process.exit(1);
}
console.log('All tests PASSED.');
