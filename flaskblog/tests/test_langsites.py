# flaskblog/tests/test_langsites.py

import unittest
from urllib.parse import quote

from flaskblog import sites
from flaskblog.langsites import dictionary
from flaskblog.tests.helpers import AppTestCase


class DictionaryFileTests(unittest.TestCase):
    """The Ukrainian dictionary file made by ``flask langsites build uk``."""

    def test_size(self):
        self.assertGreater(dictionary.size('uk'), 40000)

    def test_keys_are_sorted(self):
        keys = dictionary.index('uk').keys
        self.assertEqual(keys, sorted(keys))

    def test_lookup_ignores_stress_and_case(self):
        for term in ('собака', 'Соба́ка'):
            entries = dictionary.lookup('uk', term)
            self.assertTrue(entries, term)
            self.assertEqual('соба́ка', entries[0]['w'])
            self.assertIn('dog', entries[0]['senses'][0]['en'])
            self.assertIn('gos', [item['w'] for item in entries[0]['ca']])

    def test_search_by_translation(self):
        entries, how = dictionary.search('uk', 'dog', ['en'])
        self.assertEqual('translation', how)
        self.assertIn('собака', [entry['k'] for entry in entries[:5]])
        entries, how = dictionary.search('uk', 'perro', ['en', 'es'])
        self.assertIn('собака', [entry['k'] for entry in entries])
        entries, how = dictionary.search('uk', 'gos', ['ca'])
        self.assertIn('собака', [entry['k'] for entry in entries])

    def test_search_by_beginning(self):
        entries, how = dictionary.search('uk', 'собак', ['en'])
        self.assertEqual('prefix', how)
        self.assertTrue(all(entry['k'].startswith('собак') for entry in entries))

    def test_nothing(self):
        self.assertEqual(([], None), dictionary.search('uk', 'qqqzzz', ['en']))
        self.assertEqual([], dictionary.lookup('uk', 'qqqzzz'))

    def test_missing_language_file(self):
        self.assertFalse(dictionary.available('xx'))
        self.assertEqual(0, dictionary.size('xx'))


class HiddenSectionTests(AppTestCase):
    """Sections stay hidden until their site is enabled: only the editor
    sees them."""

    def test_registry(self):
        self.assertEqual(['ukrainian', 'english', 'spanish', 'french', 'german'],
                         [site.slug for site in sites.SECTIONS])
        self.assertEqual(['ukrainian'], [site.slug for site in sites.SECTIONS if site.enabled])

    def test_hidden_from_visitors(self):
        for url in ('/english/', '/english/dictionary?q=dog', '/spanish/', '/french/',
                    '/german/dictionary'):
            self.assertEqual(404, self.client.get(url).status_code, url)
        user = self.create_user()
        self.login_as(user)
        self.assertEqual(404, self.client.get('/english/').status_code)

    def test_ukrainian_is_open_to_everybody(self):
        for url in ('/ukrainian/', '/ukrainian/dictionary?q=dog', '/ukrainian/dictionary/собака'):
            response = self.client.get(url)
            self.assertEqual(200, response.status_code, url)
            self.assertNotIn('лише ви як адміністратор', response.get_data(as_text=True))
        menu = self.client.get('/grammar').get_data(as_text=True)
        self.assertIn('href="/ukrainian/"', menu)
        self.assertNotIn('href="/english/"', menu)

    def test_unknown_section(self):
        self.create_admin()
        self.login(self.create_user('someone').email)
        self.assertEqual(404, self.client.get('/klingon/').status_code)

    def test_catalan_pages_still_work(self):
        self.assertEqual(200, self.client.get('/grammar').status_code)
        self.assertEqual(200, self.client.get('/dictionary').status_code)


class AdminSectionTests(AppTestCase):

    def setUp(self):
        super().setUp()
        self.login_as(self.create_admin())

    def test_home(self):
        body = self.client.get('/ukrainian/').get_data(as_text=True)
        self.assertIn('Українська', body)
        self.assertIn('/ukrainian/dictionary', body)
        hidden = self.client.get('/english/').get_data(as_text=True)
        self.assertIn('лише ви як адміністратор', hidden)
        self.assertIn('href="/english/"', hidden)  # in the editor's menu

    def test_section_without_material(self):
        response = self.client.get('/german/')
        self.assertEqual(200, response.status_code)
        self.assertIn('ще готуються', response.get_data(as_text=True))
        self.assertIn('нічого не знайдено', self.client.get('/german/dictionary?q=Hund').get_data(as_text=True))

    def test_search_and_word_page(self):
        body = self.client.get('/ukrainian/dictionary?q=dog').get_data(as_text=True)
        self.assertIn('Слова з перекладом', body)
        self.assertIn('/ukrainian/dictionary/' + quote('собака'), body)
        word = self.client.get('/ukrainian/dictionary/собака')
        self.assertEqual(200, word.status_code)
        body = word.get_data(as_text=True)
        self.assertIn('соба́ка', body)
        self.assertIn('dog (animal)', body)
        self.assertIn('perro', body)
        self.assertIn('/dictionary?q=gos', body)
        self.assertIn('жіночий рід', self.client.get('/ukrainian/dictionary/авеню').get_data(as_text=True))

    def test_unknown_word(self):
        self.assertEqual(404, self.client.get('/ukrainian/dictionary/qqqzzz').status_code)

    def test_interface_language_orders_translations(self):
        body = self.client.get('/ukrainian/dictionary/собака?lang=es').get_data(as_text=True)
        self.assertLess(body.index('perro'), body.index('dog (animal)'))
        self.assertIn('Diccionario', body)

    def test_aspect_partner(self):
        body = self.client.get('/ukrainian/dictionary/написати').get_data(as_text=True)
        self.assertIn('доконаний вид', body)
        self.assertIn('/ukrainian/dictionary/' + quote('писати'), body)


if __name__ == '__main__':
    unittest.main()
