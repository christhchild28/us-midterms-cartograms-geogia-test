
  /* ---------- fourth view: election districts (real shapes, shaded by margin) ---------- */
  var ED = /*EDDATA*/null;
  (function () {
    if (!ED) return;
    var edmap = document.getElementById('edmap'), wrap = document.getElementById('mapwrap'), aside = document.querySelector('.side'),
      edcard = document.getElementById('edcard'), edBtn = document.querySelector('.seg button[data-ed]'), zbox = document.getElementById('edzoom'),
      hintEl = document.getElementById('hint'), N = ED.id.length, ES = ED.es, ZMAX = 60;
    edBtn.parentNode.classList.add('has-ed');
    var built = false, on = false, vb = null, VB0 = vb0.slice(), sel = -1, peek = -1, paths = {}, hlh = null, hlp = null, stat = null;
    var R = new Array(N), BB = new Int32Array(4 * N), M = new Float64Array(N), adAgg = {};

    function pathOf(i) {
      var d = '';
      R[i].forEach(function (a) { for (var q = 0; q < a.length; q += 2) d += (q ? 'L' : 'M') + (a[q] / ES).toFixed(4) + ',' + (a[q + 1] / ES).toFixed(4); d += 'Z'; });
      return d;
    }
    function keyOf(i) {
      var t = ED.a[i] + ED.b[i]; if (!t) return 'z';
      var k = Math.round(Math.max(-1, Math.min(1, M[i] / .6)) * 12) + 12;
      return (ED.p[i] / 10 < ED.partial ? 'p' : 'f') + k;
    }
    function build() {
      if (built) return; built = true;
      var d = {}, i, cA = 0, cB = 0;
      for (i = 0; i < N; i++) {
        var bx0 = 1e9, by0 = 1e9, bx1 = -1e9, by1 = -1e9, dd = '', t = ED.a[i] + ED.b[i];
        R[i] = ED.r[i].map(dz);
        R[i].forEach(function (a) {
          for (var q = 0; q < a.length; q += 2) {
            var x = a[q], y = a[q + 1];
            if (x < bx0) bx0 = x; if (x > bx1) bx1 = x; if (y < by0) by0 = y; if (y > by1) by1 = y;
            dd += (q ? 'L' : 'M') + (x / ES).toFixed(4) + ',' + (y / ES).toFixed(4);
          }
          dd += 'Z';
        });
        BB[4 * i] = bx0; BB[4 * i + 1] = by0; BB[4 * i + 2] = bx1; BB[4 * i + 3] = by1;
        M[i] = t ? (ED.a[i] - ED.b[i]) / t : 0;
        var k = keyOf(i); d[k] = (d[k] || '') + dd;
        var pid = ED.par[i], g = adAgg[pid] || (adAgg[pid] = { a: 0, b: 0 }); g.a += ED.a[i]; g.b += ED.b[i];
        if (ED.a[i] > ED.b[i]) cA++; else if (ED.b[i] > ED.a[i]) cB++;
      }
      stat = { a: cA, b: cB };
      var gF = mk('g', {}, edmap), gA = mk('g', {}, edmap), gH = mk('g', {}, edmap);
      Object.keys(d).sort().forEach(function (k) { paths[k] = mk('path', { 'class': 'edfill', d: d[k], 'fill-opacity': k.charAt(0) === 'p' ? .5 : 1 }, gF); });
      var ad = '';
      ED.pr.forEach(function (rs) { rs.forEach(function (a) { var o = dz(a); for (var q = 0; q < o.length; q += 2) ad += (q ? 'L' : 'M') + (o[q] / ES).toFixed(4) + ',' + (o[q + 1] / ES).toFixed(4); ad += 'Z'; }); });
      mk('path', { 'class': 'edad', d: ad }, gA);
      hlh = mk('path', { 'class': 'hlh' }, gH); hlp = mk('path', { 'class': 'hlp' }, gH);
      document.getElementById('edcut').textContent = ED.partial; document.querySelector('.edcut2').textContent = ED.partial;
      var tk = document.getElementById('edticks'); tk.innerHTML = '<span>' + esc(META.b) + ' +60</span><span>Even</span><span>' + esc(META.a) + ' +60</span>'; document.getElementById('edticks2').innerHTML = '<span>' + esc(META.b) + ' +60</span><span>' + esc(META.a) + ' +60</span>';
      var nz = ED.nvotes;
      document.getElementById('edstats').textContent = META.a + ' carried ' + fmt(cA) + ' of ' + fmt(nz) + ' ' + ED.plural + ' with votes counted, ' + META.b + ' carried ' + fmt(cB) + '. ' +
        fmt(ED.npartial) + ' were under ' + ED.partial + '% reporting in this snapshot.';
    }
    function edRecolor() {
      if (!built) return;
      readStops();
      Object.keys(paths).forEach(function (k) {
        paths[k].setAttribute('fill', k === 'z' ? css(stops.n) : css(colorAt((+k.slice(1) - 12) / 12 * .6)));
      });
      var st = []; for (var j = -6; j <= 6; j++) st.push(css(colorAt(j / 10)));
      document.getElementById('edramp').style.background = document.getElementById('edramp2').style.background = 'linear-gradient(90deg,' + st.join(',') + ')';
    }

    /* ---- view box: zoom and pan ---- */
    function zoomed() { return vb[2] < VB0[2] * .98; }
    function clampVB() {
      var cx = vb[0] + vb[2] / 2, cy = vb[1] + vb[3] / 2;
      cx = Math.max(VB0[0], Math.min(VB0[0] + VB0[2], cx)); cy = Math.max(VB0[1], Math.min(VB0[1] + VB0[3], cy));
      vb[0] = cx - vb[2] / 2; vb[1] = cy - vb[3] / 2;
    }
    function setVB() {
      edmap.setAttribute('viewBox', vb.map(function (v) { return +v.toFixed(5); }).join(' '));
      var z = zoomed(); edmap.style.touchAction = z ? 'none' : 'pan-y'; edmap.style.cursor = z ? 'grab' : '';
      zbox.querySelector('[data-z=out]').disabled = !z; zbox.querySelector('[data-z=reset]').disabled = !z;
      zbox.querySelector('[data-z=in]').disabled = vb[2] <= VB0[2] / ZMAX * 1.01;
    }
    function zoomBy(k, fx, fy) {
      var w = Math.max(VB0[2] / ZMAX, Math.min(VB0[2], vb[2] / k)), s = w / vb[2], h = vb[3] * s;
      vb = [vb[0] + (vb[2] - w) * fx, vb[1] + (vb[3] - h) * fy, w, h]; clampVB(); setVB();
    }
    function frac(cx, cy) { var r = edmap.getBoundingClientRect(); return [(cx - r.left) / r.width, (cy - r.top) / r.height]; }

    /* ---- hit test (point in polygon over the bounding-box candidates) ---- */
    function inside(i, px, py) {
      var c = false;
      R[i].forEach(function (a) {
        var n = a.length / 2;
        for (var p = 0, q = n - 1; p < n; q = p++) {
          var xi = a[2 * p], yi = a[2 * p + 1], xj = a[2 * q], yj = a[2 * q + 1];
          if ((yi > py) !== (yj > py) && px < (xj - xi) * (py - yi) / (yj - yi) + xi) c = !c;
        }
      });
      return c;
    }
    function hitPt(px, py) {
      var best = -1, ba = 1e30;
      for (var i = 0; i < N; i++) {
        if (px < BB[4 * i] || px > BB[4 * i + 2] || py < BB[4 * i + 1] || py > BB[4 * i + 3]) continue;
        if (inside(i, px, py)) { var a = (BB[4 * i + 2] - BB[4 * i]) * (BB[4 * i + 3] - BB[4 * i + 1]); if (a < ba) { ba = a; best = i; } }
      }
      return best;
    }
    function hitAt(cx, cy) {
      var f = frac(cx, cy), r = edmap.getBoundingClientRect(), x = (vb[0] + f[0] * vb[2]) * ES, y = (vb[1] + f[1] * vb[3]) * ES, tol = 7 / r.width * vb[2] * ES;
      var h = hitPt(x, y); if (h >= 0) return h;
      var o = [[tol, 0], [-tol, 0], [0, tol], [0, -tol]];
      for (var j = 0; j < 4; j++) { h = hitPt(x + o[j][0], y + o[j][1]); if (h >= 0) return h; }
      return -1;
    }

    /* ---- card ---- */
    function lead(a, b) { return (a > b ? META.a : META.b) + ' +' + Math.round(Math.abs((a - b) / (a + b)) * 100); }
    function pill(col, txt, dark) { return '<span class="pn-p" style="background:' + col + ';color:' + (dark ? '#fff' : '#0b0b0b') + '">' + esc(txt) + '</span>'; }
    function cardHTML(i) {
      var a = ED.a[i], b = ED.b[i], t = a + b, pid = ED.par[i], cid = ED.lab[i], pc = ED.p[i] / 10, g = adAgg[pid];
      var rgb = t ? colorAt(M[i]) : null, col = t ? css(rgb) : 'var(--n)';
      var title = ED.pl + ' ' + pid + ' · ' + ED.cl + ' ' + cid, sub = fmt(t) + ' votes · ' + Math.round(pc) + '% reporting';
      var body = '';
      if (t) {
        var rows = [[META.a, a, a / t, css(stops.bm)], [META.b, b, b / t, css(stops.rm)]].sort(function (x, y) { return y[1] - x[1]; }).map(function (r, k) {
          return '<tr class="' + (k ? '' : 'win') + '"><td><span class="nm2"><i style="background:' + r[3] + '"></i>' + esc(r[0]) + '</span></td><td class="num">' + fmt(r[1]) + '</td><td class="num">' + (r[2] * 100).toFixed(1) + '%</td></tr>';
        }).join('');
        body = '<div class="pn-key"><div class="edsplit"><i style="width:' + (a / t * 100).toFixed(2) + '%;background:' + css(stops.bm) + '"></i><i style="width:' + (b / t * 100).toFixed(2) + '%;background:' + css(stops.rm) + '"></i></div>' +
          '<div class="pn-rel">Its ' + esc(ED.pn) + ' overall: <b>' + esc(lead(g.a, g.b)) + '</b></div></div>' +
          '<table class="pn-t"><thead><tr><th>Candidate</th><th class="num">Votes</th><th class="num">Share</th></tr></thead><tbody>' + rows + '</tbody></table>';
        if (pc < ED.partial) body += '<p class="ednote">Only <b>' + Math.round(pc) + '%</b> of scanners had reported when this snapshot was taken, so this count is partial.</p>';
      } else {
        body = '<p class="ednote" style="padding-top:6px">No votes were counted here in this snapshot. Its ' + esc(ED.pn) + ' overall: <b>' + esc(lead(g.a, g.b)) + '</b>.</p>';
      }
      return '<div class="pn-bar" style="background:' + col + '"></div>' +
        '<div class="pn-hd"><div style="min-width:0"><span class="pn-n">' + title + '</span><span class="pn-c">' + sub + '</span></div>' +
        '<div class="pn-r">' + (t ? pill(col, lead(a, b), lum(rgb) < .3) : pill('var(--n)', 'No votes', false)) +
        '<button type="button" class="pn-b pn-x" aria-label="Close">✕</button></div></div>' + body;
    }
    function emptyHTML() {
      return '<div class="pn-empty"><h2>Tap any shape</h2><p>Each shape is one ' + esc(ED.noun) + ', the smallest unit results are reported for. Thick lines are ' + esc(ED.pn) + ' borders.</p></div>';
    }
    function pad() { document.body.style.paddingBottom = (on && mqPhone.matches && edcard.classList.contains('open')) ? (edcard.offsetHeight + 24) + 'px' : ''; }
    function show() {
      var i = peek >= 0 ? peek : sel;
      var d = i < 0 ? '' : pathOf(i); hlh.setAttribute('d', d); hlp.setAttribute('d', d);
      edcard.classList.toggle('open', i >= 0); edcard.innerHTML = i >= 0 ? cardHTML(i) : emptyHTML(); pad();
    }
    function reveal() {
      if (!mqPhone.matches || sel < 0) return;
      setTimeout(function () {
        var b = hlp.getBoundingClientRect(), lim = innerHeight - edcard.offsetHeight - 12, dy = Math.min(b.bottom - lim, b.top - 70);
        if (dy > 0) window.scrollBy({ top: dy, behavior: RM ? 'auto' : 'smooth' });
      }, 120);
    }
    edcard.addEventListener('click', function (e) { if (e.target.closest('.pn-x')) { sel = -1; peek = -1; show(); } });
    if (window.ResizeObserver) new ResizeObserver(pad).observe(edcard);

    /* ---- pointers: tap selects, drag pans when zoomed, two fingers pinch, mouse hover previews ---- */
    var ptrs = {}, nptr = 0, g = null;
    function start() {
      var ks = Object.keys(ptrs);
      if (ks.length >= 2) {
        var a = ptrs[ks[0]], b = ptrs[ks[1]], r = edmap.getBoundingClientRect(), mx = (a.x + b.x) / 2, my = (a.y + b.y) / 2;
        g = { type: 'two', d0: Math.max(10, Math.hypot(a.x - b.x, a.y - b.y)), vb: vb.slice(), px: vb[0] + (mx - r.left) / r.width * vb[2], py: vb[1] + (my - r.top) / r.height * vb[3] };
      } else if (ks.length === 1) {
        var p = ptrs[ks[0]]; g = { type: 'one', x0: p.x, y0: p.y, vb: vb.slice(), moved: false, was: g ? g.moved || g.type === 'two' : false };
        if (g.was) g.moved = true;
      } else g = null;
    }
    edmap.addEventListener('pointerdown', function (e) {
      ptrs[e.pointerId] = { x: e.clientX, y: e.clientY, t: e.pointerType }; nptr = Object.keys(ptrs).length;
      try { edmap.setPointerCapture(e.pointerId); } catch (_) {}
      start();
    });
    edmap.addEventListener('pointermove', function (e) {
      var p = ptrs[e.pointerId];
      if (!p) {
        if (e.pointerType === 'mouse' && on) { var h = hitAt(e.clientX, e.clientY); if (h !== peek) { peek = h; show(); } }
        return;
      }
      p.x = e.clientX; p.y = e.clientY; if (!g) return;
      var r = edmap.getBoundingClientRect();
      if (g.type === 'two' && nptr >= 2) {
        var ks = Object.keys(ptrs), a = ptrs[ks[0]], b = ptrs[ks[1]], d = Math.hypot(a.x - b.x, a.y - b.y), mx = (a.x + b.x) / 2, my = (a.y + b.y) / 2;
        var w = Math.max(VB0[2] / ZMAX, Math.min(VB0[2], g.vb[2] / (d / g.d0))), h2 = g.vb[3] * (w / g.vb[2]);
        vb = [g.px - (mx - r.left) / r.width * w, g.py - (my - r.top) / r.height * h2, w, h2]; clampVB(); setVB();
      } else if (g.type === 'one') {
        var dx = e.clientX - g.x0, dy = e.clientY - g.y0;
        if (!g.moved && Math.hypot(dx, dy) > 7) g.moved = true;
        if (g.moved && zoomed()) { vb[0] = g.vb[0] - dx / r.width * g.vb[2]; vb[1] = g.vb[1] - dy / r.height * g.vb[3]; clampVB(); setVB(); }
      }
    });
    function lift(e) {
      var wasOne = g && g.type === 'one' && !g.moved;
      delete ptrs[e.pointerId]; nptr = Object.keys(ptrs).length;
      try { edmap.releasePointerCapture(e.pointerId); } catch (_) {}
      if (e.type === 'pointerup' && wasOne && nptr === 0) {
        var i = hitAt(e.clientX, e.clientY); sel = (i < 0 || i === sel) ? -1 : i; peek = -1; show(); reveal();
      }
      if (nptr) start(); else g = null;
    }
    edmap.addEventListener('pointerup', lift); edmap.addEventListener('pointercancel', lift);
    edmap.addEventListener('pointerleave', function (e) { if (e.pointerType === 'mouse' && peek >= 0) { peek = -1; show(); } });
    edmap.addEventListener('wheel', function (e) {
      if (!(e.ctrlKey || e.metaKey)) return;
      e.preventDefault(); var f = frac(e.clientX, e.clientY); zoomBy(e.deltaY < 0 ? 1.25 : .8, f[0], f[1]);
    }, { passive: false });
    edmap.addEventListener('dblclick', function (e) { var f = frac(e.clientX, e.clientY); zoomBy(2, f[0], f[1]); });
    zbox.addEventListener('click', function (e) {
      var b = e.target.closest('button'); if (!b || b.disabled) return;
      if (b.dataset.z === 'reset') { vb = VB0.slice(); setVB(); } else zoomBy(b.dataset.z === 'in' ? 1.7 : 1 / 1.7, .5, .5);
    });

    /* ---- enter / exit ---- */
    var edPrevMode = 0;   // colour mode (0 winner, 1 swing) to restore when leaving Precincts
    function enter() {
      if (on) return;
      track('view', 'precincts');
      build(); on = true; edOn = true;
      selected = null; clearSel(); showCard(null); hideTip(); document.getElementById('lensctl').hidden = true;
      /* the Precincts view has no swing baseline (election-district lines changed after the earlier race): hide Color by and show winner shading */
      var swc = document.querySelector('.swctl'); if (swc) { edPrevMode = colorMode; swc.hidden = true; if (colorMode === 1) setMode(0); }
      wrap.classList.add('ed-on'); aside.classList.add('ed-on');
      document.querySelectorAll('.seg:not(.sm) button').forEach(function (b) { b.setAttribute('aria-pressed', b === edBtn ? 'true' : 'false'); });
      hintEl.textContent = 'Each shape is one ' + ED.noun + ', the smallest unit results are reported for. Shading is the margin; thick lines are ' + ED.pn + ' borders. Pinch or use + and − to zoom, drag to pan, tap for numbers.';
      vb = VB0.slice(); edmap.setAttribute('viewBox', vb.join(' ')); setVB(); edRecolor(); sel = peek = -1; show();
      try { history.replaceState(null, '', '#precincts'); } catch (e) {}
    }
    function exit() {
      if (!on) return;
      on = false; edOn = false; wrap.classList.remove('ed-on'); aside.classList.remove('ed-on');
      edBtn.setAttribute('aria-pressed', 'false'); sel = peek = -1; edcard.classList.remove('open'); pad();
      var swc = document.querySelector('.swctl'); if (swc) { swc.hidden = false; if (edPrevMode === 1) setMode(1); }
      uiMode();
    }
    edBtn.addEventListener('click', enter);
    document.querySelectorAll('.seg:not(.sm) button:not([data-ed])').forEach(function (b) { b.addEventListener('click', exit, true); });
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', edRecolor);
    new MutationObserver(edRecolor).observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });
    window.__ed = { enter: enter, exit: exit, zoomBy: zoomBy, hitAt: hitAt, pick: function (i) { sel = i; show(); }, N: N, vb: function () { return vb; } };
    if (h0 === 'precincts') enter();
  })();
