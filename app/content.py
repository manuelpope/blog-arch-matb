"""Markdown article loader: parses front matter and reads .md files."""
from datetime import datetime
from pathlib import Path

import frontmatter

from app.cache import list_render_cache
from app.config import CONTENT_DIR


def _to_dict(slug: str, post: frontmatter.Post) -> dict:
    """Convert a frontmatter Post into a plain dict."""
    return {
        "slug": slug,
        "title": post.metadata.get("title", "Untitled"),
        "description": post.metadata.get("description", ""),
        "date": _normalize_date(post.metadata.get("date", "")),
        "tags": post.metadata.get("tags", []),
        "content": post.content,
    }


def _normalize_date(value) -> str:
    """Front matter `date` may be a date object or string — normalize."""
    if isinstance(value, datetime):
        return value.date().isoformat()
    return str(value) if value else ""


def _directory_mtime(path: Path) -> float:
    """Return max mtime across .md files; 0.0 if dir missing."""
    if not path.exists():
        return 0.0
    return max(
        (f.stat().st_mtime for f in path.glob("*.md")),
        default=0.0,
    )


def get_all_posts() -> list[dict]:
    """List all published posts, newest first. Cached."""
    cache_key = "__all_posts__"
    sentinel = Path(str(CONTENT_DIR))  # directory as cache sentinel
    cached = list_render_cache.get(cache_key, source=sentinel)
    if cached is not None:
        return cached

    posts: list[dict] = []
    for f in sorted(CONTENT_DIR.glob("*.md")):
        post = frontmatter.load(f)
        if post.metadata.get("draft", False):
            continue
        posts.append(_to_dict(f.stem, post))

    posts.sort(key=lambda p: p["date"], reverse=True)

    list_render_cache.set(cache_key, posts, source=sentinel)
    return posts


def get_post(slug: str) -> dict | None:
    """Load a single post by slug. Cached per-file by mtime."""
    f = CONTENT_DIR / f"{slug}.md"
    if not f.exists():
        return None

    cache_key = f"post:{slug}"
    cached = list_render_cache.get(cache_key, source=f)
    if cached is not None:
        return cached

    post = frontmatter.load(f)
    result = _to_dict(slug, post)
    list_render_cache.set(cache_key, result, source=f)
    return result
