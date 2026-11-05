// Renders the share GIF/MP4 (720x900, 20 fps) from elections/<id>/index.html. Usage: node capture-gif.js <config.json>
// Needs: playwright (chromium) and ffmpeg on PATH. Text and colours come from the config and the page's own numbers.
const { chromium } = require('playwright'); const fs = require('fs'); const path = require('path'); const { execSync } = require('child_process');
const cfgPath = path.resolve(process.argv[2] || process.env.CARTOGRAM_CONFIG);
const cfg = JSON.parse(fs.readFileSync(cfgPath, 'utf8')); const dir = path.dirname(cfgPath);
const ramps = JSON.parse(fs.readFileSync(path.join(__dirname, '../common/ramps.json'), 'utf8'));
const ramp = c => (typeof c.ramp === 'object' ? c.ramp : ramps[c.ramp || 'blue']);
const cache = path.join(dir, '.cache'); const frames = path.join(cache, 'frames'); fs.rmSync(frames, { recursive: true, force: true }); fs.mkdirSync(frames, { recursive: true });
const W = 720, H = 900, STEP = 50;
(async () => {
  const b = await chromium.launch();
  const ctx = await b.newContext({ viewport: { width: W, height: H }, deviceScaleFactor: 1, colorScheme: 'light' });
  const p = await ctx.newPage();
  await p.addInitScript(() => {
    let now = 0, id = 0, cbs = [], timers = [];   // virtual clock so the frames are deterministic
    window.__vt = { step(ms) { now += ms; const q = cbs; cbs = []; q.forEach(f => f(now)); const due = timers.filter(t => t.t <= now); timers = timers.filter(t => t.t > now); due.forEach(t => t.f(...t.a)); } };
    performance.now = () => now; window.requestAnimationFrame = f => { cbs.push(f); return ++id; }; window.cancelAnimationFrame = () => {};
    window.setTimeout = (f, ms, ...a) => { timers.push({ t: now + (ms || 0), f, a }); return ++id; };
  });
  await p.goto('file://' + path.join(dir, 'index.html'));
  await p.waitForFunction(() => !document.getElementById('bLens').disabled, { timeout: 30000 });
  await p.addStyleTag({ content: `
 body{padding:0!important;overflow:hidden}
 .wrap{max-width:none!important;margin:0!important}
 .wrap>*:not(.grid){display:none!important}
 .grid>aside{display:none!important}
 .grid{display:block!important}
 .tip{display:none!important}
 .mapwrap{position:absolute;left:0;right:0;top:206px;height:640px;max-width:none!important}
 svg.map{width:100%!important;height:100%!important}
 .ov{position:absolute;left:36px;right:36px;font-family:"Archivo","Helvetica Neue",Arial,sans-serif;z-index:9}
 .ov .k{font:500 15px/1 "IBM Plex Mono",ui-monospace,Menlo,monospace;letter-spacing:.09em;text-transform:uppercase;color:#75746f;top:0}
 .ov .h{font-weight:800;font-size:46px;line-height:1.02;letter-spacing:-.02em;color:#0b0b0b;margin:12px 0 10px}
 .ov .s{font-size:23px;line-height:1.3;color:#52514e}
 .ov.top{top:34px}
 .ov.bot{bottom:20px;display:flex;justify-content:space-between;align-items:center;font-size:14px;color:#75746f}
 .dots{display:flex;gap:16px}.dots i{display:inline-block;width:11px;height:11px;border-radius:3px;margin-right:6px;vertical-align:-1px}` });
  // all wording comes from the page's own numbers + config
  const T = await p.evaluate(([unit, target]) => {
    const g = window.__ga, M = g.META, t = g.tot, pct = v => Math.round(v * 100), byPop = g.C.slice().sort((x, y) => y.pop - x.pop);
    const tgt = (g.C.find(c => c.name === target) || byPop[1] || byPop[0]);
    return { a: M.a, b: M.b, state: M.state, people: M.people || (M.state + ' residents'), land: pct(t.landD), pop: pct(t.popD / g.totPop), cx: tgt.cx, cy: tgt.cy };
  }, [cfg.hex && cfg.hex.unit || 10000, cfg.lens && cfg.lens.gif_target]);
  const unit = (cfg.hex && cfg.hex.unit || 10000).toLocaleString('en-US');
  const S1 = ['By land area', `${T.a} carried ${T.land < 40 ? 'just ' : ''}${T.land}% of ${T.state}.`];
  await p.evaluate(([state, office, ca, cb, a, b, src]) => {
    document.getElementById('tips').click();
    const top = document.createElement('div'); top.className = 'ov top'; top.innerHTML = '<div class="k"></div><div class="h" id="oh"></div><div class="s" id="os"></div>'; top.firstChild.textContent = state + ' · ' + office; document.body.appendChild(top);
    const bot = document.createElement('div'); bot.className = 'ov bot'; bot.innerHTML = '<div class="dots"><span><i></i></span><span><i></i></span></div><div id="src"></div>';
    const sp = bot.querySelectorAll('span'); [[ca, a], [cb, b]].forEach(([c, n], k) => { sp[k].firstChild.style.background = c; sp[k].appendChild(document.createTextNode(n)); });
    bot.querySelector('#src').textContent = src; document.body.appendChild(bot);
    window.__stage = (h, s) => { document.getElementById('oh').textContent = h; document.getElementById('os').textContent = s; };
  }, [T.state, `${(cfg.race.date || '').match(/\d{4}/) || ''} ${cfg.race.office}`.trim(), ramp(cfg.candidates.a).mid_d, ramp(cfg.candidates.b).mid_d, T.a, T.b, (cfg.text && cfg.text.gif_source) || '']);
  let n = 0;
  async function shot() { await p.screenshot({ path: path.join(frames, `f${String(n++).padStart(4, '0')}.png`) }); }
  async function run(ms) { for (let t = 0; t < ms; t += STEP) { await p.evaluate(s => window.__vt.step(s), STEP); await shot(); } }
  const stage = (h, s) => p.evaluate(([h, s]) => window.__stage(h, s), [h, s]);
  await stage(...S1); await p.evaluate(s => window.__vt.step(s), STEP); await run(1400);
  await stage('Magnify the people', 'Crowded counties swell as the lens passes over them.');
  await p.evaluate(() => window.__ga.setView('lens')); await run(1000);
  await p.evaluate(([x, y]) => { window.__ga.lens.tx = x; window.__ga.lens.ty = y; window.__ga.lensKick(); }, [T.cx, T.cy]); await run(1300);
  await stage('Sized by residents', 'Every county, resized by population.');
  await p.evaluate(() => document.querySelector('#lsize button[data-s="2"]').click()); await run(2500);
  await stage(`One hex = ${unit} people`, `${T.pop}% of ${T.people} live in counties ${T.a} won.`);
  await p.evaluate(() => window.__ga.setView('pop')); await run(2800);
  await stage(...S1);
  await p.evaluate(() => window.__ga.setView('land')); await run(1000);
  console.log('frames', n); await b.close();
  const out = path.join(dir, 'media'); fs.mkdirSync(out, { recursive: true });
  const pal = path.join(cache, 'palette.png'), base = path.join(out, cfg.id);
  execSync(`ffmpeg -y -loglevel error -framerate 20 -i ${frames}/f%04d.png -vf "palettegen=stats_mode=diff" ${pal}`);
  execSync(`ffmpeg -y -loglevel error -framerate 20 -i ${frames}/f%04d.png -i ${pal} -lavfi "paletteuse=dither=bayer:bayer_scale=5:diff_mode=rectangle" ${base}.gif`);
  execSync(`ffmpeg -y -loglevel error -framerate 20 -i ${frames}/f%04d.png -c:v libx264 -preset veryfast -crf 24 -pix_fmt yuv420p -movflags +faststart ${base}.mp4`);
  console.log('wrote', base + '.gif', fs.statSync(base + '.gif').size, 'and .mp4', fs.statSync(base + '.mp4').size);
})();
