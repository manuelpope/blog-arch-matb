"""Server-side Mermaid renderer using Playwright headless Chromium."""
import asyncio
import hashlib
from playwright.async_api import async_playwright
from app.cache import svg_memory_cache

DARK_VARS = {
    "primaryColor": "#27272a",
    "primaryTextColor": "#fafafa",
    "primaryBorderColor": "#3f3f46",
    "lineColor": "#a1a1aa",
    "secondaryColor": "#1f1f23",
    "tertiaryColor": "#1a1a1a",
    "fontFamily": "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
    "fontSize": "14px",
}

LIGHT_VARS = {
    "primaryColor": "#f4f4f5",
    "primaryTextColor": "#1a1a1a",
    "primaryBorderColor": "#d4d4d8",
    "lineColor": "#71717a",
    "secondaryColor": "#f4f4f5",
    "tertiaryColor": "#fafafa",
    "fontFamily": "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
    "fontSize": "14px",
}


async def render_svg(mermaid_code: str, theme: str = "dark") -> str:
    """Render Mermaid to SVG using headless Chromium. Cached in memory by code hash."""
    cache_key = hashlib.md5(f"{theme}:{mermaid_code}".encode()).hexdigest()
    cached = svg_memory_cache.get(cache_key)
    if cached is not None:
        return cached

    theme_vars = DARK_VARS if theme == "dark" else LIGHT_VARS
    mermaid_theme = "dark" if theme == "dark" else "neutral"
    bg = "#0f0f0f" if theme == "dark" else "#ffffff"

    # Build the JS theme variables string
    vars_json = "{\n"
    for k, v in theme_vars.items():
        vars_json += f'      {k}: "{v}",\n'
    vars_json += "    }"

    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<script src="https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js"></script>
<style>body {{ margin: 0; padding: 20px; background: {bg}; }}</style>
</head><body>
<pre class="mermaid">{mermaid_code}</pre>
<script>
  mermaid.initialize({{
    startOnLoad: true,
    theme: '{mermaid_theme}',
    securityLevel: 'loose',
    themeVariables: {vars_json}
  }});
</script>
</body></html>"""

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1400, "height": 900})
        await page.set_content(html)
        await page.wait_for_timeout(2000)
        result = await page.evaluate("""
            () => {
              const svg = document.querySelector('.mermaid svg');
              const error = document.querySelector('.mermaid .error-icon, .mermaid-error, [class*="error"]');
              if (error || (svg && svg.getAttribute('aria-roledescription') === 'error')) {
                const text = error ? error.textContent : 'Syntax error';
                return { error: text };
              }
              if (!svg) return { error: 'No SVG rendered' };
              return { svg: new XMLSerializer().serializeToString(svg) };
            }
        """)
        await browser.close()

    if "error" in result:
        return f'<pre class="mermaid-error">{mermaid_code}</pre>'

    svg = result["svg"]
    svg_memory_cache.set(cache_key, svg)
    return svg


def render_svg_sync(mermaid_code: str, theme: str = "dark") -> str:
    """Synchronous wrapper for render_svg."""
    return asyncio.run(render_svg(mermaid_code, theme))
