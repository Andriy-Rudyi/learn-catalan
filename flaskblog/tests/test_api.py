# flaskblog/tests/test_api.py

import unittest

from flaskblog import db
from flaskblog.api.routes import RateLimiter
from flaskblog.models import Word
from flaskblog.tests.helpers import AppTestCase


class ApiTests(AppTestCase):

    def setUp(self):
        super().setUp()
        word = Word(term='anar', translation='йти', translation_en='go',
                    part_of_speech='verb', level='A1', example_ca='Vaig a la feina.')
        word.set_translation('fr', 'aller', 'Je vais au travail.')
        db.session.add(word)
        db.session.add(Word(term='casa', translation='дім', translation_en='house', part_of_speech='noun'))
        db.session.commit()

    def get(self, url, **kwargs):
        response = self.client.get(url, **kwargs)
        return response, response.get_json()

    def test_word_with_every_translation(self):
        response, body = self.get('/api/v1/words/anar')
        self.assertEqual(200, response.status_code)
        self.assertEqual('*', response.headers['Access-Control-Allow-Origin'])
        data = body['data']
        self.assertEqual('anar', data['term'])
        self.assertEqual({'en', 'fr', 'uk'}, set(data['translations']))
        self.assertEqual('aller', data['translations']['fr']['translation'])
        self.assertTrue(data['conjugation'].endswith('/api/v1/conjugations/anar'))
        self.assertNotIn('Set-Cookie', response.headers)

    def test_choose_languages(self):
        _, body = self.get('/api/v1/words/anar?lang=fr')
        self.assertEqual(['fr'], list(body['data']['translations']))
        # Only words translated into French.
        _, body = self.get('/api/v1/words?lang=fr')
        self.assertEqual(['anar'], [w['term'] for w in body['data']])
        response, body = self.get('/api/v1/words?lang=xx')
        self.assertEqual(400, response.status_code)
        self.assertEqual('unknown-language', body['error']['code'])

    def test_search_and_pages(self):
        _, body = self.get('/api/v1/words?q=house')
        self.assertEqual(['casa'], [w['term'] for w in body['data']])
        _, body = self.get('/api/v1/words?per_page=1')
        self.assertEqual(2, body['meta']['total'])
        self.assertIn('page=2', body['links']['next'])
        self.assertIsNone(body['links']['prev'])

    def test_missing_word_and_address(self):
        response, body = self.get('/api/v1/words/nope')
        self.assertEqual(404, response.status_code)
        self.assertEqual('not-found', body['error']['code'])
        response, body = self.get('/api/v1/no-such-endpoint')
        self.assertEqual(404, response.status_code)
        self.assertIn('error', body)

    def test_conjugation(self):
        response, body = self.get('/api/v1/conjugations/parlar')
        self.assertEqual(200, response.status_code)
        present = body['data']['moods']['indicatiu']['present']
        self.assertEqual({'person': '1s', 'form': 'jo parlo'}, present[0])
        response, body = self.get('/api/v1/conjugations/xyzzyq')
        self.assertEqual(404, response.status_code)
        self.assertEqual('unknown-verb', body['error']['code'])
        _, body = self.get('/api/v1/verbs?q=parl')
        self.assertIn('parlar', body['data'])

    def test_languages_and_description(self):
        _, body = self.get('/api/v1/languages')
        counts = {lang['code']: lang['words'] for lang in body['data']}
        self.assertEqual(1, counts['fr'])
        self.assertEqual(0, counts['de'])
        _, spec = self.get('/api/v1/openapi.json')
        self.assertEqual('3.0.3', spec['openapi'])
        self.assertIn('/conjugations/{verb}', spec['paths'])
        self.assertEqual(200, self.client.get('/developers').status_code)

    def test_dictionary_csv_has_every_language(self):
        response = self.client.get('/api/v1/dictionary.csv')
        header = response.data.decode().splitlines()[0]
        self.assertIn('translation_en', header)
        self.assertIn('translation_fr', header)

    def test_rate_limit(self):
        self.app.config['API_RATE_LIMIT'] = 2
        headers = {'X-Forwarded-For': '203.0.113.9'}
        self.assertEqual(200, self.client.get('/api/v1/languages', headers=headers).status_code)
        self.assertEqual(200, self.client.get('/api/v1/languages', headers=headers).status_code)
        response = self.client.get('/api/v1/languages', headers=headers)
        self.assertEqual(429, response.status_code)
        self.assertIn('Retry-After', response.headers)
        other = {'X-Forwarded-For': '203.0.113.10'}
        self.assertEqual(200, self.client.get('/api/v1/languages', headers=other).status_code)

    def test_rate_limiter_window(self):
        limiter = RateLimiter()
        self.assertTrue(limiter.allow('a', 1, now=0)[0])
        self.assertFalse(limiter.allow('a', 1, now=30)[0])
        self.assertTrue(limiter.allow('a', 1, now=61)[0])


