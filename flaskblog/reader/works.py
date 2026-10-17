"""Texts to read on the site (/reading), each split into parts to read in
one sitting. A play is a folder in data/works/ with work.json (title,
author, characters) and one file per scene, a{act}s{scene}.json:

    {"act": 1, "scene": 1, "setting": "Venècia. Un carrer.",
     "blocks": [{"stage": "Entren RODERIGO i IAGO."},
                {"speaker": "RODERIGO", "lines": ["...", "..."]}]}

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

Scene = namedtuple('Scene', 'act scene setting blocks words')


def _words(scene):
    text = ' '.join(block.get('stage', '') + ' ' + ' '.join(block.get('lines', ()))
                    for block in scene['blocks'])
    return len(re.findall(r"[^\W\d_]+(?:['’·-][^\W\d_]+)*", text))


@functools.lru_cache(maxsize=None)
def load(slug):
    """The work with its scenes in order, or None."""
    if not re.fullmatch(r'[a-z0-9-]+', slug or ''):
        return None
    folder = os.path.join(WORKS_DIR, slug)
    try:
        with io.open(os.path.join(folder, 'work.json'), encoding='utf-8') as handle:
            work = json.load(handle)
    except OSError:
        return None
    scenes = []
    for path in glob.glob(os.path.join(folder, 'a*s*.json')):
        with io.open(path, encoding='utf-8') as handle:
            data = json.load(handle)
        scenes.append(Scene(data['act'], data['scene'], data.get('setting', ''),
                            data['blocks'], _words(data)))
    scenes.sort(key=lambda s: (s.act, s.scene))
    work['scenes'] = scenes
    work['acts'] = sorted({s.act for s in scenes})
    work['words'] = sum(s.words for s in scenes)
    return work


def all_works():
    names = sorted(os.path.basename(path) for path in glob.glob(os.path.join(WORKS_DIR, '*'))
                   if os.path.isdir(path))
    return [work for work in map(load, names) if work and work['scenes']]


def find_scene(work, act, scene):
    """(previous, this, next) scene, or None when there is no such scene."""
    scenes = work['scenes']
    for k, item in enumerate(scenes):
        if (item.act, item.scene) == (act, scene):
            return (scenes[k - 1] if k else None, item,
                    scenes[k + 1] if k + 1 < len(scenes) else None)
    return None


def act_title(act):
    """"Acte primer" (Catalan, like the text itself)."""
    if 0 < act < len(ORDINALS):
        return 'Acte ' + ORDINALS[act]
    return 'Acte %d' % act


def scene_label(scene):
    return 'Acte %s, escena %d' % (ROMAN[scene.act] if scene.act < len(ROMAN) else scene.act,
                                   scene.scene)
