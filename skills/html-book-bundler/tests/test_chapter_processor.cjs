'use strict';
const cp = require('../scripts/chapter_processor.cjs');

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

console.log('\n[Test] chapter_processor.cjs Cheerio processing');

const html1 = '<p>This is a paragraph</p><ul><li>One</li><li>Two</li><li>Three</li></ul>';
const res1 = cp.prepareChapter(html1, 0, 'Title', ['c1.html'], '', 'Book', false, 'en', 'Chapter', 'ltr');

assert(res1.includes('class="grid"'), 'autoEnrichLists converts simple lists to grid');
assert(res1.includes('This is a paragraph'), 'Preserves content');

const html2 = '<p>' + 'A'.repeat(500) + '</p>';
const res2 = cp.prepareChapter(html2, 1, 'Title', [], '', 'Book', false, 'en', 'Chapter', 'ltr');
assert(res2.includes('<details class="long-para">'), 'autoCollapseLongParas wraps long texts');

console.log(`\nResults: ${passed} passed, ${failed} failed`);
if (failed > 0) process.exit(1);
