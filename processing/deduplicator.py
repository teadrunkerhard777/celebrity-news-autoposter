import re
from datetime import datetime, timedelta, timezone
from difflib import SequenceMatcher


DEFAULTS = {
    "text_limit": 1600,
    "time_window_hours": 36,
    "min_shared_tokens": 5,
    "min_token_overlap": 0.45,
    "min_token_jaccard": 0.20,
    "dense_match_tokens": 7,
    "stop_words": set(),
    "noise_prefixes": (),
    "terminal_events": {},
    "terminal_min_shared_entity_tokens": 2,
    "terminal_noise_tokens": set(),
}


def normalize_title(title):
    normalized = re.sub(r"[^\w\s]", " ", (title or "").casefold())
    return " ".join(normalized.split())


def title_similarity(first, second):
    return SequenceMatcher(
        None,
        normalize_title(first),
        normalize_title(second),
    ).ratio()


def titles_are_similar(first, second, threshold=0.75):
    return title_similarity(first, second) >= threshold


def meaningful_tokens(text, settings=None):
    """Return generic normalized tokens shared by dedup and selection."""

    return _meaningful_tokens(text, _settings(settings))


def remove_duplicates(news_items, settings=None, debug=False):
    """Remove URL, title, and conservative cross-source event duplicates."""

    unique = []
    seen_urls = set()

    for item in news_items:
        url = item.get("url", "")

        if url in seen_urls:
            continue

        duplicate_index = None
        event_details = None

        for index, existing in enumerate(unique):
            if titles_are_similar(item.get("title"), existing.get("title")):
                duplicate_index = index
                break

            details = compare_event_fingerprints(item, existing, settings)

            if details["is_duplicate"]:
                duplicate_index = index
                event_details = details
                break

        if duplicate_index is None:
            seen_urls.add(url)
            unique.append(item)
            continue

        seen_urls.add(url)

        # Title duplicates preserve stable first occurrence.
        if event_details is None:
            continue

        existing = unique[duplicate_index]
        preferred = _choose_preferred(existing, item)

        if debug:
            print(
                "[EVENT DEDUP] "
                f"{existing.get('source')} / {item.get('source')}: "
                f"{', '.join(event_details['shared_tokens'])}"
            )

        if preferred is item:
            unique[duplicate_index] = item

    return unique


def build_event_fingerprint(news_item, settings=None):
    """Build a project-neutral fingerprint from category, text, and hints."""

    values = _settings(settings)
    body = news_item.get("article_text") or news_item.get("description", "")
    text = f"{news_item.get('title', '')} {body[:values['text_limit']]}"
    category = news_item.get("event_category")
    terminal = _build_terminal_signature(news_item.get("title", ""), values)

    return {
        "categories": [category] if category else [],
        "tokens": sorted(_meaningful_tokens(text, values)),
        "terminal_event": terminal["event"],
        "terminal_entities": terminal["entities"],
        # Geography is optional project data, never a global requirement.
        "locations": sorted(set(news_item.get("event_locations", []))),
    }


