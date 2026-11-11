# flaskblog/tests/test_pivot.py

import gzip
import json
import os
import tempfile
import unittest

from flaskblog import db
from flaskblog.models import Word
from flaskblog.tests.helpers import AppTestCase
from flaskblog.vocabulary import pivot, wiktionary
from flaskblog.vocabulary import service as vocabulary_service


def _gz(folder, name, rows):
    with gzip.open(os.path.join(folder, name), 'wt', encoding='utf-8') as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + '\n')


class WiktionaryConvertTests(unittest.TestCase):

    def test_keys(self):
        self.assertEqual('кавун', wiktionary.uk_key('Каву́н'))
        self.assertEqual("м'який", wiktionary.uk_key('м’яки́й'))
        self.assertEqual('rush towards', wiktionary.en_key('to rush towards (someone)'))
        self.assertEqual(['house', 'home'], wiktionary.gloss_parts('house, home'))
        self.assertTrue(wiktionary.is_ukrainian('каву́н'))
        self.assertFalse(wiktionary.is_ukrainian('etc.'))

    def test_convert(self):
        with tempfile.TemporaryDirectory() as folder, tempfile.TemporaryDirectory() as out:
            _gz(folder, wiktionary.DOWNLOADS['ukrainian'], [
                {'word': 'написати', 'pos': 'verb',
                 'forms': [{'form': 'написа́ти', 'tags': ['canonical', 'perfective']},
                           {'form': 'писа́ти', 'tags': ['imperfective']}],
                 'senses': [{'glosses': ['to write']}]},
                {'word': 'кавуна', 'pos': 'noun',
                 'senses': [{'glosses': ['genitive of кавун'], 'tags': ['form-of'], 'form_of': [{}]}]},
                {'word': 'кавун', 'pos': 'noun', 'forms': [{'form': 'каву́н', 'tags': ['canonical']}],
                 'senses': [{'glosses': ['watermelon'], 'tags': ['masculine', 'inanimate']}]},
            ])
            _gz(folder, wiktionary.DOWNLOADS['english'], [
                {'word': 'watermelon', 'pos': 'noun', 'senses': [{'glosses': ['fruit'], 'translations': [
                    {'lang_code': 'uk', 'word': 'каву́н', 'sense': 'fruit'},
                    {'lang_code': 'uk', 'word': 'etc.', 'sense': 'fruit'},
                    {'lang_code': 'es', 'word': 'sandía', 'sense': 'fruit'},
                    {'lang_code': 'ca', 'word': 'síndria', 'sense': 'fruit'},
                    {'lang_code': 'de', 'word': 'Wassermelone', 'sense': 'fruit'}]}]},
                {'word': 'zzz', 'pos': 'noun', 'translations': [{'lang_code': 'es', 'word': 'zzz'}]},
            ])
            _gz(folder, wiktionary.DOWNLOADS['spanish'], [
                {'word': 'sandía', 'pos': 'noun', 'translations': [{'lang_code': 'uk', 'word': 'кавун'}]},
            ])
            counts = wiktionary.convert(folder, out)
            self.assertEqual({'uk-en.jsonl': 2, 'senses.jsonl': 1, 'uk-es.jsonl': 1}, counts)
            rows = [json.loads(line) for line in open(os.path.join(out, 'uk-en.jsonl'), encoding='utf-8')]
            self.assertEqual({'uk': 'написати', 'pos': 'verb', 'senses': [{'en': 'to write'}],
                              'stressed': 'написа́ти', 'aspect': 'pf', 'pair': 'писа́ти'}, rows[0])
            self.assertEqual(('каву́н', 'm'), (rows[1]['stressed'], rows[1]['gender']))
            sense = json.loads(open(os.path.join(out, 'senses.jsonl'), encoding='utf-8').read())
            self.assertEqual({'en': 'watermelon', 'pos': 'noun', 'sense': 'fruit', 'uk': ['каву́н'],
                              'es': ['sandía'], 'ca': ['síndria']}, sense)
            pair = json.loads(open(os.path.join(out, 'uk-es.jsonl'), encoding='utf-8').read())
            self.assertEqual({'uk': 'каву́н', 'pos': 'noun', 'es': ['sandía'], 'direct': ['sandía']}, pair)
        wiktionary.load.cache_clear()


