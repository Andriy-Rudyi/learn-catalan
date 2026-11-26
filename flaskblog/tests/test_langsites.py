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
        parts = ('grammar', 'conjugator', 'phonetics', 'course', 'text', 'reading', 'translator')
        for site in sites.SECTIONS:
            home = self.client.get('/{}/'.format(site.slug)).get_data(as_text=True)
            for part in parts + ('dictionary',):
                self.assertIn('href="/{}/{}"'.format(site.slug, part), home, (site.slug, part))
            for part in parts:
                response = self.client.get('/{}/{}'.format(site.slug, part))
                self.assertEqual(200, response.status_code, (site.slug, part))
            # Some real starter material in every section, the translator still to come.
            for part in ('grammar', 'phonetics', 'course'):
                body = self.client.get('/{}/{}'.format(site.slug, part)).get_data(as_text=True)
                self.assertNotIn('ще готуються', body, (site.slug, part))
                self.assertIn('unit-number-big', body, (site.slug, part))
            self.assertIn('ще готуються', self.client.get('/{}/translator'.format(site.slug)).get_data(as_text=True))
        self.assertEqual(404, self.client.get('/ukrainian/nothing').status_code)
        self.assertEqual(404, self.client.get('/ukrainian/lessons').status_code)

    def test_starter_material(self):
        self.assertIn('bin', self.client.get('/german/conjugator').get_data(as_text=True))
        self.assertIn('DELE', self.client.get('/spanish/course').get_data(as_text=True))
        self.assertIn('ne … pas', self.client.get('/french/grammar').get_data(as_text=True))
        self.assertIn('The seven cases', self.client.get('/ukrainian/grammar').get_data(as_text=True))
        self.assertIn('data-lang="de"', self.client.get('/german/phonetics').get_data(as_text=True))

    def test_text_page(self):
        body = self.client.get('/spanish/text').get_data(as_text=True)
        self.assertIn('id="reader-source"', body)
        self.assertIn('"wordUrl": "/spanish/word"', body)
        self.assertIn('"synonyms": false', body)
        self.assertIn('Los sábados', body)  # the example text

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

    def test_learning_and_known_language_pickers(self):
        body = self.client.get('/grammar').get_data(as_text=True)
        self.assertIn('Вивчаю', body)
        self.assertIn('Знаю', body)
        for url in ('/home', '/ukrainian/', '/english/', '/spanish/', '/french/', '/german/'):
            self.assertIn('href="{}"'.format(url), body)
        # Sorted by the language's own name: Catalan is not put first.
        self.assertLess(body.index('>Català<'), body.index('>Deutsch<'))
        self.assertLess(body.index('>Deutsch<'), body.index('>English<'))
        self.assertLess(body.index('>Français<'), body.index('>Українська<'))
        french = self.client.get('/french/grammar').get_data(as_text=True)
        self.assertIn('<li class="lc-menu-heading"><span lang="fr">Français</span>', french)
        self.assertRegex(french, r'class="dropdown-item active" href="/french/"')

    def test_bootstrap_is_served_by_the_site(self):
        body = self.client.get('/').get_data(as_text=True)
        self.assertNotIn('cdn.jsdelivr.net', body)
        self.assertIn('/static/vendor/bootstrap-5.3.3/bootstrap.min.css', body)
        self.assertIn('/static/flex-gap.css', body)
        self.assertEqual(200, self.client.get('/static/vendor/bootstrap-5.3.3/bootstrap.bundle.min.js').status_code)

    def test_part_without_material(self):
        self.assertIn('Готується', self.client.get('/german/').get_data(as_text=True))  # translator
        self.assertIn('нічого не знайдено',
                      self.client.get('/german/dictionary?q=qqqzzz').get_data(as_text=True))

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
        self.assertGreater(dictionary.size('fr'), 80000)
        self.assertGreater(dictionary.size('de'), 80000)

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
        maison = next(e for e in dictionary.lookup('fr', 'maison') if e['pos'] == 'noun')
        self.assertEqual(['casa'], maison['ca'])
        self.assertIn({'en': 'house'}, maison['senses'])  # Wiktionary
        self.assertEqual('f', maison['g'])
        hund = dictionary.lookup('de', 'Hund')[0]
        self.assertEqual('m', hund['g'])
        self.assertIn('dog', hund['senses'][0]['en'])
        self.assertTrue(dictionary.meta('fr')['sources'])

    def test_ukrainian_derived_through_english(self):
        hund = dictionary.lookup('de', 'Hund')[0]
        words = [item['w'].replace('\u0301', '') for item in hund['uk']]
        self.assertIn('собака', words)
        self.assertTrue(all(item['unsure'] for item in hund['uk']))
        # Not for descriptions of names and places.
        for entry in dictionary.lookup('de', 'Behne'):
            self.assertNotIn('uk', entry)
        # A Ukrainian equivalent that came from elsewhere is kept as it is.
        maison = next(e for e in dictionary.lookup('fr', 'maison') if e['pos'] == 'noun')
        self.assertEqual(['дім, будинок'], maison['uk'])
        for code in ('de', 'es', 'fr'):
            self.assertTrue(any('derived through English' in source
                                for source in dictionary.meta(code)['sources']), code)

    def test_inflected_forms(self):
        from flaskblog.langsites import kaikki
        for code, form, lemma in (('uk', 'собаки', 'собака'), ('es', 'abrió', 'abrir'),
                                  ('fr', 'ouvrit', 'ouvrir'), ('de', 'ging', 'gehen'),
                                  ('fr', "C'était", 'être'), ('fr', 'acheva-t-elle', 'achever')):
            entries, found = dictionary.find(code, form)
            self.assertTrue(entries, (code, form))
            self.assertEqual(lemma, dictionary.key(found), (code, form))
        entries, found = dictionary.find('fr', 'suis')
        self.assertEqual({'suivre', 'être'}, {entry['k'] for entry in entries})
        self.assertEqual([], kaikki.lemmas('es', 'qqqzzz'))
        self.assertEqual([], kaikki.lemmas('en', 'walked'))  # English has rules, no table

    def test_most_words_of_the_translated_chapter_are_found(self):
        from flaskblog.langsites import reading
        for code in ('uk', 'es', 'fr', 'de', 'en'):
            chapter = reading.part(reading.work(code, 'martin-eden'), 1)
            words = [m.group() for p in chapter['paragraphs'] for m in reading.WORD.finditer(p)]
            found = sum(1 for word in words if dictionary.find(code, word)[0])
            self.assertGreater(found / len(words), 0.9, code)

    def test_words_as_they_stand_in_a_text(self):
        for word, form in (('walked', 'walk'), ('Houses', 'house'), ('ran', 'run'),
                           ('went', 'go'), ('stopped', 'stop'), ('cities', 'city'), ('Hath', 'have')):
            entries, found = dictionary.find('en', word)
            self.assertEqual(form, found, word)
        self.assertEqual(([], None), dictionary.find('en', 'qqqzzz'))


