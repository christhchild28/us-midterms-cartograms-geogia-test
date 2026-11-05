t=open('morph.template.html').read()
def rep(old,new,cnt=1):
    global t
    assert t.count(old)==cnt,(old[:60],t.count(old))
    t=t.replace(old,new)
rep("<title>Georgia Land vs People</title>","<title>Georgia Population Lens</title>")
# CSS
rep(".county.hl .cp { stroke: var(--ink); stroke-width: 2px; }",".county.hl .cp, .county.sel .cp { stroke: var(--ink) !important; stroke-width: 2px !important; }")
rep(".sf { stroke: none; pointer-events: none; }",""".sf { stroke: none; pointer-events: none; }
.seg button:disabled { opacity: .4; cursor: default; }
.lensctl { display: flex; align-items: center; flex-wrap: wrap; gap: 6px 18px; margin: 0 0 8px; }
.lensctl[hidden] { display: none; }
.seg.sm button { padding: 8px 14px; font-size: 14px; min-height: 36px; }
.rng { display: inline-flex; align-items: center; gap: 10px; font-size: 14px; color: var(--ink-2); min-height: 44px; }
.rng input { width: 96px; accent-color: var(--ink); }
.rng output { font-family: var(--f-mono); font-size: 13px; min-width: 3.2em; color: var(--ink); }
svg.map.lensmode { touch-action: none; cursor: grab; }
.sout { fill: none; stroke: var(--ink-2); stroke-width: 1.2px; stroke-dasharray: 4 3; vector-effect: non-scaling-stroke; pointer-events: none; }
.lring { fill: none; stroke: var(--ink); stroke-width: 1.2px; stroke-dasharray: 3 3; vector-effect: non-scaling-stroke; pointer-events: none; }""")
# HTML controls
rep("""      <button type="button" data-m="pop" aria-pressed="false">People</button>
    </div>
    <label class="tog"><input type="checkbox" id="outline" checked> Land outlines</label>
  </div>""","""      <button type="button" data-m="pop" aria-pressed="false">People</button>
      <button type="button" data-m="lens" aria-pressed="false" id="bLens" disabled>Lens</button>
    </div>
    <label class="tog"><input type="checkbox" id="outline"> Land outlines</label>
    <label class="tog"><input type="checkbox" id="tips" checked> Tooltips</label>
  </div>
  <div class="lensctl" id="lensctl" hidden>
    <div class="seg sm" role="group" aria-label="Lens mode" id="lsize"><button type="button" data-s="1" aria-pressed="true">Magnify</button><button type="button" data-s="2" aria-pressed="false">Whole map</button></div>
  </div>""")
