const fs = require('fs');
const path = require('path');
const https = require('https');

const ASSETS_MAP = {
  "cover.png": "https://picsum.photos/id/1019/800/1000",
  "car.png": "https://picsum.photos/id/1071/800/600",
  "shack.png": "https://picsum.photos/id/1015/800/600",
  "yacht.png": "https://picsum.photos/id/384/800/600",
  "ankh.png": "https://picsum.photos/id/1058/800/600"
};

const TMP_ASSETS_DIR = path.join(process.cwd(), 'tmp_assets');
if (!fs.existsSync(TMP_ASSETS_DIR)) fs.mkdirSync(TMP_ASSETS_DIR, { recursive: true });

async function downloadImage(url, filename) {
  return new Promise((resolve, reject) => {
    const options = {
      headers: { 'User-Agent': 'Mozilla/5.0' },
      timeout: 10000
    };
    https.get(url, options, (res) => {
      if (res.statusCode === 301 || res.statusCode === 302) {
        return downloadImage(res.headers.location, filename).then(resolve).catch(reject);
      }
      if (res.statusCode !== 200) {
        return reject(new Error(`Status ${res.statusCode}`));
      }
      const chunks = [];
      res.on('data', chunk => chunks.push(chunk));
      res.on('end', () => {
        const buffer = Buffer.concat(chunks);
        fs.writeFileSync(path.join(TMP_ASSETS_DIR, filename), buffer);
        console.log(`✓ ${filename}`);
        resolve(buffer.toString('base64'));
      });
    }).on('error', reject).on('timeout', () => reject(new Error('Timeout')));
  });
}

async function bundle() {
  console.log("🛠️ Building V14 Final...");
  
  const assetsBase64 = {};
  for (const [filename, url] of Object.entries(ASSETS_MAP)) {
    try {
      const b64 = await downloadImage(url, filename);
      assetsBase64[filename] = `data:image/jpeg;base64,${b64}`;
    } catch (err) {
      console.warn(`! ${filename} fallback`);
      assetsBase64[filename] = "data:image/gif;base64,R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=";
    }
  }

  const chaptersDir = '.bookruns/egyptian_cross/stages/06_design/chapters_designed';
  const chapterFiles = fs.readdirSync(chaptersDir)
    .filter(f => f.startsWith('chapter') && f.endsWith('.html'))
    .sort((a, b) => parseInt(a.match(/\d+/)[0]) - parseInt(b.match(/\d+/)[0]));

  const localChapters = [];
  const globalTitles = [];

  for (const file of chapterFiles) {
    let content = fs.readFileSync(path.join(chaptersDir, file), 'utf8');
    const title = (content.match(/<h1>(.*?)<\/h1>/) || ["", "Глава"])[1];
    globalTitles.push(title);

    let body = (content.match(/<body[^>]*>([\s\S]*?)<\/body>/) || ["", content])[1];
    body = body.replace(/src="assets\/([^"]+)"/g, 'data-src="$1"');
    localChapters.push(body);
  }

  let template = fs.readFileSync('egyptian_cross_template.html', 'utf8');
  template = template
    .replace(/{{BOOK_TITLE}}/g, 'ТАЙНА ЕГИПЕТСКОГО КРЕСТА')
    .replace('{{ASSETS}}', JSON.stringify(assetsBase64))
    .replace('{{LOCAL_CHAPTERS}}', JSON.stringify(localChapters))
    .replace('{{GLOBAL_TITLES}}', JSON.stringify(globalTitles));

  const finalPath = 'outputs/egyptian_cross/Egyptian_Cross_Absolute_V14.html';
  fs.writeFileSync(finalPath, template);

  console.log(`✨ DONE: ${finalPath}`);
  process.exit(0); // Гарантированный выход
}

bundle();