class DeriveTests(unittest.TestCase):

    def test_bundled_dictionaries(self):
        numbers = wiktionary.stats()
        self.assertGreater(numbers['uk-en headwords'], 25000)
        self.assertGreater(numbers['uk-es headwords'], 25000)

    def test_meanings(self):
        self.assertEqual([['touch'], ['play', 'strum']],
                         pivot.english_meanings('touch; play, strum (an instrument)'))

    def test_one_meaning(self):
        (proposals,) = pivot.derive('síndria', 'noun', [['watermelon']])
        self.assertEqual('каву́н', proposals[0]['uk'])
        self.assertEqual(['en', 'es', 'wikt'], proposals[0]['evidence'])
        self.assertTrue(proposals[0]['sure'])

    def test_each_meaning_gets_its_own_word(self):
        touch, play = pivot.ukrainian('tocar', 'verb', 'touch; play (an instrument)')
        self.assertIn('торкати', touch)
        self.assertEqual('грати', play)

    def test_part_of_speech_and_aspect(self):
        # "play" as a noun would be "гра"; the verb is asked for.
        (proposals,) = pivot.derive('jugar', 'verb', [['play']])
        words = [wiktionary.uk_key(p['uk']) for p in proposals]
        self.assertIn('грати', words)
        self.assertNotIn('гра', words)
        # Perfective verbs stand under their imperfective partner.
        (text,) = pivot.ukrainian('escriure', 'verb', 'write')
        self.assertEqual('писати', text.split(', ')[0])

    def test_nothing_without_agreement(self):
        self.assertEqual([[]], pivot.derive('xyzzyq', 'noun', [['qwertyuiop']]))
        # A proper name is not proposed for a common word.
        for proposals in pivot.derive('donzell', 'noun', [['wormwood']]):
            self.assertFalse([p for p in proposals if p['uk'][:1].isupper()])

    def test_evaluate(self):
        numbers = pivot.evaluate([('síndria', 'noun', 'watermelon', 'кавун'),
                                  ('gos', 'noun', 'dog', 'кіт')])
        self.assertEqual(2, numbers['words'])
        self.assertGreaterEqual(numbers['sure']['right'], 1)
        self.assertLess(numbers['sure']['right'], numbers['sure']['proposals'])


class ImportTests(AppTestCase):

    def setUp(self):
        super().setUp()
        vocabulary_service.import_rows([
            {'term': 'síndria', 'part_of_speech': 'noun', 'translation_en': 'watermelon'},
            {'term': 'tocar', 'part_of_speech': 'verb', 'translation_en': 'touch; play (an instrument)'},
            {'term': 'gos', 'part_of_speech': 'noun', 'translation_en': 'dog', 'translation_uk': 'пес'},
            {'term': 'xyzzyq', 'translation_en': 'qwertyuiop'},
        ], seed=True)
        db.session.commit()

    def test_import_as_drafts_and_remove(self):
        self.assertEqual(2, pivot.import_translations())
        db.session.commit()
        self.assertEqual(0, pivot.import_translations())
        melon = Word.query.filter_by(term='síndria').one()
        self.assertEqual('кавун', melon.translations['uk'].translation)
        self.assertFalse(melon.translations['uk'].reviewed)
        tocar = Word.query.filter_by(term='tocar').one()
        self.assertEqual('грати', tocar.senses[1].translations['uk'].text)
        self.assertEqual('пес', Word.query.filter_by(term='gos').one().translation)

        body = self.client.get('/dictionary/sindria').get_data(as_text=True)
        self.assertIn('кавун', body)
        self.assertIn('Машинний переклад', body)
        self.assertEqual(1, vocabulary_service.search('кавун').count())

        # A checked translation stays when the derived ones are taken away.
        tocar.translations['uk'].reviewed = True
        db.session.commit()
        self.assertEqual(1, pivot.remove_translations())
        db.session.commit()
        self.assertNotIn('uk', Word.query.filter_by(term='síndria').one().translations)
        self.assertIn('uk', Word.query.filter_by(term='tocar').one().translations)
        self.assertEqual('пес', Word.query.filter_by(term='gos').one().translation)

    def test_export(self):
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, 'uk-ca.jsonl')
            count = pivot.export([('síndria', 'noun', 'watermelon'), ('jugar', 'verb', 'play'),
                                  ('tocar', 'verb', 'touch; play (an instrument)')], path)
            rows = {wiktionary.uk_key(row['uk']): row
                    for row in map(json.loads, open(path, encoding='utf-8'))}
        self.assertEqual(count, len(rows))
        self.assertEqual([{'w': 'síndria', 'pos': 'noun', 'en': ['watermelon'],
                           'evidence': ['en', 'es', 'wikt']}], rows['кавун']['ca'])
        self.assertEqual({'jugar', 'tocar'}, {item['w'] for item in rows['грати']['ca']})


if __name__ == '__main__':
    unittest.main()
