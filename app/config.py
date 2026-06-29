"""Application constants and config."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
CONTENT_DIR = BASE_DIR / "content" / "posts"
STATIC_DIR = BASE_DIR / "app" / "static"

SITE_URL = os.environ.get("SITE_URL", "https://thepipeline.dev")
SITE_TITLE = os.environ.get("SITE_TITLE", "The Pipeline")
SITE_DESCRIPTION = os.environ.get(
    "SITE_DESCRIPTION",
    "Articles on distributed architecture, financial systems, and AI engineering.",
)
AUTHOR_NAME = os.environ.get("AUTHOR_NAME", "Manuel Tobón")
AUTHOR_INITIALS = "".join(n[0] for n in AUTHOR_NAME.split())
AUTHOR_EMAIL = os.environ.get("AUTHOR_EMAIL", "manuelpope@gmail.com")
AUTHOR_LINKEDIN = os.environ.get(
    "AUTHOR_LINKEDIN",
    "https://linkedin.com/in/manuel-andres-tobon-bayona-een",
)

POSTS_PER_PAGE = int(os.environ.get("POSTS_PER_PAGE", "20"))
