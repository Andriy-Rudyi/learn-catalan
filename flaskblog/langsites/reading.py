"""Texts to read in a language section, with every word clickable.

A section's works come from two places, in the same formats as the
Catalan reading (flaskblog/reader/works.py):

* ``langsites/data/<code>/works/<slug>/`` with its own work.json and
  chapters (``c01.json``...) or scenes (``a1s1.json``...);
* the Catalan site's works whose original is in that language
  (``reader/data/works/<slug>/original/<code>/``), e.g. Martin Eden in
  English.

``flask langsites import-play <xml> <code> <slug>`` turns a play marked up
in Jon Bosak's Shakespeare XML into scenes.
"""

import functools
import glob
import io
import json
import os
import re
import xml.etree.ElementTree as ET

from flaskblog.langsites.dictionary import DATA_DIR
from flaskblog.reader.works import WORKS_DIR as CATALAN_WORKS

WORD = re.compile(r"[^\W\d_]+(?:['’-][^\W\d_]+)*")


def _read(path):
    with io.open(path, encoding='utf-8') as handle:
        return json.load(handle)


def _parts(folder):
    chapters = sorted(glob.glob(os.path.join(folder, 'c[0-9]*.json')))
    if chapters:
        return 'novel', chapters
    scenes = glob.glob(os.path.join(folder, 'a[0-9]*s[0-9]*.json'))

    def order(path):
        act, scene = re.search(r'a(\d+)s(\d+)\.json$', path).groups()
        return int(act), int(scene)
    return 'play', sorted(scenes, key=order)


@functools.lru_cache(maxsize=16)
def works(code):
    """The works of a section: [{slug, title, author, year, level, kind,
    source, files}], in title order."""
    found = []
    for folder in sorted(glob.glob(os.path.join(DATA_DIR, code, 'works', '*'))):
        try:
            work = _read(os.path.join(folder, 'work.json'))
        except OSError:
            continue
        kind, files = _parts(folder)
        work.update(kind=kind, files=files, slug=os.path.basename(folder))
        found.append(work)
    for folder in sorted(glob.glob(os.path.join(CATALAN_WORKS, '*'))):
        original = os.path.join(folder, 'original', code)
        if not os.path.isdir(original):
            continue
        work = _read(os.path.join(folder, 'work.json'))
        kind, files = _parts(original)
        if not files:
            continue
        info = work.get('original', {})
        found.append({'slug': work['slug'], 'title': info.get('title', work['title']),
                      'author': work.get('author'), 'year': work.get('year'),
                      'level': work.get('level'), 'source': info.get('source'),
                      'kind': kind, 'files': files})
    return sorted(found, key=lambda work: work['title'])


def work(code, slug):
    return next((item for item in works(code) if item['slug'] == slug), None)


def part(work_info, number):
    """Part *number* (1-based) of a work: a chapter
    ({chapter, paragraphs}) or a scene ({act, scene, setting, blocks})."""
    if not 1 <= number <= len(work_info['files']):
        return None
    return _read(work_info['files'][number - 1])


def part_title(work_info, number):
    path = work_info['files'][number - 1]
    if work_info['kind'] == 'novel':
        return int(re.search(r'c(\d+)\.json$', path).group(1))
    act, scene = re.search(r'a(\d+)s(\d+)\.json$', path).groups()
    return int(act), int(scene)


def tokens(text):
    """[(text, is_word)] pieces of a line, for making the words clickable."""
    pieces, position = [], 0
    for match in WORD.finditer(text):
        if match.start() > position:
            pieces.append((text[position:match.start()], False))
        pieces.append((match.group(), True))
        position = match.end()
    if position < len(text):
        pieces.append((text[position:], False))
    return pieces


# -- importing ------------------------------------------------------------------------------------

def _text(element):
    return ' '.join(''.join(element.itertext()).split())


def import_play(xml_path, code, slug, **info):
    """Write a play in Bosak's Shakespeare XML (PLAY/ACT/SCENE/SPEECH) as
    scene files under langsites/data/<code>/works/<slug>/. Returns the
    number of scenes."""
    root = ET.parse(xml_path).getroot()
    folder = os.path.join(DATA_DIR, code, 'works', slug)
    os.makedirs(folder, exist_ok=True)
    count = 0
    for act_number, act in enumerate(root.findall('ACT'), 1):
        for scene_number, scene in enumerate(act.findall('SCENE'), 1):
            title = _text(scene.find('TITLE'))
            setting = re.sub(r'^SCENE [IVXLC]+\.\s*', '', title)
            blocks = []
            for element in scene:
                if element.tag == 'STAGEDIR':
                    blocks.append({'stage': _text(element)})
                elif element.tag == 'SPEECH':
                    speaker = ' / '.join(_text(s) for s in element.findall('SPEAKER'))
                    lines = []
                    for line in element:
                        if line.tag == 'LINE':
                            lines.append(_text(line))
                        elif line.tag == 'STAGEDIR' and lines:
                            lines[-1] += ' [' + _text(line) + ']'
                    blocks.append({'speaker': speaker, 'lines': lines})
            with io.open(os.path.join(folder, 'a{}s{}.json'.format(act_number, scene_number)), 'w',
                         encoding='utf-8') as handle:
                json.dump({'act': act_number, 'scene': scene_number, 'setting': setting,
                           'blocks': blocks}, handle, ensure_ascii=False, indent=1)
                handle.write('\n')
            count += 1
    work_info = dict(info)
    work_info.setdefault('title', _text(root.find('TITLE')))
    with io.open(os.path.join(folder, 'work.json'), 'w', encoding='utf-8') as handle:
        json.dump(work_info, handle, ensure_ascii=False, indent=1)
        handle.write('\n')
    works.cache_clear()
    return count
