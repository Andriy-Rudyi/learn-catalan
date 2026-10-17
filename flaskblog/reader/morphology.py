"""What a Catalan word in running text is, and its synonyms in the same form.

Click "convingueren" and you get *convenir*, simple past, 3rd person plural,
and synonyms put into that same slot (acordaren, pactaren...); click "cases"
and you get *casa*, plural, and plural synonyms (llars, habitatges...).

* Verbs: every simple form of every verb the conjugator knows (verbecc with
  this project's corrections, flaskblog/conjugation). Forms are looked up by
  their first three letters, expanding only the verbs that start that way,
  as ReeeWriter does; forms that do not start like their infinitive (vaig,
  sóc, puc) are indexed once, up front.
* Nouns and adjectives: the plural rule and the list of singular candidates
  come from ReeeWriter; feminine forms from the thesaurus (word^feminine).
* Synonyms: the Softcatalà thesaurus (data/thesaurus.txt, CC BY 4.0).

The plural rule and singular candidates are ported from ReeeWriter,
https://github.com/neuronids/reeewriter, Copyright (c) 2026 neuronids,
MIT License.
"""

import functools
import io
import json
import os
import re
import threading

from flaskblog.conjugation.normalizer import strip_accents

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
THESAURUS_FILE = os.path.join(DATA_DIR, 'thesaurus.txt')
PLURALS_FILE = os.path.join(DATA_DIR, 'plural_exceptions.json')

MAX_GROUPS_PER_WORD = 12   # thesaurus groups kept per word, as ReeeWriter does
MAX_GROUPS = 10            # groups offered for one click
MAX_ITEMS = 16             # synonyms per group

# Tenses made of one word; compound ones (he parlat, vaig parlar) are two.
SIMPLE_TENSES = {
    ('indicatiu', 'present'), ('indicatiu', 'imperfet'), ('indicatiu', 'passat-simple'),
    ('indicatiu', 'futur'), ('subjuntiu', 'present'), ('subjuntiu', 'imperfet'),
    ('condicional', 'present'), ('imperatiu', 'imperatiu-present'),
    ('infinitiu', 'infinitiu-present'), ('gerundi', 'gerundi'), ('particip', 'particip'),
}
# Moods whose forms come with the subject pronoun ("jo parlo").
WITH_PRONOUN = ('indicatiu', 'subjuntiu', 'condicional')

APOSTROPHES = "'’"
_EDGE_START = re.compile(r"^[«“\"(¿¡\[]+")
_EDGE_END = re.compile(r"[.,;:!?»”\")\]…]+$")
_ELIDED = re.compile(r"^(l|d|s|m|t|n)['’](?=\w)", re.IGNORECASE)
_CLITIC = r"(?:lo|la|los|les|li|ho|hi|ne|me|te|se|nos|vos|ns|ls|n|l|m|t|s|us|en|el)"
_HYPHEN_CLITICS = re.compile(r"(?:-" + _CLITIC + r")+$", re.IGNORECASE)
_APOSTROPHE_CLITICS = re.compile(r"['’](?:m|t|l|n|s|ls|ns|hi|ho|ls)(?:-" + _CLITIC + r")*$",
                                 re.IGNORECASE)

# The word before tells a noun from a verb: "les obres" / "ells obren".
DETERMINERS = set(
    'el la els les un una uns unes del dels al als pel pels aquest aquesta aquests '
    'aquestes aquell aquella aquells aquelles molt molta molts moltes algun alguna '
    'alguns algunes tot tota tots totes cap dos dues tres meu meva teu teva seu seva '
    'nostre nostra vostre vostra'.split()
)
BEFORE_VERBS = set(
    'jo tu ell ella nosaltres vosaltres ells elles no que qui ja hi ho li em et ens us es '
    'va van vas vaig vam vau ha han he hem heu havia havien hauria podria vol volen pot poden'.split()
)


