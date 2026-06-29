"""FastAPI server entry point."""
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles

from app.cache import (
    list_render_cache,
    md_render_cache,
    page_render_cache,
    svg_memory_cache,
)
from app.config import STATIC_DIR
from app.feeds import generate_rss, generate_sitemap
from app.templates import (
    about_page,
    blog_index_page,
    blog_post_page,
    home_page,
    portfolio_page,
)


app = FastAPI(title="The Pipeline Blog")


# Static files (CSS, JS, cached diagrams)
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# === Pages ===

@app.get("/", response_class=HTMLResponse)
async def home():
    return home_page()


@app.get("/blog", response_class=HTMLResponse)
async def blog_index():
    return blog_index_page()


@app.get("/blog/{slug}", response_class=HTMLResponse)
async def blog_post(slug: str):
    page = blog_post_page(slug)
    if page is None:
        raise HTTPException(status_code=404)
    return page


@app.get("/about", response_class=HTMLResponse)
async def about():
    return about_page()


@app.get("/portfolio", response_class=HTMLResponse)
async def portfolio():
    return portfolio_page()


# === Feeds ===

@app.get("/rss.xml", response_class=PlainTextResponse)
async def rss():
    cache_key = "xml:rss"
    cached = list_render_cache.get(cache_key)
    if cached is not None:
        return cached
    body = generate_rss()
    list_render_cache.set(cache_key, body)
    return body


@app.get("/sitemap.xml", response_class=PlainTextResponse)
async def sitemap():
    cache_key = "xml:sitemap"
    cached = list_render_cache.get(cache_key)
    if cached is not None:
        return cached
    body = generate_sitemap()
    list_render_cache.set(cache_key, body)
    return body


# === Health check ===

@app.get("/health")
async def health():
    return {"status": "ok"}


# === Cache observability ===

@app.get("/api/cache/stats")
async def cache_stats():
    return {
        "md_compile": md_render_cache.stats(),
        "pages": page_render_cache.stats(),
        "lists": list_render_cache.stats(),
        "diagrams_memory": svg_memory_cache.stats(),
    }


@app.post("/api/cache/invalidate")
async def cache_invalidate():
    md_render_cache.invalidate()
    page_render_cache.invalidate()
    list_render_cache.invalidate()
    svg_memory_cache.invalidate()
    return {"ok": True}