rep("Tap any county to grow or shrink it in place.</p>","Tap any county to grow or shrink it in place, or try Lens.</p>")
rep("function setHot(c) { if (hot) hot.g.classList.remove('hl'); hot = c; if (c) c.g.classList.add('hl'); }","function setHot(c) { if (hot) hot.g.classList.remove('hl'); hot = c; if (c) { c.g.classList.add('hl'); if (view === 'lens') gC.appendChild(c.g); } }")
# data
rep("  var D = /*DATA*/;","  var D = /*DATA*/;\n  var LENS = /*LENS*/;")
rep("raf = 0, ghostOn = true;","raf = 0, ghostOn = false;")
# draw uses warp when lens active
rep("    if (t <= 0) d = ringPath(R, K);\n    else if (t >= 1 && w <= 0)","    if (t <= 0) d = (lens.a > 0.0005 && LF) ? warpPath(c) : ringPath(R, K);\n    else if (t >= 1 && w <= 0)")
LENSJS = r'''
  /* ---------- lens ---------- */
  var view = 'land', LF = null, CK = null, NN = LENS.nx * LENS.ny, FLD = new Float32Array(2 * NN), FA = new Float32Array(2 * NN), FB = new Float32Array(2 * NN), tipsOn = true, startLens = h0 === 'lens', lensDrag = false, viewTok = 0, lensInit = false;
  var lens = { x: 0, y: 0, tx: 0, ty: 0, a: 0, at: 0, b: 1, bt: 1, g: 0, gt: 0, raf: 0, last: 0 }, GF = null;
  var LR = LENS.radii, vb0 = [B[0], B[1], B[2] - B[0], B[3] - B[1]];
  var sOut = mk('path', { 'class': 'sout', d: ringPath(LENS.outline, LENS.outline.length / 2) }, gTop); sOut.style.opacity = 0;
  var lensRing = mk('circle', { 'class': 'lring', r: LR[0], cx: 0, cy: 0 }, gTop); lensRing.style.opacity = 0;
  C.forEach(function (c) {
    var K = c.K; c.vi = new Int32Array(K); c.vfx = new Float32Array(K); c.vfy = new Float32Array(K);
    for (var k = 0; k < K; k++) {
      var gx = (c.R[2 * k] / 1000 - LENS.ox) / LENS.h, gy = (c.R[2 * k + 1] / 1000 - LENS.oy) / LENS.h;
      gx = Math.max(0, Math.min(LENS.nx - 1.0001, gx)); gy = Math.max(0, Math.min(LENS.ny - 1.0001, gy));
      var ix = Math.floor(gx), iy = Math.floor(gy);
      c.vi[k] = iy * LENS.nx + ix; c.vfx[k] = gx - ix; c.vfy[k] = gy - iy;
    }
  });
  function loadLens() {
    var btn = document.getElementById('bLens');
    if (!window.DecompressionStream) { btn.hidden = true; return; }
    try {
      var bin = atob(LENS.data), u8 = new Uint8Array(bin.length);
      for (var i = 0; i < bin.length; i++) u8[i] = bin.charCodeAt(i);
      new Response(new Blob([u8]).stream().pipeThrough(new DecompressionStream('gzip'))).arrayBuffer().then(function (buf) {
        var raw = new Int16Array(buf), nx = LENS.nx, ny = LENS.ny, nf = raw.length / (2 * NN), f, y, x;
        for (f = 0; f < nf; f++) for (y = 0; y < ny; y++) { var o = f * 2 * NN + y * nx * 2; for (x = 1; x < nx; x++) { raw[o + 2 * x] += raw[o + 2 * x - 2]; raw[o + 2 * x + 1] += raw[o + 2 * x - 1]; } }
        var nc0 = LENS.centers.length, gb = nc0 * 2 * NN; GF = new Float32Array(2 * NN); for (var gi = 0; gi < 2 * NN; gi++) GF[gi] = raw[gb + gi] / LENS.scale;
        LF = raw; CK = new Int16Array(LENS.gx * LENS.gy).fill(-1);
        LENS.centers.forEach(function (c, k) { CK[c[1] * LENS.gx + c[0]] = k; });
        btn.disabled = false; if (startLens) setView('lens');
      }).catch(function () { btn.hidden = true; });
    } catch (e) { btn.hidden = true; }
  }
  function fieldInto(out, x, y, ri) {
    var fx = (x - LENS.sx) / LENS.sp, fy = (y - LENS.sy) / LENS.sp, i0 = Math.floor(fx), j0 = Math.floor(fy), tx = fx - i0, ty = fy - j0, ks = [], ws = [], tot = 0, a, b;
    var cand = [[i0, j0, (1 - tx) * (1 - ty)], [i0 + 1, j0, tx * (1 - ty)], [i0, j0 + 1, (1 - tx) * ty], [i0 + 1, j0 + 1, tx * ty]];
    for (a = 0; a < 4; a++) {
      var ci = cand[a][0], cj = cand[a][1]; if (ci < 0 || cj < 0 || ci >= LENS.gx || cj >= LENS.gy) continue;
      var k = CK[cj * LENS.gx + ci]; if (k >= 0 && cand[a][2] > 1e-4) { ks.push(k); ws.push(cand[a][2]); tot += cand[a][2]; }
    }
    if (!ks.length) {
      var best = 0, bd = 1e9; LENS.centers.forEach(function (c, k) { var d = Math.hypot(LENS.sx + c[0] * LENS.sp - x, LENS.sy + c[1] * LENS.sp - y); if (d < bd) { bd = d; best = k; } });
      ks = [best]; ws = [1]; tot = 1;
    }
    var nc = LENS.centers.length, sc = 1 / LENS.scale, n2 = 2 * NN;
    out.fill(0);
    for (a = 0; a < ks.length; a++) { var base = (ri * nc + ks[a]) * n2, w = ws[a] / tot * sc; for (b = 0; b < n2; b++) out[b] += w * LF[base + b]; }
  }
  function computeField() {
    var b = lens.b, i, n2 = 2 * NN;
    fieldInto(FLD, lens.x, lens.y, 0);
    if (lens.g > .001 && GF) { var g = lens.g; for (i = 0; i < n2; i++) FLD[i] += (GF[i] - FLD[i]) * g; }
  }
  function warpPath(c) {
    var R = c.R, K = c.K, nx = LENS.nx, a = lens.a, F = FLD, vi = c.vi, vfx = c.vfx, vfy = c.vfy, d = 'M', k, b, fx, fy, ux, uy;
    for (k = 0; k < K; k++) {
      b = vi[k] * 2; fx = vfx[k]; fy = vfy[k];
      ux = (F[b] * (1 - fx) + F[b + 2] * fx) * (1 - fy) + (F[b + 2 * nx] * (1 - fx) + F[b + 2 * nx + 2] * fx) * fy;
      uy = (F[b + 1] * (1 - fx) + F[b + 3] * fx) * (1 - fy) + (F[b + 2 * nx + 1] * (1 - fx) + F[b + 2 * nx + 3] * fx) * fy;
      d += (k ? 'L' : '') + (R[2 * k] / 1000 + a * ux).toFixed(3) + ',' + (R[2 * k + 1] / 1000 + a * uy).toFixed(3);
    }
    return d + 'Z';
  }
  function lensTick(now) {
    var dt = Math.min(60, now - (lens.last || now)); lens.last = now;
    var kp = RM ? 1 : 1 - Math.exp(-dt / 70), ka = RM ? 1 : 1 - Math.exp(-dt / 150), kb = RM ? 1 : 1 - Math.exp(-dt / 120), kg = RM ? 1 : 1 - Math.exp(-dt / 170);
    lens.x += (lens.tx - lens.x) * kp; lens.y += (lens.ty - lens.y) * kp; lens.a += (lens.at - lens.a) * ka; lens.b += (lens.bt - lens.b) * kb; lens.g += (lens.gt - lens.g) * kg;
    if (Math.abs(lens.tx - lens.x) < 1e-4 && Math.abs(lens.ty - lens.y) < 1e-4) { lens.x = lens.tx; lens.y = lens.ty; }
    if (Math.abs(lens.at - lens.a) < .002) lens.a = lens.at;
    if (Math.abs(lens.bt - lens.b) < .002) lens.b = lens.bt;
    if (Math.abs(lens.gt - lens.g) < .002) lens.g = lens.gt;
    var on = lens.a > .0005 && LF;
    if (on) computeField();
    for (var i = 0; i < C.length; i++) { var c = C[i]; if (T[i] === 0 && TT[i] === 0) c.p.setAttribute('d', on ? warpPath(c) : ringPath(c.R, c.K)); }
    var am = Math.min(1, lens.a), ge = lens.g * am, kz = 1 + .25 * am, w = vb0[2] * kz, h = vb0[3] * kz, lv = [vb0[0] + vb0[2] / 2 - w / 2, vb0[1] + vb0[3] / 2 - h / 2, w, h];
    svg.setAttribute('viewBox', lv.map(function (v, j) { return v + (LENS.gvb[j] - v) * ge; }).join(' '));
    sOut.style.opacity = .7 * ge;
    lensRing.setAttribute('cx', lens.x.toFixed(3)); lensRing.setAttribute('cy', lens.y.toFixed(3));
    lensRing.setAttribute('r', LR[0].toFixed(3)); lensRing.style.opacity = .6 * Math.min(1, lens.a * 3) * (1 - lens.g);
    var moving = lens.tx !== lens.x || lens.ty !== lens.y || lens.a !== lens.at || lens.b !== lens.bt || lens.g !== lens.gt;
    lens.raf = moving ? requestAnimationFrame(lensTick) : 0; if (!moving) lens.last = 0;
  }
  function lensKick() { if (!lens.raf) lens.raf = requestAnimationFrame(lensTick); }
  function clearSel() { C.forEach(function (c) { c.g.classList.remove('sel'); }); }
  function selectCounty(i) { clearSel(); C[i].g.classList.add('sel'); gC.appendChild(C[i].g); selected = i; showCard(i); }
  function act(i, fromChip) {
    if (view === 'land') toggleCounty(i);
    else if (view === 'pop') selectCounty(i);
    else { if (fromChip) { lens.tx = C[i].cx; lens.ty = C[i].cy; lensKick(); } selected = i; showCard(i); }
  }
  function setView(m) {
    var tok = ++viewTok, was = view; view = m; selected = null; clearSel(); showCard(null); hideTip();
    svg.classList.toggle('lensmode', m === 'lens'); document.getElementById('lensctl').hidden = m !== 'lens';
    if (m === 'lens') {
      var settled = modeNow() === 'land'; if (!settled) setAll(0);
      setTimeout(function () {
        if (tok !== viewTok) return;
        if (!lensInit) { var fu = C.filter(function (c) { return c.name === 'Fulton'; })[0]; lens.x = lens.tx = fu.cx; lens.y = lens.ty = fu.cy; lensInit = true; }
        lens.at = 1; applySize(); uiMode();
      }, settled ? 0 : (RM ? 10 : 560));
    } else {
      lens.at = 0; lensKick(); if (was === 'lens') reorder();
      setTimeout(function () { if (tok !== viewTok) return; setAll(m === 'pop' ? 1 : 0); }, was === 'lens' && !RM ? 320 : 0);
    }
    uiMode();
  }
  function applySize() {
    var s = +document.querySelector('#lsize [aria-pressed=true]').dataset.s;
    lens.gt = s === 2 ? 1 : 0; lensKick(); uiMode(); if (selected == null) showCard(null);
  }
  function cAt(x, y) { var el = document.elementFromPoint(x, y), g = el && el.closest ? el.closest('.county') : null; return g ? C[+g.dataset.i] : null; }
  function toMap(e) { var pt = svg.createSVGPoint(); pt.x = e.clientX; pt.y = e.clientY; var m = svg.getScreenCTM(); return m ? pt.matrixTransform(m.inverse()) : null; }
  function lensAim(e) {
    var c0 = cAt(e.clientX, e.clientY); if (c0 && c0.i !== selected) { selected = c0.i; showCard(c0.i); }
    if (lens.gt === 1) return;
    var q = toMap(e); if (!q) return;
    lens.tx = Math.max(vb0[0], Math.min(vb0[0] + vb0[2], q.x)); lens.ty = Math.max(vb0[1], Math.min(vb0[1] + vb0[3], q.y)); lensKick();
    var c = cAt(e.clientX, e.clientY); if (c && c.i !== selected) { selected = c.i; showCard(c.i); }
  }
  document.querySelectorAll('#lsize button').forEach(function (b) {
    b.addEventListener('click', function () {
      document.querySelectorAll('#lsize button').forEach(function (o) { o.setAttribute('aria-pressed', o === b ? 'true' : 'false'); });
      applySize();
    });
  });
  document.getElementById('tips').addEventListener('change', function (e) { tipsOn = e.target.checked; if (!tipsOn) hideTip(); });
'''
rep("  function modeNow() {",LENSJS+"  function modeNow() {")
# uiMode
rep("    var m = modeNow();\n    document.querySelectorAll('.seg button')","    var m = view === 'lens' ? 'lens' : modeNow();\n    document.querySelectorAll('.seg:not(.sm) button')")
rep("document.getElementById('hint').textContent = m === 'pop' ?","document.getElementById('hint').textContent = m === 'lens' ? (lens.gt === 1 ? 'Every county sized by its residents. The dashed line is the real state outline.' : 'Move the lens over the map (drag on a phone). Counties under it resize by population.') : m === 'pop' ?")
rep("Tap a county to return it to its land shape.'","Tap a county for its numbers.'")
rep("    try { if (m !== 'mixed') history","    try { if (m !== 'mixed') history")
# seg handler
rep("document.querySelectorAll('.seg button').forEach(function (b) { b.addEventListener('click', function () { selected = null; showCard(null); setAll(b.dataset.m === 'pop' ? 1 : 0); }); });","document.querySelectorAll('.seg:not(.sm) button').forEach(function (b) { b.addEventListener('click', function () { setView(b.dataset.m); }); });")
# card default
rep("h.textContent = 'Tap a county'; card.appendChild(h);","h.textContent = view === 'lens' ? (lens.gt === 1 ? 'Every county, sized by its people' : 'Roll the lens') : 'Tap a county'; card.appendChild(h);")
rep("p.textContent = 'Some counties are big on the map and small in people, others the reverse. Tap one here, on the map, or from the lists below to see how far it moves when residents decide its size.';","p.textContent = view === 'lens' ? (lens.gt === 1 ? 'Each county is drawn in proportion to its residents. Hover or tap one to see how much it grew or shrank from its land area.' : 'Counties under the lens swell or shrink to match their share of Georgia\\'s people. The county at the lens center is shown here.') : 'Some counties are big on the map and small in people, others the reverse. Tap one here, on the map, or from the lists below to see how far it moves when residents decide its size.';")
# chips
rep("b.addEventListener('click', function () { toggleCounty(c.i); }); return b;","b.addEventListener('click', function () { act(c.i, true); }); return b;")
# tooltip gating + handlers
rep("  function showAt(c, e) { if (c !== hot) { setHot(c); fillTip(c); } tip.classList.add('on');","  function showAt(c, e) { if (c !== hot) { setHot(c); fillTip(c); } if (!tipsOn) { tip.classList.remove('on'); return; } tip.classList.add('on');")
rep("  svg.addEventListener('pointermove', function (e) { if (e.pointerType === 'touch') return; var c = cOf(e);","  svg.addEventListener('pointerdown', function (e) { if (view !== 'lens' || !LF) return; if (e.pointerType === 'touch') { try { svg.setPointerCapture(e.pointerId); } catch (_) {} hideTip(); } lensDrag = true; lensAim(e); });\n  svg.addEventListener('pointerup', function (e) { lensDrag = false; if (view === 'lens' && e.pointerType === 'touch' && tipsOn) { var c = cAt(e.clientX, e.clientY); if (c) { setHot(c); fillTip(c); tip.classList.add('on'); place(e.clientX, e.clientY, true); } } });\n  svg.addEventListener('pointercancel', function () { lensDrag = false; });\n  svg.addEventListener('pointermove', function (e) { if (view === 'lens' && LF && (e.pointerType !== 'touch' || lensDrag)) lensAim(e); if (e.pointerType === 'touch') return; var c = cOf(e);")
rep("    toggleCounty(c.i);\n    if (e.pointerType === 'touch' || e.detail === 0 || true) { setHot(c); fillTip(c); tip.classList.add('on'); place(","    act(c.i, false);\n    if (!tipsOn || view === 'lens') { return; }\n    if (e.pointerType === 'touch' || e.detail === 0 || true) { setHot(c); fillTip(c); tip.classList.add('on'); place(")
rep("cannot touch all of their neighbors.'","cannot touch all of their neighbors. In Lens view the warp is a density-equalizing flow computed for each lens position, so counties stretch and compress without overlapping.'")
rep("window.__ga = { setAll: setAll,","window.__ga = { setView: setView, lens: lens, setAll: setAll,")
# boot: load lens
rep("  if (h0 === 'pop' || h0 === 'people') setAll(1, true);","  loadLens();\n  if (h0 === 'pop' || h0 === 'people') setAll(1, true);")
open('lens.template.html','w').write(t)
print('ok',len(t))
