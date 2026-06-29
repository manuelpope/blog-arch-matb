"""Markdown → HTML compiler.

Two layers:
  - render_markdown(md, slug)  — cache-keyed wrapper
  - _compile_markdown(md)      — the actual work (regex + Mermaid render)

The wrapper hashes the source so edits invalidate automatically;
the inner function is pure (no cache) so it's easy to test.
"""
import hashlib
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from html import escape as _html_escape

from app.cache import md_render_cache
from app.config import AUTHOR_NAME, SITE_TITLE
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name

# === Inner: the actual compile ===

def _compile_markdown(md: str) -> str:
    code_blocks: list[dict] = []

    def save_code_block(match: re.Match) -> str:
        lang = match.group(1) or "text"
        code = match.group(2)
        idx = len(code_blocks)
        code_blocks.append({"lang": lang, "code": code})
        return f"\n\n§§§CODE_BLOCK_{idx}§§§\n\n"

    md = re.sub(r"```(\w*)\n(.*?)```", save_code_block, md, flags=re.DOTALL)

    # Render all Mermaid diagrams in parallel
    rendered_svg = _render_mermaid_diagrams(code_blocks)

    # Walk placeholders, compile surrounding text, splice diagrams
    parts = re.split(r"(§§§CODE_BLOCK_\d+§§§)", md)
    out: list[str] = []
    for part in parts:
        if part.startswith("§§§CODE_BLOCK_"):
            idx = int(re.search(r"\d+", part).group())
            out.append(_render_code_block(code_blocks[idx], rendered_svg.get(idx)))
        else:
            out.append(_compile_text(part))
    return "".join(out)


def _render_code_block(block: dict, svg: str | None) -> str:
    if block["lang"] == "mermaid":
        if svg:
            return (
                f'<figure class="mermaid-figure">'
                f'<div class="mermaid-diagram">{svg}</div>'
                f'<figcaption class="mermaid-caption">📊 Click to zoom</figcaption>'
                f'</figure>'
            )
        # Fallback: client-side rendering when Chromium is unavailable
        code_escaped = _html_escape(block["code"])
        return (
            f'<figure class="mermaid-figure">'
            f'<div class="mermaid-diagram" data-fallback="true">'
            f'<pre class="mermaid">{code_escaped}</pre>'
            f'</div></figure>'
        )

    formatter = HtmlFormatter()
    try:
        lexer = get_lexer_by_name(block["lang"])
    except Exception:
        lexer = get_lexer_by_name("text")
    highlighted = highlight(block["code"], lexer, formatter)
    return f'<div class="code-block">{highlighted}</div>'


def _render_mermaid_diagrams(code_blocks: list[dict]) -> dict[int, str | None]:
    """Render each Mermaid block to SVG (parallel), respecting cache."""
    diagrams = [
        (i, b["code"]) for i, b in enumerate(code_blocks)
        if b["lang"] == "mermaid"
    ]
    if not diagrams:
        return {}

    def render_one(code: str) -> str | None:
        try:
            from mermaid_renderer import render_svg
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                if loop and loop.is_running():
                    with ThreadPoolExecutor() as ex:
                        return ex.submit(asyncio.run, render_svg(code.strip())).result()
            except RuntimeError:
                pass
            return asyncio.run(render_svg(code.strip()))
        except Exception as e:
            print(f"Mermaid render error: {e}")
            return None

    out: dict[int, str | None] = {}
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(render_one, code): (idx, code) for idx, code in diagrams}
        for future in as_completed(futures):
            idx, _ = futures[future]
            out[idx] = future.result()
    return out


def _compile_text(text: str) -> str:
    """Compile plain Markdown text (no code blocks) to HTML."""
    html = text
    html = re.sub(r"^# (.+)$", r"<h1>\1</h1>", html, flags=re.MULTILINE)
    html = re.sub(r"^## (.+)$", r"<h2>\1</h2>", html, flags=re.MULTILINE)
    html = re.sub(r"^### (.+)$", r"<h3>\1</h3>", html, flags=re.MULTILINE)
    html = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", html)
    html = re.sub(r"\*(.+?)\*", r"<em>\1</em>", html)
    html = re.sub(r"\[(.+?)\]\((.+?)\)", r'<a href="\2">\1</a>', html)
    html = re.sub(r"`(.+?)`", r"<code>\1</code>", html)
    html = _render_tables(html)
    html = _render_lists(html)
    paragraphs = html.split("\n\n")
    paragraphs = [
        f"<p>{p.strip()}</p>" if not p.strip().startswith("<") else p
        for p in paragraphs
    ]
    return "\n\n".join(paragraphs)


def _render_tables(html: str) -> str:
    lines = html.split("\n")
    out: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if (
            "|" in line
            and i + 1 < len(lines)
            and re.match(r"^\|?\s*[-:|\s]+\|?\s*$", lines[i + 1].strip())
        ):
            table_lines = [line]
            j = i + 2
            while j < len(lines) and "|" in lines[j]:
                table_lines.append(lines[j])
                j += 1
            out.append(_format_table(table_lines))
            i = j
        else:
            out.append(line)
            i += 1
    return "\n".join(out)


def _format_table(table_lines: list[str]) -> str:
    headers = [c.strip() for c in table_lines[0].split("|") if c.strip()]
    body = "".join(
        "<tr>" + "".join(f"<td>{c.strip()}</td>" for c in row.split("|") if c.strip()) + "</tr>"
        for row in table_lines[1:]
    )
    return (
        "<table>"
        f"<thead><tr>{''.join(f'<th>{h}</th>' for h in headers)}</tr></thead>"
        f"<tbody>{body}</tbody>"
        "</table>"
    )


def _render_lists(html: str) -> str:
    lines = html.split("\n")
    out: list[str] = []
    in_ul = in_ol = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith(("- ", "* ")):
            if not in_ul:
                out.append("<ul>"); in_ul = True
            out.append(f"<li>{stripped[2:]}</li>")
        elif re.match(r"^\d+\.\s", stripped):
            if not in_ol:
                out.append("<ol>"); in_ol = True
            out.append(f"<li>{re.sub(r'^\\d+\\.\\s', '', stripped)}</li>")
        else:
            if in_ul:
                out.append("</ul>"); in_ul = False
            if in_ol:
                out.append("</ol>"); in_ol = False
            out.append(line)
    if in_ul:
        out.append("</ul>")
    if in_ol:
        out.append("</ol>")
    return "\n".join(out)


# === Outer: cache-keyed wrapper ===

def render_markdown(md: str, slug: str | None = None) -> str:
    """Cache-keyed markdown → HTML. Auto-invalidates on content change."""
    content_hash = hashlib.md5(md.encode()).hexdigest()[:12]
    cache_key = f"md:{slug or 'ad-hoc'}:{content_hash}"

    cached = md_render_cache.get(cache_key)
    if cached is not None:
        return cached

    result = _compile_markdown(md)
    md_render_cache.set(cache_key, result)
    return result
