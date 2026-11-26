"""Make the audiobooks: one MP3 per chapter or scene, read by Piper.

Piper (https://github.com/OHF-Voice/piper1-gpl) is an open text-to-speech
engine that runs on a CPU; its voices are on Hugging Face
(rhasspy/piper-voices). The site does not need either: the MP3s are made
once, here, and published as assets of the GitHub release ``audiobooks``;
``flaskblog/audiobooks.json`` lists them (``--manifest``).

    pip install piper-tts lameenc
    python scripts/make_audiobooks.py --voices <folder with the .onnx voices> --out <folder>
    python scripts/make_audiobooks.py --out <folder> --manifest

.github/workflows/audiobooks.yml does all of it on GitHub: it downloads the
voices, makes the parts the release does not have yet, uploads them and
commits the new flaskblog/audiobooks.json to dev.

The texts are the site's own (flaskblog/reader/data/works for Catalan,
flaskblog/langsites for the other languages). A chapter starts with its
title; a scene with its act, number and setting, then the stage directions
and the speeches, each with the speaker's name. Paragraphs are followed by
a short pause. Mono MP3 at 40 kbit/s: about 18 MB an hour of speech.
"""

import argparse
import glob
import io
import json
import os
import re
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

# Voice for each language and its licence (shown on the site).
VOICES = {
    'ca': ('ca_ES-upc_ona-medium', 'Piper voice "upc_ona" (UPC Festcat corpus, CC BY-SA 3.0 ES)'),
    'uk': ('uk_UA-tetiana-high', 'Piper voice "tetiana" (Apache 2.0)'),
    'en': ('en_US-kristin-medium', 'Piper voice "kristin" (public domain)'),
    'es': ('es_ES-davefx-medium', 'Piper voice "davefx" (CC0)'),
    'fr': ('fr_FR-siwis-medium', 'Piper voice "siwis" (SIWIS corpus, CC BY 4.0)'),
    'de': ('de_DE-thorsten-medium', 'Piper voice "thorsten" (Thorsten-Voice, CC0)'),
}
CHAPTER = {'ca': 'Capítol', 'uk': 'Розділ', 'en': 'Chapter', 'es': 'Capítulo', 'fr': 'Chapitre',
           'de': 'Kapitel'}
ACT_SCENE = {'ca': 'Acte {act}, escena {scene}.', 'en': 'Act {act}, scene {scene}.'}
BITRATE = 40
PAUSE = 0.7  # seconds after a paragraph


def parts(lang):
    """[(slug, number, title of the work, the text's pieces)] for a language."""
    found = []
    if lang == 'ca':
        folders = sorted(glob.glob(os.path.join(ROOT, 'flaskblog', 'reader', 'data', 'works', '*')))
        sources = [(os.path.basename(folder), folder, os.path.join(folder, 'work.json')) for folder in folders]
    else:
        from flaskblog.langsites import reading
        sources = []
        for work in reading.works(lang):
            folder = os.path.dirname(work['files'][0])
            sources.append((work['slug'], folder, None, work))
    for source in sources:
        slug, folder = source[0], source[1]
        if lang == 'ca':
            with io.open(source[2], encoding='utf-8') as handle:
                info = json.load(handle)
            title = info.get('title')
        else:
            info = source[3]
            title = info.get('title')
        chapters = sorted(glob.glob(os.path.join(folder, 'c[0-9]*.json')))
        scenes = sorted(glob.glob(os.path.join(folder, 'a[0-9]*s[0-9]*.json')),
                        key=lambda p: tuple(int(n) for n in re.search(r'a(\d+)s(\d+)', p).groups()))
        for number, path in enumerate(chapters or scenes, 1):
            with io.open(path, encoding='utf-8') as handle:
                text = json.load(handle)
            if chapters:
                pieces = ['{} {}.'.format(CHAPTER[lang], text.get('chapter', number))] + text['paragraphs']
            else:
                pieces = [ACT_SCENE.get(lang, ACT_SCENE['en']).format(act=text['act'], scene=text['scene'])]
                if text.get('setting'):
                    pieces.append(text['setting'])
                for block in text['blocks']:
                    if block.get('stage'):
                        pieces.append(block['stage'])
                    else:
                        pieces.append(block['speaker'].capitalize() + '. ' + ' '.join(block['lines']))
            found.append((slug, number, title, pieces))
    return found


