# flaskblog/tests/test_dacco.py

import os
import tempfile
import textwrap
import unittest

from flaskblog.vocabulary import dacco


class DaccoDataTests(unittest.TestCase):

    def test_both_directions_are_there(self):
        self.assertEqual(18161, dacco.stats(direction='ca-en')['entries'])
        self.assertEqual(21443, dacco.stats(direction='en-ca')['entries'])

    def test_entry_with_two_parts_of_speech(self):
        entry = dacco.lookup('català')[0]
        self.assertEqual(['noun', 'adjective'], [part['pos'] for part in entry['parts']])
        noun, person, adjective = dacco.senses(entry)
        self.assertEqual(('m', 'language'), (noun['gender'], noun['category']))
        self.assertEqual('m/f', person['gender'])
        self.assertEqual(('catalana', 'catalans'), (adjective['fem'], adjective['plural']))
        self.assertGreater(entry['frequency'], 0)

    def test_senses_examples_and_gloss(self):
        first = next(dacco.senses(dacco.lookup('a')[0]))
        self.assertEqual(['to', 'into'], dacco.translations(first))
        self.assertIn({'ca': 'Anem a la platja?', 'en': 'Shall we go to the beach?'}, first['examples'])

    def test_pronominal_verbs_are_found_without_se(self):
        self.assertEqual('abalançar-se', dacco.lookup('abalançar')[0]['head'])

    def test_expressions(self):
        expressions = {x['text']: x for x in dacco.lookup('casa')[0]['expressions']}
        self.assertEqual('summer camp', expressions['casa de colònies']['senses'][0]['text'])

    def test_english_to_catalan(self):
        entry = dacco.lookup('watermelon', 'en-ca')[0]
        texts = [sense['text'] for sense in dacco.senses(entry)]
        self.assertIn('síndria', texts)


class ConvertTests(unittest.TestCase):

    def test_convert_a_small_file(self):
        xml = textwrap.dedent('''\
            <?xml version="1.0" encoding="UTF-8"?>
            <dictionary>
              <Entry frequency="10">gat<nouns><translations><date>0101</date>
                <translation catagory="animal" gender="m">cat<fems>gata</fems>
                  <catexamp>El gat dorm.</catexamp><engexamp>The cat is sleeping.</engexamp>
                  <example>Tinc un &lt;b&gt;gat&lt;/b&gt;.</example></translation>
                <grouptranslation catagory="slang"><translation gender="m">tomcat</translation></grouptranslation>
              </translations></nouns>
              <expressions>de nit tots els gats són negres
                <translations><translation>all cats are grey in the dark</translation></translations>
              </expressions></Entry>
            </dictionary>''')
        with tempfile.TemporaryDirectory() as folder:
            with open(os.path.join(folder, 'g.dic'), 'w', encoding='utf-8') as handle:
                handle.write(xml)
            entry, = dacco.convert_folder(folder)
        self.assertEqual('gat', entry['head'])
        self.assertEqual(10, entry['frequency'])
        cat, tomcat = entry['parts'][0]['senses']
        self.assertEqual({'text': 'cat', 'gender': 'm', 'category': 'animal', 'fem': 'gata',
                          'examples': [{'ca': 'El gat dorm.', 'en': 'The cat is sleeping.'}],
                          'sentences': ['Tinc un gat.']}, cat)
        self.assertEqual(('tomcat', 'slang', 1), (tomcat['text'], tomcat['category'], tomcat['group']))
        self.assertEqual('de nit tots els gats són negres', entry['expressions'][0]['text'])


if __name__ == '__main__':
    unittest.main()


from flaskblog import db  # noqa: E402
from flaskblog.models import Word  # noqa: E402
from flaskblog.tests.helpers import AppTestCase  # noqa: E402
from flaskblog.vocabulary import service as vocabulary_service  # noqa: E402


