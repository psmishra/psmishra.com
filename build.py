#!/usr/bin/env python3
"""Build psmishra.com: content/*.md -> _site/*.html.

content/ is written by the vault sync (kb-spine workflow); never edit it by hand.
  content/index.md          the homepage
  content/writing/*.md      posts (frontmatter: title, date, description?)
  content/assets/*          images referenced by posts
Usage: python3 build.py [out_dir]   (default _site)
"""
import datetime as dt
import html
import re
import shutil
import sys
from pathlib import Path

import markdown

ROOT = Path(__file__).parent
CONTENT = ROOT / "content"
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "_site"
SITE = "https://psmishra.com"
NAME = "Pratik Sagar Mishra"


def parse(path):
    text = path.read_text(encoding="utf-8")
    meta, body = {}, text
    m = re.match(r"^---\n(.*?)\n---\n?(.*)$", text, re.S)
    if m:
        body = m.group(2)
        for line in m.group(1).splitlines():
            if ":" in line and not line.startswith(" "):
                k, v = line.split(":", 1)
                meta[k.strip()] = v.strip().strip("\"'")
    return meta, body


def md(body):
    # Octarine/Obsidian syntax the browser should never see.
    body = re.sub(r"!\[\[([^\]|]+)(?:\|[^\]]*)?\]\]", lambda m: f"![](/assets/{Path(m.group(1)).name})", body)
    body = re.sub(r"\[\[(?:[^\]|]+\|)?([^\]]+)\]\]", lambda m: Path(m.group(1)).name, body)
    body = re.sub(r"(?m)^\s*#[\w/-]+(\s+#[\w/-]+)*\s*$", "", body)  # trailing tag lines
    return markdown.markdown(body, extensions=["extra", "smarty", "sane_lists"])


def page(template, **kw):
    out = (ROOT / "templates" / f"{template}.html").read_text(encoding="utf-8")
    base = (ROOT / "templates" / "base.html").read_text(encoding="utf-8")
    for k, v in kw.items():
        out = out.replace("{{" + k + "}}", v)
    kw["main"] = out
    for k, v in kw.items():
        base = base.replace("{{" + k + "}}", v)
    return re.sub(r"\{\{\w+\}\}", "", base)


def nice_date(s):
    try:
        return dt.date.fromisoformat(s[:10]).strftime("%-d %B %Y")
    except ValueError:
        return s


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    shutil.copytree(ROOT / "static", OUT / "static")
    if (CONTENT / "assets").exists():
        shutil.copytree(CONTENT / "assets", OUT / "assets")

    posts = []
    for p in sorted((CONTENT / "writing").glob("*.md")):
        meta, body = parse(p)
        slug = re.sub(r"[^a-z0-9]+", "-", p.stem.lower()).strip("-")
        title = meta.get("title") or p.stem
        date = meta.get("date", "")
        desc = meta.get("description", "")
        posts.append((date, slug, title, desc))
        d = OUT / "writing" / slug
        d.mkdir(parents=True)
        (d / "index.html").write_text(page(
            "post", title=html.escape(title), page_title=html.escape(f"{title} · {NAME}"),
            description=html.escape(desc), date=html.escape(nice_date(date)),
            iso=html.escape(date[:10]), body=md(body), url=f"{SITE}/writing/{slug}/"), encoding="utf-8")
    posts.sort(reverse=True)

    def rows(items):
        return "\n".join(
            f'<li><a href="/writing/{s}/"><span class="t">{html.escape(t)}</span>'
            f'<time datetime="{html.escape(d[:10])}">{html.escape(nice_date(d))}</time></a></li>'
            for d, s, t, _ in items)

    writing = f'<section class="writing"><h2>Writing</h2><ul class="list">{rows(posts)}</ul></section>' if posts else ""

    meta, body = parse(CONTENT / "index.md") if (CONTENT / "index.md").exists() else ({}, "")
    # The first paragraph is the hero line; every "## Heading" becomes a labelled section.
    parts = re.split(r"(?m)^##\s+(.+)$", body.strip())
    hero = md(parts[0])
    sections = "".join(
        f'<section><h2>{html.escape(parts[i].strip())}</h2><div class="prose">{md(parts[i + 1])}</div></section>'
        for i in range(1, len(parts), 2))
    desc = re.sub(r"<[^>]+>", "", hero).strip()
    (OUT / "index.html").write_text(page(
        "home", page_title=NAME, description=html.escape(desc), hero=hero,
        sections=sections, writing=writing, url=SITE + "/"), encoding="utf-8")

    if posts:
        (OUT / "writing").mkdir(exist_ok=True)
        (OUT / "writing" / "index.html").write_text(page(
            "list", page_title=f"Writing · {NAME}", description="Writing by " + NAME,
            items=rows(posts), url=SITE + "/writing/"), encoding="utf-8")

    (OUT / "404.html").write_text(page(
        "list", page_title=f"Not found · {NAME}", description="",
        items='<li class="empty">Nothing here. <a href="/">Back home</a>.</li>', url=SITE), encoding="utf-8")
    (OUT / "CNAME").write_text("psmishra.com\n")
    (OUT / ".nojekyll").write_text("")
    print(f"built {len(posts)} posts -> {OUT}")


if __name__ == "__main__":
    main()
