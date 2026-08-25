"""Celebrity-news scoring rules."""


TOPIC_SCORES = {
    "scandals_conflicts": 5,
    "legal_trouble": 5,
    "relationships": 5,
    "unusual_behavior": 4,
    "money_property": 3,
    "public_statements": 3,
    "incidents": 1,
}

INTEREST_BONUSES = {
    "scandal": (3, ("скандал",)),
    "accusations": (2, ("обвини", "обвинени")),
    "infidelity": (3, ("измена", "измены")),
    "divorce": (3, ("развод",)),
    "abuse": (3, ("абьюз",)),
    "harassment": (3, ("домогател",)),
    "court": (
        2,
        (
            "судебн",
            "в суд",
            "на суде",
            "после суда",
            "решение суда",
            "суд обязал",
            "суд признал",
        ),
    ),
    "detention": (3, ("задержан", "задержали", "задержание")),
    "alimony": (2, ("алимент",)),
    "lover": (2, ("любовни",)),
    "conflict": (2, ("конфликт", "ссор", "разборк")),
    "harsh_criticism": (2, ("разнес", "раскритиков")),
    "insult": (2, ("оскорб",)),
    "threat": (2, ("угрожал", "угрожала", "угроз")),
    "confession": (1, ("признался", "призналась")),
    "truth_reveal": (1, ("раскрыл правду", "раскрыла правду")),
}

LIFESTYLE_PENALTIES = {
    "weight_loss": (2, ("похудел", "похудела", "сбросил вес", "сбросила вес")),
    "figure": (2, ("показал фигуру", "показала фигуру")),
    "new_look": (2, ("новый образ", "новом образе")),
    "plastic_surgery": (2, ("пластика", "ринопластик", "пластическ")),
    "photo_shoot": (2, ("фотосесси",)),
    "birthday": (2, ("день рождения",)),
    "family_trip": (2, ("семейное путешествие", "отдых с семьей")),
    "children": (
        2,
        (
            "показал детей",
            "показала детей",
            "показал ребенка",
            "показала ребенка",
        ),
    ),
    "beauty": (2, ("секрет красоты", "секрет молодости")),
    "outfit": (1, ("наряд", "платье", "талия")),
}

MAX_LIFESTYLE_PENALTY = 3


def calculate_score(news_item):
    """Score a relevant item by topic, news interest, and lifestyle framing."""

    text = (
        f"{news_item.get('title', '')} "
        f"{news_item.get('description', '')}"
    ).casefold()

    topic_score = sum(
        TOPIC_SCORES.get(topic, 0)
        for topic in news_item.get("matched_topics", [])
    )
    interest_score = sum(
        points
        for points, keywords in INTEREST_BONUSES.values()
        if any(keyword in text for keyword in keywords)
    )
    lifestyle_penalty = sum(
        points
        for points, keywords in LIFESTYLE_PENALTIES.values()
        if any(keyword in text for keyword in keywords)
    )

    # The cap keeps a strong scandal viable despite incidental lifestyle wording.
    lifestyle_penalty = min(
        lifestyle_penalty,
        MAX_LIFESTYLE_PENALTY,
    )
    return max(0, topic_score + interest_score - lifestyle_penalty)
