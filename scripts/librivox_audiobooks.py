"""Audiobooks read by people: LibriVox recordings, matched word by word to the site's text.

LibriVox (https://librivox.org) volunteers read books whose text is in the
public domain, and their recordings are in the public domain too (Public
Domain Mark), so the site may use them freely, also with advertising.
scripts/librivox.json says which recording goes with which work.

For every part (a chapter, or a scene cut out of an act):

1. the recording is downloaded from archive.org;
2. faster-whisper (MIT; the Whisper models are MIT too) writes down what is
   heard, with the time of every word;
3. those words are matched to the site's text (flaskblog/audiobook_text.py)
   with difflib, so every word of the text gets its start, and the words
   the reader said differently get times in between; LibriVox's spoken
   notice at the start ("This is a LibriVox recording...") matches nothing
   and is simply skipped;
4. the part is written as a mono MP3 (40 kbit/s, as the Piper parts) with
   its .mp3.json and .timing.json, the same files make_audiobooks.py
   writes, so the rest (release, GitHub Pages, flaskblog/audiobooks.json)
   is the same. The timings hold each word's start, so the page lights up
   exactly the word being read.

    pip install faster-whisper
    python scripts/librivox_audiobooks.py --out <folder> [--only en:martin-eden] [--parts 1-12]

Needs ffmpeg. .github/workflows/audiobooks.yml runs it (job "librivox").
"""

import argparse
import difflib
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

CONFIG = os.path.join(ROOT, 'scripts', 'librivox.json')
DOWNLOAD = 'https://archive.org/download/{item}/{file}'
MODEL = 'small.en'
BITRATE = 40
# How parts made here are marked; make_audiobooks.py leaves them alone.
SOURCE = 'librivox'
VERSION = 3

_WORD = re.compile(r'\S+')
_PLAIN = re.compile(r"[^\w']+", re.UNICODE)


def config():
    with io.open(CONFIG, encoding='utf-8') as handle:
        return json.load(handle)


def works():
    """[(lang, slug, settings)] of the recordings in scripts/librivox.json."""
    return [(lang, slug, settings) for lang, by_slug in sorted(config().items()) if not lang.startswith('_')
            for slug, settings in sorted(by_slug.items())]


def handled(lang, slug):
    """True if the work is read by LibriVox (make_audiobooks.py skips it)."""
    return any(lang == found_lang and slug == found_slug for found_lang, found_slug, _ in works())


def plain(word):
    """A word for matching: lower case, letters and digits only."""
    return _PLAIN.sub('', word.lower().replace('’', "'")).strip("'")


def text_words(pieces):
    """[(piece, sentence start, sentence end, word start, word)] in reading order."""
    from flaskblog import audiobook_text

    found = []
    for index, piece in enumerate(pieces):
        for start, end in audiobook_text.sentences(piece):
            for match in _WORD.finditer(piece[start:end]):
                found.append((index, start, end, start + match.start(), match.group()))
    return found


def match(pieces, heard, offset=0.0):
    """Sentence timings ([piece, start, end, from, to, [word starts]]) of
    *pieces* from *heard* ([(word, start, end)]); *offset* is subtracted
    from every time (for a scene cut out of an act)."""
    words = text_words(pieces)
    if not words:
        return []
    ours = [plain(item[4]) for item in words]
    theirs = [plain(item[0]) for item in heard]
    starts, ends = [None] * len(words), [None] * len(words)
    matcher = difflib.SequenceMatcher(None, ours, theirs, autojunk=False)
    for block in matcher.get_matching_blocks():
        for step in range(block.size):
            _word, start, end = heard[block.b + step]
            starts[block.a + step] = start - offset
            ends[block.a + step] = end - offset
    # Words not heard as written: share the time between their neighbours.
    known = [index for index, value in enumerate(starts) if value is not None]
    if not known:
        return []
    for index in range(len(words)):
        if starts[index] is not None:
            continue
        before = max((k for k in known if k < index), default=None)
        after = min((k for k in known if k > index), default=None)
        if before is None:
            starts[index] = ends[index] = max(0.0, starts[after] - 0.3 * (after - index))
        elif after is None:
            starts[index] = ends[index] = ends[before] + 0.3 * (index - before)
        else:
            share = (starts[after] - ends[before]) / (after - before)
            starts[index] = ends[before] + share * (index - before - 1) + share * 0.05
            ends[index] = starts[index] + share * 0.9
    sentences, current = [], None
    for index, (piece, start, end, _at, _word) in enumerate(words):
        key = (piece, start, end)
        if current is None or current[0] != key:
            current = (key, [])
            sentences.append(current)
        current[1].append(index)
    out = []
    for (piece, start, end), indexes in sentences:
        begin = max(0.0, starts[indexes[0]])
        finish = max(begin, max(ends[index] for index in indexes))
        out.append([piece, start, end, round(begin, 2), round(finish, 2),
                    [round(max(0.0, starts[index]), 2) for index in indexes]])
    return out


