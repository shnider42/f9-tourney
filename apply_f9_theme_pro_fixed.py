#!/usr/bin/env python3
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

EMBED_LOGO = r"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"

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
