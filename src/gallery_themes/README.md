# Gallery themes

A theme is the decorative layer behind the root gallery (`index.html`): background art, glow, textures. It never changes the content or layout.

- **Choose one:** set `"theme"` in `gallery.config.json` at the repo root, or run `python3 src/site_index.py --theme <name>` for a one-off build.
- **Roll back to plain:** `"theme": "plain"`, then `python3 src/site_index.py`.
- **Current themes:** `plain` (nothing added), `nevada-morph` (Nevada's county outlines morph from land to population shapes as the intro scrolls, a red/blue glow behind the headline, plain hexagon outlines behind the Elections band).

## Adding a theme
Create `src/gallery_themes/<name>.py` (use underscores for hyphens: `nevada-morph` is `nevada_morph.py`) with one function:

```python
def build(root):          # root = repo root path
    return {
        'css':    '',     # CSS appended to the page <style>
        'top':    '',     # HTML placed right after <body>
        'bottom': '',     # HTML or <script> placed right before </body>
    }
```

The page already provides these CSS variables, for light and dark: `--bg --ink --ink2 --ink3 --hair --raised --n --soft` and the party colors `--bm --bd --rm --rd` (mid and deep blue and red). `.band` is the Elections band, and `main` sits above the background at z-index 1. Keep text contrast intact, respect `prefers-reduced-motion`, and keep the theme self-contained: no external requests. A theme that fails to build falls back to `plain` with a warning.
