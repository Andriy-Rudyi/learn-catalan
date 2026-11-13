"""Ukrainian-English and Ukrainian-Spanish dictionaries from Wiktionary.

The source is Wiktionary (CC BY-SA 4.0 and GFDL) as machine-readable
extracts made by wiktextract and published on https://kaikki.org:

* the Ukrainian entries of the English Wiktionary
  (``kaikki.org-dictionary-Ukrainian.jsonl.gz``): Ukrainian headwords with
  English glosses;
* the translation tables of the English entries of the English Wiktionary
  (``kaikki.org-dictionary-English.jsonl.gz``): for one meaning of an
  English word, its Ukrainian, Spanish and Catalan translations;
* the translation tables of the Spanish entries of the Spanish Wiktionary
  (``eswiktionary/Español``): Spanish words with Ukrainian translations.

``flask vocabulary wiktionary-convert <folder>`` (:func:`convert`) reads the
three downloads and writes, in ``data/sources/wiktionary/``:

``uk-en.jsonl``, Ukrainian headwords::

    {"uk": "кавун", "stressed": "каву́н", "pos": "noun", "gender": "m",
     "senses": [{"en": "watermelon"}]}

(verbs also have ``aspect``, "impf" or "pf", and ``pair``, the verb of the
other aspect);

``senses.jsonl``, the translation tables that have a Ukrainian word::

    {"en": "watermelon", "pos": "noun", "sense": "fruit",
     "uk": ["каву́н"], "es": ["sandía", ...], "ca": ["síndria", ...]}

``uk-es.jsonl``, Ukrainian words with their Spanish equivalents: the ones
the Spanish Wiktionary gives (listed in ``direct`` too) and the ones that
translate the same meaning of an English word in the tables above::

    {"uk": "каву́н", "pos": "noun", "es": ["sandía", "melón de agua"],
     "direct": ["sandía"]}

``ca-en.jsonl``, Catalan words with the English words whose translation
tables list them (all tables, with or without Ukrainian), each with the
Spanish words of the same table::

    {"ca": "síndria", "pos": "noun", "en": [["watermelon", ["sandía", ...]]]}

Ukrainian words keep their stress mark (U+0301); :func:`uk_key` takes it
away for comparing. Credit Wiktionary and keep these files and what is made
from them under CC BY-SA.
"""

import functools
import gzip
import io
import json
import os
import re

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'sources', 'wiktionary')
UK_EN = 'uk-en.jsonl'
SENSES = 'senses.jsonl'
UK_ES = 'uk-es.jsonl'
CA_EN = 'ca-en.jsonl'

# The downloads :func:`convert` looks for in its folder.
DOWNLOADS = {
    'ukrainian': 'kaikki.org-dictionary-Ukrainian.jsonl.gz',
    'english': 'kaikki.org-dictionary-English.jsonl.gz',
    'spanish': 'kaikki.org-dictionary-Español.jsonl.gz',
}

SOURCE = {
    'name': 'Wiktionary (English and Spanish editions), extracted by wiktextract (kaikki.org)',
    'url': 'https://kaikki.org',
    'licence': 'CC BY-SA 4.0',
}

# wiktextract's parts of speech -> the site's.
POS = {
    'noun': 'noun', 'name': 'noun', 'verb': 'verb', 'adj': 'adjective', 'adv': 'adverb',
    'pron': 'pronoun', 'det': 'pronoun', 'num': 'numeral', 'prep': 'preposition',
    'conj': 'conjunction', 'intj': 'interjection', 'particle': 'adverb',
    'phrase': 'phrase', 'prep_phrase': 'phrase', 'proverb': 'phrase',
}
_SKIP_TAGS = {'form-of', 'alt-of', 'obsolete', 'archaic', 'misspelling'}
_GENDER_TAGS = (('masculine', 'm'), ('feminine', 'f'), ('neuter', 'n'))

_STRESS = '́'
_APOSTROPHES = str.maketrans({'’': "'", 'ʼ': "'", '`': "'"})
_BRACKETS = re.compile(r'\([^)]*\)|\[[^\]]*\]')
_SPACES = re.compile(r'\s+')


def uk_key(text):
    """A Ukrainian word for comparing: no stress mark, one apostrophe, lower case."""
    return _SPACES.sub(' ', (text or '').replace(_STRESS, '').translate(_APOSTROPHES)).strip().lower()


_NOT_UKRAINIAN = re.compile(r'[A-Za-z0-9]|[ыэёъ]', re.I)
_CYRILLIC = re.compile('[а-щьюяіїєґ]', re.I)


