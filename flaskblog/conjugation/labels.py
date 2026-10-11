"""Ukrainian labels for the Catalan moods, tenses and persons."""

MOOD_LABELS = {
    "indicatiu": "Дійсний спосіб (indicatiu)",
    "subjuntiu": "Умовний спосіб (subjuntiu)",
    "condicional": "Умовний час (condicional)",
    "imperatiu": "Наказовий спосіб (imperatiu)",
    "infinitiu": "Інфінітив (infinitiu)",
    "gerundi": "Дієприслівник (gerundi)",
    "particip": "Дієприкметник (particip)",
}

TENSE_LABELS = {
    "present": "Теперішній",
    "imperfet": "Минулий незакінчений (imperfet)",
    "passat-simple": "Минулий простий (passat simple)",
    "passat-perifrastic": "Минулий складний (passat perifràstic)",
    "perfet": "Минулий завершений (perfet)",
    "plusquamperfet": "Давноминулий (plusquamperfet)",
    "passat-anterior": "Передминулий (passat anterior)",
    "futur": "Майбутній",
    "futur-perfet": "Майбутній завершений",
    "condicional-perfet": "Завершений",
    "imperatiu-present": "Наказові форми",
    "infinitiu-present": "Простий",
    "infinitiu-perfet": "Складений",
    "gerundi": "Простий",
    "gerundi-compost": "Складений",
    "particip": "Форми",
}

# Row headings, per mood, for the tenses that are not conjugated by person.
PERSON_LABELS = ("1 ос. одн.", "2 ос. одн.", "3 ос. одн.", "1 ос. мн.", "2 ос. мн.", "3 ос. мн.")
IMPERATIVE_PERSON_LABELS = ("tu", "ell / ella", "nosaltres", "vosaltres", "ells / elles")
PARTICIPLE_PERSON_LABELS = ("чол. одн.", "жін. одн.", "чол. мн.", "жін. мн.")

# Moods whose forms are listed without a person column.
UNINFLECTED_MOODS = ("infinitiu", "gerundi")

MOOD_ORDER = (
    "indicatiu",
    "subjuntiu",
    "condicional",
    "imperatiu",
    "infinitiu",
    "gerundi",
    "particip",
)


def mood_label(name):
    return MOOD_LABELS.get(name, name.replace("-", " ").capitalize())


def tense_label(name):
    return TENSE_LABELS.get(name, name.replace("-", " ").capitalize())


def person_labels(mood, count):
    """Row headings for a mood's forms."""
    if mood == "imperatiu":
        labels = IMPERATIVE_PERSON_LABELS
    elif mood == "particip":
        labels = PARTICIPLE_PERSON_LABELS
    elif mood in UNINFLECTED_MOODS:
        labels = ()
    else:
        labels = PERSON_LABELS
    if len(labels) < count:
        return list(labels) + [""] * (count - len(labels))
    return list(labels[:count])


def ordered_moods(moods):
    """Yield ``(name, label, tenses)`` in the order they should be shown."""
    for name in MOOD_ORDER:
        if name in moods:
            yield name, mood_label(name), moods[name]
    for name in moods:
        if name not in MOOD_ORDER:
            yield name, mood_label(name), moods[name]


# Messages for the error codes the service returns.
ERROR_MESSAGES = {
    "empty": "Введіть дієслово в інфінітиві, наприклад «parlar».",
    "too-long": "Це задовго для дієслова — перевірте, чи не вставилося кілька слів.",
    "not-a-single-word": (
        "Введіть одне дієслово в інфінітиві, без займенників та інших слів "
        "(наприклад «parlar», а не «jo parlo»)."
    ),
    "not-catalan-letters": (
        "У слові є символи, яких не буває в каталонських дієсловах."
    ),
    "unknown-verb": "Такого дієслова немає в каталонському словнику дієслів.",
    "internal": "Не вдалося відмінити це дієслово. Спробуйте інше.",
}

DEFAULT_ERROR_MESSAGE = "Не вдалося розпізнати дієслово."


def error_message(code):
    return ERROR_MESSAGES.get(code, DEFAULT_ERROR_MESSAGE)
