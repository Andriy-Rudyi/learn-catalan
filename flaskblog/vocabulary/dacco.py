"""DACCO, the open Catalan-English dictionary (CC BY-SA 2.5), as data.

``data/sources/dacco/entries.jsonl`` holds its Catalan-to-English part, one
entry a line, read from the PDF the DACCO team published (2012-01) with
:func:`parse_pdf` (``flask vocabulary dacco-parse``)::

    {"head": "català",
     "blocks": [{"pos": "noun",
                 "senses": [{"n": 1, "gender": "m", "text": "Catalan"},
                            {"n": 2, "gender": "m/f", "text": "Catalan"}]},
                {"pos": "adjective", "senses": [{"text": "Catalan"}]}],
     "expressions": [{"ca": "...", "en": "...", "gender": "f", "split_guess": true}],
     "notes": ["..."]}

A sense's ``text`` holds the English translations separated by " / ",
sometimes with a Catalan gloss in square brackets ("[amb un verb de
moviment] to / into") and labels in brackets ("(Am.)"). ``domain`` is a
subject label ("sport"), ``examples`` are pairs {"ca", "en"}.

Most expressions are printed with a gender between the Catalan phrase and
its English, which splits them. The others were split by guessing where the
English starts; they carry ``split_guess`` and need a look before they are
shown.

Nothing here is in the site's dictionary yet: the module only reads the
data, finds the entries for a word and builds the English-to-Catalan index
a future English site needs. Whatever is made from it stays under CC BY-SA
and credits DACCO (http://www.catalandictionary.org).
"""

import functools
import io
import json
import os
import re

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         'data', 'sources', 'dacco', 'entries.jsonl')

SOURCE = {
    'name': 'DACCO: The Open Source English-Catalan Dictionary (2012-01)',
    'url': 'http://www.catalandictionary.org',
    'licence': 'CC BY-SA 2.5',
}


@functools.lru_cache(maxsize=1)
def load():
    try:
        with io.open(DATA_FILE, encoding='utf-8') as handle:
            return [json.loads(line) for line in handle if line.strip()]
    except OSError:
        return []


def senses(entry):
    """Every sense of an entry with its part of speech and gender."""
    for block in entry.get('blocks', []):
        for sense in block.get('senses', []):
            yield dict(sense, pos=block.get('pos'), gender=sense.get('gender') or block.get('gender'))


_GLOSS = re.compile(r'\[[^\]]*\]')


def translations(sense):
    """The English words of a sense, without the Catalan gloss."""
    text = _GLOSS.sub('', sense.get('text', ''))
    return [part.strip() for part in text.split(' / ') if part.strip() and part.strip() != '-']


def _key(term):
    return (term or '').strip().lower()


@functools.lru_cache(maxsize=1)
def _index():
    index = {}
    for entry in load():
        head = _key(entry['head'])
        index.setdefault(head, []).append(entry)
        # A verb listed as "abalançar-se" is found as "abalançar" too.
        for ending in ('-se', "'s"):
            if head.endswith(ending):
                index.setdefault(head[:-len(ending)], []).append(entry)
    return index


def lookup(term):
    """The DACCO entries for a Catalan word ("abalançar" finds "abalançar-se")."""
    return _index().get(_key(term), [])


_ARTICLE = re.compile(r'^(to|the|a|an)\s+', re.I)
_BRACKETS = re.compile(r'\([^)]*\)')


def english_key(text):
    """"to rush towards (someone)" -> "rush towards"."""
    text = _BRACKETS.sub('', text).strip().lower()
    return re.sub(r'\s+', ' ', _ARTICLE.sub('', text)).strip()


@functools.lru_cache(maxsize=1)
def english_index():
    """English word -> [(Catalan head, part of speech, sense number)], for
    looking words up the other way (a future English site)."""
    index = {}
    for entry in load():
        for sense in senses(entry):
            for word in translations(sense):
                key = english_key(word)
                if key:
                    index.setdefault(key, []).append((entry['head'], sense.get('pos'), sense.get('n')))
    return index


def stats(words=()):
    """Numbers about the data, and how much of *words* (Catalan terms) it covers."""
    entries = load()
    all_senses = [s for e in entries for s in senses(e)]
    words = {_key(w) for w in words}
    found = {w for w in words if lookup(w)}
    return {
        'entries': len(entries),
        'senses': len(all_senses),
        'translations': sum(len(translations(s)) for s in all_senses),
        'examples': sum(len(s.get('examples', [])) for s in all_senses)
        + sum(len(x.get('examples', [])) for e in entries for x in e.get('expressions', [])),
        'expressions': sum(len(e.get('expressions', [])) for e in entries),
        'expressions_to_check': sum(1 for e in entries for x in e.get('expressions', [])
                                    if x.get('split_guess')),
        'notes': sum(len(e.get('notes', [])) for e in entries),
        'words': len(words),
        'words_found': len(found),
        'new_heads': len({_key(e['head']) for e in entries} - words) if words else None,
    }