def compare_event_fingerprints(first, second, settings=None):
    """Compare two different-source items using configurable generic facts."""

    values = _settings(settings)
    result = {
        "is_duplicate": False,
        "shared_tokens": [],
        "shared_categories": [],
        "shared_locations": [],
        "token_overlap": 0.0,
        "token_jaccard": 0.0,
        "time_delta_hours": None,
        "terminal_event": None,
        "shared_terminal_entities": [],
    }

    first_date = _parse_datetime(first.get("published_at"))
    second_date = _parse_datetime(second.get("published_at"))

    if first_date is None or second_date is None:
        return result

    delta = abs(first_date - second_date)
    result["time_delta_hours"] = delta.total_seconds() / 3600

    if delta > timedelta(hours=values["time_window_hours"]):
        return result

    first_fp = _read_or_build(first, values)
    second_fp = _read_or_build(second, values)
    shared_categories = (
        set(first_fp.get("categories", []))
        & set(second_fp.get("categories", []))
    )

    if not shared_categories:
        return result

    first_terminal = _read_terminal_signature(first, first_fp, values)
    second_terminal = _read_terminal_signature(second, second_fp, values)
    shared_terminal_entities = (
        set(first_terminal["entities"])
        & set(second_terminal["entities"])
    )
    same_terminal_event = (
        first_terminal["event"]
        and first_terminal["event"] == second_terminal["event"]
    )

    if (
        same_terminal_event
        and len(shared_terminal_entities)
        >= values["terminal_min_shared_entity_tokens"]
    ):
        # A named person's terminal event remains the same across short updates.
        return {
            **result,
            "is_duplicate": True,
            "shared_categories": sorted(shared_categories),
            "terminal_event": first_terminal["event"],
            "shared_terminal_entities": sorted(shared_terminal_entities),
        }

    if first.get("source") and first.get("source") == second.get("source"):
        return result

    first_tokens = set(first_fp.get("tokens", []))
    second_tokens = set(second_fp.get("tokens", []))

    if not first_tokens or not second_tokens:
        return result

    shared_tokens = first_tokens & second_tokens
    token_overlap = len(shared_tokens) / min(len(first_tokens), len(second_tokens))
    token_jaccard = len(shared_tokens) / len(first_tokens | second_tokens)
    shared_locations = (
        set(first_fp.get("locations", []))
        & set(second_fp.get("locations", []))
    )
    enough_facts = (
        len(shared_tokens) >= values["min_shared_tokens"]
        and token_overlap >= values["min_token_overlap"]
    )
    location_or_dense = bool(shared_locations) or (
        len(shared_tokens) >= values["dense_match_tokens"]
        and token_jaccard >= values["min_token_jaccard"]
    )

    return {
        **result,
        "is_duplicate": enough_facts and location_or_dense,
        "shared_tokens": sorted(shared_tokens),
        "shared_categories": sorted(shared_categories),
        "shared_locations": sorted(shared_locations),
        "token_overlap": token_overlap,
        "token_jaccard": token_jaccard,
    }


def _settings(settings):
    return {**DEFAULTS, **(settings or {})}


def _read_or_build(item, settings):
    fingerprint = item.get("event_fingerprint")
    return fingerprint if isinstance(fingerprint, dict) else build_event_fingerprint(item, settings)


def _read_terminal_signature(item, fingerprint, settings):
    event = fingerprint.get("terminal_event")
    entities = fingerprint.get("terminal_entities")

    if event and isinstance(entities, list):
        return {"event": event, "entities": entities}

    # Existing history fingerprints can derive the compact signature from title.
    return _build_terminal_signature(item.get("title", ""), settings)


def _build_terminal_signature(title, settings):
    normalized = (title or "").casefold()
    event = next(
        (
            name
            for name, keywords in settings["terminal_events"].items()
            if any(keyword in normalized for keyword in keywords)
        ),
        None,
    )

    if event is None:
        return {"event": None, "entities": []}

    event_tokens = {
        token
        for keyword in settings["terminal_events"][event]
        for token in re.findall(r"[\w-]+", keyword, flags=re.UNICODE)
    }
    noise_tokens = set(settings["terminal_noise_tokens"])
    proper_name_tokens = {
        token.casefold().strip("_-")
        for token in re.findall(r"[^\W\d_][\w-]*", title, flags=re.UNICODE)
        if token[:1].isupper()
    }
    entities = sorted(
        token
        for token in proper_name_tokens
        if len(token) >= 2
        and token not in noise_tokens
        and token not in settings["stop_words"]
        and not any(
            token.startswith(event_token) or event_token.startswith(token)
            for event_token in event_tokens
        )
    )
    return {"event": event, "entities": entities}


def _meaningful_tokens(text, settings):
    stop_words = set(settings["stop_words"])
    noise_prefixes = tuple(settings["noise_prefixes"])
    tokens = set()

    for token in re.findall(r"[\w-]+", text.casefold(), flags=re.UNICODE):
        token = token.strip("_-")

        if len(token) < 4 or token in stop_words:
            continue

        if any(token.startswith(prefix) for prefix in noise_prefixes):
            continue

        tokens.add(token)

    return tokens


def _parse_datetime(value):
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value)
        except ValueError:
            return None

    if not isinstance(value, datetime):
        return None

    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)

    return value.astimezone(timezone.utc)


def _choose_preferred(first, second):
    if first.get("score", 0) != second.get("score", 0):
        return first if first.get("score", 0) > second.get("score", 0) else second

    def quality(item):
        body = item.get("article_text", "")
        return bool(body), bool(item.get("image_url")), len(body)

    return second if quality(second) > quality(first) else first
