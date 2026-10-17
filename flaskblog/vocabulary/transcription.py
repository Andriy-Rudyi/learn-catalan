"""How a Catalan word sounds: a transcription in IPA and in Ukrainian letters.

Central Catalan (Barcelona), in the same broad IPA as the pronunciation
lessons ([ˈkazə], [puɾˈta], [ʃukuˈlatə]): ˈ before the stressed syllable,
unstressed a/e as [ə] and o as [u], [ɾ]/[r], [ʎ ɲ ʃ ʒ tʃ dʒ], voiced [z]
between vowels, b d ɡ written as such (no [β ð ɣ]).

Where it comes from, most reliable first:

1. what an editor typed in for the word (Word.pronunciation);
2. the words transcribed in the pronunciation lessons (phonetics/data);
3. the spelling rules below.

The rules know where the stress falls and how each letter sounds, but not
whether a stressed e or o without a written accent is open ([ɛ], [ɔ]) or
closed ([e], [o]): that is learnt word by word. Such words get the closed
vowel and ``certain=False``, and the page says the transcription is
approximate. So does a final -r after the stressed vowel outside
infinitives (silent in many words, pronounced in others).
"""

import functools
import io
import json
import os
import re
import unicodedata
from collections import namedtuple

Transcription = namedtuple('Transcription', 'ipa cyrillic certain source')

VOWELS = set('aeiouàèéíïòóúü')
FRONT = set('eièéí')   # c, g, qu, gu sound different before these
ACCENTED = {'à': 'a', 'è': 'ɛ', 'é': 'e', 'í': 'i', 'ò': 'ɔ', 'ó': 'o', 'ú': 'u'}
IPA_VOWELS = set('aəeɛiouɔ')
# Unstressed in a phrase ("pa amb tomàquet", "de debò").
FUNCTION_WORDS = set(
    'el la els les lo un una uns unes de del dels a al als en i o que per pel pels '
    'amb es se em et ens us li hi ho ne me te'.split()
)
# Two consonants that start a syllable together (pla, tren...).
_CLUSTERS = {(a, b) for a in ('p', 'b', 't', 'd', 'k', 'ɡ', 'f') for b in ('l', 'ɾ')}
_CONSONANT_PHONES = set('p b t d k ɡ f s z ʃ ʒ tʃ dʒ dz m n ɲ ŋ l ʎ ɾ r j w ks ɡz'.split())
_SIMPLE = {'b': 'b', 'v': 'b', 'd': 'd', 'f': 'f', 'k': 'k', 'l': 'l', 'm': 'm', 'n': 'n',
           'p': 'p', 't': 't', 'z': 'z', 'r': 'R', 'w': 'w', 'y': 'j'}
# A single s before these is voiced too (esmorzar [əzmuɾˈza]).
_VOICED = set('b d ɡ m n l ʎ ɲ ɾ r R z ʒ dʒ'.split())
_DEVOICE = {'b': 'p', 'd': 't', 'ɡ': 'k', 'z': 's', 'S': 's', 'ʒ': 'tʃ', 'dʒ': 'tʃ'}

LESSONS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            'phonetics', 'data', 'lessons.json')


@functools.lru_cache(maxsize=1)
def lesson_words():
    """{word: ipa} from the pronunciation lessons, for words with a single
    transcription there ("dona" has two, so the rules decide)."""
    try:
        with io.open(LESSONS_FILE, encoding='utf-8') as handle:
            lessons = json.load(handle)
    except (OSError, ValueError):
        return {}
    found = {}
    for lesson in lessons:
        pairs = [(w.get('ca'), w.get('ipa')) for w in lesson.get('words', [])]
        pairs += [(s.get('example'), s.get('example_ipa')) for s in lesson.get('sounds', [])]
        for word, ipa in pairs:
            if not word or not ipa or ipa.startswith('∅'):
                continue
            found.setdefault(word.strip().lower(), set()).add(ipa.strip().strip('[]'))
    return {word: ipas.pop() for word, ipas in found.items() if len(ipas) == 1}


# -- spelling to sounds ---------------------------------------------------------------