# -- reading the PDF ------------------------------------------------------------------------

# The PDF marks every part of an entry with its own font.
_KINDS = {
    ('Arial,Bold', 12.0): 'head',
    ('TimesNewRoman', 6.0): 'label',        # part of speech, gender, "expression", [domain]
    ('TimesNewRoman', 8.0): 'num',          # sense number
    ('TimesNewRoman', 12.0): 'text',        # translations
    ('TimesNewRoman,Bold', 12.0): 'text',
    ('TimesNewRoman,Bold', 10.0): 'ex_ca',
    ('TimesNewRoman,Italic', 10.0): 'ex_en',
    ('TimesNewRoman,BoldItalic', 8.0): 'sep',
    ('TimesNewRoman', 10.0): 'note',
}
_POS = {'noun', 'adjective', 'verb', 'adverb', 'preposition', 'conjunction', 'pronoun',
        'exclamation'}
_GENDERS = {'m': 'm', 'f': 'f', 'm / f': 'm/f', 'mf': 'm/f', 'mpl': 'm pl', 'fpl': 'f pl'}


def _spans(path):
    import pymupdf  # only needed to re-read the PDF: pip install pymupdf

    document = pymupdf.open(path)
    for page in document.pages(1, len(document)):  # page 1 is the title page
        middle = page.rect.width / 2
        found = []
        for block in page.get_text('dict')['blocks']:
            for line in block.get('lines', []):
                for span in line['spans']:
                    kind = _KINDS.get((span['font'], round(span['size'], 1)))
                    top = span['bbox'][1]
                    if kind is None or not span['text'].strip() or top < 40 or top > 805:
                        continue  # letter headings, running header and footer
                    column = 0 if span['bbox'][0] < middle - 10 else 1
                    found.append((column, round(line['bbox'][3]), span['bbox'][0], kind, span['text']))
        found.sort(key=lambda row: row[:3])
        for column, line, _x, kind, text in found:
            yield kind, text, (column, line)


def _tokens(path):
    """Spans of the same kind joined; "m /" + "/ f" joined; "fullform" dropped."""
    merged, last = [], None
    for kind, text, line in _spans(path):
        if merged and merged[-1][0] == kind and kind in ('text', 'ex_ca', 'ex_en', 'note'):
            merged[-1][1] += (' ' if line != last else '') + text
        else:
            merged.append([kind, text])
        last = line
    held = None
    for kind, text in merged:
        text = re.sub(r'\s+', ' ', text).strip()
        if kind == 'label':
            text = text.replace('fullform', '').strip()
            if text == 'm /':
                held = text
                continue
            if held and text == '/ f':
                text, held = 'm / f', None
        if held:
            yield 'label', held
            held = None
        yield kind, text


def _new_sense(block, number=None):
    sense = {'n': number, 'gender': None, 'domain': None, 'text': '', 'examples': []}
    block['senses'].append(sense)
    return sense


def _append(holder, key, text):
    holder[key] = (holder[key] + ' ' + text).strip()


