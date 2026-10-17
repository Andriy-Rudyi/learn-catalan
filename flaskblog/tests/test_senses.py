# flaskblog/tests/test_senses.py

import unittest

from flaskblog import db
from flaskblog.models import Word
from flaskblog.tests.helpers import AppTestCase
from flaskblog.vocabulary import senses, service


def texts(word, lang):
    return [sense.translations[lang].text if lang in sense.translations else ''
            for sense in word.senses]


class AlignTests(unittest.TestCase):

    def test_same_number_of_parts(self):
        self.assertEqual(['a', 'b'], senses.align(['a', 'b'], 2, 'uk'))

    def test_one_word_covers_every_meaning(self):
        self.assertEqual(['batterie', 'batterie'], senses.align(['batterie'], 2, 'fr'))

    def test_extra_parts_go_to_the_last_meaning(self):
        self.assertEqual(['laisser', 'permettre ; prêter'],
                         senses.align(['laisser', 'permettre', 'prêter'], 2, 'fr'))

    def test_missing_parts_leave_the_last_meanings_empty(self):
        self.assertEqual(['a', 'b', ''], senses.align(['a', 'b'], 3, 'uk'))

    def test_join_writes_a_repeated_meaning_once(self):
        self.assertEqual('batterie', senses.join(['batterie', 'batterie'], 'fr'))
        self.assertEqual('toucher ; jouer', senses.join(['toucher', 'jouer'], 'fr'))
        self.assertEqual('a; c', senses.join(['a', '', 'c'], 'uk'))


class SenseModelTests(AppTestCase):

    def import_csv(self, text, **kwargs):
        report = service.import_rows(service.read_rows(text), **kwargs)
        db.session.commit()
        return report

    def word(self, term):
        return Word.query.filter_by(term=term).first()

    def setUp(self):
        super().setUp()
        self.import_csv(
            'term,translation,translation_en,translation_fr,reviewed_fr\n'
            'tocar,торкатися; грати,touch; play (an instrument),toucher ; jouer,0\n'
            'bateria,акумулятор; ударні,battery; drums,batterie,0\n'
        )

    def test_meanings_follow_english(self):
        word = self.word('tocar')
        self.assertEqual(2, len(word.senses))
        self.assertEqual(['touch', 'play (an instrument)'], texts(word, 'en'))
        self.assertEqual(['торкатися', 'грати'], texts(word, 'uk'))
        self.assertEqual(['toucher', 'jouer'], texts(word, 'fr'))
        self.assertFalse(word.senses[0].translations['fr'].reviewed)
        self.assertEqual(['batterie', 'batterie'], texts(self.word('bateria'), 'fr'))
        # The strings stay as they were.
        self.assertEqual('toucher ; jouer', word.translations['fr'].translation)

    def test_english_with_more_meanings_splits_every_language_again(self):
        self.import_csv('term,translation_en\ntocar,touch; play (an instrument); be one\'s turn\n',
                        update_existing=True)
        word = self.word('tocar')
        self.assertEqual(3, len(word.senses))
        self.assertEqual(['торкатися', 'грати', ''], texts(word, 'uk'))

    def test_editing_a_meaning_rewrites_the_string(self):
        word = self.word('tocar')
        word.senses[1].translations['fr'].text = 'jouer (d’un instrument)'
        senses.sync_to_flat(word, 'fr')
        db.session.commit()
        entry = self.word('tocar').translations['fr']
        self.assertEqual('toucher ; jouer (d’un instrument)', entry.translation)
        self.assertTrue(entry.edited)

    def test_seed_leaves_translations_edited_on_the_site(self):
        word = self.word('tocar')
        self.assertTrue(word.translations['fr'].edited)  # an upload counts as the site
        word.translations['uk'].edited = False
        db.session.commit()
        rows = [{'term': 'tocar', 'translation_fr': 'palper', 'translation': 'чіпати'}]
        service.import_rows(rows, update_existing=True, seed=True)
        db.session.commit()
        word = self.word('tocar')
        self.assertEqual('toucher ; jouer', word.translations['fr'].translation)
        self.assertEqual('чіпати', word.translations['uk'].translation)
        self.assertEqual(['чіпати', 'чіпати'], texts(word, 'uk'))

    def test_word_page_lists_meanings(self):
        body = self.client.get('/dictionary/tocar?lang=uk').data.decode()
        self.assertIn('class="word-senses', body)
        self.assertIn('<li>торкатися', body)
        body = self.client.get('/dictionary/bateria?lang=fr').data.decode()
        self.assertIn('batterie <span class="word-sense-hint">(battery)</span>', body)
        self.assertIn('batterie <span class="word-sense-hint">(drums)</span>', body)
        self.assertIn('Traduction automatique', body)

    def test_switching_meanings_off(self):
        self.app.config['SENSES'] = False
        body = self.client.get('/dictionary/tocar?lang=uk').data.decode()
        self.assertNotIn('word-senses', body)
        self.assertIn('торкатися; грати', body)
        data = self.client.get('/api/v1/words/tocar').get_json()['data']
        self.assertNotIn('senses', data)

    def test_api_meanings(self):
        data = self.client.get('/api/v1/words/tocar?lang=fr').get_json()['data']
        self.assertEqual([1, 2], [sense['position'] for sense in data['senses']])
        self.assertEqual({'fr': {'text': 'jouer', 'reviewed': False}}, data['senses'][1]['translations'])

    def test_rebuild_command(self):
        word = self.word('tocar')
        word.senses.clear()
        db.session.commit()
        result = self.app.test_cli_runner().invoke(args=['vocabulary', 'senses'])
        self.assertIn('2', result.output)
        self.assertEqual(['toucher', 'jouer'], texts(self.word('tocar'), 'fr'))

    def test_editor_form_saves_english_and_meanings(self):
        self.login_as(self.create_admin())
        response = self.client.post('/dictionary/tocar/edit', data={
            'term': 'tocar', 'translation': 'торкатися; грати; бути черга',
            'translation_en': 'touch; play; be one’s turn', 'part_of_speech': 'verb',
        }, follow_redirects=True)
        self.assertEqual(200, response.status_code)
        word = self.word('tocar')
        self.assertEqual('touch; play; be one’s turn', word.translation_en)
        self.assertEqual(3, len(word.senses))
        self.assertEqual('бути черга', word.senses[2].translations['uk'].text)
        self.assertTrue(word.translations['en'].edited)


if __name__ == '__main__':
    unittest.main()
