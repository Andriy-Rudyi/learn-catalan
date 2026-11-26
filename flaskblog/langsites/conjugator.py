"""The conjugator of a language section.

* Spanish and French: verbecc (the library the Catalan conjugator uses),
  every mood and tense, loaded only when somebody conjugates a verb of
  that language. Its tenses keep their own names (presente, passé
  composé...).
* German and Ukrainian: the conjugation tables of the English Wiktionary
  (the kaikki.org extracts), turned by ``flask langsites conjugation
  <code> <extract>`` into ``langsites/data/<code>/conjugation.jsonl``, one
  verb a line, read on demand like the dictionary::

      {"k": "gehen", "w": "gehen", "tables": [
         {"title": "Präsens", "rows": [["ich", "gehe"], ["du", "gehst"], ...]}, ...]}

``conjugate(code, query)`` takes the infinitive or any form of the verb
("ging", "hablo") and returns ``{"verb", "tables", "source"}`` or None.
"""

import functools
import io
import json
import os
import threading

from flaskblog.langsites import dictionary, kaikki

FILE_NAME = 'conjugation.jsonl'
VERBECC = ('es', 'fr')

# -- tables from Wiktionary --------------------------------------------------------------------

_PERSONS = {
    'de': (('first-person', 'singular', 'ich'), ('second-person', 'singular', 'du'),
           ('third-person', 'singular', 'er / sie / es'), ('first-person', 'plural', 'wir'),
           ('second-person', 'plural', 'ihr'), ('third-person', 'plural', 'sie / Sie')),
    'uk': (('first-person', 'singular', 'я'), ('second-person', 'singular', 'ти'),
           ('third-person', 'singular', 'він / вона / воно'), ('first-person', 'plural', 'ми'),
           ('second-person', 'plural', 'ви'), ('third-person', 'plural', 'вони')),
}

# (title, tags the form must have, tags it must not have); persons as rows.
_PERSON_TABLES = {
    'de': (
        ('Präsens', {'indicative', 'present'}, {'multiword-construction'}),
        ('Präteritum', {'indicative', 'preterite'}, {'multiword-construction'}),
        ('Perfekt', {'indicative', 'perfect'}, set()),
        ('Plusquamperfekt', {'indicative', 'pluperfect'}, set()),
        ('Futur I', {'indicative', 'future-i'}, set()),
        ('Konjunktiv I', {'subjunctive-i'}, {'multiword-construction'}),
        ('Konjunktiv II', {'subjunctive-ii'}, {'multiword-construction'}),
        ('Imperativ', {'imperative'}, set()),
    ),
    'uk': (
        ('Present', {'present'}, {'active', 'passive', 'adverbial', 'imperative'}),
        ('Future', {'future'}, {'error-unrecognized-form', 'infinitive'}),
        ('Imperative', {'imperative'}, set()),
    ),
}
_SKIP = {'romanization', 'table-tags', 'inflection-template', 'class', 'canonical',
         'error-unrecognized-form', 'alternative', 'error-unknown-tag'}


def _forms_with(forms, wanted, unwanted):
    return [(form['form'], set(form.get('tags') or ())) for form in forms
            if wanted <= set(form.get('tags') or ()) and not set(form.get('tags') or ()) & unwanted
            and not set(form.get('tags') or ()) & _SKIP and form.get('form') not in ('-', '')]


def _cell(found):
    words = []
    for word, _tags in found:
        if word not in words:
            words.append(word)
    return ' / '.join(words)


def tables(code, entry):
    """The conjugation tables of a Wiktionary verb entry."""
    forms = entry.get('forms') or ()
    result = []
    for title, wanted, unwanted in _PERSON_TABLES[code]:
        rows = []
        for person, number, label in _PERSONS[code]:
            cell = _cell(_forms_with(forms, wanted | {person, number}, unwanted))
            if cell:
                rows.append([label, cell])
        if rows:
            result.append({'title': title, 'rows': rows})
    if code == 'uk':
        rows = []
        for gender, label in (('masculine', 'він'), ('feminine', 'вона'), ('neuter', 'воно')):
            cell = _cell(_forms_with(forms, {'past', gender, 'singular'}, {'passive', 'adverbial'}))
            if cell:
                rows.append([label, cell])
        cell = _cell(_forms_with(forms, {'past', 'plural'}, {'passive', 'adverbial'}))
        if cell:
            rows.append(['вони', cell])
        if rows:
            result.insert(1, {'title': 'Past', 'rows': rows})
        other = []
        for label, wanted in (('Infinitive', {'infinitive'}), ('Imperfective', {'imperfective'}),
                              ('Perfective', {'perfective'}),
                              ('Adverbial participle, present', {'adverbial', 'present'}),
                              ('Adverbial participle, past', {'adverbial', 'past'}),
                              ('Passive participle', {'passive', 'past'})):
            unwanted = {'infinitive', 'present', 'past', 'future', 'imperative'} if label in (
                'Imperfective', 'Perfective') else set()
            cell = _cell(_forms_with(forms, wanted, unwanted))
            if cell:
                other.append([label, cell])
        if other:
            result.append({'title': 'Forms', 'rows': other})
    else:
        other = []
        for label, wanted in (('Infinitiv', {'infinitive'}), ('Partizip I', {'participle', 'present'}),
                              ('Partizip II', {'participle', 'past'}), ('Hilfsverb', {'auxiliary'})):
            unwanted = {'multiword-construction', 'future'} if label == 'Infinitiv' else set()
            found = [(form['form'], set()) for form in forms
                     if wanted <= set(form.get('tags') or ()) and not set(form.get('tags') or ()) & unwanted]
            cell = _cell(found)
            if cell:
                other.append([label, cell])
        if other:
            result.append({'title': 'Grundformen', 'rows': other})
    return result


