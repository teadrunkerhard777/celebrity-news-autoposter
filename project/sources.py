"""Declarative sources and optional source-specific article hooks."""

from datetime import datetime, timedelta, timezone


now = datetime.now(timezone.utc)

# The local source makes the template demonstrable without network access.
"""Declarative sources and optional source-specific article hooks."""


SOURCES = [
    {
        "name": "StarHit",
        "type": "rss",
        "url": "https://www.starhit.ru/rss-feeds/yanews-webmaster.xml",
        "enabled": True,
    },
    {
        "name": "Super",
        "type": "html",
        "url": "https://super.ru/celebrity-news",
        "base_url": "https://super.ru",
        "item_selector": 'a[href^="/celebrity-news/"]',
        "title_selector": "div[class*='styles_text__']",
        "link_from_item": True,
        "date_selector": "time[datetime]",
        "enabled": True,
        "limit": 20,
        "headers": {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/151.0.0.0 Safari/537.36"
            )
        },
        "retries": 3,
    },
]

# A project can register a reliable body extractor without changing core code.
SOURCE_EXTRACTORS = {}
SOURCE_STOP_MARKERS = {
    "Super": ("Читайте также:",),
}
