from datetime import datetime, timezone

from project.settings import EVENT_DEDUP_SETTINGS
from storage.history import add_to_history, is_published, load_history, save_history


def news(url="https://example.test/story"):
    return {
        "title": "Python package release",
        "url": url,
        "source": "Example",
        "published_at": datetime(2026, 1, 1, tzinfo=timezone.utc),
        "description": "package release testing runner plugin benchmark community",
        "event_category": "python",
    }


def test_empty_history_round_trip(tmp_path):
    path = tmp_path / "published.json"
    save_history([], path)
    assert load_history(path) == []


def test_new_history_entry_contains_compact_fingerprint():
    history = []
    add_to_history(news(), history)

    assert history[0]["event_fingerprint"]["categories"] == ["python"]
    assert "article_text" not in history[0]


def test_legacy_history_without_fingerprint_remains_url_compatible():
    item = news()
    assert is_published(item, [{"url": item["url"]}]) is True
    assert is_published(item, [{"url": "https://other.test"}]) is False


def celebrity_news(title, source, category, url):
    return {
        "title": title,
        "url": url,
        "source": source,
        "published_at": datetime(2026, 8, 26, 8, 0, tzinfo=timezone.utc),
        "description": "",
        "event_category": category,
        "event_locations": [],
    }


def test_same_person_death_variants_are_duplicate_across_runs():
    published = celebrity_news(
        "Скончалась Долли Партон",
        "Woman.ru",
        "incidents",
        "https://woman.test/death",
    )
    candidate = celebrity_news(
        "Известна причина смерти Долли Партон",
        "7Дней.ru",
        "incidents",
        "https://7days.test/death-cause",
    )
    history = []
    add_to_history(published, history, EVENT_DEDUP_SETTINGS)

    assert history[0]["event_fingerprint"]["terminal_event"] == "death"
    assert history[0]["event_fingerprint"]["terminal_entities"] == [
        "долли",
        "партон",
    ]
    assert is_published(candidate, history, EVENT_DEDUP_SETTINGS) is True


def test_death_and_inheritance_are_distinct_history_events():
    published = celebrity_news(
        "Скончалась Долли Партон",
        "Woman.ru",
        "incidents",
        "https://woman.test/death",
    )
    inheritance = celebrity_news(
        "Стало известно, кому достанется наследство Долли Партон",
        "7Дней.ru",
        "money_property",
        "https://7days.test/inheritance",
    )
    history = []
    add_to_history(published, history, EVENT_DEDUP_SETTINGS)

    assert is_published(inheritance, history, EVENT_DEDUP_SETTINGS) is False


def test_same_divorce_with_different_titles_is_duplicate():
    published = celebrity_news(
        "Актриса Анна Иванова объявила о разводе",
        "StarHit",
        "relationships",
        "https://starhit.test/divorce",
    )
    candidate = celebrity_news(
        "Анна Иванова развелась с мужем после десяти лет брака",
        "StarHit",
        "relationships",
        "https://starhit.test/divorce-details",
    )
    history = []
    add_to_history(published, history, EVENT_DEDUP_SETTINGS)

    assert is_published(candidate, history, EVENT_DEDUP_SETTINGS) is True


def test_same_terminal_event_for_different_people_is_not_duplicate():
    published = celebrity_news(
        "Скончалась актриса Анна Иванова",
        "StarHit",
        "incidents",
        "https://starhit.test/anna",
    )
    candidate = celebrity_news(
        "Умерла певица Мария Петрова",
        "Woman.ru",
        "incidents",
        "https://woman.test/maria",
    )
    history = []
    add_to_history(published, history, EVENT_DEDUP_SETTINGS)

    assert is_published(candidate, history, EVENT_DEDUP_SETTINGS) is False