def transcribe(model, wav_path):
    """[(word, start, end)] heard in a recording."""
    segments, _info = model.transcribe(wav_path, language='en', word_timestamps=True, vad_filter=True,
                                       beam_size=1, condition_on_previous_text=False)
    heard = []
    for segment in segments:
        for word in segment.words or []:
            heard.append((word.word.strip(), word.start, word.end))
    return heard


def ffmpeg(*args):
    subprocess.run(['ffmpeg', '-nostdin', '-loglevel', 'error', '-y'] + list(args), check=True)


def download(item, file_name, folder):
    path = os.path.join(folder, file_name)
    if not os.path.exists(path):
        url = DOWNLOAD.format(item=item, file=file_name)
        request = urllib.request.Request(url, headers={'User-Agent': 'audiobook-maker'})
        with urllib.request.urlopen(request, timeout=300) as reply, open(path, 'wb') as handle:
            while True:
                block = reply.read(1 << 20)
                if not block:
                    break
                handle.write(block)
    return path


def duration(path):
    out = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', path],
                         check=True, capture_output=True, text=True).stdout
    return float(out.strip())


def write_part(source, start, end, out_mp3):
    """The stretch [start, end) of a recording as a mono MP3."""
    args = ['-i', source]
    if start:
        args = ['-ss', '%.2f' % start] + args
    if end is not None:
        args += ['-t', '%.2f' % (end - start)]
    ffmpeg(*(args + ['-ac', '1', '-ar', '22050', '-b:a', '%dk' % BITRATE, '-codec:a', 'libmp3lame', out_mp3]))


def save(out, lang, slug, number, title, mp3, sentences, credit):
    from make_audiobooks import file_name

    name = file_name(lang, slug, number)
    info = {'lang': lang, 'slug': slug, 'number': number, 'title': title,
            'seconds': round(duration(mp3)), 'bytes': os.path.getsize(mp3),
            'version': VERSION, 'source': SOURCE, 'credit': credit}
    with io.open(os.path.join(out, name + '.json'), 'w', encoding='utf-8') as handle:
        json.dump(info, handle, ensure_ascii=False)
    with io.open(os.path.join(out, name[:-len('.mp3')] + '.timing.json'), 'w', encoding='utf-8') as handle:
        json.dump({'version': VERSION, 'sentences': sentences}, handle, separators=(',', ':'))
    return info


def done(out, lang, slug, number):
    from make_audiobooks import file_name

    path = os.path.join(out, file_name(lang, slug, number) + '.json')
    if not os.path.exists(path):
        return False
    with io.open(path, encoding='utf-8') as handle:
        made = json.load(handle)
    return made.get('source') == SOURCE and made.get('version') == VERSION


def wanted(numbers, ask):
    """The part numbers asked for with --parts ("1-12,20")."""
    if not ask:
        return numbers
    chosen = set()
    for chunk in ask.split(','):
        low, _dash, high = chunk.partition('-')
        chosen.update(range(int(low), int(high or low) + 1))
    return [number for number in numbers if number in chosen]


