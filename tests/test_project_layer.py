from datetime import datetime, timezone

from article.fetcher import clean_article_text
from processing.filters import (
    add_scores,
    filter_by_minimum_score,
    filter_relevant,
)
from project.filters import is_relevant
from project.formatter import format_photo_caption, format_post
from project.scoring import calculate_score
from project.sources import SOURCE_STOP_MARKERS


def item(title, description=""):
    return {
        "title": title,
        "description": description,
        "url": "https://example.test/item",
        "source": "Example",
        "published_at": datetime(2026, 1, 2, tzinfo=timezone.utc),
    }


def test_project_filter_accepts_celebrity_event_and_rejects_lifestyle_news():
    accepted = item("Певица рассказала о разводе после измены")
    rejected = item("Певица показала новый образ для фотосессии")

    assert filter_relevant([accepted, rejected], is_relevant) == [accepted]
    assert accepted["matched_topics"] == ["relationships"]
    assert accepted["event_category"] == "relationships"
    assert rejected["matched_topics"] == []


def test_project_scoring_is_applied_by_generic_core():
    strong = item("Актриса подала в суд после обвинений в конфликте")
    weak = item("Актер попал в аварию")
    non_celebrity_crime = item("После суда задержали мужа с любовницей")
    news = [strong, weak, non_celebrity_crime]

    for news_item in news:
        is_relevant(news_item)
    add_scores(news, calculate_score)

    assert strong["score"] > weak["score"]
    assert non_celebrity_crime["score"] == 3
    assert filter_by_minimum_score(news, 4) == [strong]


def test_formatter_extracts_article_paragraphs_and_keeps_source_footer():
    news = item(
        "Звезда <ответила> бывшему мужу",
        "Короткое RSS-описание не должно использоваться.",
    )
    news["source"] = "StarHit"
    news["article_text"] = """Фото, видео: соцсети

Актриса публично ответила бывшему мужу & рассказала о конфликте.

Анна Иванова Фото: личный архив

«Я больше не намерена молчать», — заявила артистка журналистам.

По словам близких, спор начался несколько недель назад и стал публичным.

Четвертый содержательный абзац не должен попасть в короткую выжимку.
"""

    post = format_post(news)

    assert "Звезда &lt;ответила&gt; бывшему мужу" in post
    assert "ответила бывшему мужу &amp; рассказала" in post
    assert "Короткое RSS-описание" not in post
    assert "Фото, видео" not in post
    assert "Фото: личный архив" not in post
    assert "Четвертый содержательный абзац" not in post
    assert "📰 StarHit" in post
    assert "Читать источник" in post
    assert 'href="https://example.test/item"' in post


def test_photo_caption_stays_inside_safe_limit():
    news = item("Громкий конфликт двух артистов")
    news["source"] = "StarHit"
    first = (
        "Первый абзац: "
        + "важный <факт> & подтвержденный контекст. " * 6
        + "Первый абзац завершен."
    )
    second = (
        "Второй абзац: "
        + "дополнительная важная подробность события. " * 5
        + "Второй абзац завершен."
    )
    long_third = (
        "Третий длинный абзац: "
        + "эта часть не должна обрезаться посередине мысли. " * 20
    )
    news["article_text"] = "\n\n".join((first, second, long_third))

    caption = format_photo_caption(news)

    assert len(caption) <= 1000
    assert "Первый абзац завершен." in caption
    assert "Второй абзац завершен." in caption
    assert "Третий длинный абзац:" not in caption
    assert "важный &lt;факт&gt; &amp; подтвержденный контекст" in caption
    assert "…" not in caption
    assert "Читать источник" in caption


def test_photo_caption_adds_short_third_paragraph_when_it_fits():
    news = item("Артисты рассказали о завершившемся конфликте")
    news["source"] = "Super"
    news["article_text"] = """Первый абзац содержит основную подтвержденную информацию о событии.

Второй абзац добавляет важный контекст и объясняет позицию участников.

Третий короткий абзац содержит заключительный существенный факт.
"""

    caption = format_photo_caption(news)

    assert "Первый абзац содержит" in caption
    assert "Второй абзац добавляет" in caption
    assert "Третий короткий абзац содержит" in caption
    assert len(caption) <= 1000


def test_formatter_falls_back_to_description_without_article_text():
    news = item("Певица сделала заявление", "Описание события из RSS & ленты.")
    news["source"] = "StarHit"
    news["article_text"] = "   "

    caption = format_photo_caption(news)

    assert "Описание события из RSS &amp; ленты." in caption


def test_formatter_skips_exact_title_repeat():
    title = "Певица рассказала о причинах громкого развода"
    news = item(title)
    news["source"] = "Super"
    news["article_text"] = f"""{title}

Близкие пары объяснили, что конфликт продолжался несколько месяцев.
"""

    caption = format_photo_caption(news)

    assert caption.count(title) == 1
    assert "конфликт продолжался несколько месяцев" in caption


def test_formatter_skips_short_intro_similar_to_title():
    news = item(
        "Отар Кушанашвили резко осудил тех, кто выступает за отмену концерта Канье Уэста"
    )
    news["source"] = "Super"
    news["article_text"] = """Отар Кушанашвили раскритиковал выступивших за отмену концерта Канье Уэста

Журналист объяснил свою позицию и рассказал, почему не поддерживает запрет.
"""

    caption = format_photo_caption(news)

    assert "раскритиковал выступивших" not in caption
    assert "Журналист объяснил свою позицию" in caption
    assert len(caption) <= 1000


def test_formatter_keeps_distinct_first_article_paragraph():
    news = item("Актриса объявила о разводе после десяти лет брака")
    news["source"] = "Super"
    news["article_text"] = (
        "По словам адвоката, документы были поданы в суд еще на прошлой неделе."
    )

    caption = format_photo_caption(news)

    assert "По словам адвоката, документы были поданы" in caption


def test_super_stop_marker_removes_read_more_block():
    text = """Первый содержательный абзац.

Читайте также: другие новости о звездах

Этот текст после маркера не должен сохраниться.
"""

    cleaned = clean_article_text(
        text,
        source="Super",
        source_stop_markers=SOURCE_STOP_MARKERS,
    )

    assert cleaned == "Первый содержательный абзац."