def is_ukrainian(word):
    """Cyrillic, without Latin letters, digits or Russian-only letters."""
    return bool(_CYRILLIC.search(word)) and not _NOT_UKRAINIAN.search(word)


def en_key(text):
    """"to rush towards (someone)" -> "rush towards"; "a house" -> "house"."""
    text = _SPACES.sub(' ', _BRACKETS.sub(' ', text or '')).strip().lower().strip('.!?')
    return re.sub(r'^(to|a|an|the) (?=\S)', '', text)


def es_key(text):
    return _SPACES.sub(' ', _BRACKETS.sub(' ', text or '')).strip().lower()


def gloss_parts(gloss):
    """The short English equivalents in a gloss: "house, home" -> both."""
    parts = [en_key(part) for part in re.split(r'[,;]', _BRACKETS.sub(' ', gloss or ''))]
    return [part for part in parts if part and len(part.split()) <= 3]


# -- converting the downloads ----------------------------------------------------------------

def _lines(path):
    with gzip.open(path, 'rt', encoding='utf-8') as handle:
        for line in handle:
            yield line


def _gender(tags):
    for tag, gender in _GENDER_TAGS:
        if tag in tags:
            return gender
    return None


def ukrainian_entries(path):
    """Ukrainian headwords with their English glosses (inflected forms,
    alternative spellings and affixes are left out)."""
    for line in _lines(path):
        entry = json.loads(line)
        pos = POS.get(entry.get('pos'))
        if pos is None:
            continue
        senses = []
        gender = None
        for sense in entry.get('senses') or []:
            tags = set(sense.get('tags') or [])
            if tags & _SKIP_TAGS or 'form_of' in sense or 'alt_of' in sense:
                continue
            gloss = (sense.get('glosses') or [''])[-1].strip()
            if not gloss:
                continue
            gender = gender or _gender(tags)
            item = {'en': gloss}
            labels = sorted(tags - {'masculine', 'feminine', 'neuter', 'animate', 'inanimate',
                                    'personal'})
            if labels:
                item['tags'] = labels
            senses.append(item)
        if not senses:
            continue
        forms = entry.get('forms') or []
        canonical = next((form for form in forms if 'canonical' in (form.get('tags') or [])), None)
        stressed = canonical['form'] if canonical else None
        if gender is None:
            for template in entry.get('head_templates') or []:
                found = re.search(r'\b([mfn])(?:-|\b)', str((template.get('args') or {}).get('2', '')))
                if found:
                    gender = found.group(1)
                    break
        out = {'uk': entry['word'], 'pos': pos, 'senses': senses}
        if stressed and uk_key(stressed) == uk_key(entry['word']) and stressed != entry['word']:
            out['stressed'] = stressed
        if gender and pos == 'noun':
            out['gender'] = gender
        if entry.get('pos') == 'name':
            out['proper'] = True
        if pos == 'verb' and canonical:
            # "написати" is the perfective of "писати": dictionaries list the pair
            # under the imperfective.
            tags = canonical.get('tags') or []
            aspect = 'pf' if 'perfective' in tags else 'impf' if 'imperfective' in tags else None
            if aspect:
                out['aspect'] = aspect
                other = 'imperfective' if aspect == 'pf' else 'perfective'
                pair = next((form['form'] for form in forms
                             if other in (form.get('tags') or []) and ' ' not in form['form']), None)
                if pair:
                    out['pair'] = pair
        yield out


def _translations(entry, wanted, code_key):
    """{meaning: {code: [words]}} of an entry's translation tables."""
    groups = {}

    def take(items, default):
        for item in items or []:
            code = item.get('lang_code') or item.get(code_key)
            word = (item.get('word') or '').strip()
            if code not in wanted or not word or len(word) > 60:
                continue
            if code == 'uk' and not is_ukrainian(word):
                continue  # a note in English that got into the table
            words = groups.setdefault(item.get('sense') or default, {}).setdefault(code, [])
            if word not in words:
                words.append(word)

    take(entry.get('translations'), '')
    for sense in entry.get('senses') or []:
        take(sense.get('translations'), (sense.get('glosses') or [''])[-1])
    return groups


def english_senses(path):
    """Translation tables of English entries that have a Ukrainian or a
    Catalan word."""
    for line in _lines(path):
        if '"translations"' not in line:
            continue
        entry = json.loads(line)
        pos = POS.get(entry.get('pos'))
        if pos is None:
            continue
        for sense, words in _translations(entry, ('uk', 'es', 'ca'), 'code').items():
            if 'uk' in words or 'ca' in words:
                yield dict({'en': entry['word'], 'pos': pos, 'sense': sense[:120]}, **words)


