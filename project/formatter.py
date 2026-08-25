"""Telegram presentation for the celebrity-news project."""

import re
from html import escape

from generation.text import fit_text_to_html_limit


MESSAGE_LIMIT = 4000
PHOTO_CAPTION_LIMIT = 1000
SUMMARY_PARAGRAPH_LIMIT = 3
MIN_PARAGRAPH_LENGTH = 40
DUPLICATE_INTRO_MAX_LENGTH = 220
DUPLICATE_INTRO_MIN_SHARED_WORDS = 5
DUPLICATE_INTRO_OVERLAP = 0.70
BRAND_HASHTAG = "#ЗвёздныеБудни"

EDITORIAL_HASHTAGS = {
    "scandals_conflicts": (
        "#ЗвёздныеРазборки",
        "#ГромкийСкандал",
    ),
    "relationships": (
        "#ЛюбовьИДрама",
        "#ЗвёздныйРоман",
    ),
    "legal_trouble": (
        "#СудИДрама",
        "#ЗвёздныйСуд",
    ),
    "money_property": (
        "#ДеньгиЗвёзд",
        "#НаследствоИДрама",
    ),
    "public_statements": (
        "#ЖёсткоеЗаявление",
        "#СказаноГромко",
    ),
    "unusual_behavior": (
        "#НеожиданныйПоворот",
        "#ВсеОбсуждают",
    ),
    "incidents": (
        "#ГромкоеСобытие",
        "#ЧтоПроизошло",
    ),
}

HASHTAG_CATEGORY_PRIORITY = (
    "scandals_conflicts",
    "legal_trouble",
    "relationships",
    "unusual_behavior",
    "money_property",
    "public_statements",
    "incidents",
)

WORD_PATTERN = re.compile(r"[0-9a-zа-яё]+", re.IGNORECASE)
TITLE_STOP_WORDS = {
    "без",
    "был",
    "была",
    "для",
    "его",
    "как",
    "кто",
    "она",
    "они",
    "что",
    "это",
}

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

    return _format(news_item, MESSAGE_LIMIT, complete_paragraphs=False)


def format_photo_caption(news_item):
    """Build one shorter HTML-safe photo caption."""

    return _format(news_item, PHOTO_CAPTION_LIMIT, complete_paragraphs=True)


def _format(news_item, limit, complete_paragraphs):
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
    hashtags = " ".join(_editorial_hashtags(news_item))
    footer = f"{hashtags}\n\n📰 {source}\n{link}"

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
    body_budget = max(0, limit - fixed_length)

    if complete_paragraphs:
        summary = _fit_complete_paragraphs(summary, body_budget)
    else:
        summary = fit_text_to_html_limit(summary, body_budget)

    if summary:
        return f"{header}\n\n{escape(summary)}\n\n{footer}"

    return f"{header}\n\n{footer}"


def _editorial_hashtags(news_item):
    """Return the channel tag plus up to two strongest editorial tags."""

    topics = news_item.get("matched_topics") or []
    if isinstance(topics, str):
        topics = [topics]

    categories = set(topics)
    event_category = news_item.get("event_category")
    if event_category:
        categories.add(event_category)

    ordered = [
        category
        for category in HASHTAG_CATEGORY_PRIORITY
        if category in categories
    ]

    if len(ordered) == 1:
        thematic = EDITORIAL_HASHTAGS[ordered[0]]
    else:
        thematic = tuple(
            EDITORIAL_HASHTAGS[category][0]
            for category in ordered[:2]
        )

    # Preserve editorial order while protecting against repeated mappings.
    return list(dict.fromkeys((BRAND_HASHTAG, *thematic)))


def _fit_complete_paragraphs(summary, max_escaped_length):
    """Keep whole paragraphs in order until the next one would overflow."""

    selected = []

    for paragraph in summary.split("\n\n"):
        candidate = "\n\n".join((*selected, paragraph))

        if len(escape(candidate)) > max_escaped_length:
            break

        selected.append(paragraph)

    return "\n\n".join(selected)


def _extract_summary(text, title):
    """Select the first useful source paragraphs without photo credits."""

    title_text = " ".join(str(title or "").split()).casefold()
    useful = []
    fallback = []
    intro_checked = False

    for raw_paragraph in str(text or "").splitlines():
        paragraph = " ".join(raw_paragraph.split())

        if not paragraph or _is_technical_paragraph(paragraph):
            continue
        if paragraph.casefold() == title_text:
            continue

        is_quote = paragraph.startswith(("«", '"', "“"))

        if not intro_checked and _is_title_like_intro(paragraph, title_text):
            intro_checked = True
            continue

        if len(paragraph) < MIN_PARAGRAPH_LENGTH and not is_quote:
            fallback.append(paragraph)
            continue

        if not intro_checked:
            intro_checked = True

        useful.append(paragraph)
        if len(useful) == SUMMARY_PARAGRAPH_LIMIT:
            break

    selected = useful or fallback[:SUMMARY_PARAGRAPH_LIMIT]
    return "\n\n".join(selected)


def _is_title_like_intro(paragraph, title):
    """Return true for a short first paragraph that mostly repeats the title."""

    if len(paragraph) > DUPLICATE_INTRO_MAX_LENGTH:
        return False

    title_words = _meaningful_words(title)
    paragraph_words = _meaningful_words(paragraph)
    shared_words = title_words & paragraph_words
    shorter_size = min(len(title_words), len(paragraph_words))

    return (
        len(shared_words) >= DUPLICATE_INTRO_MIN_SHARED_WORDS
        and shorter_size > 0
        and len(shared_words) / shorter_size >= DUPLICATE_INTRO_OVERLAP
    )


def _meaningful_words(text):
    return {
        word.casefold()
        for word in WORD_PATTERN.findall(str(text or ""))
        if len(word) > 2 and word.casefold() not in TITLE_STOP_WORDS
    }


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
