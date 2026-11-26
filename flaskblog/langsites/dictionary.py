"""The dictionary of a language section, read from a file on demand.

``langsites/data/<code>/dictionary.jsonl`` holds one entry a line (a word
with one part of speech), sorted by its key (lower case, without stress
marks)::

    {"k": "собака", "w": "соба́ка", "pos": "noun",
     "senses": [{"en": "dog (animal)"}, {"en": "scoundrel", "tags": ["derogatory"]}],
     "es": ["perro"], "ca": [{"w": "gos", "pos": "noun"}]}

``senses`` are the meanings, explained in English (Wiktionary's glosses);
the keys named after a language (``uk``, ``en``, ``es``, ``ca``, ``fr``,
``de``) list the word's equivalents in it, each a string or ``{"w": ...}``
(``unsure`` marks a derived one that only one route supports). Optional
keys: ``g`` gender, ``asp`` aspect (``pf``, ``ipf``) and ``pair`` its aspect
partner, ``proper`` for proper names.

``langsites/data/<code>/meta.json`` names the sources of the file
(``{"sources": [...]}``), shown under the dictionary pages.

Only the keys and their byte offsets are kept in memory, as compact
strings (the server has little memory); an entry is read from the file when
a page needs it. The index of translations, for searching in another
language, is built only when somebody searches that way.
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


LANGS = ('uk', 'en', 'es', 'ca', 'fr', 'de')


def item_word(item):
    return item['w'] if isinstance(item, dict) else item


def translations(entry, lang):
    """The equivalents of an entry in *lang*, as text; for English also
    the explanations of its meanings."""
    texts = [item_word(item) for item in entry.get(lang, ())]
    if lang == 'en':
        texts += [sense['en'] for sense in entry.get('senses', ())]
    return texts


def _phrases(texts):
    found = set()
    for text in texts:
        text = text.replace(_STRESS, '')
        for part in re.split(r'[,;]', _BRACKETS.sub(' ', text).lower()):
            part = _SPACES.sub(' ', part).strip()
            if part:
                found.add(re.sub(r'^(to|a|an|the) (?=\S)', '', part))
    return found


def meta(code):
    try:
        with io.open(os.path.join(DATA_DIR, code, 'meta.json'), encoding='utf-8') as handle:
            return json.load(handle)
    except (OSError, ValueError):
        return {}


def _translation_words(entry, lang):
    texts = translations(entry, lang)
    words = set()
    for text in texts:
        text = _BRACKETS.sub(' ', text.replace(_STRESS, '')).lower()
        for part in re.split(r'[,;]', text):
            part = part.strip()
            if part:
                words.add(re.sub(r'^(to|a|an|the) (?=\S)', '', part))
                words.update(_WORDS.findall(part))
    return words


@functools.lru_cache(maxsize=4)  # 10-20 MB each: keep a few, the server has little memory
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
    query = _SPACES.sub(' ', (query or '').replace(_STRESS, '').strip().lower())
    query = re.sub(r'^(to|a|an|the) (?=\S)', '', query)
    packed = _reverse(code, lang).get(query)
    if not packed:
        return []
    idx = index(code)
    entries = [idx.read(int(position)) for position in packed.split(_SEP)[:limit * 2]]

    def exact(entry):
        return query not in _phrases(translations(entry, lang))

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


# -- a word as it stands in a text ------------------------------------------------------------

_EN_IRREGULAR = {
    'am': 'be', 'is': 'be', 'are': 'be', 'was': 'be', 'were': 'be', 'been': 'be', 'being': 'be',
    'has': 'have', 'had': 'have', 'having': 'have', 'does': 'do', 'did': 'do', 'done': 'do',
    'went': 'go', 'gone': 'go', 'goes': 'go', 'said': 'say', 'says': 'say', 'made': 'make',
    'came': 'come', 'saw': 'see', 'seen': 'see', 'took': 'take', 'taken': 'take', 'knew': 'know',
    'known': 'know', 'thought': 'think', 'found': 'find', 'gave': 'give', 'given': 'give',
    'told': 'tell', 'felt': 'feel', 'left': 'leave', 'got': 'get', 'gotten': 'get',
    'began': 'begin', 'begun': 'begin', 'brought': 'bring', 'bought': 'buy', 'caught': 'catch',
    'fought': 'fight', 'taught': 'teach', 'sought': 'seek', 'stood': 'stand', 'understood':
    'understand', 'held': 'hold', 'kept': 'keep', 'slept': 'sleep', 'met': 'meet', 'sat': 'sit',
    'spoke': 'speak', 'spoken': 'speak', 'wrote': 'write', 'written': 'write', 'ran': 'run',
    'drew': 'draw', 'drawn': 'draw', 'grew': 'grow', 'grown': 'grow', 'threw': 'throw',
    'thrown': 'throw', 'flew': 'fly', 'ate': 'eat', 'eaten': 'eat', 'fell': 'fall', 'fallen': 'fall',
    'rose': 'rise', 'risen': 'rise', 'broke': 'break', 'broken': 'break', 'chose': 'choose',
    'chosen': 'choose', 'wore': 'wear', 'worn': 'wear', 'bore': 'bear', 'born': 'bear',
    'lay': 'lie', 'lain': 'lie', 'laid': 'lay', 'paid': 'pay', 'sold': 'sell', 'heard': 'hear',
    'meant': 'mean', 'sent': 'send', 'spent': 'spend', 'built': 'build', 'lost': 'lose',
    'led': 'lead', 'fed': 'feed', 'fled': 'flee', 'won': 'win', 'struck': 'strike', 'hung': 'hang',
    'shook': 'shake', 'forgot': 'forget', 'forgotten': 'forget', 'became': 'become',
    'swam': 'swim', 'sang': 'sing', 'sung': 'sing', 'drank': 'drink', 'drunk': 'drink',
    'men': 'man', 'women': 'woman', 'children': 'child', 'feet': 'foot', 'teeth': 'tooth',
    'mice': 'mouse', 'people': 'person', 'better': 'good', 'best': 'good', 'worse': 'bad',
    'worst': 'bad', 'thee': 'thou', 'thy': 'thou', 'thine': 'thou', 'hath': 'have', 'doth': 'do',
    'art': 'be', 'hast': 'have', 'dost': 'do', 'shalt': 'shall', 'wilt': 'will',
}


def _english_bases(word):
    if word in _EN_IRREGULAR:
        yield _EN_IRREGULAR[word]
    if word.endswith("'s"):
        yield word[:-2]
    rules = (('ies', 'y'), ('ied', 'y'), ('ves', 'f'), ('ves', 'fe'), ('ses', 's'), ('xes', 'x'),
             ('ches', 'ch'), ('shes', 'sh'), ('es', 'e'), ('s', ''), ('ed', ''), ('ed', 'e'),
             ('d', ''), ('ing', ''), ('ing', 'e'), ('ier', 'y'), ('iest', 'y'), ('er', ''),
             ('est', ''), ('ly', ''), ('ily', 'y'), ('eth', ''), ('est', 'e'))
    for ending, replacement in rules:
        if word.endswith(ending) and len(word) - len(ending) >= 2:
            base = word[:-len(ending)] + replacement
            yield base
            # doubled consonant: stopped -> stop, running -> run
            if ending in ('ed', 'ing', 'er', 'est') and len(base) > 2 and base[-1] == base[-2]:
                yield base[:-1]


def find(code, word):
    """The entries for a word as it stands in a text: the word itself, then
    its dictionary form (English: plurals, past forms, -ing...). Returns
    (entries, the form found) or ([], None)."""
    word = (word or '').strip().strip("'’").replace('’', "'")
    candidates = [word, word.lower()]
    if code == 'en':
        candidates += list(_english_bases(word.lower()))
    seen = set()
    for candidate in candidates:
        if candidate in seen or not candidate:
            continue
        seen.add(candidate)
        entries = lookup(code, candidate)
        if entries:
            return entries, candidate
    return [], None
