const { test, expect } = require('node:test');
const assert = require('node:assert');

// The algorithm to test
const voidTags = new Set(['area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr']);
function updateOpenTags(stack, htmlCode) {
  const tagRegex = /<\/?([a-z0-9\-]+)[^>]*>/gi;
  let match;
  while ((match = tagRegex.exec(htmlCode)) !== null) {
    const tagFull = match[0];
    const tagName = match[1].toLowerCase();
    if (tagFull.startsWith('</')) {
      for (let i = stack.length - 1; i >= 0; i--) {
         if (stack[i].name === tagName) { stack.splice(i, 1); break; }
      }
    } else if (!voidTags.has(tagName) && !tagFull.endsWith('/>')) {
      stack.push({ name: tagName, full: tagFull });
    }
  }
}

function splitChapter(html, limit) {
  if (Buffer.byteLength(html, 'utf8') <= limit) return [html];
  const parts = [];
  const bodyMatch = html.match(/<body[^>]*>([\s\S]*?)<\/body>/i);
  if (!bodyMatch) return [html];
  
  const head = html.split(/<body/i)[0] + '<body' + (html.match(/<body([^>]*)>/i)?.[1] || '') + '>';
  const foot = '</body></html>';
  const body = bodyMatch[1];
  
  const chunks = body.split(/(?=<p|<div|<section|<blockquote|<table|<h[1-6]|<details)/i);
  
  let currentPart = '';
  let activeStack = [];
  
  for (const chunk of chunks) {
    if (Buffer.byteLength(currentPart + chunk, 'utf8') > limit && currentPart) {
      const closeTags = activeStack.slice().reverse().map(t => '</' + t.name + '>').join('');
      parts.push(head + currentPart + closeTags + foot);
      
      const openTags = activeStack.map(t => t.full).join('');
      currentPart = openTags + chunk;
      updateOpenTags(activeStack, chunk);
    } else {
      currentPart += chunk;
      updateOpenTags(activeStack, chunk);
    }
  }
  if (currentPart) {
    const closeTags = activeStack.slice().reverse().map(t => '</' + t.name + '>').join('');
    parts.push(head + currentPart + closeTags + foot);
  }
  return parts;
}

test('Fragment hierarchy preservation', () => {
    const html = '<html><body><main class="wrap"><div class="content-body"><p>foo</p><p>bar</p></div></main></body></html>';
    // Limit to 60 bytes forces split between foo and bar
    const parts = splitChapter(html, 60);

    assert.strictEqual(parts.length, 2, 'Should split into exactly 2 parts');
    assert.strictEqual(parts[0], '<html><body><main class="wrap"><div class="content-body"><p>foo</p></div></main></body></html>', 'First chunk must auto-close the wrapper');
    assert.strictEqual(parts[1], '<html><body><main class="wrap"><div class="content-body"><p>bar</p></div></main></body></html>', 'Second chunk must re-open the wrapper');
});

test('Self-closing and void tags are ignored by tag tracker', () => {
    const html = '<html><body><main class="wrap"><div class="content-body"><img src="x.jpg"><input type="text"><p>foo</p><p>bar</p></div></main></body></html>';
    const parts = splitChapter(html, 100);
    
    assert.strictEqual(parts.length, 2, 'Should split into exactly 2 parts');
    // The second chunk should NOT contain <img> or <input> wrappers! It should only re-open main and div
    assert.strictEqual(parts[1], '<html><body><main class="wrap"><div class="content-body"><p>bar</p></div></main></body></html>', 'Second chunk correctly ignores void tags from active context');
});
