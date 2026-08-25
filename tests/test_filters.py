import pytest

from project.filters import is_relevant


@pytest.mark.parametrize(
    ("title", "expected_topic"),
    (
        (
            "Милана Некрасова назвала свои главные «ред-флаги» в парнях",
            "relationships",
        ),
        (
            "Агата Муцениеце отметила первую годовщину свадьбы с Петром Дрангой",
            "relationships",
        ),
        (
            "Приянка Чопра раскрыла, на чём держится её брак с Ником Джонасом",
            "relationships",
        ),
        (
            "Адвокат рассказала, как Елена Блиновская отметит 45-летие в колонии",
            "legal_trouble",
        ),
        (
            "Отар Кушанашвили резко осудил тех, кто выступает за отмену концерта",
            "scandals_conflicts",
        ),
        (
            "Маша Миногарова наступила на разбитый бокал: страшнейшее ранение",
            "incidents",
        ),
        (
            "Илана Дылдина вышла на связь: «Лети на небо, наш ангел»",
            "incidents",
        ),
    ),
)
def test_filter_accepts_neutral_celebrity_vocabulary(title, expected_topic):
    news_item = {"title": title, "description": ""}

    assert is_relevant(news_item)
    assert expected_topic in news_item["matched_topics"]
    assert news_item["event_category"] == expected_topic
    assert news_item["event_locations"] == []


def test_filter_rejects_broad_entertainment_phrases_without_event():
    news_item = {
        "title": "Актер рассказал подробности нового концерта",
        "description": "Стало известно расписание выступлений.",
    }

    assert not is_relevant(news_item)
    assert news_item["matched_topics"] == []