def write_tables(code, extract):
    """Write conjugation.jsonl of a section from a Wiktionary extract, for
    the verbs of its dictionary. Returns the number of verbs."""
    known = set(dictionary.index(code).keys)
    verbs = {}
    for entry in kaikki._lines(extract):
        if entry.get('pos') != 'verb' or not entry.get('forms'):
            continue
        word_key = dictionary.key(entry.get('word'))
        if word_key not in known or word_key in verbs:
            continue
        found = tables(code, entry)
        if len(found) >= 2:
            verbs[word_key] = {'k': word_key, 'w': entry['word'], 'tables': found}
    out = os.path.join(dictionary.DATA_DIR, code, FILE_NAME)
    with io.open(out, 'w', encoding='utf-8') as handle:
        for word_key in sorted(verbs):
            handle.write(json.dumps(verbs[word_key], ensure_ascii=False, separators=(',', ':')) + '\n')
    dictionary.index.cache_clear()
    return len(verbs)


def available(code):
    if code in VERBECC:
        return True
    return os.path.exists(os.path.join(dictionary.DATA_DIR, code, FILE_NAME))


def _from_tables(code, word_key):
    idx = dictionary.index(code, FILE_NAME)
    positions = idx.positions(word_key)
    return idx.read(positions[0]) if positions else None


# -- verbecc --------------------------------------------------------------------------------------

_lock = threading.Lock()


@functools.lru_cache(maxsize=1)  # Spanish ~35 MB, French ~12 MB: one at a time on a small server
def _verbecc(code):
    import verbecc.config
    verbecc.config.ml = False
    from verbecc import Conjugator
    with _lock:
        return Conjugator(lang=code)


def _label(name):
    return name.replace('-', ' ').strip().capitalize()


def _from_verbecc(code, infinitive):
    try:
        result = _verbecc(code).conjugate(infinitive)
    except Exception:  # verbecc raises for words it cannot conjugate
        return None
    if not result or result.get('verb', {}).get('predicted'):
        return None
    found = []
    for mood, tenses in result.get('moods', {}).items():
        for tense, forms in tenses.items():
            rows = [[form] for form in forms if form]
            if rows:
                found.append({'title': _label(mood) + ' · ' + _label(tense), 'rows': rows})
    return {'k': dictionary.key(infinitive), 'w': result['verb']['infinitive'], 'tables': found}


# -- the page's question ----------------------------------------------------------------------

def _is_verb(code, word):
    return any(entry['pos'] == 'verb' for entry in dictionary.lookup(code, word))


def conjugate(code, query):
    """The tables for a verb given as its infinitive or any of its forms."""
    query = (query or '').strip()[:60]
    if not query or not available(code):
        return None
    candidates = [query, query.lower()] + kaikki.lemmas(code, query)
    if code == 'en':
        candidates += [form for form in (dictionary.find(code, query)[1],) if form]
    seen, others = set(), []
    for candidate in candidates:
        word_key = dictionary.key(candidate)
        if not word_key or word_key in seen:
            continue
        seen.add(word_key)
        if code in VERBECC:
            if not _is_verb(code, word_key):
                continue
            found = _from_verbecc(code, word_key)
        else:
            found = _from_tables(code, word_key)
        if found and found['tables']:
            # The other verbs the form can belong to (French "suis": suivre, être).
            others = [lemma for lemma in kaikki.lemmas(code, query)
                      if dictionary.key(lemma) != word_key and _is_verb(code, lemma)]
            return dict(found, source='verbecc' if code in VERBECC else 'wiktionary',
                        asked=query if dictionary.key(query) != word_key else None, others=others)
    return None
