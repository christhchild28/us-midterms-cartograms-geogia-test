"""Quick PNG preview of a layout json (hexes coloured by margin, county outlines)."""
import json, math, sys
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MP
P = json.load(open(sys.argv[1])); s = P['s']; r_ = s / math.sqrt(3)
fig, ax = plt.subplots(figsize=(7, 8)); cm = plt.cm.RdBu
for c in P['counties']:
    m = (c['d'] - c['r']) / (c['d'] + c['r']); col = cm(0.5 + max(-1, min(1, m / 0.6)) * 0.5)
    for x, y in c['cells']:
        ax.add_patch(MP([(x + r_ * math.cos(math.radians(-90 + 60 * t)), y + r_ * math.sin(math.radians(-90 + 60 * t))) for t in range(6)], facecolor=col, edgecolor='white', lw=0.3))
    if c['n'] >= 8 or len(sys.argv) > 3:
        ax.text(sum(x for x, _ in c['cells']) / len(c['cells']), sum(y for _, y in c['cells']) / len(c['cells']), c['name'][:6], fontsize=5, ha='center', va='center')
ax.autoscale_view(); ax.set_aspect('equal'); ax.invert_yaxis(); ax.axis('off'); plt.savefig(sys.argv[2], dpi=100, bbox_inches='tight')
