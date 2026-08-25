"""Telegram presentation for the celebrity-news project."""

from html import escape

from generation.text import fit_text_to_html_limit


MESSAGE_LIMIT = 4000
PHOTO_CAPTION_LIMIT = 1000
SUMMARY_PARAGRAPH_LIMIT = 3
MIN_PARAGRAPH_LENGTH = 40

TECHNICAL_PREFIXES = (
    "фото:",
    "фото,",
    "фото и видео:",
    "фото / видео:",
    "видео:",
    "источник фото",
    "автор фото",
    "на фото:",
    "кадр из",
    "скриншот",
    "иллюстрация:",
    "реклама",
    "читайте также",
)
PHOTO_CREDIT_MARKERS = ("фото:", "фото, видео:", "фото и видео:")
PHOTO_CREDIT_SOURCES = (
    "соцсет",
    "личный архив",
    "пресс-служб",
    "starhit",
    "legion-media",
    "globallook",
)


def format_post(news_item):
    """Build one HTML-safe text message."""

    return _format(news_item, MESSAGE_LIMIT)


def format_photo_caption(news_item):
    """Build one shorter HTML-safe photo caption."""

    return _format(news_item, PHOTO_CAPTION_LIMIT)


def _format(news_item, limit):
    source_text = " ".join(
        str(news_item.get("source") or "Источник").split()
    )
    source = escape(source_text)
    url = escape(str(news_item.get("url") or ""), quote=True)
    link = (
        f'🔗 <a href="{url}">Читать источник</a>'
        if url
        else "🔗 Читать источник"
    )
    footer = f"📰 {source}\n{link}"

    title_budget = max(
        0,
        limit - len(footer) - len("🔥 <b></b>") - 4,
    )
    title_text = fit_text_to_html_limit(
        str(news_item.get("title") or "Без заголовка"),
        min(500, title_budget),
    )
    header = f"🔥 <b>{escape(title_text)}</b>"

    fixed_length = len(header) + len(footer) + 4
    article_text = str(news_item.get("article_text") or "")
    body = (
        article_text
        if article_text.strip()
        else str(news_item.get("description") or "")
    )
    summary = _extract_summary(
        body,
        news_item.get("title", ""),
    )
    summary = fit_text_to_html_limit(
        summary,
        max(0, limit - fixed_length),
    )

    if summary:
        return f"{header}\n\n{escape(summary)}\n\n{footer}"

    return f"{header}\n\n{footer}"


def _extract_summary(text, title):
    """Select the first useful source paragraphs without photo credits."""

    title_text = " ".join(str(title or "").split()).casefold()
    useful = []
    fallback = []

    for raw_paragraph in str(text or "").splitlines():
        paragraph = " ".join(raw_paragraph.split())

        if not paragraph or _is_technical_paragraph(paragraph):
            continue
        if paragraph.casefold() == title_text:
            continue

        fallback.append(paragraph)
        is_quote = paragraph.startswith(("«", '"', "“"))

        if len(paragraph) < MIN_PARAGRAPH_LENGTH and not is_quote:
            continue

        useful.append(paragraph)
        if len(useful) == SUMMARY_PARAGRAPH_LIMIT:
            break

    selected = useful or fallback[:SUMMARY_PARAGRAPH_LIMIT]
    return "\n\n".join(selected)


def _is_technical_paragraph(paragraph):
    normalized = paragraph.casefold()

    if normalized.startswith(TECHNICAL_PREFIXES):
        return True

    # Some photo credits start with a person's name and end with the source.
    return (
        len(paragraph) <= 180
        and any(marker in normalized for marker in PHOTO_CREDIT_MARKERS)
        and any(source in normalized for source in PHOTO_CREDIT_SOURCES)
    )