def match_case(source, text):
    """*text* capitalised like *source* ("Cases" -> "Llars")."""
    if source[:1].isupper() and text:
        return text[0].upper() + text[1:]
    return text


def clean(surface):
    """The word itself, without punctuation, elided article or clitic
    pronouns: "l'home," -> "home", "fes-ho" -> "fes", "dona'm" -> "dona"."""
    word = _EDGE_END.sub('', _EDGE_START.sub('', (surface or '').strip()))
    word = _ELIDED.sub('', word)
    stripped = _HYPHEN_CLITICS.sub('', word)
    if stripped and stripped != word:
        word = stripped
    stripped = _APOSTROPHE_CLITICS.sub('', word)
    if stripped and stripped != word:
        word = stripped
    return word.strip(APOSTROPHES + '-')


# -- number (ported from ReeeWriter) ---------------------------------------------

_DEACCENT = {'à': 'a', 'í': 'i', 'ó': 'o', 'ú': 'u'}
# A stressed vowel before a final -s loses its accent in the plural:
# famós -> famosos, anglès -> anglesos (the exceptions list has nas -> nassos).
_UNSTRESS = {'à': 'a', 'é': 'e', 'è': 'e', 'í': 'i', 'ó': 'o', 'ò': 'o', 'ú': 'u'}


def _plural_rule(word):
    if re.search(r'[qg]ua$', word):
        return word[:-2] + 'ües'        # aigua -> aigües
    if word.endswith('ça'):
        return word[:-2] + 'ces'
    if word.endswith('ca'):
        return word[:-2] + 'ques'
    if word.endswith('ga'):
        return word[:-2] + 'gues'
    if word.endswith('ja'):
        return word[:-2] + 'ges'
    if word.endswith('a'):
        return word[:-1] + 'es'
    if word.endswith('ç'):
        return word[:-1] + 'ços'
    if re.search(r'(sc|st|xt)$', word):
        return word + 'os'              # bosc -> boscos, text -> textos
    if len(word) > 2 and word[-1] == 's' and word[-2] in _UNSTRESS:
        return word[:-2] + _UNSTRESS[word[-2]] + 'sos'
    if re.search(r'(s|x|ix|tx|z)$', word):
        return word + 'os'
    if word[-1:] in _DEACCENT:
        return word[:-1] + _DEACCENT[word[-1]] + 'ns'
    if word.endswith('é'):
        return word + 'ns'
    return word + 's'


@functools.lru_cache(maxsize=1)
def _plural_exceptions():
    with io.open(PLURALS_FILE, encoding='utf-8') as handle:
        return {key.lower(): value for key, value in json.load(handle).items()}


def plural(word):
    """Plural of a noun or adjective (gos -> gossos, casa -> cases)."""
    if ' ' in word:
        return word  # a phrase: left as it is
    found = _plural_exceptions().get(word.lower())
    return match_case(word, found) if found else _plural_rule(word)


def singulars(word):
    """Words *word* may be the plural of, most likely first."""
    out = []
    if word.endswith('ques'):
        out.append(word[:-4] + 'ca')
    if word.endswith('gues'):
        out.append(word[:-4] + 'ga')
    if word.endswith('ges'):
        out.append(word[:-3] + 'ja')
    if word.endswith('ces'):
        out.append(word[:-3] + 'ça')
    if word.endswith('ços'):
        out.append(word[:-3] + 'ç')
    if word.endswith('ües'):
        out.append(word[:-3] + 'ua')
    if word.endswith('es'):
        out += [word[:-2] + 'a', word[:-1]]
    if word.endswith('os'):
        out.append(word[:-2])
        # famosos -> famós, anglesos -> anglès
        for plain, accented in (('o', 'ó'), ('e', 'è'), ('e', 'é'), ('a', 'à'), ('i', 'í')):
            if word.endswith(plain + 'sos'):
                out.append(word[:-4] + accented + 's')
    # -ns plurals lost an accent: actuacions -> actuació (and plans -> pla).
    for ending, accented in (('ons', 'ó'), ('ans', 'à'), ('ins', 'í'), ('uns', 'ú'), ('éns', 'é')):
        if word.endswith(ending):
            out.append(word[:-3] + accented)
    if word.endswith('ns'):
        out.append(word[:-2])
    if word.endswith('s'):
        out.append(word[:-1])
    for single, many in _plural_exceptions().items():
        if many == word:
            out.insert(0, single)
    seen = []
    for candidate in out:
        if candidate and candidate not in seen:
            seen.append(candidate)
    return seen


