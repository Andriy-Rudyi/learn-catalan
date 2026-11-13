"""DACCO, the open Catalan-English / English-Catalan dictionary, as data.

The source is the DACCO XML (https://github.com/cpina/dacco, the
``dictionaries/cateng`` and ``dictionaries/engcat`` folders), converted
with ``flask vocabulary dacco-convert <clone>`` (:func:`convert`) into one
JSON entry a line:

* ``data/sources/dacco/ca-en.jsonl``: Catalan headwords, English translations;
* ``data/sources/dacco/en-ca.jsonl``: English headwords, Catalan translations.

An entry::

    {"head": "català", "frequency": 965000,
     "parts": [{"pos": "noun",
                "senses": [{"text": "Catalan", "gender": "m", "category": "language"},
                           {"text": "Catalan", "gender": "m/f", "category": "nationality-europe"}]},
               {"pos": "adjective",
                "senses": [{"text": "Catalan", "fem": "catalana", "plural": "catalans"}]}],
     "expressions": [{"text": "...", "senses": [...]}]}

A part can also carry ``ipa``, ``conj`` (verbs) and English verb forms
(``past``, ``participle``...). A sense's ``text`` holds the translations
separated by " / ", sometimes after a gloss in square brackets; besides
gender it can have ``category`` (a topic such as "food-fruit"),
``register``, ``transitive`` / ``intransitive`` / ``reflexive`` /
``pronominal``, ``disambiguate``, ``termcat``, ``local`` (where it is
said), ``fem`` / ``plural`` / ``fem_plural`` (forms of the headword),
``synonyms``, ``examples`` (pairs {"ca", "en"}), ``sentences`` (Catalan
sentences using the word), ``note_ca`` / ``note_en`` and ``group`` (the
number of a group of synonymous translations). Entries also hold
``expressions``, ``phrasal_verbs`` (en-ca), ``acronyms`` and
``mistakes`` (common mistakes with the word).

Nothing here is in the site's dictionary yet: the module reads the data,
finds the entries for a word in either direction and reports how much of
the dictionary it covers. Credit DACCO (http://www.catalandictionary.org)
wherever the data or anything made from it is shown or shared.
"""

import functools
import glob
import html
import io
import json
import os
import re
import xml.etree.ElementTree as ET

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'sources', 'dacco')
FILES = {'ca-en': 'ca-en.jsonl', 'en-ca': 'en-ca.jsonl'}
# Source folder in the DACCO repository for each direction.
SOURCE_FOLDERS = {'ca-en': 'cateng', 'en-ca': 'engcat'}

SOURCE = {
    'name': 'DACCO, Diccionari Obert Català de Codi Obert',
    'url': 'https://github.com/cpina/dacco',
    'site': 'http://www.catalandictionary.org',
    'licence': 'LGPL-2.1 (repository); CC BY-SA 2.5 (published PDF edition)',
}


# -- reading the converted data -------------------------------------------------------------

@functools.lru_cache(maxsize=None)
def load(direction='ca-en'):
    path = os.path.join(DATA_DIR, FILES[direction])
    try:
        with io.open(path, encoding='utf-8') as handle:
            return [json.loads(line) for line in handle if line.strip()]
    except OSError:
        return []


def senses(entry):
    """Every sense of an entry's parts, with its part of speech."""
    for part in entry.get('parts', []):
        for sense in part.get('senses', []):
            yield dict(sense, pos=part['pos'])


_GLOSS = re.compile(r'\[[^\]]*\]')


def translations(sense):
    """The translations in a sense, without the gloss in square brackets."""
    text = _GLOSS.sub('', sense.get('text', ''))
    return [part.strip() for part in text.split(' / ') if part.strip() and part.strip() != '-']


def _key(term):
    return re.sub(r'\s+', ' ', (term or '').strip().lower())


