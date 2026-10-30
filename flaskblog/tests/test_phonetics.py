# flaskblog/tests/test_phonetics.py

import re
import unittest

from flaskblog.phonetics import service, trainer
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


class TrainerDataTests(unittest.TestCase):
    """Every hand-made task in phonetics/data/trainer.json agrees with the
    transcriptions the site shows."""

    NUCLEI = set('aəeɛiouɔ')

    def setUp(self):
        self.tasks = trainer.tasks_file()

    def test_units_are_lessons(self):
        slugs = [lesson['slug'] for lesson in service.load_lessons()]
        self.assertLessEqual(set(self.tasks), set(slugs))
        self.assertNotIn('trainer', slugs)   # /phonetics/trainer would hide it
        for unit in trainer.units('uk'):
            self.assertGreaterEqual(len(unit['tasks']), trainer.QUESTIONS_PER_ROUND, unit['slug'])

    def test_sound_tasks(self):
        for slug, tasks in self.tasks.items():
            for task in tasks:
                if task['type'] != 'sound':
                    continue
                self.assertIn(task['answer'], task['options'], task)
                self.assertGreaterEqual(task['word'].count(task['mark']), task.get('nth', 1), task)
                if task['answer'] != '∅':
                    self.assertIn(task['answer'], trainer.ipa_of(task['word']).replace('ˈ', ''), task)

    def test_stress_tasks(self):
        for slug, tasks in self.tasks.items():
            for task in tasks:
                if task['type'] != 'stress':
                    continue
                self.assertEqual(task['word'], ''.join(task['syllables']), task)
                ipa = trainer.ipa_of(task['word'])
                vowels, stressed = 0, None
                for char in ipa:
                    if char == 'ˈ':
                        stressed = vowels
                    vowels += char in self.NUCLEI
                self.assertEqual((len(task['syllables']), task['answer']), (vowels, stressed), (task, ipa))

    def test_spelling_tasks(self):
        for slug, tasks in self.tasks.items():
            for task in tasks:
                if task['type'] == 'spelling':
                    self.assertIn(task['answer'], task['options'], task)
                    self.assertEqual(len(task['options']), len(set(task['options'])), task)
                    self.assertEqual(task['ipa'], trainer.ipa_of(task['answer']), task)
                elif task['type'] == 'listen':
                    self.assertEqual(len(task['options']), len(set(task['options'])), task)
                else:
                    self.assertIn(task['type'], ('sound', 'stress'), task)

    def test_word_tasks_come_from_the_lesson(self):
        for lesson, unit in zip(service.load_lessons(), trainer.units('uk')):
            transcribe = [t for t in unit['tasks'] if t['type'] == 'transcribe']
            self.assertEqual(len(lesson['words']), len(transcribe), lesson['slug'])
            for task in unit['tasks']:
                if task['type'] == 'spell':   # one spelling for the transcription
                    self.assertEqual([task['answer']],
                                     [w['ca'] for w in lesson['words'] if w['ipa'] == task['ipa']])
        # Homographs: the meaning tells which word is meant.
        dona = [t for t in trainer.units('uk')[2]['tasks'] if t['type'] == 'transcribe' and t['word'] == 'dona']
        self.assertEqual({'ˈdɔnə', 'ˈdonə'}, {t['answer'] for t in dona})
        self.assertEqual(2, len({t['meaning'] for t in dona}))


class TrainerPageTests(AppTestCase):

    def test_page(self):
        response = self.client.get('/phonetics/trainer')
        self.assertEqual(200, response.status_code)
        body = response.data.decode()
        self.assertIn('id="trainer-config"', body)
        self.assertIn('phonetics-trainer.js', body)
        self.assertIn('data-unit="naholos"', body)
        self.assertIn('kəˈfɛ', body)

    def test_links_and_sitemap(self):
        self.assertIn('href="/phonetics/trainer"', self.client.get('/phonetics').data.decode())
        lesson = service.load_lessons()[0]
        body = self.client.get('/phonetics/' + lesson['slug']).data.decode()
        self.assertIn('href="/phonetics/trainer#%s"' % lesson['slug'], body)
        self.assertIn('/phonetics/trainer', self.client.get('/sitemap.xml').data.decode())

    def test_english_meanings(self):
        body = self.client.get('/phonetics/trainer?lang=en').data.decode()
        self.assertIn('Pronunciation trainer', body)
        self.assertIn('coffee', body)

    def test_switched_off(self):
        self.app.config['PHONETICS_TRAINER'] = False
        self.assertEqual(404, self.client.get('/phonetics/trainer').status_code)
        self.assertNotIn('/phonetics/trainer', self.client.get('/phonetics').data.decode())