def _units(word):
    """The word as [kind, value] items: 'V' a vowel letter, 'C' a consonant
    sound, 'G' a glide (j, w) the spelling already decides."""
    w, n, out, i = word, len(word), [], 0

    def at(k):
        return w[k] if 0 <= k < n else ''

    while i < n:
        c, nxt = w[i], at(i + 1)
        if c in VOWELS:
            # "ix" and a final "ig" after a vowel: the i is not pronounced
            # (caixa [ˈkaʃə], vaig [ˈbatʃ]).
            if c == 'i' and i > 0 and at(i - 1) in VOWELS and (
                    nxt == 'x' or (nxt == 'g' and i + 2 == n)):
                i += 1
                continue
            out.append(['V', c])
            i += 1
        elif c == 'h':
            out.append(['H', ''])                      # silent, but ahir is a-hir
            i += 1
        elif c in "'·-":
            i += 1
        elif c == 'l' and nxt == '·' and at(i + 2) == 'l':
            out += [['C', 'l'], ['C', 'l']]            # col·legi [kulˈlɛʒi]
            i += 3
        elif c == 'l' and nxt == 'l':
            out.append(['C', 'ʎ'])
            i += 2
        elif c == 'n' and nxt == 'y':
            out.append(['C', 'ɲ'])
            i += 2
        elif c == 'r' and nxt == 'r':
            out.append(['C', 'r'])
            i += 2
        elif c == 's' and nxt == 's':
            out.append(['C', 's'])                     # massa: never voiced
            i += 2
        elif c == 's':
            out.append(['C', 'S'])                     # voiced between vowels (casa)
            i += 1
        elif c == 't' and nxt == 'x':
            out.append(['C', 'tʃ'])                    # cotxe
            i += 2
        elif c == 't' and (nxt == 'j' or (nxt == 'g' and at(i + 2) in FRONT)):
            out.append(['C', 'dʒ'])                    # platja, fetge
            i += 2
        elif c == 't' and nxt == 'z':
            out.append(['C', 'dz'])                    # dotze
            i += 2
        elif c == 't' and nxt == 'l' and at(i + 2) == 'l':
            out.append(['C', 'ʎ'])                     # ametlla
            i += 3
        elif c in ('q', 'g') and nxt in ('u', 'ü'):
            after = at(i + 2)
            sound = 'k' if c == 'q' else 'ɡ'
            if nxt == 'u' and after in FRONT:
                out.append(['C', sound])               # que, guerra: silent u
                i += 2
            elif after in VOWELS:
                out += [['C', sound], ['G', 'w']]      # quatre, aigua, qüestió
                i += 2
            else:
                out.append(['C', sound])               # agut: the u is a vowel
                i += 1
        elif c == 'c':
            if nxt == 'c' and at(i + 2) in FRONT:
                out += [['C', 'k'], ['C', 's']]        # acció
                i += 2
            else:
                out.append(['C', 's' if nxt in FRONT else 'k'])
                i += 1
        elif c == 'ç':
            out.append(['C', 's'])
            i += 1
        elif c == 'g':
            if nxt in FRONT:
                out.append(['C', 'ʒ'])
            elif i + 1 == n and at(i - 1) == 'i':
                out.append(['C', 'tʃ'])                # vaig, mig, lleig
            else:
                out.append(['C', 'ɡ'])
            i += 1
        elif c == 'j':
            out.append(['C', 'ʒ'])
            i += 1
        elif c == 'x':
            prev = at(i - 1)
            if i == 0 or prev not in VOWELS or prev == 'i':
                out.append(['C', 'ʃ'])                 # xocolata, panxa, caixa
            elif i == 1 and prev == 'e' and at(i + 1) in VOWELS:
                out += [['C', 'ɡ'], ['C', 'z']]        # examen [əɡˈzamən]
            elif nxt == 'c' and at(i + 2) in FRONT:
                out += [['C', 'k'], ['C', 's']]        # excel·lent: the c is in it
                i += 1
            else:
                out += [['C', 'k'], ['C', 's']]        # taxi, text, fax
            i += 1
        else:
            if c in _SIMPLE:
                out.append(['C', _SIMPLE[c]])
            i += 1
    return out


def _glides(units):
    """Mark the i and u that are glides (feina, noia, cuina, riu, iogurt).
    A silent h keeps two vowels apart (ahir) and is dropped here."""
    def vowel(k):
        return 0 <= k < len(units) and units[k][0] == 'V'

    for k, (kind, letter) in enumerate(units):
        if kind != 'V' or letter not in ('i', 'u'):
            continue
        glide = 'j' if letter == 'i' else 'w'
        before, after = vowel(k - 1), vowel(k + 1)
        if before and after:
            units[k] = ['G', glide]                       # noia, duia
        elif before:
            prev = units[k - 1][1]
            # In "ui" and "iu" the first one is the vowel (cuina, riu).
            if prev not in ('i', 'u') or prev != letter:
                units[k] = ['G', glide]                   # feina, nou, cuina, riu
        elif after and k == 0 and letter == 'i':
            units[k] = ['G', 'j']                         # iogurt
    return [unit for unit in units if unit[0] != 'H']