@functools.lru_cache(maxsize=None)
def _index(direction):
    """{lower-case head: (byte offset of its line, ...)} of a direction's
    file: the entries themselves are read when asked for, so a word page
    does not keep the whole dictionary in memory."""
    index = {}
    path = os.path.join(DATA_DIR, FILES[direction])
    try:
        handle = io.open(path, 'rb')
    except OSError:
        return {}
    with handle:
        offset = 0
        for line in handle:
            if line.strip():
                try:
                    start = line.index(b'{"head":"') + 9
                    head = json.loads(b'"' + line[start:line.index(b'",', start)] + b'"')
                except ValueError:
                    head = json.loads(line)['head']
                key = _key(head)
                index[key] = index.get(key, ()) + (offset,)
                if direction == 'ca-en':
                    # A verb listed as "abalançar-se" is found as "abalançar" too.
                    for ending in ('-se', "'s"):
                        if key.endswith(ending):
                            base = key[:-len(ending)]
                            index[base] = index.get(base, ()) + (offset,)
            offset += len(line)
    return index


def lookup(term, direction='ca-en'):
    """The entries for a word ("abalançar" finds "abalançar-se")."""
    offsets = _index(direction).get(_key(term), ())
    if not offsets:
        return []
    entries = []
    with io.open(os.path.join(DATA_DIR, FILES[direction]), 'rb') as handle:
        for offset in offsets:
            handle.seek(offset)
            entries.append(json.loads(handle.readline().decode('utf-8')))
    return entries


def stats(words=(), direction='ca-en'):
    """Numbers about the data, and how much of *words* (Catalan terms) it covers."""
    entries = load(direction)
    all_senses = [s for e in entries for s in senses(e)]
    words = {_key(w) for w in words}
    numbers = {
        'entries': len(entries),
        'senses': len(all_senses),
        'translations': sum(len(translations(s)) for s in all_senses),
        'examples': sum(len(s.get('examples', [])) for s in all_senses),
        'sentences': sum(len(s.get('sentences', [])) for s in all_senses),
        'expressions': sum(len(e.get('expressions', [])) for e in entries),
        'notes': sum(1 for s in all_senses if s.get('note_ca') or s.get('note_en')),
    }
    if words:
        heads = {_key(e['head']) for e in entries}
        numbers['words'] = len(words)
        numbers['words_found'] = sum(1 for w in words if lookup(w, direction))
        numbers['new_heads'] = len(heads - words)
    return numbers


# -- converting the XML -------------------------------------------------------------------------

_PARTS = {
    'nouns': 'noun', 'adjectives': 'adjective', 'verbs': 'verb', 'adverbs': 'adverb',
    'prepositions': 'preposition', 'conjunctions': 'conjunction', 'pronouns': 'pronoun',
    'exclamations': 'exclamation', 'determiners': 'determiner', 'abbreviations': 'abbreviation',
    'acronyms': 'acronym', 'verbTense': 'verb form',
}
_GROUPS = {'expressions': 'expressions', 'phrasalverbs': 'phrasal_verbs'}
_VERB_FORMS = {'past': 'past', 'participle': 'participle', 'gerund': 'gerund',
               'firstPresent': 'present_1', 'secondPresent': 'present_2', 'thirdPresent': 'present_3'}
_SENSE_ATTRS = {
    'gender': 'gender', 'catagory': 'category', 'register': 'register', 'local': 'local',
    'otherlocal': 'other_local', 'disambiguate': 'disambiguate', 'termcat': 'termcat',
    'transitive': 'transitive', 'intransitive': 'intransitive', 'reflexive': 'reflexive',
    'pronominal': 'pronominal', 'feminine': 'feminine', 'plural': 'plural_only',
    'sourceplural': 'source_plural', 'capitalized': 'capitalized', 'collocation': 'collocation',
    'falseFriend': 'false_friend', 'beforenoun': 'before_noun', 'noteng': 'no_english',
    'general': 'general',
}
_SENSE_CHILDREN = {
    'fems': 'fem', 'plural': 'plural', 'femplural': 'fem_plural', 'synonyms': 'synonyms',
    'catnote': 'note_ca', 'engnote': 'note_en', 'otherlocal': 'other_local',
    'beforenoun': 'before_noun', 'comparative': 'comparative', 'superlative': 'superlative',
    'catacro': 'acronym_ca', 'engacro': 'acronym_en', 'examples': 'examples_text',
}
_TAGS = re.compile(r'<[^>]+>')


