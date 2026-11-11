"""Ukrainian for Catalan words, derived through English and Spanish.

A Catalan word in the dictionary has English meanings (ours, or DACCO's)
and Spanish equivalents (Apertium). Wiktionary gives Ukrainian for English
and for Spanish words (flaskblog/vocabulary/wiktionary.py). A Ukrainian
word is proposed for a meaning of a Catalan word on this evidence:

* ``wikt``: Wiktionary itself lists the Catalan and the Ukrainian word as
  translations of the same meaning of an English word;
* ``en``: it translates one of the meaning's English words (a translation
  table, or the gloss of a Ukrainian entry);
* ``es``: it translates one of the Catalan word's Spanish equivalents.

Only words of the same part of speech count, and a perfective verb counts
as its imperfective partner (написати as писати). A proposal is *sure* with
two kinds of evidence (two routes agree: the English one fixes the meaning,
the Spanish one, close to Catalan, rules out the other meanings of the
English word); with ``en`` alone it is kept, as unsure, only when that
English word has a single Ukrainian equivalent of that part of speech.
Proposals are ordered by how much supports them, then by Wiktionary's own
order (it lists the usual word first). Checked against the dictionary's own hand-made Ukrainian
(``flask vocabulary pivot-report``).

``flask vocabulary pivot-export`` writes the derived Ukrainian-Catalan
dictionary to ``data/derived/uk-ca.jsonl``::

    {"uk": "каву́н", "ca": [{"w": "síndria", "pos": "noun", "en": ["watermelon"],
                              "evidence": ["en", "es", "wikt"]}]}

(``"unsure": true`` marks the proposals that are not sure); ``flask vocabulary
pivot-import`` gives the words that have no Ukrainian translation the sure
proposals, as drafts (``reviewed = False``: the page says the translation
is automatic and unchecked, and it waits on the translation platform).
"""

import functools
import io
import json
import os
import re

from flaskblog.vocabulary import apertium, wiktionary
from flaskblog.vocabulary.wiktionary import en_key, es_key, uk_key

DERIVED_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'derived', 'uk-ca.jsonl')

# Parts of speech that must agree between the Catalan and the Ukrainian word.
_STRICT_POS = ('noun', 'verb', 'adjective', 'adverb')
MAX_PER_MEANING = 3   # kept in the derived dictionary
MAX_SHOWN = 2         # put into a word's translation
_STRESS = '́'


@functools.lru_cache(maxsize=1)
def tables():
    """Lookup tables built from the Wiktionary files."""
    en_uk, es_uk, ca_uk, shown, common, imperfective, order = {}, {}, {}, {}, {}, {}, {}

    def show(word):
        key = uk_key(word)
        if key not in shown or (_STRESS in word and _STRESS not in shown[key]):
            shown[key] = word
        common[key] = common.get(key, 0) + 1
        return key

    for entry in wiktionary.load(wiktionary.UK_EN):
        key = show(entry.get('stressed') or entry['uk'])
        if entry.get('aspect') == 'pf' and entry.get('pair'):
            imperfective[key] = show(entry['pair'])
        for sense in entry['senses']:
            for english in wiktionary.gloss_parts(sense['en']):
                en_uk.setdefault(english, {}).setdefault(key, set()).add(entry['pos'])
    for row in wiktionary.load(wiktionary.SENSES):
        english = en_key(row['en'])
        for position, word in enumerate(row['uk']):
            key = show(word)
            en_uk.setdefault(english, {}).setdefault(key, set()).add(row['pos'])
            # Wiktionary lists the usual word first, regional and rare ones after it.
            order[english, key] = min(order.get((english, key), 99), position)
            for catalan in row.get('ca', []):
                ca_uk.setdefault(catalan.lower(), []).append((key, english, row['pos']))
    for row in wiktionary.load(wiktionary.UK_ES):
        key = show(row['uk'])
        for spanish in row['es']:
            es_uk.setdefault(es_key(spanish), {}).setdefault(key, set()).add(row['pos'])
    return {'en_uk': en_uk, 'es_uk': es_uk, 'ca_uk': ca_uk, 'shown': shown, 'common': common,
            'imperfective': imperfective, 'order': order}


