"""RSS feed and sitemap generation."""
from datetime import datetime
from html import escape

from app.config import AUTHOR_NAME, SITE_DESCRIPTION, SITE_TITLE, SITE_URL
from app.content import get_all_posts


def generate_rss() -> str:
    posts = get_all_posts()
    items = "\n".join(
        f"""
    <item>
        <title><![CDATA[{post['title']}]]></title>
        <link>{SITE_URL}/blog/{post['slug']}</link>
        <guid>{SITE_URL}/blog/{post['slug']}</guid>
        <description><![CDATA[{post['description']}]]></description>
        <pubDate>{_format_pub_date(post['date'])}</pubDate>
        <author>{escape(AUTHOR_NAME)}</author>
        {chr(10).join(f'<category>{escape(t)}</category>' for t in post['tags'])}
    </item>"""
        for post in posts
    )

    last_build = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S +0000")

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
    <channel>
        <title>{escape(SITE_TITLE)}</title>
        <link>{SITE_URL}</link>
        <description>{escape(SITE_DESCRIPTION)}</description>
        <atom:link href="{SITE_URL}/rss.xml" rel="self" type="application/rss+xml"/>
        <lastBuildDate>{last_build}</lastBuildDate>
        {items}
    </channel>
</rss>"""


def generate_sitemap() -> str:
    posts = get_all_posts()
    static_urls = [
        ("/", "1.0", "weekly"),
        ("/blog", "0.9", "weekly"),
        ("/portfolio", "0.7", "monthly"),
        ("/about", "0.6", "monthly"),
    ]
    post_urls = [
        (f"/blog/{post['slug']}", "0.8", "monthly") for post in posts
    ]
    urls = "\n".join(
        f'  <url><loc>{SITE_URL}{path}</loc>'
        f'<changefreq>{freq}</changefreq><priority>{prio}</priority></url>'
        for path, prio, freq in static_urls + post_urls
    )

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{urls}
</urlset>"""


def _format_pub_date(date_str: str) -> str:
    if not date_str:
        return ""
    try:
        dt = datetime.fromisoformat(date_str)
        return dt.strftime("%a, %d %b %Y %H:%M:%S +0000")
    except (ValueError, TypeError):
        return ""
