"""The site's own translator, built to get better as it is used.

A sentence is translated, best first, from:

1. the translation memory: sentences people translated, the ones approved
   on /translator (TranslationMemory) and the ones bundled with the course
   (dictionary examples, grammar examples);
2. word by word: the dictionary's fixed expressions, contractions (del, al),
   articles as the target language uses them, clitics (l', d', -ho) and the
   reader's analysis of forms (decidiren -> decidir). This is a gloss, not a
   translation, and is shown as one.

When the memory has a sentence close to the one asked for, it is offered
too. Every approved correction goes into the memory, so the next time the
same sentence comes out right.

Catalan is the language of the site: one side of every translation is
Catalan. Into Catalan, word by word uses the dictionary the other way round.
"""

import difflib
import hashlib
import re
import time
import unicodedata
from collections import defaultdict, namedtuple

from flask import current_app

from flaskblog import db
from flaskblog.languages import SOURCE
from flaskblog.models import TranslationMemory, Word

MAX_TEXT = 2000           # characters per request
CACHE_SECONDS = 300       # dictionary and bundled memory
MEMORY_SECONDS = 60       # approved sentences from the database
SIMILAR_RATIO = 0.6       # how close a memory sentence must be to be offered
LEVEL_RANK = {'A1': 0, 'A2': 1, 'B1': 2, 'B2': 3, 'C1': 4}

Pair = namedtuple('Pair', 'source target origin')

APOSTROPHES = "'’"
_SENTENCE = re.compile(r'[^.!?…]+[.!?…]*["»”)]*\s*|\S+')
_TOKEN = re.compile(r"[\w·]+(?:['’][\w·]+)*(?:-[\w·]+)*|[^\w\s]", re.UNICODE)
_ELIDED = re.compile(r"^([ldmtsn])['’](?=\w)", re.IGNORECASE)
_CLITIC = re.compile(r"^(.+?)(-(?:hi|ho|la|les|li|lo|los|me|ne|nos|se|te|us|vos|en|el|m|t|s|n|l|ns|ls))+$",
                     re.IGNORECASE)
_PARENTHESES = re.compile(r'\([^)]*\)')

# Function words the dictionary cannot translate word for word.
ARTICLES = {
    'uk': {},
    'en': {'el': 'the', 'la': 'the', 'els': 'the', 'les': 'the', "l'": 'the', 'lo': 'the',
           'un': 'a', 'una': 'a', 'uns': 'some', 'unes': 'some'},
    'fr': {'el': 'le', 'la': 'la', 'els': 'les', 'les': 'les', "l'": "l'", 'lo': 'le',
           'un': 'un', 'una': 'une', 'uns': 'des', 'unes': 'des'},
}
CONTRACTIONS = {
    'al': {'uk': 'до', 'en': 'to the', 'fr': 'au'},
    'als': {'uk': 'до', 'en': 'to the', 'fr': 'aux'},
    'del': {'uk': 'з', 'en': 'of the', 'fr': 'du'},
    'dels': {'uk': 'з', 'en': 'of the', 'fr': 'des'},
    'pel': {'uk': 'через', 'en': 'through the', 'fr': 'par le'},
    'pels': {'uk': 'через', 'en': 'through the', 'fr': 'par les'},
    "d'": {'uk': 'з', 'en': 'of', 'fr': "d'"},
    'de': {'uk': 'з', 'en': 'of', 'fr': 'de'},
    'a': {'uk': 'до', 'en': 'to', 'fr': 'à'},
}
# "va obrir", "ha obert": the auxiliary goes, the verb says what tense it is.
PAST_AUXILIARIES = {'vaig', 'vas', 'vares', 'va', 'vam', 'vàrem', 'vau', 'vàreu', 'van', 'varen'}
PERFECT_AUXILIARIES = {'he', 'has', 'ha', 'hem', 'heu', 'han', 'havia', 'havies', 'havíem', 'havíeu', 'havien'}
# Elided and attached pronouns, as the dictionary has them.
CLITICS = {"m'": 'em', "t'": 'et', "s'": 'es', "n'": 'en', "l'": 'el',
           '-me': 'em', '-te': 'et', '-se': 'es', '-ne': 'en', '-n': 'en', '-hi': 'hi', '-ho': 'ho',
           '-la': 'el', '-les': 'el', '-li': 'li', '-lo': 'el', '-los': 'el', '-l': 'el',
           '-nos': 'ens', '-ns': 'ens', '-vos': 'us', '-us': 'us', '-m': 'em', '-t': 'et', '-s': 'es'}


