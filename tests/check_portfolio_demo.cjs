// Disposable browser context: no production server, database, API, or browser profile.
const assert = require('node:assert/strict');
const path = require('node:path');
const fs = require('node:fs');
const {pathToFileURL} = require('node:url');
const {chromium} = require(process.env.AIEYU_PLAYWRIGHT || 'playwright');
const root = path.resolve(__dirname, '..');
const artifacts = path.join(root, 'apps', 'portfolio_demo');
const reportDir = path.join(root, 'dist', 'portfolio');

(async () => {
  const browser = await chromium.launch({channel: process.env.AIEYU_BROWSER || 'msedge', headless: true});
  const errors = [], requests = [];
  try {
    const context = await browser.newContext({viewport:{width:1440,height:1080},offline:true});
    await context.route(/^https?:/, route => {requests.push(route.request().url());return route.abort();});
    const page = await context.newPage();
    page.on('pageerror', e => errors.push(e.message));
    const url = pathToFileURL(path.join(reportDir, 'AIeyu-demo.html')).href;
    await page.goto(url);
    await page.getByRole('heading',{name:'每一次错题， 都有下一步。'}).waitFor();
    await page.screenshot({path:path.join(artifacts,'preview.png'),fullPage:true,animations:'disabled'});
    assert.match(await page.locator('#metrics').innerText(), /0\s+已提交/);
    await page.getByRole('button',{name:'开始 3 题体验'}).click();
    await page.locator('#submit').click();
    assert.match(await page.locator('#quiz-message').innerText(), /未选择/);
    // One wrong answer selects location practice; two correct answers remain correct.
    await page.locator('input[name=d1][value="0"]').check();
    await page.locator('input[name=d2][value="3"]').check();
    await page.locator('input[name=d3][value="2"]').check();
    await page.locator('#submit').click();
    assert.match(await page.locator('.result').innerText(), /2 \/ 3/);
    assert.equal(await page.locator('.explanation').count(), 3);
    assert.equal(await page.locator('.incorrect .answer-tag').innerText(), '你的选择');
    assert.equal(await page.locator('.incorrect').evaluate(el=>getComputedStyle(el).borderTopColor), 'rgb(160, 56, 50)');
    await page.locator('summary').first().click();
    assert.equal(await page.locator('details[open]').count(), 1);
    await page.evaluate(()=>window.scrollTo(0,0));
    await page.screenshot({path:path.join(artifacts,'feedback.png'),fullPage:true,animations:'disabled'});
    await page.getByRole('button',{name:'查看学习中心'}).click();
    assert.match(await page.locator('#metrics').innerText(), /67%/);
    await page.locator('#review-mistakes').click();
    assert.equal(await page.locator('.question').count(), 1);
    await page.getByRole('button',{name:'查看学习中心'}).click();
    assert.match(await page.locator('#metrics').innerText(), /3\s+已提交/);
    await page.locator('#recommendation button').click();
    assert.equal(await page.locator('input[name=d1]').count(), 0);
    await page.locator('input[name=l1][value="2"]').check();
    await page.locator('input[name=l2][value="0"]').check();
    await page.locator('#submit').click();
    assert.match(await page.locator('.result').innerText(), /2 \/ 2/);
    await page.getByRole('button',{name:'查看学习中心'}).click();
    assert.match(await page.locator('#metrics').innerText(), /80%/);
    // Re-answering the original question correctly removes its latest-error entry.
    await page.locator('[data-view=practice]').first().click();
    await page.getByRole('button',{name:'重做诊断'}).click();
    for(const [id,value] of [['d1','1'],['d2','3'],['d3','2']])await page.locator(`input[name=${id}][value="${value}"]`).check();
    await page.locator('#submit').click();
    await page.getByRole('button',{name:'查看学习中心'}).click();
    assert.match(await page.locator('#mistakes').innerText(), /没有待复习/);
    await page.locator('[data-view=words]').first().click();
    await page.locator('#flip').click();
    assert.match(await page.locator('#word-card').innerText(), /书；书籍/);
    await page.locator('#again').click();
    for(let i=0;i<4;i++){await page.locator('#flip').click();await page.locator('#known').click();}
    assert.match(await page.locator('#word-card').innerText(), /已完成一轮/);
    await page.locator('#restart-words').click();
    assert.match(await page.locator('#word-card').innerText(), /0 \/ 4/);
    await page.locator('[data-view=about]').first().click();
    assert.match(await page.locator('#about').innerText(), /未声称|尚未整体接入/);
    await page.locator('#reset').click();
    assert.match(await page.locator('#metrics').innerText(), /0\s+已提交/);
    for(const width of [390,320]){
      await page.setViewportSize({width,height:844});
      for(const view of ['home','practice','words','about']){
        await page.locator(`nav [data-view=${view}]`).click();
        assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth), `${view} overflows at ${width}`);
      }
      await page.locator('nav [data-view=home]').click();
      if(width===390)await page.screenshot({path:path.join(artifacts,'mobile.png'),fullPage:true,animations:'disabled'});
    }
    // File entry point, reload and keyboard navigation also work without a server.
    await page.reload();
    assert.match(await page.locator('#metrics').innerText(), /0\s+已提交/);
    const keyboardPage = await context.newPage();
    await keyboardPage.goto(url);
    await keyboardPage.keyboard.press('Tab');
    assert.equal(await keyboardPage.locator('.skip').evaluate(el=>el===document.activeElement), true);
    assert.deepEqual(errors, []);
    assert.deepEqual(requests, []);
    fs.writeFileSync(path.join(reportDir,'browser-validation.json'), JSON.stringify({passed:true,widths:[1440,390,320],pageErrors:errors,networkRequests:requests,checks:['empty submission','score and explanations','wrong-answer review','targeted new questions','latest-error removal','word retry queue','reset','responsive overflow','file reload','keyboard navigation']},null,2));
    console.log('PASS: offline file demo; full learning loop, vocabulary, reset, keyboard, 1440/390/320px; 0 network requests; 0 page errors.');
  }finally{await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
