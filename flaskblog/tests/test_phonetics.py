# flaskblog/tests/test_phonetics.py

import re
import unittest

from flaskblog.phonetics import service
from flaskblog.tests.helpers import AppTestCase

RUSSIAN_ONLY = re.compile('[ыЫэЭъЪёЁ]')
LEVELS = {'A1', 'A2', 'B1', 'B2', 'C1'}
KEYS = {'number', 'slug', 'title', 'section', 'level', 'summary',
        'explanation', 'sounds', 'words', 'exercises'}


class PhoneticsDataTests(unittest.TestCase):

    def setUp(self):
        self.lessons = service.load_lessons()

    def test_lessons_are_numbered_without_gaps(self):
        numbers = [lesson['number'] for lesson in self.lessons]
        self.assertEqual(list(range(1, len(numbers) + 1)), numbers)
        self.assertGreaterEqual(len(numbers), 10)

    def test_every_lesson_is_complete(self):
        slugs = set()
        for lesson in self.lessons:
            self.assertTrue(KEYS <= set(lesson), lesson['number'])
            self.assertRegex(lesson['slug'], r'^[a-z0-9-]+$')
            self.assertNotIn(lesson['slug'], slugs)
            slugs.add(lesson['slug'])
            self.assertIn(lesson['level'], LEVELS)
            self.assertIn(lesson['section'], service.SECTION_ORDER)
            for sound in lesson['sounds']:
                for key in ('spelling', 'ipa', 'example', 'uk'):
                    self.assertTrue(sound.get(key), (lesson['number'], sound))
            for word in lesson['words']:
                for key in ('ca', 'ipa', 'uk'):
                    self.assertTrue(word.get(key), (lesson['number'], word))
            for block in lesson['exercises']:
                self.assertTrue(block['instruction'])
                for item in block['items']:
                    self.assertTrue(item['q'] and item['a'], lesson['number'])

    def test_no_russian_letters_or_drafting_leftovers(self):
        for lesson in self.lessons:
            text = repr(lesson)
            self.assertIsNone(RUSSIAN_ONLY.search(text), lesson['number'])
            self.assertNotIn('?..', text, lesson['number'])
            self.assertNotIn('TODO', text, lesson['number'])

    def test_transcriptions_have_no_brackets(self):
        # The templates add the [ ] around the IPA.
        for lesson in self.lessons:
            for entry in lesson['sounds'] + lesson['words']:
                for key in ('ipa', 'example_ipa'):
                    self.assertNotRegex(entry.get(key) or '', r'[\[\]/]', lesson['number'])


class PhoneticsPageTests(AppTestCase):

    def test_index_lists_every_lesson(self):
        body = self.client.get('/phonetics').data.decode()
        for lesson in service.load_lessons():
            self.assertIn('/phonetics/' + lesson['slug'], body)

    def test_lesson_page(self):
        lesson = service.load_lessons()[0]
        response = self.client.get('/phonetics/' + lesson['slug'])
        self.assertEqual(200, response.status_code)
        body = response.data.decode()
        self.assertIn(lesson['title'], body)
        self.assertIn('btn-speak', body)
        self.assertIn('speak.js', body)

    def test_unknown_lesson_is_404(self):
        self.assertEqual(404, self.client.get('/phonetics/nope').status_code)

    def test_menu_links_to_phonetics(self):
        body = self.client.get('/').data.decode()
        navbar = body[body.index('<nav'):body.index('</nav>')]
        self.assertIn('Фонетика', navbar)
        self.assertLess(navbar.index('Дієвідміна'), navbar.index('Фонетика'))
