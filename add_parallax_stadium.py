#!/usr/bin/env python3
"""
add_parallax_stadium.py
-----------------------
One-step enhancer: adds a parallax Rocket League stadium background to the F9 theme.
Usage:
    python add_parallax_stadium.py
This script will:
  - Patch templates/index.html and templates/admin.html to inject parallax layers
  - Append CSS to static/theme.css
  - Append JS logic to static/app.js
  - Make .bak backups first
"""

import re
from pathlib import Path

def patch_html(path: Path):
    if not path.exists():
        return
    html = path.read_text(encoding="utf-8")
    if 'p-layer p-stadium' in html:
        print(f"[skip] {path.name}: already patched")
        return
    bak = path.with_suffix(path.suffix + ".bak")
    if not bak.exists():
        bak.write_text(html, encoding="utf-8")
    html = re.sub(r'(<div\s+class="hero"[^>]*>)',
                  r"\1\n  <!-- Parallax layers -->\n  <div class=\"p-layer p-stadium\" data-depth=\"0.15\"></div>\n  <div class=\"p-layer p-vignette\" data-depth=\"0.05\"></div>",
                  html, count=1, flags=re.I)
    path.write_text(html, encoding="utf-8")
    print(f"[ok] patched {path.name}")

def append_css(path: Path):
    css = """
/* ==== Parallax Stadium ==== */
.hero { isolation: isolate; }
.p-layer {
  position: absolute; inset: -8%;
  background-repeat: no-repeat; background-position: center; background-size: cover;
  pointer-events: none; will-change: transform; z-index: 0;
  transition: transform 120ms ease-out;
}
.p-stadium {
  background-image: url("{{ url_for('static', filename='stadium.jpg') }}");
  filter: saturate(0.9) brightness(0.6) contrast(1.05) blur(0.2px);
  opacity: 0.42;
}
.p-vignette {
  background: radial-gradient(120% 85% at 50% 40%, transparent 0%, transparent 45%, rgba(0,0,0,0.45) 100%);
  mix-blend-mode: multiply;
}
@media (prefers-reduced-motion: reduce) {
  .p-layer { transform: none !important; transition: none !important; }
}
"""
    if not path.exists():
        return
    txt = path.read_text(encoding="utf-8")
    if ".p-stadium" in txt:
        print(f"[skip] {path.name}: already has parallax CSS")
        return
    bak = path.with_suffix(path.suffix + ".bak")
    if not bak.exists():
        bak.write_text(txt, encoding="utf-8")
    txt += "\n" + css
    path.write_text(txt, encoding="utf-8")
    print(f"[ok] appended parallax CSS")

def patch_js(path: Path):
    js = """
// --- Parallax for hero layers ---
const heroes = document.querySelectorAll('.hero');
heroes.forEach(hero => {
  const layers = hero.querySelectorAll('.p-layer');
  if (!layers.length) return;
  let rect = hero.getBoundingClientRect();
  let cx = rect.left + rect.width / 2;
  let cy = rect.top + rect.height / 2;
  const apply = (mx, my) => {
    const dx = (mx - cx) / rect.width;
    const dy = (my - cy) / rect.height;
    layers.forEach(layer => {
      const depth = parseFloat(layer.dataset.depth || '0.1');
      const tx = (-dx * 30) * depth;
      const ty = (-dy * 20) * depth;
      layer.style.transform = `translate3d(${tx}px, ${ty}px, 0)`;
    });
  };
  hero.addEventListener('mousemove', e => apply(e.clientX, e.clientY));
  const recalc = () => {
    rect = hero.getBoundingClientRect();
    cx = rect.left + rect.width / 2;
    cy = rect.top + rect.height / 2;
  };
  window.addEventListener('scroll', recalc, { passive: true });
  window.addEventListener('resize', recalc);
  recalc();
  apply(cx + 1, cy + 1);
});
"""
    if not path.exists():
        return
    txt = path.read_text(encoding="utf-8")
    if "p-layer" in txt and "translate3d" in txt:
        print(f"[skip] {path.name}: already has parallax JS")
        return
    bak = path.with_suffix(path.suffix + ".bak")
    if not bak.exists():
        bak.write_text(txt, encoding="utf-8")
    txt += "\n" + js
    path.write_text(txt, encoding="utf-8")
    print(f"[ok] appended parallax JS")

def main():
    app_root = Path(".")
    templates = app_root / "templates"
    static = app_root / "static"

    patch_html(templates / "index.html")
    patch_html(templates / "admin.html")
    append_css(static / "theme.css")
    patch_js(static / "app.js")
    print("\\n✅ Done! Restart your app and move your mouse over the hero to see the stadium parallax.")

if __name__ == "__main__":
    main()