def _clean(text):
    text = html.unescape(_TAGS.sub('', text or ''))
    return re.sub(r'\s+', ' ', text).strip()


def _value(value):
    value = _clean(value)
    return True if value == 'true' else value


def _gender(value):
    value = re.sub(r'\s*/\s*', '/', value or '').strip()
    return {'mf': 'm/f'}.get(value, value)


def _sense(element, group=None):
    sense = {'text': _clean(''.join([element.text or ''] + [child.tail or '' for child in element]))}
    for name, key in _SENSE_ATTRS.items():
        if name in element.attrib and element.attrib[name] not in ('', 'false'):
            sense[key] = _gender(element.attrib[name]) if key == 'gender' else _value(element.attrib[name])
    pending = {}
    for child in element:
        tag = child.tag
        if tag in ('catexamp', 'engexamp'):
            lang = 'ca' if tag == 'catexamp' else 'en'
            if lang in pending:  # a sentence without its pair
                sense.setdefault('examples', []).append(pending)
                pending = {}
            pending[lang] = _clean(child.text)
            if 'ca' in pending and 'en' in pending:
                sense.setdefault('examples', []).append(pending)
                pending = {}
        elif tag == 'example':
            sense.setdefault('sentences', []).append(_clean(ET.tostring(child, encoding='unicode',
                                                                          method='text')))
        elif tag in _SENSE_CHILDREN:
            sense[_SENSE_CHILDREN[tag]] = _clean(''.join(child.itertext()))
    if pending:
        sense.setdefault('examples', []).append(pending)
    if group is not None:
        sense['group'] = group
    return sense


def _senses(translations_element, start_group=1):
    found = []
    group = start_group
    for child in translations_element:
        if child.tag == 'translation':
            found.append(_sense(child))
        elif child.tag == 'grouptranslation':
            shared = {key: _value(child.attrib[name]) for name, key in _SENSE_ATTRS.items()
                      if name in child.attrib}
            for translation in child:
                if translation.tag == 'translation':
                    found.append(dict(shared, **_sense(translation, group)))
            group += 1
    return found


def _phrase(element):
    """An expression or phrasal verb: its text and its senses."""
    item = {'text': _clean(element.text), 'senses': []}
    for name in ('register', 'local', 'intransitive', 'ipa'):
        if element.attrib.get(name):
            item[name] = _value(element.attrib[name])
    for child in element:
        if child.tag == 'translations':
            item['senses'] += _senses(child)
    return item


def _entry(element):
    entry = {'head': _clean(element.text), 'parts': []}
    if element.attrib.get('frequency', '').isdigit():
        entry['frequency'] = int(element.attrib['frequency'])
    if element.attrib.get('hasSound') == 'true':
        entry['sound'] = True
    for child in element:
        if child.tag in _GROUPS:
            entry.setdefault(_GROUPS[child.tag], []).append(_phrase(child))
        elif child.tag == 'mistakes':
            entry.setdefault('mistakes', []).append(_clean(child.text))
        elif child.tag in _PARTS:
            part = {'pos': _PARTS[child.tag], 'senses': []}
            for name in ('ipa', 'conj', 'inceptive', 'double', 'ie'):
                if child.attrib.get(name):
                    part[name] = _value(child.attrib[name])
            for sub in child:
                if sub.tag == 'translations':
                    part['senses'] += _senses(sub)
                elif sub.tag in _VERB_FORMS:
                    part.setdefault('forms', {})[_VERB_FORMS[sub.tag]] = _clean(sub.text)
                elif sub.tag == 'mistakes':
                    entry.setdefault('mistakes', []).append(_clean(sub.text))
                elif sub.tag in ('catacro', 'engacro'):
                    part[sub.tag.replace('acro', '_acronym')] = _clean(sub.text)
                elif sub.tag == 'expressions':
                    entry.setdefault('expressions', []).append(_phrase(sub))
            entry['parts'].append(part)
    return entry


