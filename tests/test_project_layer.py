from datetime import datetime, timezone

from processing.filters import (
    add_scores,
    filter_by_minimum_score,
    filter_relevant,
)
from project.filters import is_relevant
from project.formatter import format_photo_caption, format_post
from project.scoring import calculate_score


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


def test_formatter_escapes_html_and_keeps_project_footer():
    news = item("Python <release>", "Safer & faster")
    news["matched_topics"] = ["python"]

    post = format_post(news)

    assert "Python &lt;release&gt;" in post
    assert "Safer &amp; faster" in post
    assert "#python" in post
    assert 'href="https://example.test/item"' in post


def test_photo_caption_stays_inside_safe_limit():
    news = item("Python release", "word " * 1000)
    news["matched_topics"] = ["python"]

    assert len(format_photo_caption(news)) <= 1000
