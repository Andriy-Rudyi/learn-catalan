"""Make the audiobooks: one MP3 per chapter or scene, read by Piper.

Piper (https://github.com/OHF-Voice/piper1-gpl) is an open text-to-speech
engine that runs on a CPU; its voices are on Hugging Face
(rhasspy/piper-voices). The site does not need either: the MP3s are made
once, here, and published as assets of the GitHub release ``audiobooks``;
``flaskblog/audiobooks.json`` lists them (``--manifest``), and
``flaskblog/audiobook_timings/`` keeps when each sentence is read, for the
text shown while listening.

    pip install piper-tts lameenc
    python scripts/make_audiobooks.py --voices <folder with the .onnx voices> --out <folder>
    python scripts/make_audiobooks.py --out <folder> --manifest

.github/workflows/audiobooks.yml does all of it on GitHub: it downloads the
voices, makes the parts the release does not have yet, uploads them and
commits the new flaskblog/audiobooks.json to dev.

The texts are the site's own, as flaskblog/audiobook_text.py lays them
out (the same text the listening page shows). They are read sentence by
sentence, without the quotation marks; a short pause follows each sentence
and a longer one each paragraph. Mono MP3 at 40 kbit/s: about 18 MB an hour of speech.
"""

import argparse
import glob
import io
import json
import os
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
BITRATE = 40
PAUSE = 0.7  # seconds after a paragraph
SENTENCE_PAUSE = 0.25  # seconds between the sentences of a paragraph
# Version of the way a part is made: parts made otherwise are made again.
# 2: sentence by sentence, with the timings for the text shown while
#    listening; quotation marks no longer read out.
VERSION = 2


def parts(lang):
    """[(slug, number, title of the work, the text's pieces)] for a language."""
    from flaskblog import audiobook_text
    return audiobook_text.parts(lang)


def synthesize(voice, pieces, out_path):
    """Read *pieces* aloud into an MP3, sentence by sentence.

    Returns (seconds, bytes, timings): timings are
    [piece, first character, end character, start second, end second] for
    every sentence, the characters counted in the piece as it is shown.
    """
    import lameenc

    from flaskblog import audiobook_text

    state = {'encoder': None, 'rate': 22050, 'samples': 0}
    data = bytearray()

    def add(audio):
        if state['encoder'] is None:
            return
        data.extend(state['encoder'].encode(audio))
        state['samples'] += len(audio) // 2

    def silence(seconds):
        add(bytes(int(state['rate'] * seconds) * 2))

    def now():
        return state['samples'] / float(state['rate'])

    timings = []
    for index, piece in enumerate(pieces):
        spans = audiobook_text.sentences(piece)
        for position, (start, end) in enumerate(spans):
            words = audiobook_text.spoken(piece[start:end])
            if not words:
                continue
            began = None
            for chunk in voice.synthesize(words):
                if state['encoder'] is None:
                    state['rate'] = chunk.sample_rate
                    encoder = lameenc.Encoder()
                    encoder.set_bit_rate(BITRATE)
                    encoder.set_in_sample_rate(state['rate'])
                    encoder.set_channels(1)
                    encoder.set_quality(5)
                    state['encoder'] = encoder
                if began is None:
                    began = now()
                add(chunk.audio_int16_bytes)
            if began is not None:
                timings.append([index, start, end, round(began, 2), round(now(), 2)])
            if position < len(spans) - 1:
                silence(SENTENCE_PAUSE)
        silence(PAUSE)
    data += state['encoder'].flush()
    with open(out_path, 'wb') as handle:
        handle.write(data)
    return round(now()), len(data), timings


def timing_path(mp3_path):
    """<part>.timing.json next to <part>.mp3."""
    return mp3_path[:-len('.mp3')] + '.timing.json'


def file_name(lang, slug, number):
    return '{}-{}-{:02d}.mp3'.format(lang, slug, number)


RELEASE = 'https://github.com/Andriy-Rudyi/learn-catalan/releases/download/audiobooks/'
# The release keeps the files, but serves them as downloads
# (application/octet-stream), which Safari on iPhone and older Android
# browsers refuse to play. The workflow copies them to GitHub Pages, which
# serves audio/mpeg, and the manifest points there (--base).
PAGES = 'https://andriy-rudyi.github.io/learn-catalan/audio/'
MANIFEST = os.path.join(ROOT, 'flaskblog', 'audiobooks.json')
TIMINGS = os.path.join(ROOT, 'flaskblog', 'audiobook_timings')


def write_manifest(out, base=RELEASE):
    """flaskblog/audiobooks.json from the .json files next to the MP3s."""
    works = {}
    for path in sorted(glob.glob(os.path.join(out, '*.mp3.json'))):
        with io.open(path, encoding='utf-8') as handle:
            info = json.load(handle)
        works.setdefault(info['lang'], {}).setdefault(info['slug'], []).append(
            (info['number'], {'file': os.path.basename(path)[:-5], 'seconds': info['seconds'],
                              'bytes': info['bytes']}))
    credits = {}
    for path in sorted(glob.glob(os.path.join(out, '*.mp3.json'))):
        with io.open(path, encoding='utf-8') as handle:
            info = json.load(handle)
        if info.get('credit'):
            credits.setdefault(info['lang'], {})[info['slug']] = info['credit']
    data = {'base': base,
            'voices': {lang: VOICES[lang][1] for lang in works},
            'credits': credits,
            'works': {lang: {slug: [item for _number, item in sorted(found, key=lambda pair: pair[0])]
                             for slug, found in sorted(slugs.items())}
                      for lang, slugs in sorted(works.items())}}
    with io.open(MANIFEST, 'w', encoding='utf-8') as handle:
        json.dump(data, handle, ensure_ascii=False, indent=1)
        handle.write('\n')
    # The timings of the sentences, for the text shown while listening.
    os.makedirs(TIMINGS, exist_ok=True)
    for path in sorted(glob.glob(os.path.join(out, '*.timing.json'))):
        name = os.path.basename(path)[:-len('.timing.json')] + '.json'
        with io.open(path, encoding='utf-8') as source, io.open(os.path.join(TIMINGS, name), 'w', encoding='utf-8') as target:
            target.write(source.read())
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

    import librivox_audiobooks
    os.makedirs(args.out, exist_ok=True)
    for lang in args.langs.split(','):
        name, _credit = VOICES[lang]
        voice = PiperVoice.load(os.path.join(args.voices, name + '.onnx'))
        listing = {}
        for slug, number, title, pieces in parts(lang):
            if librivox_audiobooks.handled(lang, slug):
                continue  # read by a person: scripts/librivox_audiobooks.py
            path = os.path.join(args.out, file_name(lang, slug, number))
            started = time.time()
            if os.path.exists(path + '.json'):
                with io.open(path + '.json', encoding='utf-8') as handle:
                    made = json.load(handle)
                if made.get('version') == VERSION:
                    listing[file_name(lang, slug, number)] = made
                    continue
            seconds, size, timings = synthesize(voice, pieces, path)
            info = {'lang': lang, 'slug': slug, 'number': number, 'title': title,
                    'seconds': seconds, 'bytes': size, 'version': VERSION}
            with io.open(path + '.json', 'w', encoding='utf-8') as handle:
                json.dump(info, handle, ensure_ascii=False)
            with io.open(timing_path(path), 'w', encoding='utf-8') as handle:
                json.dump({'version': VERSION, 'sentences': timings}, handle, separators=(',', ':'))
            print('{} {}s audio in {:.0f}s'.format(file_name(lang, slug, number), seconds,
                                                   time.time() - started), flush=True)


if __name__ == '__main__':
    main()
