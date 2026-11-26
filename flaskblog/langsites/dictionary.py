"""The dictionary of a language section, read from a file on demand.

``langsites/data/<code>/dictionary.jsonl`` holds one entry a line (a word
with one part of speech), sorted by its key (lower case, without stress
marks)::

    {"k": "собака", "w": "соба́ка", "pos": "noun",
     "senses": [{"en": "dog (animal)"}, {"en": "scoundrel", "tags": ["derogatory"]}],
     "es": ["perro"], "ca": [{"w": "gos", "pos": "noun"}]}

``senses`` are the meanings, explained in English (Wiktionary's glosses);
the other keys are equivalents in the languages of the site (``ca`` with
the Catalan word's part of speech; ``unsure`` marks a derived one that only
one route supports). Optional keys: ``g`` gender, ``asp`` aspect (``pf``,
``ipf``) and ``pair`` its aspect partner, ``proper`` for proper names.

Only the keys and their byte offsets are kept in memory, as compact
strings (the server has little memory); an entry is read from the file when
a page needs it. The index of translations, for searching in English,
Spanish or Catalan, is built only when somebody searches that way.
"""

import bisect
import functools
import io
import json
import os
import re

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
FILE_NAME = 'dictionary.jsonl'

_STRESS = '́'
_APOSTROPHES = str.maketrans({'’': "'", 'ʼ': "'", '`': "'"})
_SPACES = re.compile(r'\s+')
_BRACKETS = re.compile(r'\([^)]*\)|\[[^\]]*\]')
_WORDS = re.compile(r"[^\W\d_]+(?:['\-][^\W\d_]+)*")
_SEP = '\x1f'


def key(text):
    """A word for comparing: lower case, no stress mark, one apostrophe."""
    text = (text or '').replace(_STRESS, '').translate(_APOSTROPHES)
    return _SPACES.sub(' ', text).strip().lower()


def path(code):
    return os.path.join(DATA_DIR, code, FILE_NAME)


def available(code):
    return os.path.exists(path(code))


class _Index(object):
    """Sorted keys of a dictionary file and the byte offset of each entry."""

    def __init__(self, code):
        self.code = code
        keys, offsets = [], []
        try:
            with io.open(path(code), 'rb') as handle:
                offset = 0
                for line in handle:
                    if line.strip():
                        start = line.index(b'"k":"') + 5
                        end = line.index(b'"', start)
                        keys.append(line[start:end].decode('utf-8'))
                        offsets.append(offset)
                    offset += len(line)
        except OSError:
            pass
        self.keys = keys
        self.offsets = offsets

    def __len__(self):
        return len(self.keys)

    def read(self, position):
        with io.open(path(self.code), 'rb') as handle:
            handle.seek(self.offsets[position])
            return json.loads(handle.readline().decode('utf-8'))

    def positions(self, word_key):
        start = bisect.bisect_left(self.keys, word_key)
        end = bisect.bisect_right(self.keys, word_key)
        return range(start, end)

    def prefixed(self, prefix, limit):
        start = bisect.bisect_left(self.keys, prefix)
        found = []
        for position in range(start, len(self.keys)):
            if not self.keys[position].startswith(prefix) or len(found) >= limit:
                break
            found.append(position)
        return found


@functools.lru_cache(maxsize=8)
def index(code):
    return _Index(code)


def size(code):
    """Number of headwords (a word with several parts of speech counts once)."""
    keys = index(code).keys
    return sum(1 for i, k in enumerate(keys) if i == 0 or keys[i - 1] != k)


def lookup(code, term):
    """The entries for a word (every part of speech), in file order."""
    idx = index(code)
    return [idx.read(position) for position in idx.positions(key(term))]


def suggestions(code, prefix, limit=10):
    """Headwords that start with *prefix*, each once."""
    idx = index(code)
    words, seen = [], set()
    for position in idx.prefixed(key(prefix), limit * 3):
        entry = idx.read(position)
        if entry['k'] not in seen:
            seen.add(entry['k'])
            words.append(entry)
        if len(words) >= limit:
            break
    return words


def _translation_words(entry, lang):
    if lang == 'en':
        texts = [sense['en'] for sense in entry.get('senses', ())]
    elif lang == 'ca':
        texts = [item['w'] for item in entry.get(lang, ())]
    else:
        texts = entry.get(lang, ())
    words = set()
    for text in texts:
        text = _BRACKETS.sub(' ', text).lower()
        for part in re.split(r'[,;]', text):
            part = part.strip()
            if part:
                words.add(re.sub(r'^(to|a|an|the) (?=\S)', '', part))
                words.update(_WORDS.findall(part))
    return words


@functools.lru_cache(maxsize=16)
def _reverse(code, lang):
    """{translation word: "position\x1fposition..."} for one language."""
    idx = index(code)
    found = {}
    try:
        with io.open(path(code), encoding='utf-8') as handle:
            position = 0
            for line in handle:
                if not line.strip():
                    continue
                entry = json.loads(line)
                for word in _translation_words(entry, lang):
                    found.setdefault(word, []).append(str(position))
                position += 1
    except OSError:
        return {}
    assert position == len(idx)
    return {word: _SEP.join(positions) for word, positions in found.items()}


def by_translation(code, lang, query, limit=50):
    """Entries whose translation into *lang* has *query* (a word or a
    phrase), the ones where it is a whole equivalent first."""
    query = _SPACES.sub(' ', (query or '').strip().lower())
    query = re.sub(r'^(to|a|an|the) (?=\S)', '', query)
    packed = _reverse(code, lang).get(query)
    if not packed:
        return []
    idx = index(code)
    entries = [idx.read(int(position)) for position in packed.split(_SEP)[:limit * 2]]

    def exact(entry):
        texts = (_translation_words(entry, lang) if lang != 'en' else
                 {re.sub(r'^(to|a|an|the) (?=\S)', '', part.strip().lower())
                  for sense in entry.get('senses', ())
                  for part in re.split(r'[,;]', _BRACKETS.sub(' ', sense['en']))})
        return query not in texts

    entries.sort(key=lambda entry: (exact(entry), len(entry['k'])))
    return entries[:limit]


def search(code, query, langs, limit=50):
    """Entries for *query*: the word itself, then words that start with it,
    then words whose translation (in *langs*, in that order) is *query*.
    Returns (entries, how) with how one of 'word', 'prefix',
    'translation' or None."""
    query = (query or '').strip()
    if not query:
        return [], None
    found = lookup(code, query)
    if found:
        return found, 'word'
    for lang in langs:
        found = by_translation(code, lang, query, limit)
        if found:
            return found, 'translation'
    found = suggestions(code, query, limit)
    if found:
        return found, 'prefix'
    return [], None