def synthesize(voice, pieces, out_path):
    import lameenc
    encoder, rate, seconds = None, 22050, 0.0
    data = bytearray()
    for piece in pieces:
        piece = re.sub(r'\s+', ' ', piece).strip()
        if not piece:
            continue
        for chunk in voice.synthesize(piece):
            if encoder is None:
                rate = chunk.sample_rate
                encoder = lameenc.Encoder()
                encoder.set_bit_rate(BITRATE)
                encoder.set_in_sample_rate(rate)
                encoder.set_channels(1)
                encoder.set_quality(5)
            data += encoder.encode(chunk.audio_int16_bytes)
            seconds += len(chunk.audio_int16_bytes) / 2.0 / rate
        data += encoder.encode(bytes(int(rate * PAUSE) * 2))
        seconds += PAUSE
    data += encoder.flush()
    with open(out_path, 'wb') as handle:
        handle.write(data)
    return round(seconds), len(data)


def file_name(lang, slug, number):
    return '{}-{}-{:02d}.mp3'.format(lang, slug, number)


RELEASE = 'https://github.com/Andriy-Rudyi/learn-catalan/releases/download/audiobooks/'
# The release keeps the files, but serves them as downloads
# (application/octet-stream), which Safari on iPhone and older Android
# browsers refuse to play. The workflow copies them to GitHub Pages, which
# serves audio/mpeg, and the manifest points there (--base).
PAGES = 'https://andriy-rudyi.github.io/learn-catalan/audio/'
MANIFEST = os.path.join(ROOT, 'flaskblog', 'audiobooks.json')


def write_manifest(out, base=RELEASE):
    """flaskblog/audiobooks.json from the .json files next to the MP3s."""
    works = {}
    for path in sorted(glob.glob(os.path.join(out, '*.mp3.json'))):
        with io.open(path, encoding='utf-8') as handle:
            info = json.load(handle)
        works.setdefault(info['lang'], {}).setdefault(info['slug'], []).append(
            (info['number'], {'file': os.path.basename(path)[:-5], 'seconds': info['seconds'],
                              'bytes': info['bytes']}))
    data = {'base': base,
            'voices': {lang: VOICES[lang][1] for lang in works},
            'works': {lang: {slug: [item for _number, item in sorted(found, key=lambda pair: pair[0])]
                             for slug, found in sorted(slugs.items())}
                      for lang, slugs in sorted(works.items())}}
    with io.open(MANIFEST, 'w', encoding='utf-8') as handle:
        json.dump(data, handle, ensure_ascii=False, indent=1)
        handle.write('\n')
    return sum(len(found) for slugs in works.values() for found in slugs.values())


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--voices')
    parser.add_argument('--out', required=True)
    parser.add_argument('--langs', default=','.join(VOICES))
    parser.add_argument('--manifest', action='store_true',
                        help='only write flaskblog/audiobooks.json from the files in --out')
    parser.add_argument('--base', default=RELEASE,
                        help='address the MP3s are played from (with --manifest)')
    args = parser.parse_args()
    if args.manifest:
        print('parts:', write_manifest(args.out, args.base))
        return
    from piper import PiperVoice
    os.makedirs(args.out, exist_ok=True)
    for lang in args.langs.split(','):
        name, _credit = VOICES[lang]
        voice = PiperVoice.load(os.path.join(args.voices, name + '.onnx'))
        listing = {}
        for slug, number, title, pieces in parts(lang):
            path = os.path.join(args.out, file_name(lang, slug, number))
            started = time.time()
            if os.path.exists(path + '.json'):
                with io.open(path + '.json', encoding='utf-8') as handle:
                    listing[file_name(lang, slug, number)] = json.load(handle)
                continue
            seconds, size = synthesize(voice, pieces, path)
            info = {'lang': lang, 'slug': slug, 'number': number, 'title': title,
                    'seconds': seconds, 'bytes': size}
            with io.open(path + '.json', 'w', encoding='utf-8') as handle:
                json.dump(info, handle, ensure_ascii=False)
            print('{} {}s audio in {:.0f}s'.format(file_name(lang, slug, number), seconds,
                                                   time.time() - started), flush=True)


if __name__ == '__main__':
    main()
