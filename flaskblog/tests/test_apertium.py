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


if __name__ == '__main__':
    unittest.main()