class SiteMeaningTests(unittest.TestCase):

    def test_verbs_lose_to_and_keep_the_gloss(self):
        sense = {'text': '[instrument] to play / to strum'}
        self.assertEqual('play, strum (instrument)', dacco.site_meaning(sense, 'verb'))
        self.assertEqual('to go; out', dacco.site_meaning({'text': 'to go; out'}, 'noun').replace(',', ';'))

    def test_site_word(self):
        fields = dacco.site_word(dacco.lookup('abacà')[0])
        self.assertEqual(('noun', 'm'), (fields['part_of_speech'], fields['gender']))
        self.assertEqual('Manila hemp', fields['translation_en'])
        long_entry = max(dacco.load(), key=lambda e: len(list(dacco.senses(e))))
        self.assertLessEqual(len(dacco.site_word(long_entry)['translation_en']), 255)


class ImportTests(AppTestCase):

    def setUp(self):
        super().setUp()
        vocabulary_service.import_rows([
            {'term': 'tocar', 'part_of_speech': 'verb', 'translation_en': 'touch; play (an instrument)',
             'translation_uk': 'торкатися; грати'},
            {'term': 'abalançar', 'part_of_speech': 'verb', 'translation_en': 'rush at'},
        ], seed=True)
        db.session.commit()
        self.entries = [entry for term in self.SAMPLE for entry in dacco.lookup(term)]
        self.added = dacco.import_words(self.entries)
        db.session.commit()

    SAMPLE = ('abacà', 'tocar', 'abalançar', 'casa', 'síndria', 'a', 'Hawaii')

    def test_new_words_are_added_once(self):
        self.assertEqual(5, self.added)  # tocar and abalançar(-se) are there
        self.assertEqual(0, dacco.import_words(self.entries))
        word = Word.query.filter_by(term='abacà').one()
        self.assertEqual('dacco', word.source)
        self.assertEqual('Manila hemp', word.translation_en)
        self.assertEqual(1, len(word.senses))

    def test_words_already_there_are_left_alone(self):
        tocar = Word.query.filter_by(term='tocar').one()
        self.assertIsNone(tocar.source)
        self.assertEqual('touch; play (an instrument)', tocar.translation_en)
        # Our "abalançar" is DACCO's "abalançar-se".
        self.assertEqual(0, Word.query.filter_by(term='abalançar-se').count())

    def test_word_page_shows_the_dacco_entry(self):
        body = self.client.get('/dictionary/tocar').get_data(as_text=True)
        self.assertIn('Словник DACCO', body)
        self.assertIn('tocar ferro', body)
        self.assertIn('cpina/dacco', body)
        slug = Word.query.filter_by(term='abacà').one().slug
        body = self.client.get('/dictionary/' + slug).get_data(as_text=True)
        self.assertIn('Manila hemp', body)
        self.assertIn('перекладу вашою мовою ще немає', body)

    def test_switched_off(self):
        self.app.config['DACCO'] = False
        slug = Word.query.filter_by(term='abacà').one().slug
        self.assertEqual(404, self.client.get('/dictionary/' + slug).status_code)
        self.assertNotIn('Словник DACCO', self.client.get('/dictionary/tocar').get_data(as_text=True))
        self.assertEqual(0, vocabulary_service.search('abacà').count())

    def test_remove_and_sitemap(self):
        sitemap = self.client.get('/sitemap.xml').get_data(as_text=True)
        self.assertNotIn('/dictionary/abaca', sitemap)
        self.assertIn('/dictionary/tocar', sitemap)
        self.assertEqual(self.added, dacco.remove_words())
        db.session.commit()
        self.assertEqual(2, Word.query.count())

    def test_a_seeded_word_stops_being_imported(self):
        vocabulary_service.import_rows([{'term': 'abacà', 'translation_uk': 'манільська конопля',
                                         'translation_en': 'Manila hemp'}], update_existing=True, seed=True)
        self.assertIsNone(Word.query.filter_by(term='abacà').one().source)
