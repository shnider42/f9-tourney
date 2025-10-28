# Retry: write a fixed script without f-strings to avoid brace escaping issues.
from pathlib import Path, PurePosixPath
import base64

root = Path("/mnt/data")
fixed_path = root / "apply_f9_theme_pro_fixed.py"

logo_src = Path("/mnt/data/8e57b537-a410-4d3b-984e-d8f6c610bdc8.png")
logo_b64 = ""
if logo_src.exists():
    logo_b64 = base64.b64encode(logo_src.read_bytes()).decode("ascii")

fixed_code = r'''#!/usr/bin/env python3
"""
apply_f9_theme_pro.py (fixed)
Deep theme transform (Rocket League look) for the RL Flask app.
- Writes static assets (theme.css, hero_bg.svg, rl_ball.svg, chevrons.svg) if present alongside script
- Adds a full hero header and wraps main sections in styled panels
- Replaces basic lists with styled roster items + status tags
- Links in theme.css and uses your f9_logo.png (or an embedded fallback)

Usage:
  python apply_f9_theme_pro_fixed.py
  python apply_f9_theme_pro_fixed.py --logo path/to/logo.png
"""
import argparse, base64, re
from pathlib import Path

HERO = r"""
<div class="hero mb-4">
  <div class="hero-inner">
    <img class="logo" src="{{ url_for('static', filename='f9_logo.png') }}" alt="F9">
    <h1>F9 1v1 Signups</h1>
    <p>Cap: {{ caps[0] }} players + {{ caps[1] }} subs. Rocket League 1v1 tournament signups.</p>
  </div>
</div>
"""

PLAYERS_T = r"""
<div class="section-title"><img src="{{ url_for('static', filename='chevrons.svg') }}" alt> <span>Players</span></div>
"""

SUBS_T = r"""
<div class="section-title"><img src="{{ url_for('static', filename='chevrons.svg') }}" alt> <span>Subs</span></div>
"""

WAIT_T = r"""
<div class="section-title"><img src="{{ url_for('static', filename='chevrons.svg') }}" alt> <span>Waitlist</span></div>
"""

EMBED_LOGO = r"__LOGO_B64__"

def write_bytes(p:Path, b:bytes):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(b)

def write_text(p:Path, s:str):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(s, encoding='utf-8')

def ensure_link(html:str)->str:
    if "theme.css" in html: return html
    return re.sub(r"(</head>)",
                  "\n  <link rel=\"stylesheet\" href=\"{{ url_for('static', filename='theme.css') }}\">\n\\1",
                  html, flags=re.I)

def inject_hero(html:str)->str:
    if 'class="hero' in html: return html
    m = re.search(r"<body[^>]*>", html, flags=re.I)
    if not m: return html
    return html[:m.end()] + HERO + html[m.end():]

def patch_section_titles(html:str)->str:
    html = re.sub(r"<h4>\s*Players\s*</h4>", PLAYERS_T, html, flags=re.I)
    html = re.sub(r"<h4>\s*Subs\s*</h4>", SUBS_T, html, flags=re.I)
    html = re.sub(r"<h4>\s*Waitlist\s*</h4>", WAIT_T, html, flags=re.I)
    return html

def wrap_first_form(html:str)->str:
    m = re.search(r"<form[^>]*>", html, flags=re.I)
    if not m: return html
    start = m.start()
    if '<div class="panel' in html[:start]:
        return html
    html = html[:start] + '<div class="panel mb-4">' + html[start:]
    html = html.replace("</form>", "</form></div>", 1)
    return html

def wrap_roster_columns(html:str)->str:
    html = html.replace('<div class="col-md-4">\n      ', '<div class="col-md-4">\n      <div class="panel roster">')
    html = html.replace('      </ol>\n    </div>', '      </ol>\n      </div>\n    </div>')
    return html

def add_tags_to_items(html:str)->str:
    pattern = r"(<li><strong>\{\{ r.display_name \}\}</strong>\s*<small class=\"text-muted\">\(\{\{ r.discord \}\}\)</small>)(.*?)</li>"
    repl = r"\1 <span class=\"tag rank\">{% if r.rank %}{{ r.rank }}{% elif r.region %}{{ r.region }}{% else %}{{ r.status }}{% endif %}</span></li>"
    return re.sub(pattern, repl, html)

def upgrade_index(html:str)->str:
    html = ensure_link(html)
    html = inject_hero(html)
    html = patch_section_titles(html)
    html = wrap_first_form(html)
    html = wrap_roster_columns(html)
    html = add_tags_to_items(html)
    return html

def upgrade_admin(html:str)->str:
    html = ensure_link(html)
    html = inject_hero(html)
    html = html.replace('<div class="col-md-4">', '<div class="col-md-4"><div class="panel">')
    html = html.replace('</ul>\n    </div>', '</ul>\n    </div>\n    </div>')
    return html

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--logo', type=str, help='PNG logo for the header (optional).')
    args = ap.parse_args()

    app_root = Path('.').resolve()
    static = app_root / 'static'
    templates = app_root / 'templates'
    static.mkdir(exist_ok=True); templates.mkdir(exist_ok=True)

    # Copy theme assets if present next to this script
    here = Path(__file__).resolve().parent
    for name in ['theme.css','hero_bg.svg','rl_ball.svg','chevrons.svg']:
        src = here / 'static' / name if (here / 'static' / name).exists() else here / name
        if src.exists():
            write_bytes(static / name, src.read_bytes())

    # Ensure logo
    logo_dst = static / 'f9_logo.png'
    if args.logo and Path(args.logo).exists():
        write_bytes(logo_dst, Path(args.logo).read_bytes())
    else:
        if EMBED_LOGO and not logo_dst.exists():
            write_bytes(logo_dst, base64.b64decode(EMBED_LOGO))

    # Patch templates
    for name, upgr in [('index.html', upgrade_index),
                       ('admin.html', upgrade_admin),
                       ('thanks.html', ensure_link),
                       ('closed.html', ensure_link)]:
        t = templates / name
        if not t.exists():
            continue
        bak = t.with_suffix(t.suffix + '.bak')
        if not bak.exists():
            write_text(bak, t.read_text(encoding='utf-8'))
        html = t.read_text(encoding='utf-8')
        new_html = upgr(html)
        if new_html != html:
            write_text(t, new_html)
            print(f"[ok] themed {{name}}")
        else:
            print(f"[skip] {{name}} unchanged")

if __name__ == "__main__":
    main()
'''

# Inject logo b64
fixed_code = fixed_code.replace("__LOGO_B64__", logo_b64)

fixed_path.write_text(fixed_code, encoding="utf-8")
print("Wrote:", fixed_path)
