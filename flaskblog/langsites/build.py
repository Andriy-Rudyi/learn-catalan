"""Making the dictionary files of the language sections.

``flask langsites build uk`` writes ``langsites/data/uk/dictionary.jsonl``
(see langsites/dictionary.py) from the Wiktionary files the Catalan
dictionary already uses (flaskblog/vocabulary/wiktionary.py):

* ``uk-en.jsonl``: Ukrainian words with their meanings explained in
  English, stress, gender and aspect (English Wiktionary, CC BY-SA);
* ``uk-es.jsonl``: Spanish equivalents of Ukrainian words (the
  translation tables of the Spanish Wiktionary, CC BY-SA);
* ``data/derived/uk-ca.jsonl``: Catalan words derived for Ukrainian ones
  (flaskblog/vocabulary/pivot.py).

A word gets one entry per part of speech. The other languages will be
built the same way from their own Wiktionary extracts.
"""

import csv
import io
import json
import os
import re

from flaskblog.langsites import dictionary, kaikki
from flaskblog.vocabulary import apertium, dacco, pivot, wiktionary

_VOCABULARY_DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                'vocabulary', 'data')
_WIKTIONARY = 'Wiktionary (CC BY-SA 4.0), via kaikki.org'
_DACCO = 'DACCO, Diccionari Obert Català de Codi Obert (LGPL 2.1)'
_APERTIUM = 'Apertium spa-cat (GPL 2.0)'
_DERIVED = 'Catalan equivalents derived through English and Spanish (this project)'
_SITE = 'Translations of the Catalan dictionary of this site'

BUILDERS = {}


def _builder(code):
    def register(function):
        BUILDERS[code] = function
        return function
    return register


def _write_meta(code, sources):
    out = os.path.join(dictionary.DATA_DIR, code, 'meta.json')
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with io.open(out, 'w', encoding='utf-8') as handle:
        json.dump({'sources': sources}, handle, ensure_ascii=False, indent=1)
        handle.write('\n')


def _write(code, entries):
    out = dictionary.path(code)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    rows = sorted(entries.values(), key=lambda entry: (entry['k'], entry['pos'], entry['w']))
    with io.open(out, 'w', encoding='utf-8') as handle:
        for entry in rows:
            ordered = {'k': entry['k']}
            ordered.update((name, value) for name, value in entry.items() if name != 'k' and value)
            handle.write(json.dumps(ordered, ensure_ascii=False, separators=(',', ':')) + '\n')
    dictionary.index.cache_clear()
    dictionary._reverse.cache_clear()
    return len(rows)


def _add_unique(items, values):
    for value in values:
        if value not in items:
            items.append(value)


@_builder('uk')
def build_ukrainian(extract=None):
    entries = {}

    def entry(word, pos):
        word_key = dictionary.key(word)
        item = entries.get((word_key, pos))
        if item is None:
            item = entries[word_key, pos] = {'k': word_key, 'w': word, 'pos': pos,
                                             'senses': [], 'es': [], 'ca': []}
        elif wiktionary._STRESS in word and wiktionary._STRESS not in item['w']:
            item['w'] = word
        return item

    for row in wiktionary.load(wiktionary.UK_EN):
        item = entry(row.get('stressed') or row['uk'], row['pos'])
        for sense in row['senses']:
            if sense not in item['senses']:
                item['senses'].append(sense)
        for name, short in (('gender', 'g'), ('aspect', 'asp'), ('pair', 'pair'), ('proper', 'proper')):
            if row.get(name) and not item.get(short):
                item[short] = row[name]

    explained = {word_key for word_key, _pos in entries}
    for row in wiktionary.load(wiktionary.UK_ES):
        word_key = dictionary.key(row['uk'])
        item = entries.get((word_key, row['pos']))
        if item is None and word_key in explained:
            continue  # Wiktionary has the word, but not with this part of speech
        item = item or entry(row['uk'], row['pos'])
        _add_unique(item['es'], row['es'])

    try:
        with io.open(pivot.DERIVED_FILE, encoding='utf-8') as handle:
            derived = [json.loads(line) for line in handle if line.strip()]
    except OSError:
        derived = []
    for row in derived:
        word_key = dictionary.key(row['uk'])
        for catalan in row['ca']:
            item = entries.get((word_key, catalan.get('pos')))
            if item is None:
                continue  # only for a word and part of speech the dictionary has
            value = {'w': catalan['w'], 'pos': catalan.get('pos')}
            if catalan.get('unsure'):
                value['unsure'] = True
            if not any(existing['w'] == value['w'] for existing in item['ca']):
                item['ca'].append(value)

    for item in entries.values():
        if not item['senses'] and not item['es']:
            item['drop'] = True
    _write_meta('uk', [_WIKTIONARY, _DERIVED])
    return _write('uk', {k: v for k, v in entries.items() if not v.get('drop')})


