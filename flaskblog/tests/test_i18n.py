# flaskblog/tests/test_i18n.py

import glob
import json
import os
import re
import unittest

from flaskblog import db, i18n
from flaskblog.grammar import service as grammar_service
from flaskblog.models import GrammarUnit, UserWord, Word
from flaskblog.phonetics import service as phonetics_service
from flaskblog.tests.helpers import AppTestCase
from flaskblog.vocabulary import service as vocabulary_service

CYRILLIC = re.compile('[Ѐ-ӿ]')
LANGUAGE_LINK = re.compile(r'<a class="btn lang-toggle.*?</a>', re.S)
GRAMMAR_DIR = os.path.join(os.path.dirname(grammar_service.__file__), 'data')


def cyrillic_snippets(html):
    """Bits of an English page that are still in Ukrainian."""
    html = LANGUAGE_LINK.sub('', html)  # the link to the Ukrainian version
    return [html[max(m.start() - 40, 0):m.end() + 40] for m in CYRILLIC.finditer(html)][:5]


class LanguageChoiceTests(AppTestCase):

    def _nav(self, url, **kwargs):
        return self.client.get(url, **kwargs).data.decode()

    def test_ukrainian_is_the_default(self):
        self.assertIn('Граматика', self._nav('/'))
        self.assertIn('<html lang="uk">', self._nav('/'))

    def test_english_by_query_parameter_is_remembered(self):
        response = self.client.get('/?lang=en')
        body = response.data.decode()
        self.assertIn('<html lang="en">', body)
        self.assertIn('Grammar', body)
        self.assertIn('lang=en', response.headers.get('Set-Cookie', ''))
        # The cookie keeps the choice on the next page.
        self.assertIn('Grammar', self._nav('/grammar'))

    def test_switching_back_to_ukrainian(self):
        self.client.get('/?lang=en')
        self.assertIn('Граматика', self._nav('/?lang=uk'))
        self.assertIn('Граматика', self._nav('/grammar'))

    def test_browser_language(self):
        english = {'Accept-Language': 'en-GB,en;q=0.9'}
        self.assertIn('Grammar', self._nav('/', headers=english))
        russian = {'Accept-Language': 'ru-RU,ru;q=0.9'}
        self.assertIn('Граматика', self._nav('/', headers=russian))
        # Someone who reads neither gets English rather than Ukrainian.
        german = {'Accept-Language': 'de-DE,de;q=0.9'}
        self.assertIn('Grammar', self._nav('/', headers=german))

    def test_unknown_language_is_ignored(self):
        self.assertIn('Граматика', self._nav('/?lang=xx'))

    def test_switch_link_keeps_the_page_and_its_filters(self):
        body = self._nav('/dictionary?level=A1')
        self.assertIn('href="/dictionary?level=A1&amp;lang=en"', body)


class PluralTests(AppTestCase):

    def _plural(self, lang, count):
        with self.app.test_request_context('/?lang=' + lang):
            return i18n.plural(count, ('юніт', 'юніти', 'юнітів'), ('unit', 'units'))

    def test_ukrainian_forms(self):
        self.assertEqual('1 юніт', self._plural('uk', 1))
        self.assertEqual('3 юніти', self._plural('uk', 3))
        self.assertEqual('5 юнітів', self._plural('uk', 5))
        self.assertEqual('11 юнітів', self._plural('uk', 11))
        self.assertEqual('21 юніт', self._plural('uk', 21))
        self.assertEqual('22 юніти', self._plural('uk', 22))
        self.assertEqual('112 юнітів', self._plural('uk', 112))

    def test_english_forms(self):
        self.assertEqual('1 unit', self._plural('en', 1))
        self.assertEqual('70 units', self._plural('en', 70))


