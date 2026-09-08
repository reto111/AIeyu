// Optional browser regression: uses a disposable database and fresh browser profile.
const assert = require('node:assert/strict');
const {spawn} = require('node:child_process');
const fs = require('node:fs');
const path = require('node:path');
const {chromium} = require(process.env.AIEYU_PLAYWRIGHT || 'playwright');
const root = path.resolve(__dirname, '..');
const out = path.join(root, 'data/processed/vocabulary_learning/browser');
fs.mkdirSync(out, {recursive: true});
const server = spawn(process.env.AIEYU_PYTHON || 'python', ['-X','utf8','-B','tests/vocabulary_preview_server.py'],
  {cwd: root, windowsHide: true, stdio: ['pipe','pipe','inherit']});
let browser;
const errors = [];
async function main() {
  const url = await new Promise((resolve, reject) => {
    let output = '';
    server.stdout.on('data', (data) => {output += data; if (output.includes('\n')) resolve(output.trim());});
    server.on('error', reject);
    server.on('exit', (code) => {if (!output) reject(new Error(`Preview server exited ${code}`));});
  });
  browser = await chromium.launch({channel: process.env.AIEYU_BROWSER || 'msedge', headless: true});
  const context = await browser.newContext({viewport: {width: 1440, height: 1000}});
  const page = await context.newPage();
  page.on('pageerror', (error) => errors.push(error.message));
  await page.goto(url + '/register.html');
  await page.locator('[name="display_name"]').fill('browser-grade-' + Date.now());
  await page.locator('[name="student_year"]').selectOption('1');
  await page.locator('[name="password"]').fill('sample-password-123');
  await page.locator('[name="confirmation"]').fill('sample-password-123');
  await page.screenshot({path:path.join(out,'registration-desktop.png'),fullPage:true});
  await page.locator('#authSubmit').click();
  await page.waitForURL('**/login.html**');
  const beforeLogin = await (await context.request.get(url+'/api/auth/status')).json();
  assert.equal(beforeLogin.authenticated, false);
  await page.locator('[name="password"]').fill('sample-password-123');
  await page.locator('#authSubmit').click();
  await page.waitForURL(url + '/');
  await page.locator('[data-view="words"]').click();
  await page.locator('#generalStageStatus').filter({hasText:'大一'}).waitFor();
  assert.equal(await page.locator('#generalStageInput').inputValue(), '1');
  await page.locator('#wordCountInput').fill('50');
  await page.locator('#startWordsBtn').click();
  await page.locator('#wordCard').waitFor();
  assert.equal(await page.locator('#wordMeaning').isVisible(), false);
  await page.locator('[data-word-result="fuzzy"]').click();
  await page.locator('#wordMeaning').waitFor();
  await page.locator('#nextWordBtn').click();
  assert.match(await page.locator('#wordText').innerText(), /\u0301/);
  await page.locator('[data-word-result="known"]').click();
  await page.locator('#wordMeaning').waitFor();
  for (const width of [1440,390,320]) {
    await page.setViewportSize({width, height: 950});
    await page.screenshot({path:path.join(out,`words-${width}.png`),fullPage:true});
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth+1), true, `Overflow at ${width}`);
    const boxes = [];
    for (const id of ['prevWordBtn','nextWordBtn','markWordWrongBtn']) boxes.push(await page.locator('#'+id).boundingBox());
    assert.ok(boxes.every(Boolean));
    for (let i=1; i<boxes.length; i++) assert.ok(boxes[i].x>=boxes[i-1].x+boxes[i-1].width-1 || boxes[i].y>=boxes[i-1].y+boxes[i-1].height-1, 'Overlapping word buttons');
  }
  await page.locator('#prevWordBtn').click();
  assert.equal(await page.locator('#wordText').innerText(), 'а');
  await page.locator('[data-exam-system="TEM4_RU"][data-exam-scope="words"]').click();
  assert.equal(await page.locator('#generalLearningControls').isVisible(), false);
  const practiceBefore = await page.locator('#practiceTitle').innerText();
  await page.locator('[data-exam-system="TEM8_RU"][data-exam-scope="words"]').click();
  assert.equal(await page.locator('#practiceTitle').innerText(), practiceBefore);
  await page.locator('[data-exam-system="GENERAL"]').click();
  await page.locator('#generalStageInput').selectOption('3');
  await page.locator('#generalStageStatus').filter({hasText:'进阶'}).waitFor();
  await page.reload();
  await page.locator('#generalStageStatus').filter({hasText:'进阶'}).waitFor();
  await page.locator('#startReviewWordsBtn').click();
  await page.locator('#wordCard').waitFor();
  assert.equal(await page.locator('#wordText').innerText(), 'а');
  assert.deepEqual(errors, []);
  console.log(JSON.stringify({registration:true, grade:true, words:true, scopes:true, review:true,
    stage_saved:true, viewports:[1440,390,320], page_errors:errors, screenshots:out}));
}
main().catch((error) => {console.error(error); process.exitCode=1;}).finally(async () => {
  if (browser) await browser.close();
  server.stdin.end('\n');
});
