#!/usr/bin/env python3
"""apply_f9_theme.py

Drop-in theming script for the RL 1v1 Flask app.
- Adds an F9 dark theme (theme.css) under static/
- Injects a header logo into templates
- Ensures templates link to theme.css

Usage:
    python apply_f9_theme.py            # run from your app root (where 'templates/' lives)
    python apply_f9_theme.py --logo path/to/logo.png   # optional: use your own logo

Safe to re-run. Creates backups with .bak once per file.
"""
import argparse, base64, re
from pathlib import Path

THEME_CSS = r"""
/* F9 Dark Esports Theme */
:root {
  --bg: #1E1E1E;
  --panel: #2a2a2a;
  --text: #E9E6DA;
  --accent: #E15B3E;
  --accent-hover: #ff7355;
  --border: #333;
}
html, body {
  background: var(--bg);
  color: var(--text);
  font-family: 'Segoe UI', Roboto, Arial, sans-serif;
}
h1, h2, h3, h4 { color: var(--text); font-weight: 600; }
a, .btn-link { color: var(--accent); }
.btn-primary {
  background-color: var(--accent);
  border-color: var(--accent);
  color: var(--bg);
  font-weight: 600;
}
.btn-primary:hover {
  background-color: var(--accent-hover);
  border-color: var(--accent-hover);
  color: var(--bg);
}
input, textarea, select {
  background-color: var(--panel);
  color: var(--text);
  border: 1px solid #444;
}
.form-label { color: var(--text); }
.alert {
  border-radius: 0.4rem;
  background-color: var(--panel);
  color: var(--text);
  border: 1px solid var(--accent);
}
.list-group-item {
  background-color: var(--panel);
  color: var(--text);
  border: 1px solid var(--border);
}
.badge {
  background-color: var(--accent) !important;
  color: var(--bg) !important;
}
.header-logo { text-align:center; margin: 1rem 0 0.5rem; }
.header-logo img { height: 60px; }
"""

LINK_TAG = '{{ url_for(\'static\', filename=\'theme.css\') }}'

def ensure_theme_link(html:str)->str:
    # If already linked, skip
    if 'theme.css' in html:
        return html
    # Insert link after Bootstrap CSS link if found, else before </head>
    pattern = r'(</head>)'
    link_el = f"""  <link rel=\"stylesheet\" href=\"{{ url_for('static', filename='theme.css') }}\">\n\1"""
    new_html, n = re.subn(pattern, link_el, html, flags=re.IGNORECASE)
    if n == 0:
        return html + "\n<link rel=\"stylesheet\" href=\"" + LINK_TAG + "\">\n"
    return new_html

def ensure_logo_header(html:str)->str:
    if 'header-logo' in html and 'f9_logo' in html:
        return html
    body_match = re.search(r'<body[^>]*>', html, flags=re.IGNORECASE)
    if not body_match:
        return html
    insert_at = body_match.end()
    header = """\n  <div class=\"header-logo\">\n    <img src=\"{{ url_for('static', filename='f9_logo.png') }}\" alt=\"F9 Logo\">\n  </div>\n"""
    return html[:insert_at] + header + html[insert_at:]

def write_if_missing(path:Path, content:str):
    if not path.exists():
        path.write_text(content, encoding='utf-8')
        return True
    return False

def backup_once(path:Path):
    bak = path.with_suffix(path.suffix + '.bak')
    if not bak.exists():
        bak.write_text(path.read_text(encoding='utf-8'), encoding='utf-8')

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--logo', type=str, help='Path to PNG logo (optional). Defaults to embedded low-res.')
    args = ap.parse_args()

    app_root = Path('.').resolve()
    templates = app_root / 'templates'
    static = app_root / 'static'
    templates.mkdir(exist_ok=True)
    static.mkdir(exist_ok=True)

    # Write theme.css
    theme_css = static / 'theme.css'
    write_if_missing(theme_css, THEME_CSS)

    # Write logo
    logo_path = static / 'f9_logo.png'
    if args.logo:
        src = Path(args.logo).expanduser().resolve()
        if src.exists():
            logo_path.write_bytes(src.read_bytes())
        else:
            print(f"[warn] --logo path not found: {src}; using embedded logo")
            logo_b64 = "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"
            logo_path.write_bytes(base64.b64decode(logo_b64))
    else:
        logo_b64 = "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"
        logo_path.write_bytes(base64.b64decode(logo_b64))

    # Patch known templates if present
    targets = ['index.html', 'admin.html', 'thanks.html', 'closed.html']
    for name in targets:
        t = templates / name
        if not t.exists():
            continue
        backup_once(t)
        html = t.read_text(encoding='utf-8')
        html2 = ensure_theme_link(html)
        html3 = ensure_logo_header(html2)
        if html3 != html:
            t.write_text(html3, encoding='utf-8')
            print(f"[ok] Patched {name}")
        else:
            print(f"[skip] {name} already themed")


if __name__ == '__main__':
    main()