_PARENTHESES = re.compile(r'\([^)]*\)')


def english_meanings(translation):
    """"touch; play, strum (an instrument)" -> [["touch"], ["play", "strum"]]."""
    meanings = []
    for part in (translation or '').split(';'):
        words = [en_key(item) for item in _PARENTHESES.sub(' ', part).split(',')]
        meanings.append([word for word in words if word])
    return meanings


def _fits(found_pos, pos):
    return pos not in _STRICT_POS or pos in found_pos


def derive(term, pos, meanings, spanish=None):
    """Proposals for each meaning of a Catalan word:
    [[{"uk": ..., "evidence": [...], "sure": bool}, ...] per meaning]."""
    data = tables()
    imperfective = data['imperfective']

    def lemma(key):
        # A perfective verb stands under its imperfective partner.
        return imperfective.get(key, key)

    if spanish is None:
        spanish = apertium.spanish(term, pos)
    via_es = {}
    for word in spanish:
        for key, found in data['es_uk'].get(es_key(word), {}).items():
            if _fits(found, pos):
                via_es[lemma(key)] = via_es.get(lemma(key), 0) + 1
    direct = [(lemma(key), english) for key, english, found in data['ca_uk'].get(term.lower(), [])
              if _fits({found}, pos)]
    result = []
    for words in meanings:
        proposals = {}

        def note(key, kind, position=99):
            item = proposals.setdefault(key, {'evidence': set(), 'support': 0, 'order': 99})
            if kind != 'wikt':  # the same table as 'en': not a second support
                item['support'] += 1
            item['evidence'].add(kind)
            item['order'] = min(item['order'], position)

        for english in words:
            found = {}
            for key, parts in data['en_uk'].get(english, {}).items():
                if _fits(parts, pos):
                    position = data['order'].get((english, key), 99)
                    found[lemma(key)] = min(found.get(lemma(key), 99), position)
            for key, position in found.items():
                note(key, 'en', position)
                if len(found) == 1:
                    note(key, 'only')
        for key, english in direct:
            if english in words:
                note(key, 'wikt')
        for key in list(proposals):
            if key in via_es:
                note(key, 'es')
                proposals[key]['support'] += via_es[key] - 1
        ranked = []
        for key, item in proposals.items():
            evidence = item['evidence'] - {'only'}
            sure = len(evidence) >= 2
            if (not sure and 'only' not in item['evidence']) or len(key.split()) > 3:
                continue
            if data['shown'][key][:1].isupper() != term[:1].isupper():
                continue  # a proper name for a common word, or the other way round
            ranked.append({
                'uk': data['shown'][key],
                'evidence': sorted(evidence),
                'sure': sure,
                'rank': (-len(evidence), ' ' in key, -item['support'], item['order'],
                         -data['common'].get(key, 0), len(key)),
            })
        ranked.sort(key=lambda item: item['rank'])
        for item in ranked:
            del item['rank']
        result.append(ranked[:MAX_PER_MEANING])
    return result


def ukrainian(term, pos, translation_en, sure_only=True):
    """The Ukrainian of each meaning as text ("кавун" / "грати, заграти"),
    '' for a meaning nothing was found for."""
    texts = []
    for proposals in derive(term, pos, english_meanings(translation_en)):
        words = [p['uk'].replace(_STRESS, '') for p in proposals if p['sure'] or not sure_only]
        words = words[:MAX_SHOWN]
        texts.append(', '.join(words))
    return texts


# -- the dictionary's words -----------------------------------------------------------------

