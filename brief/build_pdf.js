// Renders brief.html to the submission PDF using the pre-installed Chromium.
// Usage: node build_pdf.js
const { chromium } = require('playwright');
const path = require('path');
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.goto('file://' + path.join(__dirname, 'brief.html'));
  await page.pdf({ path: path.join(__dirname, '..', 'Soham_Patil_2023AM11045_Tresata_Brief.pdf'),
                   format: 'A4', printBackground: true, preferCSSPageSize: true });
  await browser.close();
})();
