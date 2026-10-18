"""Fixed choices for dictionary entries.

Kept as plain tuples rather than database tables: they change rarely and
this way a new topic needs no migration.
"""

from flaskblog.i18n import gettext

PARTS_OF_SPEECH = (
    ('noun', 'іменник'),
    ('verb', 'дієслово'),
    ('adjective', 'прикметник'),
    ('adverb', 'прислівник'),
    ('pronoun', 'займенник'),
    ('numeral', 'числівник'),
    ('preposition', 'прийменник'),
    ('conjunction', 'сполучник'),
    ('interjection', 'вигук'),
    ('article', 'артикль'),
    ('phrase', 'вираз'),
)

TOPICS = (
    ('greetings', 'Вітання та знайомство'),
    ('family', 'Сім’я та люди'),
    ('food', 'Їжа та напої'),
    ('home', 'Дім і побут'),
    ('city', 'Місто й транспорт'),
    ('work', 'Робота й навчання'),
    ('time', 'Час і дати'),
    ('numbers', 'Числа'),
    ('body', 'Тіло та здоров’я'),
    ('clothes', 'Одяг'),
    ('nature', 'Природа й погода'),
    ('animals', 'Тварини'),
    ('travel', 'Подорожі'),
    ('shopping', 'Покупки та гроші'),
    ('feelings', 'Почуття та характер'),
    ('colors', 'Кольори'),
    ('communication', 'Спілкування'),
    ('leisure', 'Дозвілля та спорт'),
    ('society', 'Суспільство'),
    ('culture', 'Каталонська культура'),
    ('basics', 'Базова лексика'),
)

LEVELS = (
    ('A1', 'A1 (початковий)'),
    ('A2', 'A2 (елементарний)'),
    ('B1', 'B1 (середній)'),
    ('B2', 'B2 (вище середнього)'),
    ('C1', 'C1 (продвинутий)'),
)

GENDERS = (
    ('m', 'чоловічий (el)'),
    ('f', 'жіночий (la)'),
    ('mf', 'чоловічий і жіночий'),
)

PART_OF_SPEECH_LABELS = dict(PARTS_OF_SPEECH)
TOPIC_LABELS = dict(TOPICS)
LEVEL_LABELS = dict(LEVELS)
GENDER_LABELS = dict(GENDERS)

# Columns of the dictionary CSV, in order.
CSV_COLUMNS = (
    'term',
    'translation',
    'part_of_speech',
    'gender',
    'pronunciation',
    'topic',
    'level',
    'example_ca',
    'example_uk',
    'notes',
    'translation_en',
    'example_en',
    'notes_en',
)


def _label(labels, value):
    if value in labels:
        return gettext(labels[value])
    return value or ''


def part_of_speech_label(value):
    return _label(PART_OF_SPEECH_LABELS, value)


def topic_label(value):
    return _label(TOPIC_LABELS, value)


def level_label(value):
    return _label(LEVEL_LABELS, value)


def gender_label(value):
    return _label(GENDER_LABELS, value)
