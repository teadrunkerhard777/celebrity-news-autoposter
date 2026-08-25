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

CELEBRITY_CONTEXT_KEYWORDS = (
    "певец",
    "певица",
    "актер",
    "актёр",
    "актриса",
    "артист",
    "рэпер",
    "блогер",
    "телеведущ",
    "ведущий шоу",
    "ведущая шоу",
    "ведущий программы",
    "ведущая программы",
    "музыкант",
    "модель ",
    "моделью",
    "продюсер",
    "режисс",
    "спортсмен",
    "футболист",
    "звезд",
    "звёзд",
    "шоумен",
    "хореограф",
    "балерин",
    "участник шоу",
    "участница шоу",
)

CELEBRITY_CONTEXT_BONUS = 1
NON_CELEBRITY_INCIDENT_PENALTY = 3
MAX_NON_CELEBRITY_CRIME_SCORE = 3
MAX_NON_CELEBRITY_CONFLICT_SCORE = 1

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
    "new_look": (
        2,
        ("новый образ", "новом образе", "сменил образ", "сменила образ"),
    ),
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
    "swimwear": (2, ("купальник", "полугол")),
    "subscriber_reaction": (
        2,
        ("рассмешил подписчиков", "рассмешила подписчиков"),
    ),
    "hair_change": (
        2,
        ("покрасился", "покрасилась", "прическ", "причёск"),
    ),
    "fan_disapproval": (
        2,
        ("фанаты не оценили", "не оценили фанаты"),
    ),
    "transformation": (2, ("преображени",)),
    "interior": (2, ("показал интерьер", "показала интерьер")),
}

MAX_LIFESTYLE_PENALTY = 5


def calculate_score(news_item):
    """Score a relevant item by topic, news interest, and lifestyle framing."""

    text = (
        f"{news_item.get('title', '')} "
        f"{news_item.get('description', '')}"
    ).casefold()

    matched_topics = news_item.get("matched_topics", [])
    topic_score = sum(
        TOPIC_SCORES.get(topic, 0)
        for topic in matched_topics
    )
    has_celebrity_context = any(
        keyword in text for keyword in CELEBRITY_CONTEXT_KEYWORDS
    )
    interest_score = sum(
        points
        for points, keywords in INTEREST_BONUSES.values()
        if any(keyword in text for keyword in keywords)
    )

    incident_penalty = 0
    if "incidents" in matched_topics and not has_celebrity_context:
        # Keep domestic crime and tragedy from outranking celebrity events.
        interest_score = 0
        incident_penalty = NON_CELEBRITY_INCIDENT_PENALTY

    lifestyle_penalty = sum(
        points
        for points, keywords in LIFESTYLE_PENALTIES.values()
        if any(keyword in text for keyword in keywords)
    )

    # Multiple weak signals add up, while a real event still survives the cap.
    lifestyle_penalty = min(
        lifestyle_penalty,
        MAX_LIFESTYLE_PENALTY,
    )
    celebrity_bonus = CELEBRITY_CONTEXT_BONUS if has_celebrity_context else 0
    score = max(
        0,
        topic_score
        + interest_score
        + celebrity_bonus
        - incident_penalty
        - lifestyle_penalty,
    )
    has_crime_or_incident = any(
        topic in matched_topics
        for topic in ("legal_trouble", "incidents")
    )
    if has_crime_or_incident and not has_celebrity_context:
        # Non-celebrity crime stays below genuine celebrity events.
        return min(score, MAX_NON_CELEBRITY_CRIME_SCORE)
    if (
        set(matched_topics) == {"scandals_conflicts"}
        and not has_celebrity_context
    ):
        # A generic dispute alone should not rank as celebrity entertainment.
        return min(score, MAX_NON_CELEBRITY_CONFLICT_SCORE)
    return score