class _Entries(dict):
    """{(key, part of speech): entry} with helpers to fill the lists."""

    def get_entry(self, word, pos):
        word = (word or '').strip()
        word_key = dictionary.key(word)
        if not word_key or len(word_key) > 80:
            return None
        item = self.get((word_key, pos))
        if item is None:
            item = self[word_key, pos] = {'k': word_key, 'w': word, 'pos': pos, 'senses': []}
        return item

    def add(self, word, pos, lang, values):
        item = self.get_entry(word, pos)
        if item is None:
            return None
        items = item.setdefault(lang, [])
        for value in values:
            value = value.strip() if isinstance(value, str) else value
            if value and value not in items:
                items.append(value)
        return item


_DACCO_POS = {'exclamation': 'interjection', 'verb form': 'verb', 'acronym': 'noun',
              'abbreviation': 'noun', 'determiner': 'pronoun'}


@_builder('en')
def build_english(extract=None):
    """English: the meanings of Wiktionary's translation tables with their
    Ukrainian, Spanish and Catalan words, and DACCO's English-Catalan part."""
    entries = _Entries()
    for row in wiktionary.load(wiktionary.SENSES):
        item = entries.get_entry(row['en'], row['pos'])
        if item is None:
            continue
        sense = {'en': row['sense']}
        if sense not in item['senses']:
            item['senses'].append(sense)
        for lang in ('uk', 'es', 'ca'):
            entries.add(row['en'], row['pos'], lang, row.get(lang, ()))
    with io.open(os.path.join(_VOCABULARY_DATA, 'sources', 'dacco', 'en-ca.jsonl'), encoding='utf-8') as handle:
        for line in handle:
            row = json.loads(line)
            for part in row['parts']:
                pos = _DACCO_POS.get(part['pos'], part['pos'])
                entries.add(row['head'], pos, 'ca', [sense['text'] for sense in part['senses']])
            for expression in row.get('expressions', ()):
                entries.add(expression['text'], 'phrase', 'ca',
                            [sense['text'] for sense in expression.get('senses', ())])
    _write_meta('en', [_WIKTIONARY, _DACCO])
    return _write('en', entries)


def _add_meanings(entries, extract, add_new=True):
    """The English meanings of a Wiktionary extract (langsites/kaikki.py):
    for the words the entries have, and, with *add_new*, new words."""
    for found in kaikki.entries(extract):
        item = entries.get((dictionary.key(found['w']), found['pos']))
        if item is None:
            if not add_new:
                continue
            item = entries.get_entry(found['w'], found['pos'])
            if item is None:
                continue
        for sense in found['senses']:
            if sense not in item['senses']:
                item['senses'].append(sense)
        if found.get('g') and not item.get('g'):
            item['g'] = found['g']


_NOT_EQUIVALENT = re.compile(
    r'^(an? |the )?((male|female|unisex) )?(surname|given name|placename|place name|town|city|village|'
    r'river|municipality|commune|quarter|district|region|province|island|mountain|lake)\b'
    r'|^(alternative|obsolete|archaic|dated|nonstandard) (spelling|form) of|^(abbreviation|initialism|acronym) of',
    re.I)
_DERIVED_UK = 'Ukrainian equivalents derived through English (this project), marked as unchecked'


def _derive_ukrainian(entries, per_meaning=2, limit=4):
    """Give the entries without Ukrainian a Ukrainian equivalent derived
    from their English meanings (the Wiktionary tables of pivot.py): a
    Ukrainian word is taken when an English word of a meaning has only it
    for that part of speech, or when two English words of the meaning agree
    on it. Each is marked ``unsure`` (shown as unchecked). Returns how many
    entries got one."""
    data = pivot.tables()
    en_uk, shown, order = data['en_uk'], data['shown'], data['order']
    imperfective = data['imperfective']
    added = 0
    for item in entries.values():
        if item.get('uk'):
            continue
        # Short glosses only ("dog, hound"): a long one is a description
        # ("a quarter in Schortens, East Frisia, Germany"), not equivalents.
        glosses = [sense['en'] for sense in item.get('senses', ())] + list(item.get('en', ()))
        meanings = [wiktionary.gloss_parts(gloss) for gloss in glosses
                    if len(re.sub(r'\([^)]*\)', ' ', gloss).split()) <= 8 and not _NOT_EQUIVALENT.match(gloss)]
        found = []
        for words in meanings:
            votes = {}
            for english in words:
                candidates = {}
                for key, parts in en_uk.get(english, {}).items():
                    if item['pos'] not in pivot._STRICT_POS or item['pos'] in parts:
                        key = imperfective.get(key, key)
                        candidates[key] = min(candidates.get(key, 99), order.get((english, key), 99))
                for key, position in candidates.items():
                    vote = votes.setdefault(key, [0, 99, False])
                    vote[0] += 1
                    vote[1] = min(vote[1], position)
                    vote[2] = vote[2] or len(candidates) == 1
            chosen = sorted((key for key, (count, _pos, only) in votes.items() if only or count >= 2),
                            key=lambda key: (-votes[key][0], votes[key][1], len(key)))
            if not chosen and words:
                # The usual word: the one Wiktionary lists first for the
                # meaning's first English word.
                first = [key for key, (_count, position, _only) in votes.items() if position == 0
                         and any(english == words[0] for english in words[:1])
                         and key in {imperfective.get(k, k) for k in en_uk.get(words[0], {})}]
                chosen = sorted(first, key=len)[:1]
            for key in chosen[:per_meaning]:
                word = shown.get(key, key)
                # No proper names (and German nouns are capitalised anyway).
                if word[:1].isupper() or len(key.split()) > 3:
                    continue
                if word not in [entry['w'] for entry in found]:
                    found.append({'w': word, 'unsure': True})
        if found:
            item['uk'] = found[:limit]
            added += 1
    return added


