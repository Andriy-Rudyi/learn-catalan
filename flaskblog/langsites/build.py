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

import io
import json
import os

from flaskblog.langsites import dictionary
from flaskblog.vocabulary import pivot, wiktionary

BUILDERS = {}


def _builder(code):
    def register(function):
        BUILDERS[code] = function
        return function
    return register


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
def build_ukrainian():
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
    return _write('uk', {k: v for k, v in entries.items() if not v.get('drop')})


def build(code):
    if code not in BUILDERS:
        raise KeyError(code)
    return BUILDERS[code]()