def spanish_pairs(path):
    """Spanish headwords of the Spanish Wiktionary with Ukrainian translations."""
    for line in _lines(path):
        if '"uk"' not in line:
            continue
        entry = json.loads(line)
        pos = POS.get(entry.get('pos'))
        if pos is None:
            continue
        for words in _translations(entry, ('uk',), 'code').values():
            for word in words.get('uk', []):
                yield {'uk': word, 'es': entry['word'], 'pos': pos}


def _write(path, rows):
    count = 0
    with io.open(path, 'w', encoding='utf-8') as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, separators=(',', ':')) + '\n')
            count += 1
    return count


def convert(folder, out_dir=DATA_DIR):
    """Convert the three downloads in *folder*; returns {file: rows}."""
    os.makedirs(out_dir, exist_ok=True)
    counts = {}
    counts[UK_EN] = _write(os.path.join(out_dir, UK_EN),
                           ukrainian_entries(os.path.join(folder, DOWNLOADS['ukrainian'])))
    tables = list(english_senses(os.path.join(folder, DOWNLOADS['english'])))
    senses = [row for row in tables if 'uk' in row]
    counts[SENSES] = _write(os.path.join(out_dir, SENSES), senses)
    # Catalan word (with its part of speech) -> the English words it translates.
    catalan = {}
    for row in tables:
        spanish = [es_key(word) for word in row.get('es', [])][:4]
        for word in row.get('ca', []):
            item = catalan.setdefault((word.lower(), row['pos']), {'ca': word, 'pos': row['pos'], 'en': []})
            known = next((pair for pair in item['en'] if pair[0] == row['en']), None)
            if known is None:
                item['en'].append([row['en'], spanish])
            else:
                known[1].extend(es for es in spanish if es not in known[1])
    counts[CA_EN] = _write(os.path.join(out_dir, CA_EN), catalan.values())
    # Ukrainian word (with its part of speech) -> its Spanish words.
    grouped = {}

    def add(uk, es, pos, direct):
        row = grouped.setdefault((uk_key(uk), pos), {'uk': uk, 'pos': pos, 'es': []})
        if _STRESS in uk and _STRESS not in row['uk']:
            row['uk'] = uk
        if es not in row['es']:
            row['es'].append(es)
        if direct and es not in row.setdefault('direct', []):
            row['direct'].append(es)

    for pair in spanish_pairs(os.path.join(folder, DOWNLOADS['spanish'])):
        add(pair['uk'], pair['es'], pair['pos'], True)
    for sense in senses:
        for uk in sense['uk']:
            for es in sense.get('es', []):
                add(uk, es, sense['pos'], False)
    counts[UK_ES] = _write(os.path.join(out_dir, UK_ES), grouped.values())
    load.cache_clear()
    _catalan_index.cache_clear()
    return counts


# -- reading ------------------------------------------------------------------------------------

@functools.lru_cache(maxsize=None)
def load(name):
    """The rows of one of the files (UK_EN, SENSES, UK_ES)."""
    try:
        with io.open(os.path.join(DATA_DIR, name), encoding='utf-8') as handle:
            return [json.loads(line) for line in handle if line.strip()]
    except OSError:
        return []


@functools.lru_cache(maxsize=1)
def _catalan_index():
    index = {}
    for row in load(CA_EN):
        index.setdefault(row['ca'].lower(), []).append((row['pos'], row['en']))
    return index


def english(term, part_of_speech=None, spanish=(), limit=3):
    """English words whose Wiktionary translation tables list this Catalan
    word, those of its part of speech (all when none matches). With
    *spanish* (the word's Spanish equivalents), only the English words
    whose table lists one of them as well: the two agree on the meaning."""
    rows = _catalan_index().get((term or '').strip().lower(), [])
    if part_of_speech:
        rows = [row for row in rows if row[0] == part_of_speech] or rows
    wanted = {es_key(word) for word in spanish}
    words = []
    for _pos, found in rows:
        for word, same_table in found:
            if word not in words and (not wanted or wanted & set(same_table)):
                words.append(word)
    return words[:limit]


def stats():
    return {
        'uk-en headwords': len(load(UK_EN)),
        'uk-en meanings': sum(len(entry['senses']) for entry in load(UK_EN)),
        'translation tables with Ukrainian': len(load(SENSES)),
        'ca-en Catalan words': len(load(CA_EN)),
        'uk-es headwords': len(load(UK_ES)),
        'uk-es pairs': sum(len(row['es']) for row in load(UK_ES)),
    }