@_builder('de')
def build_german(extract=None):
    """German: the English Wiktionary's German words with their English
    meanings and gender (an extract from kaikki.org)."""
    if not extract:
        raise ValueError('German needs a Wiktionary extract (kaikki.org-dictionary-German.jsonl.gz)')
    entries = _Entries()
    _add_meanings(entries, extract)
    _derive_ukrainian(entries)
    _write_meta('de', [_WIKTIONARY, _DERIVED_UK])
    return _write('de', entries)


@_builder('es')
def build_spanish(extract=None):
    """Spanish: Apertium's Spanish-Catalan pairs, the Ukrainian of the
    Spanish Wiktionary's tables and the English of the English one."""
    entries = _Entries()
    for pair in apertium.load():
        if pair['dir'] in ('both', 'es-ca'):
            pos = 'phrase' if ' ' in pair['es'] else apertium.POS[pair['pos']]
            entries.add(pair['es'], pos, 'ca', [pair['ca']])
    for row in wiktionary.load(wiktionary.UK_ES):
        for spanish in row['es']:
            entries.add(spanish, row['pos'], 'uk', [row['uk']])
    for row in wiktionary.load(wiktionary.SENSES):
        for spanish in row.get('es', ()):
            entries.add(spanish, row['pos'], 'en', [row['en']])
    if extract:
        _add_meanings(entries, extract)
    _derive_ukrainian(entries)
    _write_meta('es', [_APERTIUM, _WIKTIONARY, _DERIVED_UK])
    return _write('es', entries)


def _csv(name):
    with io.open(os.path.join(_VOCABULARY_DATA, 'translations', name), encoding='utf-8') as handle:
        return {row['term']: row['translation'] for row in csv.DictReader(handle) if row['translation']}


_SPLIT = re.compile(r'\s*[,;]\s*')
_PARENS = re.compile(r'\([^)]*\)')


@_builder('fr')
def build_french(extract=None):
    """French: the French translations of the site's Catalan words, turned
    round; the Ukrainian and English of the same Catalan word go with them."""
    entries = _Entries()
    with io.open(os.path.join(_VOCABULARY_DATA, 'words.csv'), encoding='utf-8') as handle:
        pos_of = {row['term']: row['part_of_speech'] for row in csv.DictReader(handle)}
    ukrainian, english = _csv('uk.csv'), _csv('en.csv')
    for term, french in _csv('fr.csv').items():
        pos = pos_of.get(term) or 'phrase'
        for word in _SPLIT.split(_PARENS.sub(' ', french)):
            word = ' '.join(word.split())
            if not word or len(word) > 60:
                continue
            entries.add(word, 'phrase' if ' ' in word and pos != 'verb' else pos, 'ca', [term])
            if term in ukrainian:
                entries.add(word, 'phrase' if ' ' in word and pos != 'verb' else pos, 'uk', [ukrainian[term]])
            if term in english:
                entries.add(word, 'phrase' if ' ' in word and pos != 'verb' else pos, 'en', [english[term]])
    if extract:
        _add_meanings(entries, extract)
    _derive_ukrainian(entries)
    _write_meta('fr', ([_SITE, _WIKTIONARY] if extract else [_SITE]) + [_DERIVED_UK])
    return _write('fr', entries)


def build(code, extract=None):
    if code not in BUILDERS:
        raise KeyError(code)
    return BUILDERS[code](extract) if extract else BUILDERS[code]()
