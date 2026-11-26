"""Word forms and dictionary entries from Wiktionary extracts.

The extracts are the per-language files that wiktextract makes from the
English Wiktionary, published on https://kaikki.org (CC BY-SA 4.0), e.g.
``kaikki.org-dictionary-German.jsonl.gz``. One entry a line: a word with
one part of speech, its English meanings (``senses``) and its inflected
``forms``; an inflected form may also have an entry of its own whose
meaning is "form of" another word.

``flask langsites forms <code> <extract>`` writes
``langsites/data/<code>/forms.tsv``: one line per form, sorted, ``form
<TAB> dictionary form|dictionary form``, only for the words the section's
dictionary has. A word in a text is looked up there with a binary search
in the file (``lemmas``), so nothing of it stays in memory.

``flask langsites build de <extract>`` makes a dictionary from an extract
alone (German has no other source in the project).
"""

import functools
import gzip
import io
import json
import os
import re

from flaskblog.langsites import dictionary

FORMS_FILE = 'forms.tsv'

_SKIP_TAGS = {'romanization', 'table-tags', 'inflection-template', 'class', 'auxiliary',
              'canonical', 'diminutive', 'augmentative', 'error-unknown-tag', 'alternative',
              'obsolete', 'archaic', 'misspelling', 'abbreviation', 'transliteration'}
_POS = {'noun': 'noun', 'verb': 'verb', 'adj': 'adjective', 'adv': 'adverb', 'pron': 'pronoun',
        'prep': 'preposition', 'conj': 'conjunction', 'intj': 'interjection', 'num': 'numeral',
        'det': 'pronoun', 'article': 'article', 'phrase': 'phrase', 'name': 'noun'}
_GENDERS = (('masculine', 'm'), ('feminine', 'f'), ('neuter', 'n'))
_SINGLE = re.compile(r"^[^\s\d]{1,40}$")


def _lines(path):
    opener = gzip.open if path.endswith('.gz') else io.open
    with opener(path, 'rt', encoding='utf-8') as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def _form_of(entry):
    """The dictionary forms an entry is an inflected form of."""
    found = []
    for sense in entry.get('senses', ()):
        for target in sense.get('form_of', ()) or ():
            word = target.get('word')
            if word and word not in found:
                found.append(word)
    return found


def _is_form_entry(entry):
    senses = entry.get('senses') or ()
    return bool(senses) and all('form_of' in sense or 'form-of' in (sense.get('tags') or ())
                                for sense in senses)


def forms(path, known):
    """{form key: {dictionary form key}} for the words in *known* (keys)."""
    found = {}

    def add(form, lemma_key):
        form_key = dictionary.key(form)
        if form_key and form_key != lemma_key and _SINGLE.match(form_key):
            found.setdefault(form_key, set()).add(lemma_key)

    for entry in _lines(path):
        word_key = dictionary.key(entry.get('word'))
        if word_key in known:
            for form in entry.get('forms', ()):
                tags = set(form.get('tags') or ())
                if form.get('form') and not tags & _SKIP_TAGS:
                    add(form['form'], word_key)
        for lemma in _form_of(entry):
            lemma_key = dictionary.key(lemma)
            if lemma_key in known:
                add(entry.get('word'), lemma_key)
    return found


def write_forms(code, path):
    """Write the forms file of a section. Returns the number of forms."""
    known = set(dictionary.index(code).keys)
    found = forms(path, known)
    out = os.path.join(dictionary.DATA_DIR, code, FORMS_FILE)
    with io.open(out, 'w', encoding='utf-8', newline='\n') as handle:
        for form_key in sorted(found):
            handle.write('{}\t{}\n'.format(form_key, '|'.join(sorted(found[form_key]))))
    _size.cache_clear()
    return len(found)


@functools.lru_cache(maxsize=8)
def _size(code):
    try:
        return os.path.getsize(os.path.join(dictionary.DATA_DIR, code, FORMS_FILE))
    except OSError:
        return 0


def lemmas(code, word):
    """The dictionary forms of an inflected *word* (binary search in the
    sorted forms file, read from disk)."""
    target = dictionary.key(word)
    size = _size(code)
    if not target or not size:
        return []
    path = os.path.join(dictionary.DATA_DIR, code, FORMS_FILE)
    with io.open(path, 'rb') as handle:
        low, high = 0, size
        while low < high:
            middle = (low + high) // 2
            handle.seek(middle)
            if middle:
                handle.readline()  # to the start of the next line
            line = handle.readline()
            if not line:
                high = middle
                continue
            form = line.split(b'\t', 1)[0].decode('utf-8')
            if form < target:
                low = middle + 1
            else:
                high = middle
        handle.seek(low)
        if low:
            handle.readline()
        for _ in range(2):
            line = handle.readline()
            if not line:
                break
            form, _tab, rest = line.decode('utf-8').rstrip('\n').partition('\t')
            if form == target:
                return rest.split('|')
            if form > target:
                break
    return []


def entries(path, limit=4):
    """Dictionary entries of an extract: the words that are not only
    inflected forms, with up to *limit* English meanings and the gender."""
    for entry in _lines(path):
        word = entry.get('word')
        pos = _POS.get(entry.get('pos'))
        if not word or not pos or _is_form_entry(entry) or len(word) > 60:
            continue
        senses, gender = [], None
        for sense in entry.get('senses', ()):
            tags = set(sense.get('tags') or ())
            if 'form-of' in tags or 'form_of' in sense or tags & {'obsolete', 'archaic', 'misspelling'}:
                continue
            for name, short in _GENDERS:
                if name in tags and gender is None:
                    gender = short
            for gloss in sense.get('glosses', ())[:1]:
                if gloss and {'en': gloss} not in senses:
                    senses.append({'en': gloss})
        if senses:
            yield {'w': word, 'pos': 'phrase' if ' ' in word else pos, 'senses': senses[:limit], 'g': gender}
