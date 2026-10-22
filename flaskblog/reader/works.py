"""Texts to read on the site (/reading), each split into parts to read in
one sitting. A work is a folder in data/works/ with work.json (title,
author, kind...) and its parts.

A play ("kind": "play", the default) has one file per scene, a{act}s{scene}.json:

    {"act": 1, "scene": 1, "setting": "Venècia. Un carrer.",
     "blocks": [{"stage": "Entren RODERIGO i IAGO."},
                {"speaker": "RODERIGO", "lines": ["...", "..."]}]}

A novel ("kind": "novel") has one file per chapter, c{NN}.json:

    {"chapter": 1, "paragraphs": ["L'un va obrir la porta...", "..."]}

The text the translation was made from may sit beside it in
original/{lang}/c{NN}.json, paragraph for paragraph (the same list
length), for translating the work into other languages later; the site
does not load it.

Every word of the text can be clicked: the page uses the same panel as /text.
"""

import functools
import glob
import io
import json
import os
import re
from collections import namedtuple

WORKS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'works')
ROMAN = ['', 'I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X']
ORDINALS = ['', 'primer', 'segon', 'tercer', 'quart', 'cinquè']
WORD = re.compile(r"[^\W\d_]+(?:['’·-][^\W\d_]+)*")

Scene = namedtuple('Scene', 'act scene setting blocks words')
Chapter = namedtuple('Chapter', 'number paragraphs words')


def _words(scene):
    text = ' '.join(block.get('stage', '') + ' ' + ' '.join(block.get('lines', ()))
                    for block in scene['blocks'])
    return len(WORD.findall(text))


@functools.lru_cache(maxsize=None)
def load(slug):
    """The work with its scenes or chapters in order, or None."""
    if not re.fullmatch(r'[a-z0-9-]+', slug or ''):
        return None
    folder = os.path.join(WORKS_DIR, slug)
    try:
        with io.open(os.path.join(folder, 'work.json'), encoding='utf-8') as handle:
            work = json.load(handle)
    except OSError:
        return None
    work.setdefault('kind', 'play')
    scenes, chapters = [], []
    if work['kind'] == 'novel':
        for path in glob.glob(os.path.join(folder, 'c[0-9]*.json')):
            with io.open(path, encoding='utf-8') as handle:
                data = json.load(handle)
            chapters.append(Chapter(data['chapter'], data['paragraphs'],
                                    sum(len(WORD.findall(p)) for p in data['paragraphs'])))
        chapters.sort(key=lambda c: c.number)
    else:
        for path in glob.glob(os.path.join(folder, 'a*s*.json')):
            with io.open(path, encoding='utf-8') as handle:
                data = json.load(handle)
            scenes.append(Scene(data['act'], data['scene'], data.get('setting', ''),
                                data['blocks'], _words(data)))
        scenes.sort(key=lambda s: (s.act, s.scene))
    work['scenes'] = scenes
    work['acts'] = sorted({s.act for s in scenes})
    work['chapters'] = chapters
    work['parts'] = chapters or scenes
    work['words'] = sum(part.words for part in work['parts'])
    return work


def all_works():
    names = sorted(os.path.basename(path) for path in glob.glob(os.path.join(WORKS_DIR, '*'))
                   if os.path.isdir(path))
    return [work for work in map(load, names) if work and work['parts']]


def find_scene(work, act, scene):
    """(previous, this, next) scene, or None when there is no such scene."""
    scenes = work['scenes']
    for k, item in enumerate(scenes):
        if (item.act, item.scene) == (act, scene):
            return (scenes[k - 1] if k else None, item,
                    scenes[k + 1] if k + 1 < len(scenes) else None)
    return None


def find_chapter(work, number):
    """(previous, this, next) chapter, or None when there is no such chapter."""
    chapters = work['chapters']
    for k, item in enumerate(chapters):
        if item.number == number:
            return (chapters[k - 1] if k else None, item,
                    chapters[k + 1] if k + 1 < len(chapters) else None)
    return None


def roman(number):
    """46 -> "XLVI"."""
    out = ''
    for value, letters in ((1000, 'M'), (900, 'CM'), (500, 'D'), (400, 'CD'), (100, 'C'),
                           (90, 'XC'), (50, 'L'), (40, 'XL'), (10, 'X'), (9, 'IX'),
                           (5, 'V'), (4, 'IV'), (1, 'I')):
        while number >= value:
            out += letters
            number -= value
    return out


def chapter_label(chapter):
    """"Capítol XLVI" (Catalan, like the text itself)."""
    return 'Capítol %s' % roman(chapter.number)


def act_title(act):
    """"Acte primer" (Catalan, like the text itself)."""
    if 0 < act < len(ORDINALS):
        return 'Acte ' + ORDINALS[act]
    return 'Acte %d' % act


def scene_label(scene):
    return 'Acte %s, escena %d' % (ROMAN[scene.act] if scene.act < len(ROMAN) else scene.act,
                                   scene.scene)