class ConjugatorTests(AppTestCase):

    def test_tables_from_wiktionary(self):
        from flaskblog.langsites import conjugator
        gehen = conjugator.conjugate('de', 'ging')
        self.assertEqual('gehen', gehen['w'])
        self.assertEqual('ging', gehen['asked'])
        titles = [table['title'] for table in gehen['tables']]
        for title in ('Präsens', 'Präteritum', 'Perfekt', 'Konjunktiv II', 'Imperativ', 'Grundformen'):
            self.assertIn(title, titles)
        presens = gehen['tables'][0]['rows']
        self.assertEqual(['ich', 'gehe'], presens[0])
        self.assertEqual(['du', 'gehst'], presens[1])
        chytaty = conjugator.conjugate('uk', 'читати')
        tables = {table['title']: dict(table['rows']) for table in chytaty['tables']}
        self.assertEqual('чита́ю', tables['Present']['я'])
        self.assertEqual('чита́ла', tables['Past']['вона'])
        self.assertEqual('прочита́ти', tables['Forms']['Perfective'])
        self.assertEqual('написати', dictionary.key(conjugator.conjugate('uk', 'написав')['w']))

    def test_verbecc_for_spanish_and_french(self):
        from flaskblog.langsites import conjugator
        hablar = conjugator.conjugate('es', 'hablo')
        self.assertEqual('hablar', hablar['w'])
        self.assertEqual(['yo hablo'], hablar['tables'][0]['rows'][0])
        suis = conjugator.conjugate('fr', 'suis')
        self.assertEqual({'suivre', 'être'}, {suis['w']} | set(suis['others']))
        self.assertIsNone(conjugator.conjugate('es', 'qqqzzz'))
        self.assertIsNone(conjugator.conjugate('en', 'go'))  # English has no tables yet

    def test_pages(self):
        body = self.client.get('/german/conjugator?verb=ging').get_data(as_text=True)
        self.assertIn('tense-card', body)
        self.assertIn('gingst', body)
        body = self.client.get('/french/conjugator?verb=suis').get_data(as_text=True)
        self.assertIn('Також може бути формою', body)
        self.assertIn('nous sommes', body)
        self.assertIn('не знайдено', self.client.get('/spanish/conjugator?verb=qqqzzz').get_data(as_text=True))
        empty = self.client.get('/spanish/conjugator').get_data(as_text=True)
        self.assertIn('Основні дієслова', empty)
        self.assertIn('/spanish/conjugator?verb=hablar', empty)
        english = self.client.get('/english/conjugator').get_data(as_text=True)
        self.assertIn('ще готується', english)
        self.assertIn('Основні дієслова', english)
        self.assertIn('form of', self.client.get('/german/conjugator?verb=ging&lang=en').get_data(as_text=True))


