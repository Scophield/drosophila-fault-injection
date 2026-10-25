// Local-only browser QA of generated README previews and delivered media.
// Uses an existing Chrome and Playwright; does not visit or modify GitHub.
const fs = require('node:fs');
const path = require('node:path');
const {pathToFileURL} = require('node:url');
const {chromium} = require('playwright');

(async () => {
  const root = path.resolve(__dirname, '../..');
  const browserPath = process.argv[2];
  if (!browserPath || !fs.existsSync(browserPath)) throw new Error('Pass an existing Chrome executable path.');
  const browser = await chromium.launch({headless:true, executablePath:browserPath});
  const report = {scope:'Local rendering of actual README Markdown; not live GitHub', viewports:[], videos:[]};
  try {
    for (const [name,width,height,dark] of [['desktop',1280,1000,false],['mobile',390,844,false],['desktop-dark',1280,1000,true],['mobile-dark',390,844,true]]) {
      const context = await browser.newContext({viewport:{width,height},deviceScaleFactor:1});
      const page = await context.newPage();
      await page.goto(pathToFileURL(path.join(root,'preview',dark?'readme-dark.html':'readme.html')).href);
      await page.waitForFunction(() => Array.from(document.images).every(im=>im.complete&&im.naturalWidth>0));
      const state = await page.evaluate(() => ({width:innerWidth,scrollWidth:document.documentElement.scrollWidth,images:Array.from(document.images).map(im=>({src:im.getAttribute('src'),loaded:im.complete&&im.naturalWidth>0})),headings:Array.from(document.querySelectorAll('h1,h2')).map(e=>e.textContent)}));
      if (state.scrollWidth>width) throw new Error(`${name}: page-wide overflow`);
      await page.screenshot({path:path.join(root,'preview',`${name}.png`)});
      await page.screenshot({path:path.join(root,'preview',`${name}-full.png`),fullPage:true});
      await page.locator('a[href="#results"]').click();
      if (!page.url().endsWith('#results')) throw new Error('Local anchor navigation failed');
      await page.screenshot({path:path.join(root,'preview',`${name}-results.png`)});
      await page.locator('summary').first().click();
      await page.locator('h3').first().scrollIntoViewIfNeeded();
      await page.screenshot({path:path.join(root,'preview',`${name}-demo-expanded.png`)});
      if (await page.locator('body').innerText().then(t=>t.includes('@@SLOT'))) throw new Error('Unresolved preview text');
      report.viewports.push({name,width,height,...state});
      await context.close();
    }
    const context = await browser.newContext({viewport:{width:1440,height:1000}});
    const page = await context.newPage();
    await page.goto(pathToFileURL(path.join(root,'preview','media.html')).href);
    for (const [id,key,duration] of [['a',6,17],['b',13.8,17],['c',15.1,18],['overview',14.8,26]]) {
      const handle = page.locator(`#video-${id}`);
      await handle.evaluate(async v=>{v.muted=true;await v.play();});
      await page.waitForTimeout(180);
      const playback = await handle.evaluate(v=>({duration:v.duration,currentTime:v.currentTime,readyState:v.readyState,error:v.error&&v.error.code}));
      if (playback.error||playback.currentTime<=0||Math.abs(playback.duration-duration)>.02) throw new Error(JSON.stringify(playback));
      await handle.evaluate(async(v,t)=>{v.pause();if(Math.abs(v.currentTime-t)<.001)return;await new Promise(resolve=>{v.addEventListener('seeked',resolve,{once:true});v.currentTime=t;});},key);
      await handle.screenshot({path:path.join(root,'preview',`video-${id}-event.png`)});
      report.videos.push({id,keyWallSeconds:key,...playback});
    }
    await context.close();
    fs.writeFileSync(path.join(root,'preview','browser-check.json'),JSON.stringify(report,null,2)+'\n');
    console.log(JSON.stringify({passed:true,viewports:report.viewports.length,videos:report.videos.length},null,2));
  } finally {await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