# -- text helpers ---------------------------------------------------------------------

def normalise(text):
    """Lower case, one kind of apostrophe, no punctuation: the key of a sentence."""
    text = unicodedata.normalize('NFC', text or '').lower().replace('’', "'")
    text = re.sub(r"[^\w\s'·-]", ' ', text)
    return ' '.join(text.split())


def key_of(text):
    return hashlib.sha1(normalise(text).encode('utf-8')).hexdigest()


def sentences(text):
    """The text cut into sentences, each with the spaces after it."""
    text = unicodedata.normalize('NFC', (text or '').replace('\r\n', '\n'))
    return [part for part in _SENTENCE.findall(text) if part]


def _first_meaning(translation, lang):
    """'дім, будинок; рід' -> 'дім': the first word of the first meaning."""
    for meaning in (translation or '').split(';'):
        for item in _PARENTHESES.sub('', meaning).split(','):
            text = item.strip()
            if lang == 'en' and text.startswith('to '):
                text = text[3:]
            if text:
                return text
    return None


def _cached(name, seconds, build):
    store = current_app.extensions.setdefault('translator_cache', {})
    entry = store.get(name)
    now = time.monotonic()
    if entry is None or entry[0] < now:
        entry = (now + seconds, build())
        store[name] = entry
    return entry[1]


def forget():
    """Drop the caches (after an approval, and in tests)."""
    current_app.extensions.pop('translator_cache', None)


# -- what the translator knows --------------------------------------------------------------

def _dictionary():
    """{lang: {'words': {term: (gloss, full)}, 'phrases': {tokens: term},
    'reverse': {phrase: term}}} from the dictionary in the database."""
    out = {}
    words = Word.query.all()
    phrases = {}
    for word in words:
        tokens = tuple(normalise(word.term).replace("'", "' ").split())
        if len(tokens) > 1:
            phrases[tokens] = word.term.lower()
    for lang in ('uk', 'en', 'fr'):
        glosses, reverse = {}, {}
        for word in words:
            entry = word.translation_in(lang, fallback=False)
            if entry is None:
                continue
            full = entry.translation
            if word.senses:
                sense = word.senses[0].text_in(lang, fallback=False)
                first = sense.text if sense is not None else full
            else:
                first = full
            glosses[word.term.lower()] = (_first_meaning(first, lang), full, word.slug)
            rank = (LEVEL_RANK.get(word.level, 5), len(word.term))
            for meaning in full.split(';'):
                for item in _PARENTHESES.sub('', meaning).split(','):
                    item = normalise(item)
                    if lang == 'en' and item.startswith('to '):
                        item = item[3:]
                    if item and (item not in reverse or rank < reverse[item][1]):
                        reverse[item] = (word.term, rank)
        out[lang] = {'words': glosses, 'reverse': {k: v[0] for k, v in reverse.items()},
                     'rank': {k: v[1] for k, v in reverse.items()}}
    out['phrases'] = phrases
    out['terms'] = {word.term.lower() for word in words}
    return out


def dictionary():
    return _cached('dictionary', CACHE_SECONDS, _dictionary)


def _bundled_pairs():
    """{lang: [(catalan, translation)]}: the course's own translated sentences."""
    from flaskblog.grammar import service as grammar
    pairs = defaultdict(list)
    for word in Word.query.filter(Word.example_ca.isnot(None)):
        for lang, entry in word.translations.items():
            if entry.example and word.example_ca:
                pairs[lang].append((word.example_ca, entry.example))
    try:
        for unit in grammar.load_units():
            for example in unit.get('examples', []):
                if example.get('ca') and example.get('uk'):
                    pairs['uk'].append((example['ca'], example['uk']))
        for version in grammar.load_translations('en').values():
            for example in version.get('examples', []):
                if example.get('ca') and example.get('en'):
                    pairs['en'].append((example['ca'], example['en']))
    except (OSError, ValueError):
        pass
    return dict(pairs)


