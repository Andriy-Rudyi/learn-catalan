# flaskblog/tests/test_audiobooks.py

import io
import json
from unittest import mock

from flaskblog import audiobooks
from flaskblog.tests.helpers import AppTestCase

BASE = 'https://example.org/audio/'
MANIFEST = {
    'base': BASE,
    'voices': {'ca': 'Piper voice "upc_ona"', 'en': 'Piper voice "kristin"', 'uk': 'Piper voice "tetiana"'},
    'works': {
        'ca': {'martin-eden': [{'file': 'ca-martin-eden-%02d.mp3' % n, 'seconds': 1500 + n, 'bytes': 1}
                               for n in range(1, 47)],
               'othello': [{'file': 'ca-othello-%02d.mp3' % n, 'seconds': 600, 'bytes': 1} for n in range(1, 16)]},
        'en': {'othello': [{'file': 'en-othello-%02d.mp3' % n, 'seconds': 600, 'bytes': 1} for n in range(1, 16)]},
        'uk': {'martin-eden': [{'file': 'uk-martin-eden-01.mp3', 'seconds': 1726, 'bytes': 1}]},
    },
}


class AudiobookTests(AppTestCase):

    def setUp(self):
        super().setUp()
        patcher = mock.patch.object(audiobooks, 'manifest', return_value=MANIFEST)
        patcher.start()
        self.addCleanup(patcher.stop)

    def config(self, body):
        start = body.index('id="audiobook-config">') + len('id="audiobook-config">')
        return json.loads(body[start:body.index('</script>', start)])

    def test_parts(self):
        parts = audiobooks.parts('ca', 'martin-eden')
        self.assertEqual(46, len(parts))
        self.assertEqual(BASE + 'ca-martin-eden-01.mp3', parts[0]['url'])
        self.assertEqual([], audiobooks.parts('de', 'martin-eden'))
        self.assertEqual('1:02:03', audiobooks.clock(3723))
        self.assertEqual('5:07', audiobooks.clock(307))

    def test_catalan_audiobook_page(self):
        body = self.client.get('/reading/martin-eden/listen').get_data(as_text=True)
        self.assertIn('id="ab-audio"', body)
        self.assertIn('static/audiobook.js', body)
        config = self.config(body)
        self.assertEqual(46, len(config['parts']))
        self.assertEqual(BASE + 'ca-martin-eden-02.mp3', config['parts'][1]['url'])
        self.assertTrue(config['parts'][0]['title'])
        self.assertEqual('audiobook:ca:martin-eden', config['store'])
        self.assertIn('/reading/martin-eden/1', body)  # read the part
        self.assertIn('upc_ona', body)  # the voice is credited
        # The player's settings do not hide the site's: same design and menu as the other pages.
        self.assertNotIn('data-design=""', body)
        self.assertIn('href="/reading"', body)
        self.assertTrue(config['strings']['error'])
        scenes = self.config(self.client.get('/reading/othello/listen').get_data(as_text=True))
        self.assertEqual(15, len(scenes['parts']))

    def test_links_from_the_reading(self):
        self.assertIn('/reading/martin-eden/listen', self.client.get('/reading/martin-eden').get_data(as_text=True))
        self.assertIn('/reading/martin-eden/listen?part=3', self.client.get('/reading/martin-eden/3').get_data(as_text=True))
        self.assertIn('/reading/othello/listen?part=1', self.client.get('/reading/othello/1/1').get_data(as_text=True))

    def test_sections(self):
        body = self.client.get('/ukrainian/reading/martin-eden/listen').get_data(as_text=True)
        self.assertEqual(1, len(self.config(body)['parts']))
        self.assertIn('LangWave', body)  # the section's menu
        self.assertIn('/ukrainian/reading/martin-eden/listen', self.client.get('/ukrainian/reading/martin-eden').get_data(as_text=True))
        self.assertIn('/english/reading/othello/listen?part=2', self.client.get('/english/reading/othello/2').get_data(as_text=True))

    def test_no_audio_no_page(self):
        self.assertEqual(404, self.client.get('/german/reading/martin-eden/listen').status_code)
        self.assertEqual(404, self.client.get('/reading/nothing/listen').status_code)
        self.assertNotIn('/listen', self.client.get('/german/reading/martin-eden').get_data(as_text=True))
        with mock.patch.object(audiobooks, 'manifest', return_value={}):
            self.assertEqual(404, self.client.get('/reading/martin-eden/listen').status_code)
            self.assertNotIn('/listen', self.client.get('/reading/martin-eden').get_data(as_text=True))


