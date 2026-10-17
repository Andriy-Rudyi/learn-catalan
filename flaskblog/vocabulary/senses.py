"""Meanings (senses) of dictionary words.

A translation is attached to a meaning, not to the word: "tocar" has two
meanings, *touch* and *play (an instrument)*, and each language translates
each of them. English is the pivot: the meanings of a word are the parts of
its English translation separated by ";" ("touch; play (an instrument)").

Every language keeps its meanings joined the same way in
WordTranslation.translation as well ("toucher ; jouer (d'un instrument)").
That string is what the bundled CSV files, imports and the editor's form
work with, and what the site shows with SENSES=False, so turning meanings
off (or removing their tables with ``flask db downgrade``) loses nothing.
The two are kept in step here:

* :func:`sync_from_flat` after a translation string changed: split it into
  the word's meanings;
* :func:`sync_to_flat` after a meaning changed (the translation platform):
  join the meanings back into the string.

Splitting a language into the English meanings: the same number of parts
goes one to one; a single part covers every meaning (French "batterie" is
both *battery* and *drums*); more parts than meanings put the extra ones
into the last meaning; fewer leave the last meanings untranslated (they
show the English).
"""

import re

from flaskblog.languages import FALLBACK
from flaskblog.models import SenseTranslation, WordSense, WordTranslation

PIVOT = 'en'
_SEPARATOR = re.compile(r'\s*;\s*')
# French typography puts a space before the semicolon.
_JOINERS = {'fr': ' ; '}


def joiner(lang):
    return _JOINERS.get(lang, '; ')


def split_parts(text):
    """The meanings in a translation string, without empty ones."""
    return [part for part in _SEPARATOR.split((text or '').strip()) if part]


def align(parts, count, lang):
    """*parts* of one language spread over *count* meanings."""
    if not parts:
        return [''] * count
    if len(parts) == count:
        return list(parts)
    if len(parts) == 1:
        return list(parts) * count
    if len(parts) > count:
        return list(parts[:count - 1]) + [joiner(lang).join(parts[count - 1:])]
    return list(parts) + [''] * (count - len(parts))


def join(texts, lang):
    """Meanings back into one string; a text repeated for several meanings
    is written once."""
    seen = []
    for text in texts:
        if text and text not in seen:
            seen.append(text)
    return joiner(lang).join(seen)


def sense_count(word):
    """How many meanings the word's translations call for: the parts of the
    English translation, else of the first fallback language, else one."""
    for lang in (PIVOT,) + tuple(code for code in FALLBACK if code != PIVOT):
        entry = word.translations.get(lang)
        if entry is not None and entry.translation:
            return max(len(split_parts(entry.translation)), 1)
    for entry in word.translations.values():
        if entry.translation:
            return max(len(split_parts(entry.translation)), 1)
    return 1


def _resize(word, count):
    """Give the word exactly *count* meanings; True when that changed them."""
    changed = False
    while len(word.senses) < count:
        word.senses.append(WordSense(position=len(word.senses) + 1))
        changed = True
    while len(word.senses) > count:
        word.senses.pop()
        changed = True
    for position, sense in enumerate(word.senses, start=1):
        sense.position = position
    return changed


def _set_text(sense, lang, text, reviewed):
    entry = sense.translations.get(lang)
    if not text:
        if entry is not None:
            del sense.translations[lang]
        return
    if entry is None:
        sense.translations[lang] = SenseTranslation(lang=lang, text=text, reviewed=reviewed)
    elif entry.text != text:
        entry.text = text
        entry.reviewed = reviewed
    elif reviewed and not entry.reviewed:
        # The string was confirmed as checked (a CSV with reviewed=1).
        entry.reviewed = True


def sync_from_flat(word, langs=None):
    """Split the translation strings of *langs* (all when None) into the
    word's meanings. When the English changes the number of meanings,
    every language is split again."""
    count = sense_count(word)
    if _resize(word, count) or langs is None:
        langs = set(word.translations) | {
            lang for sense in word.senses for lang in sense.translations
        }
    for lang in langs:
        entry = word.translations.get(lang)
        flat = entry.translation if entry is not None else ''
        reviewed = entry.reviewed if entry is not None else True
        current = [
            (sense.translations[lang].text if lang in sense.translations else '')
            for sense in word.senses
        ]
        if join(current, lang) == flat and any(current) == bool(flat):
            # Already in step: keep how the meanings were filled in, which
            # a translator may have done differently from the split.
            continue
        for sense, text in zip(word.senses, align(split_parts(flat), count, lang)):
            _set_text(sense, lang, text, reviewed)


def sync_to_flat(word, lang):
    """Join the word's meanings in *lang* into its translation string (after
    a meaning was edited). The word's row is marked as edited on the site."""
    texts = [
        sense.translations[lang].text if lang in sense.translations else ''
        for sense in word.senses
    ]
    flat = join(texts, lang)
    entry = word.translations.get(lang)
    if entry is None:
        if not flat:
            return
        entry = word.translations[lang] = WordTranslation(lang=lang, translation='')
    entry.translation = flat
    entry.edited = True
    if not (entry.translation or entry.example or entry.notes):
        del word.translations[lang]


def sense_reviewed(word, lang):
    """False when any meaning of the word in *lang* is a draft."""
    return all(
        sense.translations[lang].reviewed
        for sense in word.senses if lang in sense.translations
    )


def meanings(word, lang):
    """What the word page shows, one row per meaning: (SenseTranslation in
    *lang* or its fallback, the English meaning when that is needed to tell
    two meanings with the same translation apart)."""
    shown = [sense.text_in(lang) for sense in word.senses]
    texts = [entry.text if entry is not None else '' for entry in shown]
    rows = []
    for sense, entry, text in zip(word.senses, shown, texts):
        pivot = sense.translations.get(PIVOT)
        hint = None
        if text and texts.count(text) > 1 and pivot is not None and pivot.text != text:
            hint = pivot.text
        rows.append((entry, hint))
    return rows
