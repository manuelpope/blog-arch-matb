"""HTML page templates."""
from datetime import datetime
from html import escape

from app.config import (
    AUTHOR_INITIALS,
    AUTHOR_LINKEDIN,
    AUTHOR_EMAIL,
    AUTHOR_NAME,
    SITE_DESCRIPTION,
    SITE_TITLE,
    SITE_URL,
)
from app.content import get_all_posts, get_post
from app.markdown import render_markdown


def _format_date(date_str: str) -> str:
    if not date_str:
        return ""
    try:
        dt = datetime.fromisoformat(date_str)
        return dt.strftime("%B %d, %Y")
    except (ValueError, TypeError):
        return str(date_str)


def _layout(content: str, title: str = SITE_TITLE, is_post: bool = False) -> str:
    """Wrap page content in the standard HTML document."""
    mermaid_cdn = (
        '<script src="/static/mermaid.min.js"></script>'
        '<script>'
        'mermaid.initialize({startOnLoad: false, theme: "dark", securityLevel: "loose"});'
        'document.addEventListener("DOMContentLoaded", function() {'
        '  mermaid.run({nodes: document.querySelectorAll("pre.mermaid")});'
        '});'
        '</script>'
        if is_post else ""
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="description" content="{escape(SITE_DESCRIPTION)}">
    <title>{escape(title)} — {escape(SITE_TITLE)}</title>
    <link rel="alternate" type="application/rss+xml" href="/rss.xml">
    <link rel="stylesheet" href="/static/style.css">
    <link rel="icon" href="/favicon.ico">
</head>
<body>
<header>
    <div class="container nav">
        <a href="/" class="logo">{escape(SITE_TITLE)}</a>
        <nav>
            <a href="/blog">Writing</a>
            <a href="/portfolio">Projects</a>
            <a href="/about">About</a>
        </nav>
    </div>
</header>
<main>
    {content}
</main>
<footer>
    <div class="container footer-content">
        <p>© {datetime.now().year} {escape(AUTHOR_NAME)}</p>
        <div>
            <a href="/rss.xml">RSS</a>
            <a href="/sitemap.xml">Sitemap</a>
        </div>
    </div>
</footer>
<script src="/static/app.js"></script>
{mermaid_cdn}
</body>
</html>"""


def _article_card(post: dict) -> str:
    """One row in a listing."""
    tags = "".join(
        f'<span class="tag">{escape(t)}</span>' for t in post["tags"][:2]
    )
    return f"""
<article>
    <div class="meta">
        <time>{_format_date(post['date'])}</time>
        {tags}
    </div>
    <h2><a href="/blog/{post['slug']}">{escape(post['title'])}</a></h2>
    <p>{escape(post['description'])}</p>
</article>"""


def home_page() -> str:
    posts = get_all_posts()
    cards = "".join(_article_card(p) for p in posts[:5])
    content = f"""
<div class="container">
    <section class="hero">
        <h1>Backend systems, financial platforms, and AI.</h1>
        <p>Senior engineer writing about distributed architecture, event-driven systems, and AI products. Wide experience of years  at JPMorgan Chase.</p>
        <div class="links">
            <a href="{AUTHOR_LINKEDIN}" target="_blank" rel="noopener">LinkedIn</a>
            <a href="mailto:{AUTHOR_EMAIL}">Email</a>
            <span>Buenos Aires, Argentina</span>
        </div>
    </section>
    <hr>
    <section>
        <h2 class="section-title">Latest</h2>
        <div class="articles">{cards}</div>
    </section>
</div>
"""
    return _layout(content)


def blog_index_page() -> str:
    posts = get_all_posts()
    cards = "".join(_article_card(p) for p in posts)
    content = f"""
<div class="container reading">
    <h1>Writing</h1>
    <div class="articles">{cards}</div>
</div>
"""
    return _layout(content)


def blog_post_page(slug: str) -> str | None:
    post = get_post(slug)
    if not post:
        return None

    body_html = render_markdown(post["content"], slug=post["slug"])
    tags_html = "".join(
        f'<span class="tag">{escape(t)}</span>' for t in post["tags"]
    )

    content = f"""
<article class="post">
    <div class="container reading">
        <a href="/blog" class="back-link">← All articles</a>
        <header>
            <h1>{escape(post['title'])}</h1>
            <div class="meta">
                <span class="avatar">{AUTHOR_INITIALS}</span>
                <span>
                    <strong>{escape(AUTHOR_NAME)}</strong>
                    <span class="date">· {_format_date(post['date'])}</span>
                </span>
                <div class="tags">{tags_html}</div>
            </div>
        </header>
        <div class="post-body">{body_html}</div>
    </div>
</article>
"""
    return _layout(content, title=post["title"], is_post=True)


def about_page() -> str:
    content = f"""
<div class="container reading">
    <h1>About</h1>
    <p>Senior Backend Engineer with 7+ years building mission-critical financial
       systems at <strong>JPMorgan Chase</strong>. Architect and lead for microservices
       processing millions of daily transactions at 99.9% uptime.</p>
    <p>Specialized in distributed architecture, event-driven systems, enterprise APIs,
       and AI Agents.</p>
    <h2>Stack</h2>
    <p>Java Spring Boot · Spring WebFlux · Kafka · PostgreSQL · Python · FastAPI ·
       Next.js · ChromaDB · Ollama</p>
    <h2>Contact</h2>
    <p>
        <a href="mailto:{AUTHOR_EMAIL}">Email</a> ·
        <a href="{AUTHOR_LINKEDIN}" target="_blank" rel="noopener">LinkedIn</a>
    </p>
</div>
"""
    return _layout(content)


def portfolio_page() -> str:
    projects = [
        ("AI-Powered Financial Advisory", "In progress", "2026",
         "RAG pipeline with ChromaDB and Ollama for document analysis."),
        ("Multi-Country Payment System", "Production", "2024–2025",
         "Spring WebFlux microservices with Kafka and outbox pattern."),
        ("Outbox & Inbox Pattern", "Paper", "2026",
         "Academic paper on Transactional Outbox/Inbox patterns."),
        ("Risk Metrics MCP Server", "Open source", "2026",
         "MCP server exposing VaR, CVaR, Sharpe, Sortino calculations."),
    ]
    items = "".join(
        f'<div class="project">'
        f'<h3>{escape(name)}</h3>'
        f'<span class="meta">{year} · {escape(status)}</span>'
        f'<p>{escape(desc)}</p>'
        f'</div>'
        for name, status, year, desc in projects
    )
    content = f"""
<div class="container reading">
    <h1>Projects</h1>
    <div class="projects">{items}</div>
</div>
"""
    return _layout(content)