def import_translations(words=None, sure_only=True):
    """Give each word (all by default) without a Ukrainian translation the
    derived one, meaning by meaning, as a draft. Returns how many words got
    one. The caller commits."""
    from flaskblog.models import SenseTranslation, Word, WordTranslation
    from flaskblog.vocabulary import senses

    words = Word.query.all() if words is None else words
    added = 0
    for word in words:
        if word.translations.get('uk') is not None and word.translations['uk'].translation:
            continue
        english = word.translations.get('en')
        if english is None or not english.translation:
            continue
        texts = ukrainian(word.term, word.part_of_speech, english.translation, sure_only)
        if not any(texts):
            continue
        if len(texts) != len(word.senses):
            senses.sync_from_flat(word, ['en'])
        if len(texts) != len(word.senses):
            continue
        for sense, text in zip(word.senses, texts):
            if text:
                sense.translations['uk'] = SenseTranslation(lang='uk', text=text[:255], reviewed=False)
        word.translations['uk'] = WordTranslation(
            lang='uk', translation=senses.join(texts, 'uk')[:255], reviewed=False)
        added += 1
    return added


def remove_translations():
    """Take away the derived Ukrainian translations nobody has checked or
    edited. Returns how many. The caller commits."""
    from flaskblog.models import WordTranslation

    entries = WordTranslation.query.filter_by(lang='uk', edited=False, reviewed=False).all()
    for entry in entries:
        word = entry.word
        for sense in word.senses:
            sense.translations.pop('uk', None)
        del word.translations['uk']
    return len(entries)


def export(words, path=DERIVED_FILE):
    """Write the derived Ukrainian-Catalan dictionary for *words* ((term,
    part of speech, English translation) each): one Ukrainian headword a
    line with the Catalan words it was proposed for. Returns the number of
    Ukrainian headwords."""
    by_ukrainian = {}
    for term, pos, translation in words:
        meanings = english_meanings(translation)
        for english, proposals in zip(meanings, derive(term, pos, meanings)):
            for proposal in proposals:
                rows = by_ukrainian.setdefault(proposal['uk'], [])
                if not any(row['w'] == term and row.get('pos') == pos for row in rows):
                    row = {'w': term, 'pos': pos, 'en': english, 'evidence': proposal['evidence']}
                    if not proposal['sure']:
                        row['unsure'] = True
                    rows.append({k: v for k, v in row.items() if v})
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with io.open(path, 'w', encoding='utf-8') as handle:
        for ukrainian_word in sorted(by_ukrainian, key=uk_key):
            entry = {'uk': ukrainian_word, 'ca': by_ukrainian[ukrainian_word]}
            handle.write(json.dumps(entry, ensure_ascii=False, separators=(',', ':')) + '\n')
    return len(by_ukrainian)


def evaluate(rows):
    """How the proposals compare with hand-made translations.

    *rows*: (term, part of speech, English translation, Ukrainian
    translation). A proposal is right when the hand-made Ukrainian has that
    word; a synonym counts as wrong, so the real precision is higher."""
    numbers = {}
    for term, pos, english, gold in rows:
        gold_words = {uk_key(w) for w in re.split(r'[;,()/]', gold or '') if w.strip()}
        gold_tokens = set(uk_key(gold or '').replace(',', ' ').replace(';', ' ')
                          .replace('(', ' ').replace(')', ' ').split())
        got = {'sure': False, 'unsure': False}
        for proposals in derive(term, pos, english_meanings(english)):
            for proposal in proposals:
                kind = 'sure' if proposal['sure'] else 'unsure'
                key = uk_key(proposal['uk'])
                right = key in gold_words or key in gold_tokens
                group = numbers.setdefault(kind, {'proposals': 0, 'right': 0, 'words': 0})
                group['proposals'] += 1
                group['right'] += right
                got[kind] = True
        for kind, has in got.items():
            if has:
                numbers[kind]['words'] += 1
    numbers['words'] = len(rows)
    return numbers