class ReadingTests(AppTestCase):

    def test_works_of_every_language(self):
        from flaskblog.langsites import reading
        works = {work['slug']: work for work in reading.works('en')}
        self.assertEqual(46, len(works['martin-eden']['files']))
        self.assertEqual('novel', works['martin-eden']['kind'])
        self.assertEqual(15, len(works['othello']['files']))
        self.assertEqual('play', works['othello']['kind'])
        for code, first_words in (('uk', 'Перший відімкнув'), ('es', 'El uno abrió'),
                                  ('fr', 'Le premier ouvrit'), ('de', 'Der eine schloss')):
            work = reading.work(code, 'martin-eden')
            self.assertEqual(1, len(work['files']), code)
            chapter = reading.part(work, 1)
            self.assertEqual(54, len(chapter['paragraphs']), code)  # paragraph for paragraph
            self.assertTrue(chapter['paragraphs'][0].startswith(first_words), code)
            self.assertNotIn('—', ''.join(chapter['paragraphs']), code)
            self.assertNotIn('–', ''.join(chapter['paragraphs']), code)

    def test_pages_look_like_the_catalan_reading(self):
        library = self.client.get('/english/reading').get_data(as_text=True)
        self.assertIn('reading-shelf', library)
        self.assertIn('Martin Eden', library)
        self.assertIn('Othello', library)
        contents = self.client.get('/english/reading/othello').get_data(as_text=True)
        self.assertIn('reading-toc', contents)
        chapter = self.client.get('/english/reading/martin-eden/1').get_data(as_text=True)
        self.assertIn('reader-panel', chapter)
        self.assertIn('data-words>The one opened the door', chapter)
        self.assertIn('static/reader.js', chapter)
        self.assertIn('/english/reading/martin-eden/2', chapter)
        scene = self.client.get('/english/reading/othello/1').get_data(as_text=True)
        self.assertIn('play-speaker', scene)
        self.assertIn('RODERIGO', scene)
        self.assertEqual(404, self.client.get('/english/reading/othello/16').status_code)
        self.assertEqual(404, self.client.get('/english/reading/nothing').status_code)
        for slug in ('ukrainian', 'spanish', 'french', 'german'):
            body = self.client.get('/{}/reading/martin-eden/1'.format(slug)).get_data(as_text=True)
            self.assertIn('reader-text prose', body, slug)

    def test_word_panel(self):
        data = self.client.get('/english/word?w=walked,').get_json()
        self.assertEqual('walked', data['word'])
        self.assertEqual([], data['groups'])
        reading = data['readings'][0]
        self.assertEqual('walk', reading['lemma'])
        self.assertEqual('/english/dictionary/walk', reading['url'])
        self.assertIn('Українська', reading['translation'])
        self.assertEqual([], self.client.get('/english/word?w=qqqzzz').get_json()['readings'])

    def test_translations_lead_to_other_sections(self):
        body = self.client.get('/english/dictionary/house').get_data(as_text=True)
        self.assertIn('/ukrainian/dictionary?q=', body)
        self.assertIn('/spanish/dictionary?q=casa', body)
        self.assertIn('/dictionary?q=casa', body)


if __name__ == '__main__':
    unittest.main()