class AudiobookTextTests(AppTestCase):
    """The text shown while listening, and the sound passed on through the site."""

    def setUp(self):
        super().setUp()
        patcher = mock.patch.object(audiobooks, 'manifest', return_value=MANIFEST)
        patcher.start()
        self.addCleanup(patcher.stop)
        audiobooks.timing.cache_clear()
        self.addCleanup(audiobooks.timing.cache_clear)

    def test_sentences_and_what_is_spoken(self):
        from flaskblog import audiobook_text
        piece = '«Він розуміє», подумав він. «Він мені допоможе.» Та й годі! Кінець'
        spans = audiobook_text.sentences(piece)
        self.assertEqual(['«Він розуміє», подумав він.', '«Він мені допоможе.»', 'Та й годі!', 'Кінець'],
                         [piece[start:end] for start, end in spans])
        self.assertEqual('Він розуміє , подумав він.', audiobook_text.spoken('«Він розуміє», подумав він.'))

    def test_pieces_are_the_ones_read_aloud(self):
        from flaskblog import audiobook_text
        pieces = audiobook_text.pieces('uk', 'martin-eden', 1)
        self.assertEqual('Розділ 1.', pieces[0])
        self.assertTrue(pieces[1].startswith('Перший'))
        self.assertEqual(pieces, [found for slug, number, _title, found in audiobook_text.parts('uk')
                                  if slug == 'martin-eden' and number == 1][0])
        scene = audiobook_text.pieces('ca', 'othello', 1)
        self.assertTrue(scene[0].startswith('Acte 1, escena 1'))
        self.assertIsNone(audiobook_text.pieces('uk', 'martin-eden', 99))

    def test_text_of_a_part(self):
        timings = [[0, 0, 9, 0.0, 1.25], [1, 0, 115, 1.95, 9.87]]
        with mock.patch.object(audiobooks, 'timing', return_value=timings):
            data = self.client.get('/ukrainian/reading/martin-eden/listen/1.json').get_json()
            self.assertEqual('Розділ 1.', data['pieces'][0])
            self.assertEqual(timings, data['sentences'])
            catalan = self.client.get('/reading/martin-eden/listen/2.json').get_json()
            self.assertTrue(catalan['pieces'][0].startswith('Capítol'))
        self.assertEqual([], self.client.get('/reading/othello/listen/1.json').get_json()['sentences'])
        self.assertEqual(404, self.client.get('/ukrainian/reading/martin-eden/listen/2.json').status_code)
        self.assertEqual(404, self.client.get('/german/reading/martin-eden/listen/1.json').status_code)

    def test_page_links_text_and_relay(self):
        body = self.client.get('/reading/martin-eden/listen').get_data(as_text=True)
        self.assertIn('id="ab-text"', body)
        start = body.index('id="audiobook-config">') + len('id="audiobook-config">')
        config = json.loads(body[start:body.index('</script>', start)])
        self.assertEqual('/reading/martin-eden/listen/1.json', config['parts'][0]['text'])
        self.assertEqual('/audio/ca-martin-eden-01.mp3', config['parts'][0]['proxy'])

    def test_relay_passes_a_piece(self):
        class Reply(io.BytesIO):
            status = 206

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

        with mock.patch.object(audiobooks.urllib.request, 'urlopen', return_value=Reply(b'x' * 10)) as opened:
            response = self.client.get('/audio/ca-martin-eden-01.mp3', headers={'Range': 'bytes=0-'})
        self.assertEqual(206, response.status_code)
        self.assertEqual('audio/mpeg', response.mimetype)
        self.assertEqual('bytes 0-9/1', response.headers['Content-Range'])
        self.assertEqual(BASE + 'ca-martin-eden-01.mp3', opened.call_args[0][0].full_url)
        self.assertEqual('bytes=0-0', opened.call_args[0][0].get_header('Range'))
        self.assertEqual(404, self.client.get('/audio/elsewhere.mp3', headers={'Range': 'bytes=0-'}).status_code)
        self.assertEqual(302, self.client.get('/audio/ca-martin-eden-01.mp3').status_code)  # no range: the host
