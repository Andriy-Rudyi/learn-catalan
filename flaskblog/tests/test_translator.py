# flaskblog/tests/test_translator.py

from flaskblog import db
from flaskblog.models import Translator, TranslationMemory, Word
from flaskblog.tests.helpers import AppTestCase
from flaskblog.translator import engine


class TranslatorTestCase(AppTestCase):

    def setUp(self):
        super().setUp()
        for term, pos, uk, en, fr, example in (
            ('casa', 'noun', 'дім, будинок', 'house, home', 'maison', ('Soc a casa.', 'Я вдома.')),
            ('gran', 'adjective', 'великий', 'big, large', 'grand', None),
            ('obrir', 'verb', 'відкривати', 'to open', 'ouvrir', None),
            ('porta', 'noun', 'двері', 'door', 'porte', None),
            ('germà', 'noun', 'брат', 'brother', 'frère', None),
            ('ciutat', 'noun', 'місто', 'city, town', 'ville', None),
            ('viure', 'verb', 'жити', 'to live', 'vivre', None),
            ('de debò', 'phrase', 'справді', 'really', 'vraiment', None),
        ):
            word = Word(term=term, part_of_speech=pos, level='A1')
            word.set_translation('uk', uk, example[1] if example else None)
            word.set_translation('en', en)
            word.set_translation('fr', fr)
            if example:
                word.example_ca = example[0]
            db.session.add(word)
        db.session.commit()
        engine.forget()

    def run_(self, text, source, target):
        return self.client.post('/translator/run', json={'text': text, 'source': source, 'target': target})


class EngineTests(TranslatorTestCase):

    def test_memory_sentence(self):
        sentence = engine.translate('Soc a casa.', 'ca', 'uk')['sentences'][0]
        self.assertEqual(('memory', 'Я вдома.'), (sentence['method'], sentence['target']))
        back = engine.translate('Я вдома.', 'uk', 'ca')['sentences'][0]
        self.assertEqual('Soc a casa.', back['target'])

    def test_word_by_word_with_forms_and_articles(self):
        sentence = engine.translate('La porta de la casa gran.', 'ca', 'en')['sentences'][0]
        self.assertEqual('words', sentence['method'])
        self.assertEqual('The door of the house big.', sentence['target'])
        self.assertEqual('Двері з дім великий.',
                         engine.translate('La porta de la casa gran.', 'ca', 'uk')['sentences'][0]['target'])

    def test_periphrastic_past_and_clitics(self):
        sentence = engine.translate("Va obrir la porta de debò.", 'ca', 'uk')['sentences'][0]
        self.assertEqual('Відкривати двері справді.', sentence['target'])
        verb = next(t for t in sentence['tokens'] if t.get('lemma') == 'obrir')
        self.assertEqual('passat perifràstic', verb['form'])

    def test_unknown_words_stay(self):
        sentence = engine.translate('La casa xyzzy.', 'ca', 'en')['sentences'][0]
        self.assertIn('xyzzy', sentence['target'])
        self.assertIsNone(next(t for t in sentence['tokens'] if t['text'] == 'xyzzy')['gloss'])

    def test_into_catalan(self):
        self.assertEqual('Meu germà a gran ciutat.',
                         engine.translate('Мій брат у великому місті.', 'uk', 'ca')['sentences'][0]['target'])
        self.assertEqual('Casa és gran.',
                         engine.translate('The house is big.', 'en', 'ca')['sentences'][0]['target'])

    def test_approved_correction_wins(self):
        engine.propose('ca', 'uk', 'La casa gran.', 'Великий будинок.', None, approved=True)
        db.session.commit()
        engine.forget()
        sentence = engine.translate('la casa gran', 'ca', 'uk')['sentences'][0]
        self.assertEqual(('memory', 'Великий будинок.'), (sentence['method'], sentence['target']))


class PageTests(TranslatorTestCase):

    def test_page_and_menu(self):
        self.assertIn('id="translator-form"', self.client.get('/translator').data.decode())
        self.assertIn('href="/translator"', self.client.get('/').data.decode())
        self.assertIn('/translator', self.client.get('/sitemap.xml').data.decode())

    def test_run(self):
        data = self.run_('La porta.', 'ca', 'fr').get_json()
        self.assertEqual('La porte.', data['sentences'][0]['target'])
        token = next(t for t in data['sentences'][0]['tokens'] if t.get('lemma') == 'porta')
        self.assertEqual('/dictionary/porta', token['url'])

    def test_bad_requests(self):
        self.assertEqual(400, self.run_('Hola', 'uk', 'en').status_code)   # no Catalan side
        self.assertEqual(400, self.run_('', 'ca', 'uk').status_code)
        self.assertEqual(413, self.run_('a' * (engine.MAX_TEXT + 1), 'ca', 'uk').status_code)

    def test_suggestion_needs_login_and_review(self):
        form = {'source': 'ca', 'target': 'uk', 'source_text': 'La porta gran.', 'target_text': 'Великі двері.'}
        self.assertNotEqual(200, self.client.post('/translator/suggest', data=form).status_code)
        user = self.create_user('olena')
        self.login_as(user)
        self.assertEqual('pending', self.client.post('/translator/suggest', data=form).get_json()['status'])
        row = TranslationMemory.query.one()
        self.assertEqual(TranslationMemory.PENDING, row.status)
        self.assertEqual('words', self.run_('La porta gran.', 'ca', 'uk').get_json()['sentences'][0]['method'])
        self.assertEqual(403, self.client.get('/translator/review').status_code)

        reviewer = self.create_user('taras', email='taras@example.com')
        db.session.add(Translator(user_id=reviewer.id, lang='uk'))
        db.session.commit()
        self.client.get('/logout')
        self.login_as(reviewer)
        self.assertIn('La porta gran.', self.client.get('/translator/review').data.decode())
        self.client.post('/translator/review/%d' % row.id, data={'decision': 'accept'})
        self.assertEqual(TranslationMemory.APPROVED, TranslationMemory.query.one().status)
        sentence = self.run_('La porta gran.', 'ca', 'uk').get_json()['sentences'][0]
        self.assertEqual(('memory', 'Великі двері.'), (sentence['method'], sentence['target']))

    def test_translator_suggestion_is_approved_at_once(self):
        reviewer = self.create_user('taras', email='taras@example.com')
        db.session.add(Translator(user_id=reviewer.id, lang='en'))
        db.session.commit()
        self.login_as(reviewer)
        form = {'source': 'en', 'target': 'ca', 'source_text': 'The big door.', 'target_text': 'La porta gran.'}
        self.assertEqual('approved', self.client.post('/translator/suggest', data=form).get_json()['status'])

    def test_switched_off(self):
        self.app.config['TRANSLATOR'] = False
        self.assertEqual(404, self.client.get('/translator').status_code)
        self.assertNotIn('href="/translator"', self.client.get('/').data.decode())