class MultilingualDictionaryTests(AppTestCase):

    def test_translations_are_rows_per_language(self):
        word = Word(term='aigua', translation='вода', translation_en='water')
        word.set_translation('de', 'Wasser', 'Ich trinke Wasser.')
        db.session.add(word)
        db.session.commit()
        word = Word.query.filter_by(term='aigua').first()
        self.assertEqual(['uk', 'en', 'de'], word.languages)
        self.assertEqual('Wasser', word.translation_in('de').translation)
        # A language without a translation falls back to English.
        self.assertEqual('water', word.translation_in('it').translation)
        word.translation_en = None
        db.session.commit()
        self.assertNotIn('en', Word.query.filter_by(term='aigua').first().translations)

    def test_csv_with_a_new_language(self):
        from flaskblog.vocabulary import service
        rows = service.read_rows('term,translation,translation_fr,example_fr\npa,хліб,pain,Du pain.\n')
        report = service.import_rows(rows)
        db.session.commit()
        self.assertEqual(1, report.created)
        word = Word.query.filter_by(term='pa').first()
        self.assertEqual('pain', word.translations['fr'].translation)
        exported = service.export_csv()
        self.assertIn('translation_fr', exported.splitlines()[0])
        # Updating one language leaves the others alone.
        service.import_rows(service.read_rows('term,translation_fr\npa,le pain\n'), update_existing=True)
        db.session.commit()
        word = Word.query.filter_by(term='pa').first()
        self.assertEqual(('хліб', 'le pain'), (word.translation, word.translations['fr'].translation))

    def test_reseeding_keeps_an_editors_review(self):
        from flaskblog.vocabulary import service
        csv_text = 'term,translation_fr,reviewed_fr\npa,pain,0\n'
        service.import_rows(service.read_rows(csv_text))
        db.session.commit()
        entry = Word.query.filter_by(term='pa').first().translations['fr']
        self.assertFalse(entry.reviewed)
        entry.reviewed = True
        db.session.commit()
        # The same draft text again (every deploy re-seeds): the review stays.
        service.import_rows(service.read_rows(csv_text), update_existing=True)
        db.session.commit()
        self.assertTrue(Word.query.filter_by(term='pa').first().translations['fr'].reviewed)
        # New text is a new draft.
        service.import_rows(service.read_rows('term,translation_fr,reviewed_fr\npa,du pain,0\n'),
                            update_existing=True)
        db.session.commit()
        self.assertFalse(Word.query.filter_by(term='pa').first().translations['fr'].reviewed)

    def test_bundled_files_cover_every_word(self):
        from flaskblog.vocabulary import service
        self.assertEqual(['uk', 'en', 'fr'], service.seed_languages())
        rows = service.seed_rows()
        self.assertGreater(len(rows), 3000)
        self.assertTrue(all(row.get('translation') and row.get('translation_en')
                            and row.get('translation_fr') for row in rows))
        # French is machine-translated: bundled as drafts until reviewed.
        self.assertTrue(all(row.get('reviewed_fr') == '0' for row in rows))


if __name__ == '__main__':
    unittest.main()