def parse_pdf(path):
    """The entries of the DACCO Catalan-English PDF."""
    entries = []
    entry = block = sense = expression = None
    for kind, text in _tokens(path):
        if kind == 'head':
            entry = {'head': text, 'blocks': [], 'expressions': [], 'notes': []}
            entries.append(entry)
            block = sense = expression = None
            continue
        if entry is None or kind == 'sep':
            continue
        if kind == 'note':
            entry['notes'].append(text)
            continue
        if kind == 'label' and text in _POS:
            block = {'pos': text, 'gender': None, 'senses': []}
            entry['blocks'].append(block)
            sense = expression = None
            continue
        if kind == 'label' and text == 'expression':
            expression = {'ca': '', 'gender': None, 'en': '', 'examples': [], 'split': False}
            entry['expressions'].append(expression)
            continue
        if expression is not None:
            if kind == 'num':
                # "d'hora 1 early 2 soon": numbered meanings of the expression
                if expression['en']:
                    expression['en'] += ';'
                expression['split'] = True
            elif kind == 'label':
                expression['gender'] = _GENDERS.get(text, expression['gender'])
                expression['split'] = True
            elif kind == 'text':
                _append(expression, 'en' if expression['split'] else 'ca', text)
            elif kind == 'ex_ca':
                expression['examples'].append({'ca': text, 'en': ''})
            elif kind == 'ex_en' and expression['examples']:
                _append(expression['examples'][-1], 'en', text)
            continue
        expression = None
        if block is None:
            block = {'pos': None, 'gender': None, 'senses': []}
            entry['blocks'].append(block)
        if kind == 'num':
            sense = _new_sense(block, int(text) if text.isdigit() else text)
        elif kind == 'label':
            if sense is None and not block['senses'] and not text.startswith('['):
                block['gender'] = _GENDERS.get(text, text)
                continue
            if sense is None or sense['text']:
                sense = _new_sense(block)
            if text.startswith('['):
                sense['domain'] = text.strip('[]')
            else:
                sense['gender'] = _GENDERS.get(text, text)
        elif kind == 'text':
            if sense is None or sense['examples']:
                sense = _new_sense(block)
            _append(sense, 'text', text)
        elif kind == 'ex_ca':
            if sense is None:
                sense = _new_sense(block)
            sense['examples'].append({'ca': text, 'en': ''})
        elif kind == 'ex_en' and sense is not None and sense['examples']:
            _append(sense['examples'][-1], 'en', text)
    for entry in entries:
        holders = [s for b in entry['blocks'] for s in b['senses']] + entry['expressions']
        for holder in holders:
            for example in holder['examples']:
                example['en'] = re.sub(r'^-\s*', '', example['en']).strip()
    _split_expressions(entries)
    return [_compact(entry) for entry in entries]


_WORD = re.compile(r"[\w·'’-]+", re.U)
_EN_WORDS = set("to the an of be on at in with for from by up out off somebody someone something "
                "it its your you one's not have get go make take do is are very like into over down".split())
_CA_WORDS = set("el la els les de del dels a al als en amb per que i un una uns unes no es se fer "
                "ser estar tenir anar posar hi ho li com més sense sobre fins molt tot cap dir donar".split())
_ACCENTED = re.compile(r'[àèéíïòóúüç·]')


def _split_expressions(entries):
    """Split the expressions printed without a gender, where the English
    most likely starts; mark them ``split_guess``."""
    def words(text):
        return [w.lower() for w in _WORD.findall(text)]

    catalan, english = set(), set()
    for entry in entries:
        catalan.update(words(entry['head']))
        for block in entry['blocks']:
            for sense in block['senses']:
                english.update(words(re.sub(r'\([^)]*\)|\[[^\]]*\]', '', sense['text'])))
                for example in sense['examples']:
                    catalan.update(words(example['ca']))
                    english.update(words(example['en']))
        for expression in entry['expressions']:
            if expression['split']:
                catalan.update(words(expression['ca']))
                english.update(words(expression['en']))

    def score(token, side):
        word = token.lower().strip('()[],.;:!?¿¡')
        if word in _EN_WORDS:
            return 2 if side == 'en' else -2
        if word in _CA_WORDS or word.startswith(("l'", "d'", "s'", "n'")):
            return 2 if side == 'ca' else -2
        is_ca = word in catalan or bool(_ACCENTED.search(word))
        is_en = word in english
        mine, other = (is_ca, is_en) if side == 'ca' else (is_en, is_ca)
        return 1 if mine and not other else (-1 if other and not mine else 0)

    for entry in entries:
        stem = entry['head'].lower()[:4]
        for expression in entry['expressions']:
            if expression.pop('split') or not expression['ca']:
                continue
            tokens = expression['ca'].split(' ')
            best = None
            for k in range(1, len(tokens)):
                left = tokens[:k]
                if stem not in ' '.join(left).lower() and not any(t.lower() in catalan for t in left):
                    continue
                points = sum(score(t, 'ca') for t in left) + sum(score(t, 'en') for t in tokens[k:])
                if best is None or points >= best[0]:
                    best = (points, k)
            if best:
                expression['ca'] = ' '.join(tokens[:best[1]])
                expression['en'] = ' '.join(tokens[best[1]:])
            expression['split_guess'] = True


def _compact(value):
    if isinstance(value, dict):
        return {k: _compact(v) for k, v in value.items() if v not in (None, '', [], False)}
    if isinstance(value, list):
        return [_compact(v) for v in value]
    return value


def write(entries, path=DATA_FILE):
    with io.open(path, 'w', encoding='utf-8') as handle:
        for entry in entries:
            handle.write(json.dumps(entry, ensure_ascii=False, separators=(',', ':')) + '\n')
