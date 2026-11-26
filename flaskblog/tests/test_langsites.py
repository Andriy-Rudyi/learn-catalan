# flaskblog/tests/test_langsites.py

import unittest
from unittest import mock
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


def _hidden(slug):
    """Switch a section off for the length of a test."""
    site = sites.BY_SLUG[slug]._replace(enabled=False)
    return mock.patch.multiple(
        sites, BY_SLUG=dict(sites.BY_SLUG, **{slug: site}),
        SECTIONS=tuple(site if s.slug == slug else s for s in sites.SECTIONS))


class SectionTests(AppTestCase):

    def test_registry(self):
        self.assertEqual(['ukrainian', 'english', 'spanish', 'french', 'german'],
                         [site.slug for site in sites.SECTIONS])
        self.assertTrue(all(site.enabled for site in sites.SECTIONS))

    def test_open_to_everybody(self):
        for url in ('/ukrainian/', '/ukrainian/dictionary?q=dog', '/ukrainian/dictionary/собака',
                    '/english/', '/spanish/', '/french/', '/german/dictionary?q=Hund'):
            response = self.client.get(url)
            self.assertEqual(200, response.status_code, url)
            self.assertNotIn('лише ви як адміністратор', response.get_data(as_text=True))
        menu = self.client.get('/grammar').get_data(as_text=True)
        for slug in ('ukrainian', 'english', 'spanish', 'french', 'german'):
            self.assertIn('href="/{}/"'.format(slug), menu)

    def test_every_section_has_the_parts_of_the_catalan_site(self):
        parts = ('grammar', 'lessons', 'conjugator', 'phonetics', 'course', 'text', 'reading',
                 'translator')
        for site in sites.SECTIONS:
            home = self.client.get('/{}/'.format(site.slug)).get_data(as_text=True)
            for part in parts + ('dictionary',):
                self.assertIn('href="/{}/{}"'.format(site.slug, part), home, (site.slug, part))
            for part in parts:
                response = self.client.get('/{}/{}'.format(site.slug, part))
                self.assertEqual(200, response.status_code, (site.slug, part))
                if not (part == 'reading' and site.slug == 'english'):
                    self.assertIn('ще готуються', response.get_data(as_text=True), (site.slug, part))
        self.assertEqual(404, self.client.get('/ukrainian/nothing').status_code)

    def test_section_menu_logo_and_search(self):
        body = self.client.get('/french/grammar').get_data(as_text=True)
        self.assertIn('LangWave', body)
        self.assertIn('action="/french/dictionary"', body)
        self.assertIn('href="/french/phonetics"', body)
        self.assertNotIn('href="/grammar"', body)  # the Catalan menu is not shown
        self.assertIn('href="/home"', body)  # back to the Catalan site
        self.assertNotIn('/api/words', body)  # no Catalan suggestions in the search box
        catalan = self.client.get('/grammar').get_data(as_text=True)
        self.assertIn('Learn Catalan', catalan)
        self.assertNotIn('href="/french/phonetics"', catalan)

    def test_section_without_material(self):
        self.assertIn('Готується', self.client.get('/german/').get_data(as_text=True))
        self.assertIn('нічого не знайдено',
                      self.client.get('/german/dictionary?q=Hund').get_data(as_text=True))

    def test_unknown_section(self):
        self.assertEqual(404, self.client.get('/klingon/').status_code)

    def test_catalan_pages_still_work(self):
        self.assertEqual(200, self.client.get('/grammar').status_code)
        self.assertEqual(200, self.client.get('/dictionary').status_code)


class HiddenSectionTests(AppTestCase):
    """A switched-off section: only the editor sees it."""

    def test_hidden_from_visitors(self):
        with _hidden('english'):
            for url in ('/english/', '/english/dictionary?q=dog'):
                self.assertEqual(404, self.client.get(url).status_code, url)
            self.login_as(self.create_user())
            self.assertEqual(404, self.client.get('/english/').status_code)
            self.assertNotIn('href="/english/"', self.client.get('/grammar').get_data(as_text=True))

    def test_editor_sees_it(self):
        with _hidden('english'):
            self.login_as(self.create_admin())
            body = self.client.get('/english/').get_data(as_text=True)
            self.assertIn('лише ви як адміністратор', body)
            self.assertIn('href="/english/"', body)


