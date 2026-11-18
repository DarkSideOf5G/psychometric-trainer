const {chromium}=require(process.env.PLAYWRIGHT_PATH||'/Users/demiurg/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const assert=require('node:assert/strict');
const fs=require('node:fs');
(async()=>{
 const browser=await chromium.launch({executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless:true});
 try{
 const page=await browser.newPage({viewport:{width:390,height:844}}),errors=[];
 page.on('pageerror',e=>errors.push(e.message));
 const catalog=JSON.parse(fs.readFileSync('site/data/catalog.json'));
 await page.goto(process.env.APP_URL||'http://127.0.0.1:8791/');
 await page.waitForFunction(()=>!document.querySelector('#answers').disabled);
 assert.equal(await page.locator('#topicSelect option').count(),9);
 for(const option of await page.locator('#topicSelect option').evaluateAll(os=>os.slice(1).map(o=>o.value))){
  await page.selectOption('#topicSelect',option);
  await page.waitForFunction(()=>!document.querySelector('#answers').disabled);
  const src=await page.locator('#questionBody > .picture-button img').first().getAttribute('src');
  const id=src.match(/(he-\d{4}-\d{2}-quantitative-\d-q\d+)-\d.webp/)[1];
  assert.ok(catalog.questions.find(q=>q.id===id).topics.includes(option));
  assert.ok((await page.locator('#topicExamples').innerText()).length>10);
  assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
 }
 await page.click('#languageMode');
 await page.waitForFunction(()=>!document.querySelector('#answers').disabled);
 assert.ok(await page.locator('#topicControls').isHidden());
 await page.click('#mathMode');
 await page.waitForFunction(()=>!document.querySelector('#answers').disabled);
 assert.equal(await page.locator('#topicSelect').inputValue(),'data');
 await page.selectOption('#topicSelect','');
 await page.waitForFunction(()=>!document.querySelector('#answers').disabled);
 assert.match(await page.locator('#progressText').innerText(),/2,819|2\.819|2819/);
 assert.deepEqual(errors,[]);
 console.log('Topic filtering, mode switching, all topics and mobile layout passed');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exit(1)});