class Memory(object):
    """Sentences in one direction, found by their key or by likeness."""

    def __init__(self):
        self.exact = {}
        self.items = []
        self.index = defaultdict(set)

    def add(self, source, target, origin, override=False):
        key = normalise(source)
        if not key or (key in self.exact and not override):
            return
        self.exact[key] = Pair(source, target, origin)
        number = len(self.items)
        self.items.append((key, Pair(source, target, origin)))
        for token in set(key.split()):
            if len(token) > 3:
                self.index[token].add(number)

    def find(self, sentence):
        return self.exact.get(normalise(sentence))

    def similar(self, sentence):
        """The closest sentence that is not the same, or None."""
        key = normalise(sentence)
        tokens = [t for t in set(key.split()) if len(t) > 3]
        counts = defaultdict(int)
        for token in tokens:
            for number in self.index.get(token, ()):
                counts[number] += 1
        best, best_ratio = None, SIMILAR_RATIO
        for number, _count in sorted(counts.items(), key=lambda kv: -kv[1])[:40]:
            other, pair = self.items[number]
            if other == key:
                continue
            ratio = difflib.SequenceMatcher(None, key, other).ratio()
            if ratio > best_ratio:
                best, best_ratio = pair, ratio
        return best


def _bundled_memories():
    memories = {}
    for lang, pairs in _bundled_pairs().items():
        forward, backward = memories.setdefault((SOURCE, lang), Memory()), memories.setdefault((lang, SOURCE), Memory())
        for catalan, other in pairs:
            forward.add(catalan, other, 'course')
            backward.add(other, catalan, 'course')
    return memories


def _approved():
    rows = TranslationMemory.query.filter_by(status=TranslationMemory.APPROVED) \
        .order_by(TranslationMemory.id).all()
    return [(row.source_lang, row.target_lang, row.source_text, row.target_text) for row in rows]


def memory(source, target):
    """The Memory for one direction: the course's sentences, and on top of
    them (winning) the ones approved on the site."""
    def build():
        bundled = _cached('bundled', CACHE_SECONDS, _bundled_memories)
        result = Memory()
        for row in _cached('approved', MEMORY_SECONDS, _approved):
            if (row[0], row[1]) == (source, target):
                result.add(row[2], row[3], 'people')
            elif (row[1], row[0]) == (source, target):
                result.add(row[3], row[2], 'people')
        base = bundled.get((source, target))
        if base is not None:
            for _key, pair in base.items:
                result.add(pair.source, pair.target, pair.origin)
        return result
    return _cached('memory:%s:%s' % (source, target), MEMORY_SECONDS, build)


# -- word by word -------------------------------------------------------------------------------

def _tokens(sentence):
    """Words and punctuation; elided articles and clitic pronouns apart."""
    out = []
    for match in _TOKEN.finditer(sentence):
        text = match.group(0)
        space = match.end() < len(sentence) and sentence[match.end()].isspace()
        if not re.match(r'\w', text):
            out.append({'text': text, 'space': space, 'punct': True})
            continue
        elided = _ELIDED.match(text)
        if elided:
            out.append({'text': text[:2], 'space': False, 'punct': False})
            text = text[2:]
        clitics = []
        attached = _CLITIC.match(text)
        if attached and '-' in text:
            head, _, tail = text.partition('-')
            clitics = ['-' + part for part in tail.split('-')]
            text = head
        out.append({'text': text, 'space': space and not clitics, 'punct': False})
        for number, clitic in enumerate(clitics):
            last = number == len(clitics) - 1
            out.append({'text': clitic, 'space': space and last, 'punct': False})
    return out


def _next_word(tokens, i):
    """The next word after tokens[i], skipping clitics ("va", "-ho"), or None."""
    for token in tokens[i + 1:]:
        if token['punct']:
            return None
        if token['text'].startswith('-') or token['text'].lower().replace('’', "'") in CLITICS:
            continue
        return token['text']
    return None


