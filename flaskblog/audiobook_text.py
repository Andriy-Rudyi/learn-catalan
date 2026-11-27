"""The text of the audiobooks, as it is read aloud and shown while listening.

scripts/make_audiobooks.py reads these pieces aloud sentence by sentence
and keeps when each sentence starts and ends
(``flaskblog/audiobook_timings/<file>.json``); the listening page
(templates/audiobook.html, static/audiobook.js) shows the same pieces and
lights up the word being read. Both take the text from here, so that the
character positions of the timings match what the page shows.

A chapter starts with its title; a scene with its act, number and setting,
then the stage directions and the speeches, each with the speaker's name.
"""

import functools
import glob
import io
import json
import os
import re

ROOT = os.path.dirname(os.path.abspath(__file__))

CHAPTER = {'ca': 'Capítol', 'uk': 'Розділ', 'en': 'Chapter', 'es': 'Capítulo', 'fr': 'Chapitre',
           'de': 'Kapitel'}
ACT_SCENE = {'ca': 'Acte {act}, escena {scene}.', 'en': 'Act {act}, scene {scene}.'}

# The end of a sentence: . ! ? … (repeated), closing quotes or brackets,
# then a space.
_SENTENCE_END = re.compile(r'[.!?…]+[»”"’)\]]*(?=\s)')
# Read aloud, quotation marks are named ("lapki vidkryti"): they are left
# out of what the voice gets, and only there.
_UNSPOKEN = re.compile(r'[«»“”„"‹›*_]')


def _tidy(text):
    return re.sub(r'\s+', ' ', text or '').strip()


def _sources(lang):
    """[(slug, folder, title)] of the works of a language."""
    if lang == 'ca':
        found = []
        for folder in sorted(glob.glob(os.path.join(ROOT, 'reader', 'data', 'works', '*'))):
            with io.open(os.path.join(folder, 'work.json'), encoding='utf-8') as handle:
                found.append((os.path.basename(folder), folder, json.load(handle).get('title')))
        return found
    from flaskblog.langsites import reading
    return [(work['slug'], os.path.dirname(work['files'][0]), work.get('title'))
            for work in reading.works(lang)]


def _files(folder):
    chapters = sorted(glob.glob(os.path.join(folder, 'c[0-9]*.json')))
    if chapters:
        return chapters, True
    scenes = sorted(glob.glob(os.path.join(folder, 'a[0-9]*s[0-9]*.json')),
                    key=lambda path: tuple(int(n) for n in re.search(r'a(\d+)s(\d+)', path).groups()))
    return scenes, False


def _pieces(lang, path, novel, number):
    with io.open(path, encoding='utf-8') as handle:
        text = json.load(handle)
    if novel:
        pieces = ['{} {}.'.format(CHAPTER[lang], text.get('chapter', number))] + list(text['paragraphs'])
    else:
        pieces = [ACT_SCENE.get(lang, ACT_SCENE['en']).format(act=text['act'], scene=text['scene'])]
        if text.get('setting'):
            pieces.append(text['setting'])
        for block in text['blocks']:
            if block.get('stage'):
                pieces.append(block['stage'])
            else:
                pieces.append(block['speaker'].capitalize() + '. ' + ' '.join(block['lines']))
    return [piece for piece in (_tidy(piece) for piece in pieces) if piece]


def parts(lang):
    """[(slug, number, title of the work, pieces)] of every work of a language."""
    found = []
    for slug, folder, title in _sources(lang):
        files, novel = _files(folder)
        for number, path in enumerate(files, 1):
            found.append((slug, number, title, _pieces(lang, path, novel, number)))
    return found


@functools.lru_cache(maxsize=8)
def pieces(lang, slug, number):
    """The pieces of one part (a chapter or a scene), or None."""
    for found_slug, folder, _title in _sources(lang):
        if found_slug != slug:
            continue
        files, novel = _files(folder)
        if 1 <= number <= len(files):
            return _pieces(lang, files[number - 1], novel, number)
    return None


def sentences(piece):
    """[(start, end)] character spans of the sentences of a piece."""
    spans, start = [], 0
    for match in _SENTENCE_END.finditer(piece):
        end = match.end()
        if piece[start:end].strip():
            spans.append((start, end))
        start = end
        while start < len(piece) and piece[start].isspace():
            start += 1
    if piece[start:].strip():
        spans.append((start, len(piece)))
    return spans


def spoken(text):
    """What the voice gets for a sentence: without quotation marks."""
    return _tidy(_UNSPOKEN.sub(' ', text))