class AdminSectionTests(AppTestCase):

    def setUp(self):
        super().setUp()
        self.login_as(self.create_admin())

    def test_home(self):
        body = self.client.get('/ukrainian/').get_data(as_text=True)
        self.assertIn('Українська', body)
        self.assertIn('/ukrainian/dictionary', body)

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


class OtherDictionariesTests(unittest.TestCase):
    """The English, Spanish and French dictionaries (flask langsites build)."""

    def test_sizes(self):
        self.assertGreater(dictionary.size('en'), 35000)
        self.assertGreater(dictionary.size('es'), 60000)
        self.assertGreater(dictionary.size('fr'), 4000)
        self.assertFalse(dictionary.available('de'))

    def test_english(self):
        house = dictionary.lookup('en', 'house')
        noun = next(entry for entry in house if entry['pos'] == 'noun')
        self.assertIn('дім', noun['uk'])
        self.assertIn('casa', noun['ca'])
        self.assertIn('human abode', [sense['en'] for sense in noun['senses']])
        self.assertIn('albergar', next(e for e in house if e['pos'] == 'verb')['ca'])  # DACCO
        entries, how = dictionary.search('en', 'хата', ['uk'])
        self.assertIn('house', [entry['k'] for entry in entries])

    def test_spanish_and_french(self):
        casa = dictionary.lookup('es', 'casa')[0]
        self.assertIn('casa', casa['ca'])
        self.assertIn('дім', [w.replace('\u0301', '') for w in casa['uk']])
        self.assertIn('house', casa['en'])
        maison = dictionary.lookup('fr', 'maison')[0]
        self.assertEqual(['casa'], maison['ca'])
        self.assertTrue(dictionary.meta('fr')['sources'])

    def test_words_as_they_stand_in_a_text(self):
        for word, form in (('walked', 'walk'), ('Houses', 'house'), ('ran', 'run'),
                           ('went', 'go'), ('stopped', 'stop'), ('cities', 'city'), ('Hath', 'have')):
            entries, found = dictionary.find('en', word)
            self.assertEqual(form, found, word)
        self.assertEqual(([], None), dictionary.find('en', 'qqqzzz'))


class ReadingTests(AppTestCase):

    def test_english_works(self):
        from flaskblog.langsites import reading
        works = {work['slug']: work for work in reading.works('en')}
        self.assertEqual(46, len(works['martin-eden']['files']))
        self.assertEqual('novel', works['martin-eden']['kind'])
        self.assertEqual(15, len(works['othello']['files']))
        self.assertEqual('play', works['othello']['kind'])
        self.assertEqual([], reading.works('de'))

    def test_pages(self):
        library = self.client.get('/english/reading').get_data(as_text=True)
        self.assertIn('Martin Eden', library)
        self.assertIn('Othello', library)
        chapter = self.client.get('/english/reading/martin-eden/1').get_data(as_text=True)
        self.assertIn('<span class="lw">latch-key</span>', chapter)
        self.assertIn('/english/reading/martin-eden/2', chapter)
        scene = self.client.get('/english/reading/othello/1').get_data(as_text=True)
        self.assertIn('RODERIGO', scene)
        self.assertIn('<span class="lw">Tush</span>', scene)
        self.assertEqual(404, self.client.get('/english/reading/othello/16').status_code)
        self.assertEqual(404, self.client.get('/english/reading/nothing/1').status_code)
        self.assertIn('ще готуються', self.client.get('/german/reading').get_data(as_text=True))

    def test_lookup(self):
        data = self.client.get('/english/lookup?q=walked').get_json()
        self.assertEqual('walk', data['form'])
        self.assertEqual('/english/dictionary/walk', data['url'])
        self.assertTrue(any(row['text'] for entry in data['entries'] for row in entry['translations']))
        self.assertEqual([], self.client.get('/english/lookup?q=qqqzzz').get_json()['entries'])

    def test_translations_lead_to_other_sections(self):
        body = self.client.get('/english/dictionary/house').get_data(as_text=True)
        self.assertIn('/ukrainian/dictionary?q=', body)
        self.assertIn('/spanish/dictionary?q=casa', body)
        self.assertIn('/dictionary?q=casa', body)


if __name__ == '__main__':
    unittest.main()
