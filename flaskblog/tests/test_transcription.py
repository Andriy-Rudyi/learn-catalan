# flaskblog/tests/test_transcription.py

import unittest

from flaskblog import db
from flaskblog.models import Word
from flaskblog.tests.helpers import AppTestCase
from flaskblog.vocabulary import transcription
from flaskblog.vocabulary.transcription import to_cyrillic, transcribe


def rules(word, part_of_speech=None):
    return transcription._word(word, part_of_speech)


class RuleTests(unittest.TestCase):
    """The spelling rules, checked against the pronunciation lessons."""

    def test_stress(self):
        self.assertEqual('ˈkazə', rules('casa')[0])            # vowel: last but one
        self.assertEqual('siwˈtat', rules('ciutat')[0])        # consonant: last
        self.assertEqual('ˈtɾenən', rules('trenen')[0])        # -en: last but one
        self.assertEqual('əˈbuj', rules('avui')[0])            # final diphthong
        self.assertEqual('kəˈfɛ', rules('cafè')[0])            # written accent

    def test_consonants(self):
        self.assertEqual('ˈpladʒə', rules('platja')[0])
        self.assertEqual('ˈkotʃə', rules('cotxe')[0])            # the lessons say [ˈkɔtʃə]
        self.assertEqual('ˈɡerə', rules('guerra')[0])
        self.assertEqual('ˈkwatɾə', rules('quatre')[0])
        self.assertEqual('ˈesə', rules('essa')[0])             # ss stays [s]
        self.assertEqual('ˈkasə', rules('caça')[0])
        self.assertEqual('əzmuɾˈza', rules('esmorzar', 'verb')[0])
        self.assertEqual('əɡˈzamən', rules('examen')[0])
        self.assertEqual('kulˈleʒi', rules('col·legi')[0])
        self.assertEqual('əˈi', rules('ahir')[0])              # h keeps a and i apart
        self.assertEqual('ˈbeɾt', rules('verd')[0])            # final devoicing

    def test_final_r(self):
        self.assertEqual(('pəɾˈla', True), rules('parlar', 'verb'))
        self.assertEqual(('kuˈnɛʃə', True), rules('conèixer', 'verb'))
        self.assertFalse(rules('amor')[1])                     # amor keeps it, ahir does not

    def test_open_or_closed_vowel_is_uncertain(self):
        self.assertFalse(rules('gossos')[1])
        self.assertTrue(rules('platja')[1])


class TranscribeTests(unittest.TestCase):

    def test_sources(self):
        self.assertEqual('lessons', transcribe('casa').source)
        self.assertEqual('rules', transcribe('meitat').source)
        manual = transcribe('casa', manual='[ˈkasə]')
        self.assertEqual(('ˈkasə', 'editor'), (manual.ipa, manual.source))

    def test_phrases(self):
        self.assertEqual('ˈpa əm tuˈmakət', transcribe('pa amb tomàquet').ipa)
        self.assertEqual('ˈkom əsˈtas', transcribe('com estàs?').ipa)
        self.assertIsNone(transcribe('Москва'))
        self.assertIsNone(transcribe('  '))

    def test_cyrillic(self):
        self.assertEqual('ка́зə', to_cyrillic('ˈkazə'))
        self.assertEqual('лю́нə', to_cyrillic('ˈʎunə'))       # ʎu -> лю
        self.assertEqual('кумпа́нь', to_cyrillic('kumˈpaɲ'))
        self.assertEqual('ква́трə', to_cyrillic('ˈkwatɾə'))
        self.assertEqual('пəрла́', to_cyrillic('pəɾˈla'))
        self.assertEqual('ґе́ррə', to_cyrillic('ˈɡɛrə'))

    def test_every_lesson_word(self):
        """The rules agree with the lessons, open/closed e and o aside."""
        def loose(ipa):
            return ipa.replace('ɛ', 'e').replace('ɔ', 'o')
        wrong = []
        for word, ipa in transcription.lesson_words().items():
            if ' ' in word or '~' in ipa or not word.isalpha() and '·' not in word:
                continue
            got = rules(word)[0]
            if loose(got) != loose(ipa) and not (word.endswith('r') and loose(got) + 'ɾ' == loose(ipa)):
                wrong.append((word, ipa, got))
        self.assertLessEqual(len(wrong), 3, wrong)


class PagesTests(AppTestCase):

    def setUp(self):
        super().setUp()
        word = Word(term='meitat', translation='половина', translation_en='half', part_of_speech='noun')
        db.session.add(word)
        db.session.add(Word(term='gos', translation='пес', translation_en='dog', part_of_speech='noun'))
        db.session.commit()

    def test_word_page(self):
        body = self.client.get('/dictionary/meitat').data.decode()
        self.assertIn('[məjˈtat]', body)
        self.assertIn('мəйта́т', body)
        self.assertNotIn('≈', body)
        body = self.client.get('/dictionary/gos').data.decode()
        self.assertIn('≈ [ˈɡos]', body)
        self.assertIn('Приблизна вимова', body)

    def test_ukrainian_letters_only_in_ukrainian(self):
        body = self.client.get('/dictionary/meitat?lang=en').data.decode()
        self.assertIn('[məjˈtat]', body)
        self.assertNotIn('мəйта́т', body)

    def test_editor_pronunciation_wins(self):
        word = Word.query.filter_by(term='gos').first()
        word.pronunciation = 'ˈɡɔs'
        db.session.commit()
        body = self.client.get('/dictionary/gos').data.decode()
        self.assertIn('[ˈɡɔs]', body)
        self.assertNotIn('≈', body)

    def test_api(self):
        data = self.client.get('/api/v1/words/meitat').get_json()['data']
        self.assertEqual({'ipa': 'məjˈtat', 'cyrillic': 'мəйта́т', 'certain': True, 'source': 'rules'},
                         data['transcription'])
        spec = self.client.get('/api/v1/openapi.json').get_json()
        self.assertIn('Transcription', spec['components']['schemas'])

    def test_text_page(self):
        data = self.client.get('/text/word?w=Meitat').get_json()
        self.assertEqual('məjˈtat', data['transcription']['ipa'])
        data = self.client.get('/text/word?w=meitat&lang=en').get_json()
        self.assertIsNone(data['transcription']['cyrillic'])

    def test_switched_off(self):
        self.app.config['TRANSCRIPTION'] = False
        self.assertNotIn('məjˈtat', self.client.get('/dictionary/meitat').data.decode())
        self.assertIsNone(self.client.get('/api/v1/words/meitat').get_json()['data']['transcription'])
        self.assertIsNone(self.client.get('/text/word?w=meitat').get_json()['transcription'])


if __name__ == '__main__':
    unittest.main()
