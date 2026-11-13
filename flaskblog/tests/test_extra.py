# flaskblog/tests/test_extra.py

from flaskblog import db
from flaskblog.models import Word
from flaskblog.tests.helpers import AppTestCase
from flaskblog.vocabulary import extra
from flaskblog.vocabulary import service as vocabulary_service


class ExtraWordsTests(AppTestCase):

    def test_list(self):
        listed = extra.words()
        self.assertGreater(len(listed), 400)
        self.assertIn('balma', listed)
        self.assertFalse([word for word in listed if word.startswith('#')])

    def test_import(self):
        vocabulary_service.import_rows([{'term': 'balma', 'translation_en': 'rock shelter'}], seed=True)
        db.session.commit()
        self.assertEqual(2, extra.import_words(['balma', 'babarota', 'banasta']))
        db.session.commit()
        self.assertEqual(0, extra.import_words(['babarota', 'banasta']))
        self.assertIsNone(Word.query.filter_by(term='balma').one().source)  # was there already
        scarecrow = Word.query.filter_by(term='babarota').one()
        self.assertEqual(('extra', 'noun'), (scarecrow.source, scarecrow.part_of_speech))
        self.assertEqual('scarecrow', scarecrow.translation_en)
        self.assertFalse(scarecrow.translations['en'].reviewed)
        self.assertIn('espantapájaros', scarecrow.translations['es'].translation)
        basket = Word.query.filter_by(term='banasta').one()
        self.assertEqual({}, dict(basket.translations))
        body = self.client.get('/dictionary/banasta').get_data(as_text=True)
        self.assertIn('Перекладу цього слова ще немає', body)
        self.assertEqual(2, extra.remove_words())
        db.session.commit()
        self.assertEqual(1, Word.query.count())