def _auxiliary(low, following, morphology):
    """A tense label when *low* is "va" before an infinitive or "ha" before a
    participle (those verbs go with the main verb), else None."""
    if following is None or (low not in PAST_AUXILIARIES and low not in PERFECT_AUXILIARIES):
        return None
    slots = [slot for _lemma, kind, slot in morphology.readings(following) if kind == 'verb']
    if low in PAST_AUXILIARIES and any(slot[1] == 'infinitiu-present' for slot in slots):
        return 'passat perifràstic'
    if low in PERFECT_AUXILIARIES and any(slot[0] == 'particip' for slot in slots):
        return 'perfet' if low in ('he', 'has', 'ha', 'hem', 'heu', 'han') else 'plusquamperfet'
    return None


def _from_catalan(sentence, target, known):
    from flaskblog.reader import morphology
    from flaskblog.reader.routes import _form_label
    words = known[target]['words']
    phrases = known['phrases']
    tokens = _tokens(sentence)
    out, i, previous, pending_tense = [], 0, '', None
    while i < len(tokens):
        token = tokens[i]
        if token['punct']:
            out.append({'text': token['text'], 'gloss': token['text'], 'space': token['space'], 'punct': True})
            i += 1
            continue
        # The longest fixed expression of the dictionary starting here.
        matched = None
        for length in range(min(5, len(tokens) - i), 1, -1):
            span = tokens[i:i + length]
            if any(t['punct'] for t in span):
                continue
            key = tuple(normalise(t['text']).replace("'", "' ").strip() for t in span)
            key = tuple(part for piece in key for part in piece.split())
            if key in phrases and phrases[key] in words:
                matched = (length, phrases[key])
                break
        if matched:
            length, term = matched
            gloss, full, slug = words[term]
            out.append({'text': ' '.join(t['text'] for t in tokens[i:i + length]), 'gloss': gloss,
                        'full': full, 'lemma': term, 'slug': slug, 'space': tokens[i + length - 1]['space']})
            i += length
            continue
        text = token['text']
        low = text.lower().replace('’', "'")
        entry = {'text': text, 'space': token['space']}
        following = _next_word(tokens, i)
        auxiliary = _auxiliary(low, following, morphology)
        if auxiliary:
            entry.update(gloss='', auxiliary=auxiliary)
            pending_tense = auxiliary
            out.append(entry)
            previous = text
            i += 1
            continue
        if low in CONTRACTIONS:
            entry['gloss'] = CONTRACTIONS[low][target]
        elif low in ARTICLES['fr']:
            entry['gloss'] = ARTICLES[target].get(low, '')
        elif low in CLITICS and CLITICS[low] in words:
            entry['gloss'], entry['full'], entry['slug'] = words[CLITICS[low]]
            entry['lemma'] = CLITICS[low]
        else:
            found = None
            if low in words:
                found = (low, 'word', None)
            else:
                for lemma, kind, slot in morphology.readings(text, previous, known=lambda l: l in words):
                    if lemma.lower() in words:
                        found = (lemma.lower(), kind, slot)
                        break
            if found:
                lemma, kind, slot = found
                entry['gloss'], entry['full'], entry['slug'] = words[lemma]
                entry['lemma'] = lemma
                if kind == 'verb' and slot:
                    entry['form'] = _form_label({'kind': 'verb', 'slot': slot})
                if pending_tense:
                    entry['form'] = pending_tense
            else:
                entry['gloss'] = None    # not known: the word stays as it is
            pending_tense = None
        out.append(entry)
        previous = text
        i += 1
    return out


