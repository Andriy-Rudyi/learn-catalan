# flaskblog/tests/test_reader.py

import unittest

from flaskblog import db
from flaskblog.models import UserWord, Word
from flaskblog.reader import morphology
from flaskblog.tests.helpers import AppTestCase


def readings(result):
    return [(r['lemma'], r['kind'], tuple(r['slot'] or ()), r['plural'], r['feminine'])
            for r in result['readings']]


def synonyms(result):
    return [item['text'] for group in result['groups'] for item in group['items']]


class CleanTests(unittest.TestCase):

    def test_punctuation_elision_and_clitics(self):
        self.assertEqual('home', morphology.clean("l'home,"))
        self.assertEqual('aigua', morphology.clean('d’aigua.'))
        self.assertEqual('fes', morphology.clean('fes-ho'))
        self.assertEqual('dona', morphology.clean("dona'm"))
        self.assertEqual('Casa', morphology.clean('«Casa»'))
        # A hyphen inside a word is not a clitic.
        self.assertEqual('porta-avions', morphology.clean('porta-avions'))


class NumberTests(unittest.TestCase):

    def test_plural(self):
        for singular, plural in (('casa', 'cases'), ('gos', 'gossos'), ('actuació', 'actuacions'),
                                 ('famós', 'famosos'), ('aigua', 'aigües'), ('bosc', 'boscos'),
                                 ('llibre', 'llibres')):
            self.assertEqual(plural, morphology.plural(singular), singular)
        self.assertEqual('casa de camp', morphology.plural('casa de camp'))

    def test_singulars(self):
        self.assertIn('casa', morphology.singulars('cases'))
        self.assertIn('actuació', morphology.singulars('actuacions'))
        self.assertIn('famós', morphology.singulars('famosos'))
        self.assertEqual('gos', morphology.singulars('gossos')[0])


class AnalyseTests(unittest.TestCase):

    def test_verb_form_and_synonyms_in_the_same_form(self):
        result = morphology.analyse('decidiren')
        self.assertIn(('decidir', 'verb', ('indicatiu', 'passat-simple', 5), None, None), readings(result))
        self.assertIn('acordaren', synonyms(result))
        self.assertNotIn('acordar', synonyms(result))

    def test_irregular_forms(self):
        self.assertIn(('convenir', 'verb', ('indicatiu', 'passat-simple', 5), None, None),
                      readings(morphology.analyse('convingueren')))
        self.assertIn('anar', [r['lemma'] for r in morphology.analyse('vaig')['readings']])
        self.assertIn('ser', [r['lemma'] for r in morphology.analyse('sóc')['readings']])

    def test_noun_plural(self):
        result = morphology.analyse('cases', 'les')
        self.assertEqual(('casa', 'word', (), True, False), readings(result)[0])
        self.assertIn('habitatges', synonyms(result))
        self.assertNotIn('cas', [r['lemma'] for r in result['readings']])
        # After a determiner the noun's synonyms come first.
        self.assertEqual('word', result['groups'][0]['kind'])

    def test_word_before_a_verb(self):
        result = morphology.analyse('obres', 'tu')
        self.assertEqual('verb', result['groups'][0]['kind'])

    def test_feminine_plural_adjective(self):
        result = morphology.analyse('boniques')
        self.assertIn(('bonic', 'word', (), True, True), readings(result))
        self.assertTrue(all(not text.endswith('c') for text in synonyms(result)))

    def test_capitals_and_unknown_words(self):
        self.assertTrue(all(text[0].isupper() for text in synonyms(morphology.analyse('Decidiren'))))
        self.assertEqual([], morphology.analyse('qwxzt')['readings'])
        self.assertEqual({'word': '', 'readings': [], 'groups': []}, morphology.analyse('...'))


class TextPageTests(AppTestCase):

    def setUp(self):
        super().setUp()
        word = Word(term='decidir', part_of_speech='verb')
        word.set_translation('uk', 'вирішувати')
        word.set_translation('en', 'decide')
        db.session.add(word)
        acordar = Word(term='acordar', part_of_speech='verb')
        acordar.set_translation('uk', 'домовлятися')
        db.session.add(acordar)
        db.session.commit()

    def test_page_and_menu(self):
        body = self.client.get('/text').data.decode()
        self.assertIn('id="reader-text"', body)
        self.assertIn('href="/text"', self.client.get('/').data.decode())
        self.assertIn('/text', self.client.get('/sitemap.xml').data.decode())

    def test_word_lookup(self):
        data = self.client.get('/text/word?w=Decidiren&prev=amics').get_json()
        self.assertEqual('Decidiren', data['word'])
        reading = data['readings'][0]
        self.assertEqual('decidir', reading['lemma'])
        self.assertEqual('вирішувати', reading['translation'])
        self.assertEqual('/dictionary/decidir', reading['url'])
        self.assertEqual('/conjugator?verb=decidir', reading['conjugation_url'])
        self.assertIn('3 ос. мн.', reading['form'])
        self.assertIsNone(reading['save_url'])  # not logged in
        items = {item['text']: item for group in data['groups'] for item in group['items']}
        self.assertEqual('домовлятися', items['Acordaren']['translation'])

    def test_word_lookup_in_english(self):
        data = self.client.get('/text/word?w=decidiren&lang=en').get_json()
        self.assertEqual('decide', data['readings'][0]['translation'])
        self.assertIn('3rd', data['readings'][0]['form'])

    def test_saving_from_the_text(self):
        user = self.create_user('olena')
        self.login_as(user)
        data = self.client.get('/text/word?w=decidiren').get_json()
        self.assertEqual('/dictionary/decidir/save', data['readings'][0]['save_url'])
        self.assertFalse(data['readings'][0]['saved'])
        self.client.post('/dictionary/decidir/save')
        self.assertEqual(1, UserWord.query.filter_by(user_id=user.id).count())
        self.assertTrue(self.client.get('/text/word?w=decidiren').get_json()['readings'][0]['saved'])

    def test_switched_off(self):
        self.app.config['READER'] = False
        self.assertEqual(404, self.client.get('/text').status_code)
        self.assertEqual(404, self.client.get('/text/word?w=casa').status_code)
        self.assertNotIn('href="/text"', self.client.get('/').data.decode())


if __name__ == '__main__':
    unittest.main()
