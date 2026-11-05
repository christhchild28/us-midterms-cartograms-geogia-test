#!/usr/bin/env python3
"""One command builds a county cartogram page from an election config.

    python3 build.py elections/ga-2026-senate/config.json            # everything
    python3 build.py elections/ga-2026-senate/config.json --from lens  # resume at a step
    python3 build.py elections/ga-2026-senate/config.json --only page  # one step
    python3 build.py elections/ga-2026-senate/config.json --gif        # also render the share GIF/MP4

    python3 build.py elections/ga-2026-senate/config.json --warp       # warp-following hexmap: writes warp.html

Steps: join -> hexpack -> rings -> rings2 -> lens -> page -> verify
Warp steps (--warp): join -> warpack -> warprings -> lens -> warppage
Outputs land next to the config: layout.json, rings.json, lens-fields.json, index.html.
Intermediate caches go in elections/<id>/.cache (safe to delete)."""
import argparse, os, subprocess, sys, time
ROOT = os.path.dirname(os.path.abspath(__file__)); SRC = os.path.join(ROOT, 'src')
STEPS = [('join', 'page/join.py'), ('hexpack', 'hexpack/hexpack.py'), ('rings', 'hexpack/build_rings.py'),
         ('rings2', 'hexpack/build_rings2.py'), ('lens', 'lens/genall.py'), ('page', 'page/build_page.py'), ('verify', 'verify.py')]
WSTEPS = [('join', 'page/join.py'), ('warpack', 'hexpack/warpack.py'), ('warprings', 'hexpack/build_warp_rings.py'),
          ('lens', 'lens/genall.py'), ('warppage', 'page/build_warp_page.py'), ('warpverify', 'verify_warp.py')]
ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument('config'); ap.add_argument('--warp', action='store_true', help='build the warp-following hexmap page (warp.html)')
ap.add_argument('--from', dest='frm', choices=sorted({s for s, _ in STEPS + WSTEPS})); ap.add_argument('--only', choices=sorted({s for s, _ in STEPS + WSTEPS}))
ap.add_argument('--gif', action='store_true', help='render media/<id>.gif and .mp4 after the build (needs node + playwright + ffmpeg)')
a = ap.parse_args()
cfgp = os.path.abspath(a.config)
env = dict(os.environ, CARTOGRAM_CONFIG=cfgp, PYTHONPATH=SRC)
if a.warp: STEPS = WSTEPS
names = [s for s, _ in STEPS]
sel = [a.only] if a.only else names[names.index(a.frm):] if a.frm else names
t0 = time.time()
for name, script in STEPS:
    if name not in sel: continue
    print('\n=== %s ===' % name, flush=True); t = time.time()
    r = subprocess.run([sys.executable, os.path.join(SRC, script)], env=env)
    if r.returncode: sys.exit('step %r failed (exit %d)' % (name, r.returncode))
    print('--- %s done in %.0fs' % (name, time.time() - t), flush=True)
if a.gif:
    print('\n=== gif ===', flush=True)
    r = subprocess.run(['node', os.path.join(SRC, 'media/capture-gif.js'), cfgp], env=env)
    if r.returncode: sys.exit('gif step failed')
if os.path.dirname(os.path.dirname(cfgp)) == os.path.join(ROOT, 'elections'):   # only for configs that live in this repo
    subprocess.run([sys.executable, os.path.join(SRC, 'site_index.py')], env=env)
print('\nbuilt in %.0fs -> %s' % (time.time() - t0, os.path.join(os.path.dirname(cfgp), 'warp.html' if a.warp else 'index.html')))