# Words the dictionary cannot find from these languages (inflected
# pronouns, auxiliaries), straight to Catalan.
FUNCTION_WORDS = {
    'uk': {'я': 'jo', 'ти': 'tu', 'він': 'ell', 'вона': 'ella', 'воно': 'ell', 'ми': 'nosaltres',
           'ви': 'vosaltres', 'вони': 'ells', 'мій': 'meu', 'моя': 'meva', 'моє': 'meu', 'мої': 'meus',
           'твій': 'teu', 'твоя': 'teva', 'твоє': 'teu', 'твої': 'teus', 'наш': 'nostre', 'наша': 'nostra',
           'наше': 'nostre', 'наші': 'nostres', 'ваш': 'vostre', 'ваша': 'vostra', 'ваше': 'vostre',
           'ваші': 'vostres', 'його': 'seu', 'її': 'seva', 'їхній': 'seu', 'їхня': 'seva', 'і': 'i', 'й': 'i',
           'та': 'i', 'але': 'però', 'або': 'o', 'чи': 'o', 'що': 'que', 'не': 'no', 'так': 'sí',
           'в': 'a', 'у': 'a', 'на': 'a', 'до': 'a', 'з': 'de', 'із': 'de', 'зі': 'de', 'для': 'per a'},
    'en': {'i': 'jo', 'you': 'tu', 'he': 'ell', 'she': 'ella', 'we': 'nosaltres', 'they': 'ells',
           'is': 'és', 'are': 'són', 'am': 'soc', 'was': 'era', 'were': 'eren', 'my': 'meu', 'your': 'teu',
           'his': 'seu', 'her': 'seva', 'our': 'nostre', 'their': 'seu', 'and': 'i', 'but': 'però',
           'or': 'o', 'not': 'no', "don't": 'no', "doesn't": 'no', 'to': 'a', 'in': 'a', 'of': 'de'},
    'fr': {'je': 'jo', 'tu': 'tu', 'il': 'ell', 'elle': 'ella', 'nous': 'nosaltres', 'vous': 'vosaltres',
           'ils': 'ells', 'elles': 'elles', 'est': 'és', 'sont': 'són', 'suis': 'soc', 'mon': 'meu',
           'ma': 'meva', 'mes': 'meus', 'et': 'i', 'mais': 'però', 'ou': 'o', 'ne': '', 'pas': 'no',
           'à': 'a', 'au': 'al', 'de': 'de', 'du': 'del', 'en': 'a', 'dans': 'a'},
}

# Endings a Ukrainian stem can have in the dictionary (nominative, infinitive).
NOMINATIVE = {
    'uk': ('', 'о', 'а', 'я', 'ь', 'ий', 'ій', 'е', 'и', 'ти', 'іти', 'ати', 'ити', 'увати', 'ювати'),
    'en': ('',),
    'fr': ('',),
}


def _endings(word, lang):
    """Forms to try for a word not found as it is (very rough stemming)."""
    if lang == 'uk':
        cut = ('ами', 'ями', 'ові', 'еві', 'ого', 'ому', 'ими', 'ій', 'ий', 'ої', 'ою', 'ею', 'ів', 'ах',
               'ях', 'ам', 'ям', 'ом', 'ем', 'ть', 'ла', 'ли', 'ло', 'в', 'а', 'я', 'у', 'ю', 'і', 'и', 'е', 'о')
        stems = [word[:-len(end)] for end in cut if word.endswith(end) and len(word) - len(end) >= 3]
        # Verbs: "живе", "живуть" -> жи(ти); "працює" -> працю(вати)
        for end in ('юють', 'ують', 'ює', 'ує', 'ють', 'ить', 'ать', 'ять', 'уть', 'ете', 'емо', 'ите', 'имо',
                    'еш', 'иш', 'ю', 'у', 'е'):
            if word.endswith(end) and len(word) - len(end) >= 2:
                stems.append(word[:-len(end)])
        return [word] + stems
    if lang == 'en':
        forms = []
        for end, add in (('ies', 'y'), ('es', ''), ('s', ''), ('ed', ''), ('ed', 'e'), ('ing', ''), ('ing', 'e')):
            if word.endswith(end) and len(word) - len(end) >= 2:
                forms.append(word[:-len(end)] + add)
        return forms
    if lang == 'fr':
        return [word[:-1]] if word.endswith(('s', 'x', 'e')) and len(word) > 3 else []
    return []