def convert_folder(folder):
    """The entries of one DACCO folder (``dictionaries/cateng``), in file order."""
    entries = []
    for path in sorted(glob.glob(os.path.join(folder, '*.dic'))):
        for element in ET.parse(path).getroot().findall('Entry'):
            entries.append(_entry(element))
    return entries


def convert(repository, out_dir=DATA_DIR):
    """Convert both directions of a DACCO clone; returns {direction: count}."""
    counts = {}
    for direction, folder in SOURCE_FOLDERS.items():
        entries = convert_folder(os.path.join(repository, 'dictionaries', folder))
        write(entries, os.path.join(out_dir, FILES[direction]))
        counts[direction] = len(entries)
    load.cache_clear()
    _index.cache_clear()
    return counts


def write(entries, path):
    with io.open(path, 'w', encoding='utf-8') as handle:
        for entry in entries:
            handle.write(json.dumps(entry, ensure_ascii=False, separators=(',', ':')) + '\n')


# -- importing into the site's dictionary --------------------------------------------------

SOURCE_TAG = 'dacco'

_POS_TO_SITE = {
    'noun': 'noun', 'verb': 'verb', 'verb form': 'verb', 'adjective': 'adjective',
    'adverb': 'adverb', 'pronoun': 'pronoun', 'preposition': 'preposition',
    'conjunction': 'conjunction', 'exclamation': 'interjection',
}
_GENDER_TO_SITE = {'m': 'm', 'f': 'f', 'm/f': 'mf', 'm pl': 'm', 'f pl': 'f'}
# DACCO categories (their first part) -> the site's topics.
_TOPICS = {
    'food': 'food', 'fruit': 'food', 'animal': 'animals', 'animals': 'animals',
    'body': 'body', 'medical': 'body', 'medicine': 'body', 'household': 'home', 'tools': 'home',
    'clothes': 'clothes', 'weather': 'nature', 'plants': 'nature', 'plant': 'nature',
    'naturaldisaster': 'nature', 'astronomy': 'nature', 'geography': 'travel',
    'geograpy': 'travel', 'country': 'travel', 'region': 'travel', 'europe': 'travel',
    'river': 'travel', 'tourism': 'travel', 'city': 'city', 'transport': 'city',
    'transports': 'city', 'architecture': 'city', 'work': 'work', 'education': 'work',
    'computers': 'work', 'computer': 'work', 'financial': 'shopping', 'legal': 'society',
    'politics': 'society', 'political': 'society', 'religious': 'society',
    'religiuos': 'society', 'monarchy': 'society', 'crime': 'society',
    'topicalissues': 'society', 'media': 'society', 'nationality': 'society',
    'sports': 'leisure', 'sport': 'leisure', 'entertainment': 'leisure',
    'number': 'numbers', 'maths': 'numbers', 'time': 'time', 'timeOfDay': 'time',
    'colour': 'colors', 'color': 'colors', 'family': 'family', 'language': 'communication',
    'linguistics': 'communication', 'telephone': 'communication',
}
_MAX = 255  # WordTranslation.translation, example


def site_pos(pos):
    """The site's part of speech for a DACCO one, or None."""
    return _POS_TO_SITE.get(pos)


def gender_text(gender):
    """How a DACCO gender reads on the page: "m", "f", "m/f", "m pl"."""
    from flaskblog.i18n import gettext
    return {'m': gettext('ч.'), 'f': gettext('ж.'), 'm/f': gettext('ч./ж.'),
            'm pl': gettext('ч. мн.'), 'f pl': gettext('ж. мн.')}.get(gender, gender)


def site_meaning(sense, pos):
    """A DACCO sense in the site's style: "[instrument] to play / to strum"
    -> "play, strum (instrument)"."""
    glosses = re.findall(r'\[([^\]]*)\]', sense.get('text', ''))
    parts = []
    for item in translations(sense):
        item = item.replace(';', ',')
        if pos == 'verb' and item.lower().startswith('to '):
            item = item[3:]
        if item and item not in parts:
            parts.append(item)
    text = ', '.join(parts)
    if glosses and text:
        text += ' ({})'.format('; '.join(glosses).replace(';', ','))
    return text


