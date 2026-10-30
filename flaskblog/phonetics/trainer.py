"""The pronunciation trainer (/phonetics/trainer): self-checking practice for
every pronunciation lesson.

Each lesson becomes a unit. Its tasks come from two places:

* the lesson's practice words (data/lessons.json): write the transcription
  of a word, or the word of a transcription;
* data/trainer.json, keyed by lesson slug: tasks that need more than a word
  list. They hold only Catalan and IPA, so they need no translation:

  sound     "how is the marked part of the word pronounced?"
            {"word": "casa", "mark": "a", "nth": 2, "options": [...], "answer": "ə"}
            ("∅" is a silent letter; "nth" counts the mark in the word, from 1)
  stress    "which syllable is stressed?"
            {"word": "música", "syllables": ["mú", "si", "ca"], "answer": 0}
  spelling  "how is [kəˈfɛ] written?"
            {"ipa": "kəˈfɛ", "options": ["cafè", "café", "cafe"], "answer": "cafè"}
  listen    the page says one of the words, the learner picks it
            {"options": ["casa", "caça"]}

The transcriptions shown with the answers come from the transcription module
(the lessons first, then the rules), the same ones the dictionary shows.
The answers are checked in the browser (static/phonetics-trainer.js): this is
practice, nothing is stored on the server.
"""

import json
import os

from flaskblog.phonetics import service
from flaskblog.vocabulary import transcription

TRAINER_FILE = os.path.join(service.DATA_DIR, 'trainer.json')
QUESTIONS_PER_ROUND = 10

_cache = {}


def tasks_file():
    with open(TRAINER_FILE, encoding='utf-8') as handle:
        return json.load(handle)


def ipa_of(term):
    found = transcription.transcribe(term)
    return found.ipa if found else ''


def _lesson_tasks(lesson, extra, lang):
    """All tasks of one lesson, ready for the page."""
    tasks = []
    words = lesson.get('words', [])
    spelled = {}
    for word in words:
        spelled.setdefault(word['ipa'], set()).add(word['ca'].lower())
    for word in words:
        meaning = word.get(lang) or word.get('uk') or ''
        tasks.append({'type': 'transcribe', 'word': word['ca'], 'meaning': meaning,
                      'answer': word['ipa']})
        # "Which word is [ipa]?" only when the transcription has one spelling.
        if len(spelled[word['ipa']]) == 1:
            tasks.append({'type': 'spell', 'ipa': word['ipa'], 'meaning': meaning,
                          'answer': word['ca']})
    for task in extra:
        task = dict(task)
        if task['type'] in ('sound', 'stress'):
            task['ipa'] = ipa_of(task['word'])
        tasks.append(task)
    return tasks


def units(lang=None):
    """[{slug, number, title, level, tasks}] in lesson order, for the content
    language of the request (the meanings of the words follow it)."""
    path = service.lessons_file(lang)
    key = (path, lang)
    if key not in _cache:
        extra = tasks_file()
        _cache[key] = [
            {'slug': lesson['slug'], 'number': lesson['number'], 'title': lesson['title'],
             'level': lesson['level'],
             'tasks': _lesson_tasks(lesson, extra.get(lesson['slug'], []), lang or 'uk')}
            for lesson in service.load_lessons(path)
        ]
    return _cache[key]