def run(out, only=None, ask=None, model_name=MODEL):
    from faster_whisper import WhisperModel

    from flaskblog import audiobook_text
    from make_audiobooks import file_name

    os.makedirs(out, exist_ok=True)
    model = None
    downloads = tempfile.mkdtemp(prefix='librivox-')
    for lang, slug, settings in works():
        if only and only != '{}:{}'.format(lang, slug):
            continue
        parts = [(number, title, pieces) for found_slug, number, title, pieces in audiobook_text.parts(lang)
                 if found_slug == slug]
        numbers = wanted([number for number, _title, _pieces in parts], ask)
        if settings.get('chapters'):
            for number, title, pieces in parts:
                if number not in numbers or done(out, lang, slug, number):
                    continue
                started = time.time()
                source = download(settings['item'], settings['chapters'][number - 1], downloads)
                wav = os.path.join(downloads, 'part.wav')
                ffmpeg('-i', source, '-ac', '1', '-ar', '16000', wav)
                model = model or WhisperModel(model_name, device='cpu', compute_type='int8')
                heard = transcribe(model, wav)
                sentences = match(pieces, heard)
                mp3 = os.path.join(out, file_name(lang, slug, number))
                write_part(source, 0, None, mp3)
                info = save(out, lang, slug, number, title, mp3, sentences, settings['credit'])
                print('{} {}s, {} words heard, {:.0f}s'.format(os.path.basename(mp3), info['seconds'], len(heard),
                                                               time.time() - started), flush=True)
        else:  # a play recorded act by act: every scene is cut out of its act
            by_act = {}
            for number, title, pieces in parts:
                act = int(re.match(r'\D*(\d+)', pieces[0]).group(1))
                by_act.setdefault(act, []).append((number, title, pieces))
            for act, scenes in sorted(by_act.items()):
                todo = [scene for scene in scenes if scene[0] in numbers and not done(out, lang, slug, scene[0])]
                if not todo:
                    continue
                started = time.time()
                source = download(settings['item'], settings['acts'][str(act)], downloads)
                wav = os.path.join(downloads, 'part.wav')
                ffmpeg('-i', source, '-ac', '1', '-ar', '16000', wav)
                model = model or WhisperModel(model_name, device='cpu', compute_type='int8')
                heard = transcribe(model, wav)
                # Where each scene starts: the first matched word of its text,
                # found by matching the whole act at once.
                whole = [piece for _number, _title, pieces in scenes for piece in pieces]
                timings = match(whole, heard)
                first_piece, beginnings = 0, []
                for _number, _title, pieces in scenes:
                    spoken = [item for item in timings if first_piece < item[0] < first_piece + len(pieces)]
                    beginnings.append(spoken[0][3] if spoken else None)
                    first_piece += len(pieces)
                length = duration(source)
                first_piece = 0
                for position, (number, title, pieces) in enumerate(scenes):
                    begin = 0.0 if position == 0 else max(0.0, (beginnings[position] or 0) - 1.5)
                    following = beginnings[position + 1] if position + 1 < len(scenes) else None
                    end = max(begin, following - 1.5) if following else length
                    if (number, title, pieces) in todo:
                        mine = [[item[0] - first_piece] + item[1:3] + [round(item[3] - begin, 2), round(item[4] - begin, 2),
                                                                        [round(t - begin, 2) for t in item[5]]]
                                for item in timings if first_piece <= item[0] < first_piece + len(pieces)]
                        mp3 = os.path.join(out, file_name(lang, slug, number))
                        write_part(source, begin, end if following else None, mp3)
                        save(out, lang, slug, number, title, mp3, mine, settings['credit'])
                    first_piece += len(pieces)
                print('{} act {}: {} scenes, {} words heard, {:.0f}s'.format(slug, act, len(scenes), len(heard),
                                                                           time.time() - started), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--out', required=True)
    parser.add_argument('--only', help='one work, e.g. en:martin-eden')
    parser.add_argument('--parts', help='part numbers, e.g. 1-12,20')
    parser.add_argument('--model', default=MODEL)
    args = parser.parse_args()
    run(args.out, args.only, args.parts, args.model)


if __name__ == '__main__':
    main()
