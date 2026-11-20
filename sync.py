#!/usr/bin/env python3
"""Copy what Pratik marked `published: true` from the vault into content/.

Run by the kb-spine workflow (publish-psmishra-site.yml):
    python3 sync.py <vault_root>
Source: <vault_root>/psmishra/site/publish/  (index.md + writing/*.md)
Only files whose frontmatter says `published: true` are copied. Everything else,
including drafts, never leaves the vault. content/ is rebuilt from scratch, so
un-publishing (setting it back to false) removes the page.
Images referenced as ![[name.png]] or ![](path) are looked up next to the note,
then anywhere in the vault's attachment folders, and copied to content/assets/.
"""
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).parent
CONTENT = ROOT / "content"
IMG = re.compile(r"!\[\[([^\]|]+)(?:\|[^\]]*)?\]\]|!\[[^\]]*\]\(([^)\s]+)\)")


def is_published(text):
    m = re.match(r"^---\n(.*?)\n---", text, re.S)
    return bool(m and re.search(r"(?m)^published:\s*true\s*$", m.group(1)))


def find_image(name, note, vault):
    name = name.split("#")[0]
    if name.startswith(("http://", "https://")):
        return None
    cand = (note.parent / name)
    if cand.is_file():
        return cand
    base = Path(name).name
    for p in vault.rglob(base):
        if p.is_file() and ".git" not in p.parts and ".octarine" not in p.parts:
            return p
    return None


def main(vault):
    vault = Path(vault).resolve()
    src = vault / "psmishra" / "site" / "publish"
    if CONTENT.exists():
        shutil.rmtree(CONTENT)
    (CONTENT / "writing").mkdir(parents=True)
    (CONTENT / "writing" / ".gitkeep").write_text("")
    n = 0
    for note in [src / "index.md", *sorted((src / "writing").glob("*.md"))]:
        if not note.is_file():
            continue
        text = note.read_text(encoding="utf-8")
        if not is_published(text):
            continue

        def swap(m):
            name = m.group(1) or m.group(2)
            img = find_image(name, note, vault)
            if not img:
                return m.group(0)
            (CONTENT / "assets").mkdir(exist_ok=True)
            shutil.copy2(img, CONTENT / "assets" / img.name)
            return f"![](/assets/{img.name})"

        text = IMG.sub(swap, text)
        dest = CONTENT / note.relative_to(src)
        dest.write_text(text, encoding="utf-8")
        n += 1
    print(f"synced {n} published pages")


if __name__ == "__main__":
    main(sys.argv[1])