def _stress(units, word):
    """Index in *units* of the stressed vowel."""
    nuclei = [k for k, (kind, _letter) in enumerate(units) if kind == 'V']
    if not nuclei:
        return None
    for k in nuclei:
        if units[k][1] in ACCENTED:
            return k
    if len(nuclei) == 1:
        return nuclei[0]
    # Words ending in a vowel, a vowel and -s, -en or -in stress the last
    # syllable but one; the others (and those ending in a diphthong: avui,
    # dijous) the last.
    final = [unit for unit in units if unit[0] in ('V', 'G')][-1]
    if final[0] == 'G' and (word[-1:] in VOWELS or re.search(r'[iu]s$', word)):
        return nuclei[-1]
    if word[-1:] in VOWELS or re.search(r'[aeiouïü]s$', word) or word.endswith(('en', 'in', 'ens', 'ins')):
        return nuclei[-2]
    return nuclei[-1]


def _vowel(letter, stressed):
    if letter in ACCENTED:
        return ACCENTED[letter]
    if letter == 'ï':
        return 'i'
    if letter == 'ü':
        return 'u'
    if stressed:
        return letter
    return {'a': 'ə', 'e': 'ə', 'o': 'u'}.get(letter, letter)


def _word(word, part_of_speech=None, stressed_word=True):
    """(ipa, certain) for one word by the rules."""
    units = _glides(_units(word))
    stress = _stress(units, word) if stressed_word else None
    certain = True
    last = len(units) - 1
    vowels_total = sum(1 for kind, _v in units if kind == 'V')

    def vowel_like(k):
        return 0 <= k < len(units) and units[k][0] in ('V', 'G')

    out = []
    stressed_at = None
    for k, (kind, value) in enumerate(units):
        if kind == 'V':
            if k == stress:
                stressed_at = len(out)
                if value in ('e', 'o'):
                    certain = False                    # open or closed: not written
            out.append(_vowel(value, k == stress))
            continue
        if kind == 'G':
            out.append(value)
            continue
        phone = value
        following = units[k + 1] if k < last else None
        if phone == 'R':
            phone = 'r' if k == 0 or units[k - 1][1] in ('n', 'l', 's') else 'ɾ'
            if k == last and part_of_speech == 'verb':
                continue                               # infinitives: parlar, conèixer
            if k == last and stress == k - 1 and vowels_total > 1:
                # Final -r after the stressed vowel: silent in many words
                # (ahir [əˈi]) but not in all (amor [əˈmoɾ]).
                certain = False
                continue
        elif phone == 'S':
            voiced = vowel_like(k - 1) and (vowel_like(k + 1) or (
                following and following[0] == 'C' and following[1] in _VOICED))
            phone = 'z' if voiced else 's'             # casa, esmorzar
        elif phone == 't' and k > 0 and units[k - 1][1] == 'n' and following \
                and following[1] in ('s', 'S'):
            continue                                   # Montserrat [munsəˈrat]
        elif phone == 'n' and following and following[0] == 'C' and following[1] in ('k', 'ɡ', 'ks'):
            phone = 'ŋ'                                # cinc, anglès
        elif phone == 'n' and following and following[0] == 'C' and following[1] in ('b', 'p', 'm'):
            phone = 'm'                                # també
        if k == last and k > 0 and units[k - 1][0] == 'C' and out:
            before = out[-1]
            if phone == 't' and before in ('n', 'l'):
                continue                               # cant, molt
            if phone in ('k', 'ɡ') and before in ('n', 'ŋ'):
                out[-1] = 'ŋ'                          # blanc, sang
                continue
            if phone in ('p', 'b') and before == 'm':
                continue                               # camp, amb
            if phone in ('s', 'S') and before == 't' and len(out) > 1 and out[-2] in ('ɾ', 'r', 'n', 'l'):
                out[-1] = 's'                          # dimarts
                continue
        if k == last:
            phone = _DEVOICE.get(phone, phone)         # verd [ˈbeɾt]
        out.append(phone)
    return _with_stress_mark(out, stressed_at), certain


def _with_stress_mark(phones, stressed_at):
    """IPA with ˈ before the stressed syllable's onset: one consonant, two
    that make a cluster (tren), or a consonant and a glide (quatre)."""
    if stressed_at is None:
        return ''.join(phones)
    onset = []
    k = stressed_at - 1
    while k >= 0 and phones[k] in _CONSONANT_PHONES:
        onset.insert(0, phones[k])
        k -= 1
    if onset and onset[-1] in ('j', 'w'):
        taken = 2 if len(onset) >= 2 and onset[-2] not in ('j', 'w') else 1
    elif len(onset) >= 2 and (onset[-2], onset[-1]) in _CLUSTERS:
        taken = 2
    else:
        taken = 1 if onset else 0
    start = stressed_at - taken
    return ''.join(phones[:start]) + 'ˈ' + ''.join(phones[start:])


# -- Ukrainian letters ----------------------------------------------------------------------

