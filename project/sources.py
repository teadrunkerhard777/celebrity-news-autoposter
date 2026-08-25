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
]

# A project can register a reliable body extractor without changing core code.
SOURCE_EXTRACTORS = {}
SOURCE_STOP_MARKERS = {}