def site_word(entry):
    """The fields of a site Word for a DACCO entry, or None when it has no
    translation to show."""
    meanings = []
    for sense in senses(entry):
        text = site_meaning(sense, _POS_TO_SITE.get(sense['pos']))
        if text and text not in meanings:
            if len('; '.join(meanings + [text])) > _MAX:
                if not meanings:
                    meanings.append(text[:_MAX - 1] + '…')
                break
            meanings.append(text)
    if not meanings:
        return None
    parts = entry.get('parts', [])
    pos = _POS_TO_SITE.get(parts[0]['pos']) if parts else None
    if pos is None and ' ' in entry['head']:
        pos = 'phrase'
    gender = None
    for part in parts:
        if part['pos'] == 'noun':
            for sense in part['senses']:
                if sense.get('gender') in _GENDER_TO_SITE:
                    gender = _GENDER_TO_SITE[sense['gender']]
                    break
            break
    topic = None
    for sense in senses(entry):
        if sense.get('category'):
            topic = _TOPICS.get(sense['category'].split(',')[0].split('-')[0].strip())
            if topic:
                break
    example = next((x for s in senses(entry) for x in s.get('examples', [])
                    if x.get('ca') and x.get('en') and len(x['ca']) <= _MAX and len(x['en']) <= _MAX),
                   None)
    note = next((s['note_en'] for s in senses(entry) if s.get('note_en')), None)
    return {
        'term': entry['head'][:100],
        'part_of_speech': pos,
        'gender': gender,
        'topic': topic,
        'example_ca': example['ca'] if example else None,
        'translation_en': '; '.join(meanings),
        'example_en': example['en'] if example else None,
        'notes_en': note,
    }


def _existing_keys(words):
    keys = set()
    for term in words:
        key = _key(term)
        keys.add(key)
        keys.add(key + '-se')
        keys.add(key + "'s")
    return keys


def import_words(entries=None):
    """Add the DACCO words (*entries*, by default all of ca-en) the
    dictionary does not have yet, with their English translation, marked
    ``source='dacco'``. Safe to run again: words already there are left
    alone. Returns how many were added. The caller commits."""
    from flaskblog import db
    from flaskblog.models import Word
    from flaskblog.vocabulary import senses as word_senses

    known = _existing_keys(term for (term,) in Word.query.with_entities(Word.term))
    slugs = {slug for (slug,) in Word.query.with_entities(Word.slug)}
    added = 0
    for entry in load('ca-en') if entries is None else entries:
        if _key(entry['head']) in known:
            continue
        fields = site_word(entry)
        if fields is None:
            continue
        known.update(_existing_keys([fields['term']]))
        word = Word(
            term=fields['term'], slug=_free_slug(fields['term'], slugs),
            part_of_speech=fields['part_of_speech'], gender=fields['gender'],
            topic=fields['topic'], example_ca=fields['example_ca'], source=SOURCE_TAG,
        )
        slugs.add(word.slug)
        word.set_translation('en', fields['translation_en'], fields['example_en'], fields['notes_en'])
        word.translations['en'].reviewed = True
        db.session.add(word)
        word_senses.sync_from_flat(word, ['en'])
        added += 1
        if added % 1000 == 0:
            db.session.flush()
    return added


def _free_slug(term, slugs):
    from slugify import slugify
    base = slugify(term) or 'word'
    slug, counter = base, 1
    while slug in slugs:
        slug = '{}-{}'.format(base, counter)
        counter += 1
    return slug


def remove_words():
    """Take the imported DACCO words away again (saved copies in "My
    dictionary" go with them). Returns how many. The caller commits."""
    from flaskblog import db
    from flaskblog.models import Word

    words = Word.query.filter_by(source=SOURCE_TAG).all()
    for word in words:
        db.session.delete(word)
    return len(words)