class EnglishPagesTests(AppTestCase):
    """Every page of the English site is entirely in English."""

    def setUp(self):
        super().setUp()
        grammar_service.seed()
        vocabulary_service.import_seed()
        db.session.commit()
        self.client.get('/?lang=en')

    def assertEnglish(self, url):
        response = self.client.get(url)
        self.assertIn(response.status_code, (200, 404), url)
        snippets = cyrillic_snippets(response.data.decode())
        self.assertEqual([], snippets, url)

    def test_public_pages(self):
        unit = GrammarUnit.query.filter_by(number=17).first()
        lesson = phonetics_service.load_lessons(phonetics_service.DATA_FILE)[0]
        word = Word.query.filter_by(term='anar').first()
        for url in (
            '/',
            '/grammar',
            '/grammar?sort=topic',
            '/grammar/' + unit.slug,
            '/grammar/unit/70',
            '/phonetics',
            '/phonetics/' + lesson['slug'],
            '/dictionary',
            '/dictionary?q=house',
            '/dictionary?topic=food&level=A1',
            '/dictionary/' + word.slug,
            '/dictionary/eixir',
            '/dictionary?variety=regional',
            '/login',
            '/register',
            '/reset_password',
            '/no-such-page',
        ):
            self.assertEnglish(url)

    def test_conjugator(self):
        self.assertEnglish('/conjugator?verb=anar')
        self.assertEnglish('/conjugator?verb=rentar-se')
        self.assertEnglish('/conjugator?verb=xyzzy')
        self.assertEnglish('/conjugator?verb=eixir')

    def test_pages_for_a_logged_in_user(self):
        user = self.create_user()
        self.login_as(user)
        word = Word.query.filter_by(term='casa').first()
        db.session.add(UserWord(user_id=user.id, word_id=word.id))
        db.session.commit()
        for url in ('/my-dictionary', '/my-dictionary?status=known', '/account'):
            self.assertEnglish(url)

    def test_form_errors_and_messages(self):
        response = self.client.post('/register', data={'username': '', 'email': 'bad'})
        self.assertEqual([], cyrillic_snippets(response.data.decode()))
        self.assertIn('This field is required.', response.data.decode())
        response = self.client.post(
            '/login', data={'email': 'nobody@example.com', 'password': 'x'}
        )
        self.assertIn('Login failed', response.data.decode())

    def test_dictionary_search_finds_english_words(self):
        body = self.client.get('/dictionary?q=house').data.decode()
        self.assertIn('/dictionary/casa', body)


class EnglishContentTests(unittest.TestCase):
    """The adapted English course data is complete and has no Ukrainian left."""

    def test_every_grammar_unit_has_an_english_version(self):
        units = grammar_service.load_units()
        english = grammar_service.load_translations('en')
        self.assertEqual({u['number'] for u in units}, set(english))
        for number, version in english.items():
            for field in ('title', 'summary', 'explanation', 'examples', 'exercises'):
                self.assertTrue(version.get(field), (number, field))
            for example in version['examples']:
                self.assertTrue(example.get('ca') and example.get('en'), number)

    def test_english_grammar_files_have_no_cyrillic(self):
        for path in glob.glob(os.path.join(GRAMMAR_DIR, 'en', '*.json')):
            with open(path, encoding='utf-8') as handle:
                text = handle.read()
            self.assertIsNone(CYRILLIC.search(text), path)
            self.assertNotIn('?..', text, path)

    def test_english_phonetics_matches_the_ukrainian_course(self):
        path = phonetics_service.LANGUAGE_FILES['en']
        if not os.path.exists(path):
            self.skipTest('no English phonetics yet')
        source = phonetics_service.load_lessons(phonetics_service.DATA_FILE)
        english = phonetics_service.load_lessons(path)
        self.assertEqual([l['slug'] for l in source], [l['slug'] for l in english])
        for lesson in english:
            for key in ('title', 'summary', 'explanation'):
                self.assertIsNone(CYRILLIC.search(lesson[key]), (lesson['number'], key))
            for entry in lesson['sounds'] + lesson['words']:
                self.assertTrue(entry.get('en'), lesson['number'])
                self.assertIsNone(CYRILLIC.search(json.dumps(entry, ensure_ascii=False)),
                                  lesson['number'])
            self.assertIsNone(CYRILLIC.search(json.dumps(lesson['exercises'], ensure_ascii=False)),
                              lesson['number'])

    def test_every_dictionary_word_has_an_english_translation(self):
        with open(vocabulary_service.SEED_FILE, encoding='utf-8') as handle:
            rows = vocabulary_service.read_rows(handle.read())
        for row in rows:
            self.assertTrue(row.get('translation_en'), row['term'])
            for key in ('translation_en', 'example_en', 'notes_en'):
                self.assertIsNone(CYRILLIC.search(row.get(key) or ''), (row['term'], key))
            if row.get('example_ca'):
                self.assertTrue(row.get('example_en'), row['term'])


if __name__ == '__main__':
    unittest.main()