def _into_catalan(sentence, source, known):
    reverse = known[source]['reverse']
    tokens = _tokens(sentence) if source != 'uk' else [
        {'text': m.group(0), 'space': m.end() < len(sentence) and sentence[m.end()].isspace(),
         'punct': not re.match(r'\w', m.group(0))}
        for m in re.finditer(r"[\w'’-]+|[^\w\s]", sentence)]
    out, i = [], 0
    skip = {'en': {'the', 'a', 'an'}, 'fr': {'le', 'la', 'les', "l'", 'un', 'une', 'des'}, 'uk': set()}[source]
    while i < len(tokens):
        token = tokens[i]
        if token['punct']:
            out.append({'text': token['text'], 'gloss': token['text'], 'space': token['space'], 'punct': True})
            i += 1
            continue
        matched = None
        for length in range(min(4, len(tokens) - i), 0, -1):
            span = tokens[i:i + length]
            if any(t['punct'] for t in span):
                continue
            key = normalise(' '.join(t['text'] for t in span))
            if length == 1 and key in skip:
                break
            if key in FUNCTION_WORDS.get(source, {}) and length == 1:
                matched = (1, FUNCTION_WORDS[source][key])
                break
            if key in reverse:
                matched = (length, reverse[key])
                break
        if matched:
            length, term = matched
            out.append({'text': ' '.join(t['text'] for t in tokens[i:i + length]), 'gloss': term,
                        'lemma': term.lower(), 'space': tokens[i + length - 1]['space']})
            i += length
            continue
        low = normalise(token['text'])
        entry = {'text': token['text'], 'space': token['space']}
        if low in skip:
            entry['gloss'] = ''
        else:
            # Dictionary forms the word can come from ("місті" -> місто, міст),
            # the most common one first.
            rank = known[source]['rank']
            candidates = set()
            for stem in _endings(low, source):
                for end in NOMINATIVE.get(source, ('',)):
                    if stem + end in reverse:
                        candidates.add(stem + end)
            best = min(candidates, key=lambda k: (rank[k][0], abs(len(k) - len(low)), rank[k][1])) \
                if candidates else None
            term = reverse[best] if best else None
            entry['gloss'] = term
            if term:
                entry['lemma'] = term.lower()
                entry['guess'] = True
        out.append(entry)
        i += 1
    return out


OPENING = '«(¿¡"“'


def _join(tokens):
    """The glosses as a line of text: words apart, punctuation attached."""
    line, opened = '', True
    for token in tokens:
        gloss = token.get('gloss')
        if gloss == '':
            continue
        text = gloss if gloss is not None else token['text']
        if token.get('punct') and text not in OPENING:
            line += text
            opened = False
            continue
        if line and not opened and not line.endswith("'"):
            line += ' '
        line += text
        opened = token.get('punct', False)
    return line.strip()


def _capitalise(source, line):
    stripped = source.lstrip('«"(¡¿ ')
    if stripped[:1].isupper() and line:
        return line[0].upper() + line[1:]
    return line


# -- public ----------------------------------------------------------------------------------------

def translate(text, source, target):
    """{'sentences': [{source, target, method, similar, tokens}]} for *text*.

    method: 'memory' (a sentence people translated), 'words' (word by word)."""
    text = (text or '')[:MAX_TEXT]
    known = dictionary()
    mem = memory(source, target)
    result = []
    for sentence in sentences(text):
        stripped = sentence.strip()
        if not stripped:
            continue
        item = {'source': stripped, 'similar': None}
        pair = mem.find(stripped)
        if pair is not None:
            item.update(target=pair.target, method='memory', origin=pair.origin, tokens=None)
        else:
            if source == SOURCE:
                tokens = _from_catalan(stripped, target, known)
            else:
                tokens = _into_catalan(stripped, source, known)
            item.update(target=_capitalise(stripped, _join(tokens)), method='words', tokens=tokens)
            close = mem.similar(stripped)
            if close is not None:
                item['similar'] = {'source': close.source, 'target': close.target}
        result.append(item)
    return {'source': source, 'target': target, 'sentences': result}


def propose(source, target, source_text, target_text, user, approved):
    """A better translation of one sentence, from someone on the site."""
    row = TranslationMemory(
        source_lang=source, target_lang=target, source_key=key_of(source_text),
        source_text=source_text.strip(), target_text=target_text.strip(),
        status=TranslationMemory.APPROVED if approved else TranslationMemory.PENDING,
        created_by=user.id if user is not None else None,
    )
    if approved:
        row.decided_by = row.created_by
        from datetime import datetime
        row.decided_at = datetime.utcnow()
    db.session.add(row)
    return row