# -- gender --------------------------------------------------------------------------------

def masculines(word):
    """Masculine forms a feminine adjective may come from (bonica -> bonic,
    famosa -> famós, nova -> nou); checked against the lexicon by the caller."""
    if not word.endswith('a') or len(word) < 3:
        return []
    out = [word[:-1]]
    for ending, replacement in (('ga', 'c'), ('ja', 'ig'), ('va', 'u'), ('ssa', 's'),
                                ('osa', 'ós'), ('esa', 'ès'), ('ina', 'í'), ('ona', 'ó'),
                                ('ada', 'at'), ('ida', 'it'), ('uda', 'ut'), ('na', '')):
        if word.endswith(ending):
            out.append(word[:-len(ending)] + replacement)
    return out


# Endings of adjectives with one form for both genders.
_INVARIABLE = re.compile(r'(e|a|ista|al|ar|ble|ent|ant|aç|iç|il|ícola|cida)$')


def feminine(word, given):
    """The feminine of *word*: the thesaurus's own (*given*), the word itself
    when it does not change (jove, agradable), or None when we would only
    be guessing."""
    if given:
        return given
    if ' ' in word:
        return None
    if _INVARIABLE.search(word):
        return word
    return None


# -- thesaurus --------------------------------------------------------------------------

def _parse_group(line):
    """(pos, gloss, [(word, feminine, register, antonym)]) from a line."""
    fields = line.split('\t')
    words = []
    for raw in fields[2].split('|'):
        antonym = raw.endswith('!')
        raw = raw.rstrip('!')
        raw, _, register = raw.partition('~')
        word, _, feminine = raw.partition('^')
        word = word.strip()
        if word:
            words.append((word, feminine.strip(), register.strip(), antonym))
    return fields[0], fields[1], words


class Thesaurus(object):
    """The lines are kept as they are and a group is parsed when asked for:
    parsed up front, the thesaurus takes ten times the memory."""

    def __init__(self, path=THESAURUS_FILE):
        self.lines = []       # one group of synonyms per line
        self.index = {}       # lower-case word -> group numbers
        self.masculine = {}   # lower-case feminine form -> masculine word
        with io.open(path, encoding='utf-8') as handle:
            for line in handle:
                line = line.rstrip('\n')
                if line.count('\t') < 2:
                    continue
                number = len(self.lines)
                self.lines.append(line)
                for word, feminine, _register, _antonym in _parse_group(line)[2]:
                    key = word.lower()
                    found = self.index.get(key, ())
                    if len(found) < MAX_GROUPS_PER_WORD:
                        self.index[key] = found + (number,)
                    if feminine:
                        self.masculine.setdefault(feminine.lower(), word)
        self.group = functools.lru_cache(maxsize=512)(self._group)

    def _group(self, number):
        return _parse_group(self.lines[number])

    def __contains__(self, word):
        return word.lower() in self.index

    def is_adjective(self, word):
        return any(self.lines[number].startswith('adj')
                   for number in self.index.get(word.lower(), ()))

    def groups_of(self, word):
        return [self.group(number) for number in self.index.get(word.lower(), ())]


_thesaurus = None
_thesaurus_lock = threading.Lock()


def thesaurus():
    global _thesaurus
    if _thesaurus is None:
        with _thesaurus_lock:
            if _thesaurus is None:
                _thesaurus = Thesaurus()
    return _thesaurus


# -- verbs ------------------------------------------------------------------------------------

