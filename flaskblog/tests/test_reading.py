# flaskblog/tests/test_reading.py

import unittest

from flaskblog.reader import works
from flaskblog.tests.helpers import AppTestCase

# Othello has five acts: 3, 3, 4, 3 and 2 scenes.
OTHELLO_SCENES = [(1, 1), (1, 2), (1, 3), (2, 1), (2, 2), (2, 3), (3, 1), (3, 2), (3, 3),
                  (3, 4), (4, 1), (4, 2), (4, 3), (5, 1), (5, 2)]
SPEAKERS = {'OTEL·LO', 'DESDÈMONA', 'IAGO', 'CASSIO', 'RODERIGO', 'BRABANCI', 'EMÍLIA',
            'BIANCA', 'LODOVICO', 'GRACIÀ', 'MONTANO', 'DUX', 'BUFÓ', 'SENADOR PRIMER',
            'SENADOR SEGON', 'SENADORS', 'OFICIAL', 'MISSATGER', 'MARINER', 'CAVALLER PRIMER',
            'CAVALLER SEGON', 'CAVALLER TERCER', 'CAVALLERS', 'HERALD', 'MÚSIC', 'TOTS'}


class OthelloDataTests(unittest.TestCase):

    def setUp(self):
        self.work = works.load('othello')

    def test_every_scene_is_there(self):
        self.assertEqual(OTHELLO_SCENES, [(s.act, s.scene) for s in self.work['scenes']])
        self.assertGreater(self.work['words'], 20000)

    def test_blocks(self):
        for scene in self.work['scenes']:
            self.assertTrue(scene.setting, (scene.act, scene.scene))
            self.assertGreaterEqual(len(scene.blocks), 3, (scene.act, scene.scene))  # 2.2: the herald
            for block in scene.blocks:
                if 'stage' in block:
                    self.assertTrue(block['stage'].strip())
                    continue
                self.assertTrue(block['lines'], block)
                self.assertTrue(all(line.strip() for line in block['lines']), block)
                speakers = set(block['speaker'].replace(' i ', ', ').split(', '))
                self.assertLessEqual(speakers, SPEAKERS, block['speaker'])

    def test_no_english_left(self):
        text = ' '.join(line for scene in self.work['scenes'] for block in scene.blocks
                        for line in block.get('lines', [block.get('stage', '')]))
        for english in (' the ', ' thou ', ' my lord', 'Exeunt', 'Enter '):
            self.assertNotIn(english, text)

    def test_unknown_work(self):
        self.assertIsNone(works.load('../secret'))
        self.assertIsNone(works.load('no-such-work'))


class ReadingPagesTests(AppTestCase):

    def test_library_work_and_scene(self):
        self.assertIn('Otel·lo', self.client.get('/reading').data.decode())
        body = self.client.get('/reading/othello').data.decode()
        self.assertIn('Acte cinquè', body)
        self.assertIn('href="/reading/othello/5/2"', body)
        body = self.client.get('/reading/othello/1/1').data.decode()
        self.assertIn('class="play-speaker">RODERIGO', body)
        self.assertIn('"mode": "read"', body)
        self.assertIn('href="/reading/othello/1/2"', body)          # next scene
        last = self.client.get('/reading/othello/5/2').data.decode()
        self.assertIn('href="/reading/othello/5/1"', last)
        self.assertNotIn('rel="next"', last)

    def test_missing(self):
        self.assertEqual(404, self.client.get('/reading/othello/6/1').status_code)
        self.assertEqual(404, self.client.get('/reading/hamlet').status_code)

    def test_menu_and_sitemap(self):
        self.assertIn('href="/reading"', self.client.get('/').data.decode())
        sitemap = self.client.get('/sitemap.xml').data.decode()
        self.assertIn('/reading/othello/3/3', sitemap)

    def test_switched_off(self):
        self.app.config['READING'] = False
        self.assertEqual(404, self.client.get('/reading').status_code)
        self.assertEqual(404, self.client.get('/reading/othello/1/1').status_code)
        self.assertNotIn('href="/reading"', self.client.get('/').data.decode())
        self.app.config['READING'] = True
        self.app.config['READER'] = False
        self.assertEqual(404, self.client.get('/reading').status_code)


if __name__ == '__main__':
    unittest.main()
