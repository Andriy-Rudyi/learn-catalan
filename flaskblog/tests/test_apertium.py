# flaskblog/tests/test_apertium.py

import os
import tempfile
import textwrap
import unittest

from flaskblog import db
from flaskblog.models import Word
from flaskblog.tests.helpers import AppTestCase
from flaskblog.vocabulary import apertium
from flaskblog.vocabulary import service as vocabulary_service

METADIX = textwrap.dedent('''\
    <?xml version="1.0" encoding="UTF-8"?>
    <dictionary>
      <section id="main" type="standard">
        <e><p><l>hacer<g><b/>daño</g><s n="vblex"/></l><r>fer<g><b/>mal</g><s n="vblex"/></r></p></e>
        <e r="RL"><p><l>blando<s n="adj"/></l><r>moll<s n="adj"/></r></p></e>
        <e r="LR"><p><l>atestado<s n="adj"/></l><r>atapeït<s n="adj"/></r></p></e>
        <e><p><l>casa<s n="n"/><s n="f"/></l><r>casa<s n="n"/><s n="f"/></r></p></e>
        <e><p><l>Madrid<s n="np"/><s n="loc"/></l><r>Madrid<s n="np"/><s n="loc"/></r></p></e>
        <e><p><l>_prefix_auto_</l><r>_prefix_auto_</r></p></e>
        <e r="RL"><p><l></l><r></r></p></e>
      </section>
    </dictionary>''')


class ConvertTests(unittest.TestCase):

    def test_convert(self):
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, 'x.metadix')
            with open(path, 'w', encoding='utf-8') as handle:
                handle.write(METADIX)
            pairs = apertium.convert_file(path)
        self.assertEqual([
            {'ca': 'fer mal', 'es': 'hacer daño', 'pos': 'vblex', 'dir': 'both'},
            {'ca': 'moll', 'es': 'blando', 'pos': 'adj', 'dir': 'ca-es'},
            {'ca': 'atapeït', 'es': 'atestado', 'pos': 'adj', 'dir': 'es-ca'},
            {'ca': 'casa', 'es': 'casa', 'pos': 'n', 'dir': 'both', 'gender_ca': 'f', 'gender_es': 'f'},
        ], pairs)


class DataTests(unittest.TestCase):

    def test_bundled_pairs(self):
        self.assertGreater(apertium.stats()['pairs'], 50000)
        self.assertEqual(['sandía'], apertium.spanish('síndria', 'noun'))
        self.assertIn('blando', apertium.spanish('moll', 'adjective'))
        # Pronominal verbs are found by their base.
        self.assertTrue(apertium.spanish('abalançar-se', 'verb'))
        self.assertEqual([], apertium.spanish('xyzzyq'))


class ImportTests(AppTestCase):

    def setUp(self):
        super().setUp()
        vocabulary_service.import_rows([
            {'term': 'síndria', 'part_of_speech': 'noun', 'translation_en': 'watermelon'},
            {'term': 'tocar', 'part_of_speech': 'verb', 'translation_en': 'touch; play (an instrument)'},
            {'term': 'xyzzyq', 'translation_en': 'nothing'},
        ], seed=True)
        db.session.commit()

    def test_import_and_remove(self):
        self.assertEqual(2, apertium.import_translations())
        db.session.commit()
        self.assertEqual(0, apertium.import_translations())
        tocar = Word.query.filter_by(term='tocar').one()
        self.assertEqual('tocar', tocar.translations['es'].translation)
        self.assertEqual(['tocar', 'tocar'], [s.translations['es'].text for s in tocar.senses])
        response = self.client.get('/api/v1/words/sindria?lang=es')
        self.assertEqual('sandía', response.get_json()['data']['translations']['es']['translation'])

        # An edited translation stays when the import is taken away.
        tocar.translations['es'].edited = True
        db.session.commit()
        self.assertEqual(1, apertium.remove_translations())
        db.session.commit()
        self.assertNotIn('es', Word.query.filter_by(term='síndria').one().translations)
        self.assertIn('es', Word.query.filter_by(term='tocar').one().translations)


class ImportWordsTests(AppTestCase):

    PAIRS = [
        {'ca': 'deflactar', 'es': 'deflactar', 'pos': 'vblex', 'dir': 'both'},
        {'ca': 'desviació', 'es': 'desviación', 'pos': 'n', 'dir': 'both', 'gender_ca': 'f'},
        {'ca': 'fer mal', 'es': 'hacer daño', 'pos': 'vblex', 'dir': 'both'},
        {'ca': 'tocar', 'es': 'tocar', 'pos': 'vblex', 'dir': 'both'},      # already there
        {'ca': 'atapeït', 'es': 'atestado', 'pos': 'adj', 'dir': 'es-ca'},  # Spanish to Catalan only
        {'ca': 'RD', 'es': 'RD', 'pos': 'n', 'dir': 'both'},                # an abbreviation
    ]

    def setUp(self):
        super().setUp()
        vocabulary_service.import_rows([
            {'term': 'tocar', 'part_of_speech': 'verb', 'translation_en': 'touch', 'translation_uk': 'торкатися'},
        ], seed=True)
        db.session.commit()
        self.assertEqual(3, apertium.import_words(self.PAIRS))
        db.session.commit()

    def test_words_are_added_once_with_what_is_known(self):
        self.assertEqual(0, apertium.import_words(self.PAIRS))
        word = Word.query.filter_by(term='deflactar').one()
        self.assertEqual(('apertium', 'verb'), (word.source, word.part_of_speech))
        self.assertEqual('deflactar', word.translations['es'].translation)
        self.assertNotIn('en', word.translations)
        noun = Word.query.filter_by(term='desviació').one()
        self.assertEqual('f', noun.gender)
        # English from the Wiktionary table that lists the Spanish word too, as a draft.
        self.assertIn('deviation', noun.translation_en)
        self.assertFalse(noun.translations['en'].reviewed)
        self.assertEqual('phrase', Word.query.filter_by(term='fer mal').one().part_of_speech)
        self.assertIsNone(Word.query.filter_by(term='tocar').one().source)

    def test_page_falls_back_to_spanish(self):
        body = self.client.get('/dictionary/deflactar').get_data(as_text=True)
        self.assertIn('Переклад іспанською з відкритого словника Apertium', body)
        self.assertIn('<p class="h5 text-secondary">deflactar</p>', body)
        self.assertEqual(1, vocabulary_service.search('deflactar').count())
        self.assertNotIn('/dictionary/deflactar', self.client.get('/sitemap.xml').get_data(as_text=True))

    def test_hidden_and_removed(self):
        self.app.config['APERTIUM_WORDS'] = False
        self.assertEqual(404, self.client.get('/dictionary/deflactar').status_code)
        self.assertEqual(0, vocabulary_service.search('deflactar').count())
        self.app.config['APERTIUM_WORDS'] = True
        # Taking the Spanish translations back leaves these words alone.
        apertium.import_translations()
        db.session.commit()
        self.assertEqual(1, apertium.remove_translations())   # tocar
        self.assertIn('es', Word.query.filter_by(term='deflactar').one().translations)
        self.assertEqual(3, apertium.remove_words())
        db.session.commit()
        self.assertEqual(1, Word.query.count())


if __name__ == '__main__':
    unittest.main()
