"""Declarative sources and optional source-specific article hooks."""

import re
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
    {
        "name": "Woman.ru",
        "type": "rss",
        "url": "https://www.woman.ru/rss-feeds/rss.xml",
        "enabled": True,
    },
    {
        "name": "7Дней.ru",
        "type": "rss",
        "url": "https://7days.ru/rss/section/stars",
        "enabled": True,
        "retries": 3,
    },
]


MOJIBAKE_UTF8_SEQUENCE = re.compile(
    r"(?:Ð[\x80-\xbf]|Ñ[\x80-\xbf]|Â[\x80-\xbf]|â[\x80-\xbf]{2})"
)


def _repair_7days_text(text):
    """Repair UTF-8 byte sequences decoded as Latin-1, including mixed nodes."""

    def decode_sequence(match):
        return match.group().encode("latin-1").decode("utf-8")

    repaired = MOJIBAKE_UTF8_SEQUENCE.sub(decode_sequence, text)
    return re.sub(r"Â(?=\s|$)", "", repaired)


def extract_7days_article(soup):
    """Extract the article body and repair the site's misreported UTF-8 text."""

    body = soup.select_one("article") or soup.select_one("main") or soup
    paragraphs = []

    for node in body.find_all("p"):
        # Repair control-byte sequences before whitespace normalization drops them.
        repaired = _repair_7days_text(node.get_text(" ", strip=True))
        text = " ".join(repaired.split())

        if not text:
            continue

        paragraphs.append(text)

    return "\n\n".join(paragraphs)


# A project can register a reliable body extractor without changing core code.
SOURCE_EXTRACTORS = {
    "7Дней.ru": extract_7days_article,
}
SOURCE_STOP_MARKERS = {
    "Super": ("Читайте также:",),
    "Woman.ru": ("Фото:",),
    "7Дней.ru": ("Ранее мы писали",),
}
