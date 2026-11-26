# flaskblog/tests/test_audiobooks.py

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
