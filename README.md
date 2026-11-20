# psmishra.com

Pratik's site. Static pages on GitHub Pages.

- **Content is written in the vault**, not here: `~/vault/psmishra/site/publish/` (Octarine). Only notes with `published: true` are copied into `content/` by the kb-spine workflow `publish-psmishra-site.yml`. Never edit `content/` by hand; the next sync overwrites it.
- **Design lives here:** `templates/`, `static/site.css`, `build.py`.
- Local preview: `python3 -m venv .venv && .venv/bin/pip install markdown && .venv/bin/python sync.py ~/vault && .venv/bin/python build.py && python3 -m http.server -d _site`
- Context: `~/vault/psmishra/site/AGENTS.md`.