def _key(form):
    return strip_accents(form.lower())[:3]


class VerbForms(object):
    """Simple forms of every verb the conjugator knows, found by form.

    A hit is stored as one number, verb * 64 + slot, to keep the indexes
    small (a free hosting plan has little memory)."""

    def __init__(self, service):
        self.service = service
        self._by_prefix = None
        self._irregular = None
        self._verbs = ()
        self._slots = []
        self._slot_numbers = {}
        self._lock = threading.Lock()
        self.forms = functools.lru_cache(maxsize=256)(self._forms)
        self.bucket = functools.lru_cache(maxsize=32)(self._bucket)

    def _code(self, verb_number, slot):
        number = self._slot_numbers.get(slot)
        if number is None:
            number = self._slot_numbers[slot] = len(self._slots)
            self._slots.append(slot)
        return verb_number * 64 + number

    def _decode(self, codes):
        return [(self._verbs[code // 64], self._slots[code % 64]) for code in codes]

    def _forms(self, infinitive):
        """{(mood, tense, person): form} for one verb, simple tenses only."""
        service = self.service
        try:
            override = service._corrections.verb_overrides.get(infinitive)
            moods, _template, _stem = service._conjugate_verb(infinitive, override)
        except Exception:
            return {}
        out = {}
        for mood, tenses in moods.items():
            for tense, forms in tenses.items():
                if (mood, tense) not in SIMPLE_TENSES:
                    continue
                for person, text in enumerate(forms):
                    parts = text.split()
                    if mood in WITH_PRONOUN:
                        parts = parts[1:]
                    if len(parts) == 1:
                        out[(mood, tense, person)] = parts[0]
        return out

    def _ensure_index(self):
        if self._irregular is not None:
            return
        with self._lock:
            if self._irregular is not None:
                return
            self._verbs = tuple(self.service.infinitives)
            by_prefix, irregular = {}, {}
            for number, infinitive in enumerate(self._verbs):
                by_prefix.setdefault(_key(infinitive), []).append(number)
            # One pass over every verb (a couple of seconds, once per
            # process) for the forms a prefix search cannot reach.
            for number, infinitive in enumerate(self._verbs):
                key = _key(infinitive)
                for slot, form in self._forms(infinitive).items():
                    if _key(form) != key:
                        form = form.lower()
                        irregular[form] = irregular.get(form, ()) + (self._code(number, slot),)
            self._by_prefix = by_prefix
            self._irregular = irregular

    def _bucket(self, key):
        out = {}
        for number in self._by_prefix.get(key, ()):
            for slot, form in self._forms(self._verbs[number]).items():
                form = form.lower()
                out[form] = out.get(form, ()) + (self._code(number, slot),)
        return out

    def analyse(self, word):
        """[(infinitive, (mood, tense, person))] that *word* can be."""
        self._ensure_index()
        word = word.lower()
        codes = list(self._irregular.get(word, ()))
        for code in self.bucket(_key(word)).get(word, ()):
            if code not in codes:
                codes.append(code)
        return self._decode(codes)

    def conjugate(self, infinitive, slot):
        """*infinitive* put into *slot*, or None."""
        resolved = self.service.resolve(infinitive)
        if resolved is None:
            return None
        return self.forms(resolved).get(tuple(slot))


_verbs = None
_verbs_lock = threading.Lock()


def verbs():
    global _verbs
    if _verbs is None:
        with _verbs_lock:
            if _verbs is None:
                from flaskblog.conjugation import get_service
                _verbs = VerbForms(get_service())
    return _verbs


# -- one click ----------------------------------------------------------------------------------

def nominal_readings(word, known):
    """[(lemma, plural, feminine)] for a noun or adjective; *known* tells
    whether a lemma is a word we have (thesaurus or dictionary)."""
    words = thesaurus()
    lower = word.lower()
    out = []

    def add(lemma, plural_, feminine):
        if (known(lemma) or lemma in words) and (lemma, plural_, feminine) not in out:
            out.append((lemma, plural_, feminine))

    def add_feminine(form, plural_):
        if form in words.masculine:
            add(words.masculine[form].lower(), plural_, True)
        # Guessed masculines only for adjectives, and not when the form is a
        # word of its own that is no adjective ("casa" is not "cas").
        if form in words and not words.is_adjective(form):
            return
        for masculine in masculines(form):
            if words.is_adjective(masculine):
                add(masculine, plural_, True)

    add(lower, False, False)
    add_feminine(lower, False)
    for single in singulars(lower):
        add(single, True, False)
        add_feminine(single, True)
    return out


def analyse(surface, previous=None, known=lambda lemma: False):
    """Readings of *surface* and synonym groups in its form.

    Returns {"word": the cleaned word, "readings": [{"lemma", "kind",
    "slot", "plural", "feminine"}], "groups": [{"pos", "gloss", "kind",
    "lemma", "items": [{"text", "lemma", "register"}]}]}.
    """
    word = clean(surface)
    result = {'word': word, 'readings': [], 'groups': []}
    if not word or len(word) > 60:
        return result
    words = thesaurus()
    seen_groups = set()

    def add_group(group, kind, lemma, inflect):
        pos, gloss, entries = group
        key = (id(group), kind)
        if key in seen_groups:
            return
        items, seen = [], {word.lower(), lemma.lower()}
        for text, feminine, register, antonym in entries:
            if antonym or text.lower() == lemma.lower():
                continue
            shown = inflect(text, feminine)
            if not shown or shown.lower() in seen:
                continue
            seen.add(shown.lower())
            items.append({'text': match_case(word, shown), 'lemma': text, 'register': register or None})
            if len(items) >= MAX_ITEMS:
                break
        if items:
            seen_groups.add(key)
            result['groups'].append({'pos': pos, 'gloss': gloss or None, 'kind': kind,
                                     'lemma': lemma, 'items': items})

    # Verbs: the same mood, tense and person for every synonym.
    engine = verbs()
    for infinitive, slot in engine.analyse(word):
        result['readings'].append({'lemma': infinitive, 'kind': 'verb', 'slot': list(slot),
                                   'plural': None, 'feminine': None})
        for group in words.groups_of(infinitive):
            if not group[0].startswith('v'):
                continue

            def inflect(text, _feminine, slot=slot):
                head, _, rest = text.partition(' ')
                if rest and slot[0] == 'particip':
                    return None  # the rest of the phrase would not agree
                form = engine.conjugate(head, slot)
                return (form + (' ' + rest if rest else '')) if form else None

            add_group(group, 'verb', infinitive, inflect)

    # Nouns, adjectives and the rest: the same number and gender.
    for lemma, is_plural, is_feminine in nominal_readings(word, known):
        result['readings'].append({'lemma': lemma, 'kind': 'word', 'slot': None,
                                   'plural': is_plural, 'feminine': is_feminine})
        for group in words.groups_of(lemma):
            if group[0].startswith('v'):
                continue

            def inflect(text, given, is_plural=is_plural, is_feminine=is_feminine):
                if is_feminine:
                    text = feminine(text, given)
                    if text is None:
                        return None  # no feminine we can trust: not offered
                return plural(text) if is_plural else text

            add_group(group, 'word', lemma, inflect)

    # "les obres" is a noun, "ells obren" a verb: the word before decides
    # which groups come first.
    before = clean(previous or '').lower()
    groups, readings = result['groups'], result['readings']
    if before in DETERMINERS:
        groups.sort(key=lambda group: group['kind'] == 'verb')
        readings.sort(key=lambda reading: reading['kind'] == 'verb')
    elif before in BEFORE_VERBS:
        groups.sort(key=lambda group: group['kind'] != 'verb')
        readings.sort(key=lambda reading: reading['kind'] != 'verb')
    result['groups'] = groups[:MAX_GROUPS]
    return result
