"""Celebrity-news relevance rules and event categorization."""


TOPIC_KEYWORDS = {
    "legal_trouble": (
        "задержан",
        "задержали",
        "арестован",
        "арестовали",
        "уголовн",
        "административн",
        "приговор",
        "подал в суд",
        "подала в суд",
        "судится",
        "судебн",
        "иск к",
        "штраф",
        "полиция",
        "прокуратур",
    ),
    "incidents": (
        "дтп",
        "авари",
        "напал",
        "напала",
        "избил",
        "избила",
        "пострадал",
        "пострадала",
        "госпитализ",
        "ограб",
        "пожар",
        "пропал без вести",
        "пропала без вести",
        "несчастный случай",
    ),
    "relationships": (
        "расстались",
        "расставани",
        "развод",
        "развелся",
        "развелась",
        "изменил",
        "изменила",
        "измена",
        "любовниц",
        "любовник",
        "новый роман",
        "тайный роман",
        "подтвердил отношения",
        "подтвердила отношения",
        "воссоединились",
    ),
    "money_property": (
        "наследств",
        "алимент",
        "раздел имущества",
        "делят имущество",
        "делит имущество",
        "отсудил",
        "отсудила",
        "лишился квартиры",
        "лишилась квартиры",
        "лишился дома",
        "лишилась дома",
        "долг в",
        "долги на",
        "банкрот",
        "мошеннич",
    ),
    "scandals_conflicts": (
        "скандал",
        "конфликт",
        "публичная ссора",
        "публичные разборки",
        "разругались",
        "поссорил",
        "враждуют",
        "обвинил в",
        "обвинила в",
        "оскорбил",
        "оскорбила",
        "устроил разборки",
        "устроила разборки",
    ),
    "public_statements": (
        "громкое заявление",
        "сделал признание",
        "сделала признание",
        "признался в",
        "призналась в",
        "ответил на обвинения",
        "ответила на обвинения",
        "раскрыл правду",
        "раскрыла правду",
        "нарушил молчание",
        "нарушила молчание",
    ),
    "unusual_behavior": (
        "необычный поступок",
        "эпатажн",
        "шокировал поступком",
        "шокировала поступком",
        "устроил дебош",
        "устроила дебош",
        "вышел голым",
        "вышла голой",
    ),
}


def is_relevant(news_item):
    """Accept celebrity stories containing at least one notable event signal."""

    text = (
        f"{news_item.get('title', '')} "
        f"{news_item.get('description', '')}"
    ).casefold()
    # Word stems intentionally cover common Russian inflections for this baseline.
    matched_topics = [
        topic
        for topic, keywords in TOPIC_KEYWORDS.items()
        if any(keyword in text for keyword in keywords)
    ]

    # The first (most specific) match is used by generic event deduplication.
    news_item["matched_topics"] = matched_topics
    news_item["event_category"] = matched_topics[0] if matched_topics else None
    news_item.setdefault("event_locations", [])
    return bool(matched_topics)