_CYRILLIC = [
    ('tʃ', 'ч'), ('dʒ', 'дж'), ('dz', 'дз'), ('ks', 'кс'), ('ɡz', 'ґз'),
    ('ʎ', 'ль'), ('ɲ', 'нь'), ('ŋ', 'н'), ('ʃ', 'ш'), ('ʒ', 'ж'), ('ɾ', 'р'), ('r', 'рр'),
    ('ɡ', 'ґ'), ('g', 'ґ'), ('b', 'б'), ('d', 'д'), ('k', 'к'), ('p', 'п'), ('t', 'т'),
    ('f', 'ф'), ('s', 'с'), ('z', 'з'), ('m', 'м'), ('n', 'н'), ('l', 'л'), ('ɫ', 'л'),
    ('β', 'б'), ('ð', 'д'), ('ɣ', 'ґ'),
    ('ə', 'ə'), ('a', 'а'), ('ɛ', 'е'), ('e', 'е'), ('i', 'і'), ('ɔ', 'о'), ('o', 'о'),
    ('u', 'у'),
]
_ACUTE = '́'
# After ль and нь a vowel takes its soft letter: ʎa -> ля, ɲu -> ню.
_SOFT = {'а': 'я', 'у': 'ю', 'е': 'є', 'і': 'і'}


def to_cyrillic(ipa):
    """[ˈkazə] -> ка́зə: Ukrainian letters with the stressed vowel marked."""
    text = ipa.strip().strip('[]/')
    out, stress_next, k = [], False, 0
    while k < len(text):
        ch = text[k]
        if ch == 'ˈ':
            stress_next = True
            k += 1
        elif ch in 'ˌː.':
            k += 1
        elif ch == ' ':
            out.append(' ')
            k += 1
        elif ch == 'j':
            out.append('й')
            k += 1
        elif ch == 'w':
            after_vowel = bool(out) and out[-1].rstrip(_ACUTE)[-1:] in 'аəеіоу'
            out.append('у' if after_vowel else 'в')    # nou -> ноу, quatre -> кватрə
            k += 1
        else:
            for sound, letters in _CYRILLIC:
                if text.startswith(sound, k):
                    if sound in IPA_VOWELS and out and out[-1] in ('ль', 'нь') \
                            and letters in _SOFT:
                        out[-1] = out[-1][0]                   # лля -> ля
                        letters = _SOFT[letters]
                    if sound in IPA_VOWELS and stress_next:
                        letters += _ACUTE
                        stress_next = False
                    out.append(letters)
                    k += len(sound)
                    break
            else:
                k += 1
    return ''.join(out)


# -- public -----------------------------------------------------------------------------------

def _split(term):
    """Words of a term; an elided article stays with its word (d'acord)."""
    term = unicodedata.normalize('NFC', term.strip().lower()).replace('’', "'")
    term = re.sub(r"\b([dlsmtn])'(?=\w)", r'\1', term)
    term = re.sub(r'[?!.,;:¡¿«»"()…]', ' ', term)
    return [part for part in re.split(r"[\s\-]+", term) if part]


def transcribe(term, part_of_speech=None, manual=None):
    """Transcription of a dictionary term (a word or a phrase), or None."""
    if manual and manual.strip().strip('[]/'):
        ipa = manual.strip().strip('[]/')
        return Transcription(ipa, to_cyrillic(ipa), True, 'editor')
    if not term or not term.strip():
        return None
    lessons = lesson_words()
    key = unicodedata.normalize('NFC', term.strip().lower())
    if key in lessons:
        return Transcription(lessons[key], to_cyrillic(lessons[key]), True, 'lessons')
    words = _split(term)
    if not words or any(re.search(r"[^a-zàèéíïòóúüç·]", word) for word in words):
        return None
    parts, certain = [], True
    for word in words:
        if len(words) > 1 and word in lessons and word not in FUNCTION_WORDS:
            parts.append(lessons[word])
            continue
        stressed = word not in FUNCTION_WORDS
        ipa, sure = _word(word, part_of_speech if len(words) == 1 else None, stressed)
        parts.append(ipa)
        certain = certain and (sure or not stressed)
    ipa = ' '.join(parts)
    return Transcription(ipa, to_cyrillic(ipa), certain, 'rules')


def for_word(word):
    """The transcription shown for a dictionary word, or None when it is
    switched off (TRANSCRIPTION=False) or the term is not Catalan spelling."""
    from flask import current_app
    if not current_app.config.get('TRANSCRIPTION'):
        return None
    return transcribe(word.term, word.part_of_speech, word.pronunciation)


def as_json(found):
    if found is None:
        return None
    return {'ipa': found.ipa, 'cyrillic': found.cyrillic, 'certain': found.certain,
            'source': found.source}
