# flaskblog/tests/test_varieties.py

import csv
import json
import os
import tempfile
import unittest
from unittest import mock

from flaskblog import db
from flaskblog.models import Word
from flaskblog.tests.helpers import AppTestCase
from flaskblog.vocabulary import service, varieties

EN_EIXIR = '''==Catalan==
===Etymology===
From Latin exire.
===Verb===
{{ca-verb}}

# {{lb|ca|Valencia|Balearic}} to [[go out]]
#: {{ux|ca|Eixim ara.}}
# {{lb|ca|Valencia}} to [[appear]]

==Occitan==
===Verb===
# to go out
'''

CA_EIXIR = '''== {{-ca-}} ==
=== {{-verb-|ca}} ===
# Sortir.
# {{marca|ca|valencià}} Aparèixer.
== {{-oc-}} ==
# Sortir.
'''

EN_FORM = '''==Catalan==
===Verb===
# {{inflection of|ca|eixir||1|s|pres|ind}}
'''

EN_HEADWORD_LABEL = '''==Catalan==
===Noun===
{{ca-noun|m}} {{tlb|ca|Balearic}}

# [[boy]]
# [[lad]]
'''

EN_CENTRAL = '''==Catalan==
===Noun===
# {{lb|ca|Central Catalan}} [[boy]]
# {{lb|ca|Balearic}} [[boy]]
'''

EN_ARCHAIC = '''==Catalan==
===Verb===
# {{lb|ca|obsolete}} to [[see]]
'''


class ClassifyTests(unittest.TestCase):

    def test_every_sense_regional(self):
        result = varieties.classify(EN_EIXIR, 'en')
        self.assertEqual(2, result['senses'])
        self.assertEqual(2, result['regional'])
        self.assertEqual(['valencian', 'balearic'], result['codes'])
        self.assertFalse(result['central'])

    def test_examples_and_other_languages_are_ignored(self):
        # "#:" example lines and the Occitan section do not count as senses.
        self.assertEqual(2, varieties.classify(EN_EIXIR, 'en')['senses'])

    def test_catalan_edition_labels(self):
        result = varieties.classify(CA_EIXIR, 'ca')
        self.assertEqual((2, 1), (result['senses'], result['regional']))
        self.assertEqual(['valencian'], result['codes'])
        self.assertTrue(result['central'])

    def test_inflected_forms_are_not_senses(self):
        self.assertEqual(0, varieties.classify(EN_FORM, 'en')['senses'])

    def test_headword_label_applies_to_every_sense(self):
        result = varieties.classify(EN_HEADWORD_LABEL, 'en')
        self.assertEqual((2, 2), (result['senses'], result['regional']))

    def test_archaic(self):
        self.assertEqual(['archaic'], varieties.classify(EN_ARCHAIC, 'en')['codes'])

    def test_page_without_catalan(self):
        self.assertIsNone(varieties.classify('==Spanish==\n# x', 'en'))
        self.assertIsNone(varieties.classify(None, 'en'))


class VerdictTests(unittest.TestCase):

    def _verdict(self, en=None, ca=None):
        return varieties.verdict({
            'en': varieties.classify(en, 'en') if en else None,
            'ca': varieties.classify(ca, 'ca') if ca else None,
        })

    def test_regional_when_one_edition_marks_every_sense(self):
        self.assertEqual(('regional', ['valencian', 'balearic']), self._verdict(EN_EIXIR, CA_EIXIR))

    def test_explicit_central_label_wins(self):
        self.assertEqual('central', self._verdict(EN_CENTRAL)[0])

    def test_partial(self):
        self.assertEqual(('partial', ['valencian']), self._verdict(ca=CA_EIXIR))

    def test_no_labels_is_not_proof_of_central(self):
        plain = '==Catalan==\n===Verb===\n# to [[go out]]\n'
        self.assertEqual(('unlabelled', []), self._verdict(plain))

    def test_unknown(self):
        self.assertEqual(('unknown', []), self._verdict())


class CheckTests(unittest.TestCase):

    def test_batches_and_editions(self):
        calls = []

        def fake_fetch(titles, edition):
            calls.append((edition, list(titles)))
            pages = {'en': {'eixir': EN_EIXIR}, 'ca': {'eixir': CA_EIXIR}}[edition]
            return {t: pages[t] for t in titles if t in pages}

        terms = ['eixir'] + ['w{}'.format(i) for i in range(60)]
        results = varieties.check(terms, fetch=fake_fetch)
        self.assertEqual(4, len(calls))  # two batches of 50 per edition
        self.assertEqual('regional', varieties.verdict(results['eixir'])[0])
        self.assertEqual('unknown', varieties.verdict(results['w1'])[0])

    def test_fetch_pages_reads_the_api_response(self):
        payload = {'query': {
            'redirects': [{'from': 'Eixir', 'to': 'eixir'}],
            'pages': [
                {'title': 'eixir', 'revisions': [{'slots': {'main': {'content': EN_EIXIR}}}]},
                {'title': 'nope', 'missing': True},
            ],
        }}

        class Response:
            def __init__(self):
                self.body = json.dumps(payload).encode()

            def read(self):
                return self.body

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

        requests = []

        def opener(request, timeout):
            requests.append(request)
            return Response()

        pages = varieties.fetch_pages(['Eixir', 'nope'], 'en', opener=opener, pause=0)
        self.assertEqual({'Eixir': EN_EIXIR}, pages)
        self.assertIn('titles=Eixir%7Cnope', requests[0].full_url)
        self.assertIn('LearnCatalan', requests[0].get_header('User-agent'))


class DataFileTests(unittest.TestCase):

    def test_entries_are_valid_dictionary_words(self):
        with open(service.SEED_FILE, encoding='utf-8') as handle:
            terms = {row['term'] for row in csv.DictReader(handle)}
        entries = varieties.load()
        self.assertIn('acotxar', entries)
        self.assertIn('eixir', entries)
        for term, entry in entries.items():
            codes = varieties.parse_codes(entry['variety'])
            self.assertTrue(codes, term)
            self.assertEqual(len(codes), len(entry['variety']), term)
            self.assertIn(entry['source'], service.GENERATED_SOURCES, term)
            if entry['source'] == 'review':
                # Hand-made marks are for dictionary words and say what to
                # use instead; the Wiktionary check may also add conjugator
                # verbs, without a Central equivalent.
                self.assertIn(term, terms)
                self.assertTrue(entry.get('central'), term)


class VarietyInAppTests(AppTestCase):

    def setUp(self):
        super().setUp()
        service.import_seed()
        db.session.commit()

    def test_seed_marks_the_words(self):
        word = Word.query.filter_by(term='eixir').first()
        self.assertEqual(('valencian',), word.variety_codes)
        self.assertEqual('sortir', word.central_alternative)
        self.assertTrue(Word.query.filter_by(term='sortir').first().is_central)

    def test_manual_marks_survive_a_reseed(self):
        word = Word.query.filter_by(term='casa').first()
        word.variety, word.variety_source = 'balearic', 'manual'
        db.session.commit()
        service.apply_varieties()
        self.assertEqual(('balearic',), Word.query.filter_by(term='casa').first().variety_codes)

    def test_marks_removed_from_the_file_are_cleared(self):
        service.apply_varieties({})
        self.assertTrue(Word.query.filter_by(term='eixir').first().is_central)

    def test_dictionary_filter(self):
        central = {w.term for w in service.search(variety='central')}
        regional = {w.term for w in service.search(variety='regional')}
        self.assertNotIn('eixir', central)
        self.assertIn('sortir', central)
        # The file may also mark conjugator verbs that are not in the dictionary.
        dictionary = {word.term for word in Word.query.all()}
        self.assertEqual({t for t in varieties.load() if t in dictionary}, regional)

    def test_pages_show_the_mark(self):
        word_page = self.client.get('/dictionary/eixir').data.decode()
        self.assertIn('Не центральне слово', word_page)
        self.assertIn('sortir', word_page)
        listing = self.client.get('/dictionary?q=eixir').data.decode()
        self.assertIn('variety-badge', listing)
        self.assertNotIn('variety-badge', self.client.get('/dictionary?q=sortir&variety=central').data.decode())
        conjugator = self.client.get('/conjugator?verb=eixir').data.decode()
        self.assertIn('Не центральне слово', conjugator)
        self.assertNotIn('Не центральне слово', self.client.get('/conjugator?verb=sortir').data.decode())

    def test_english_pages(self):
        body = self.client.get('/dictionary/eixir?lang=en').data.decode()
        self.assertIn('Not Central Catalan', body)
        self.assertIn('Valencian', body)
        self.assertIn('Central Catalan uses:', body)


class CheckDialectsCommandTests(AppTestCase):

    def setUp(self):
        super().setUp()
        service.import_seed()
        db.session.commit()
        handle, self.data_file = tempfile.mkstemp(suffix='.json')
        os.close(handle)
        with open(self.data_file, 'w', encoding='utf-8') as out:
            json.dump({
                'eixir': {'variety': ['valencian'], 'central': 'sortir', 'source': 'review'},
                'acotxar': {'variety': ['valencian'], 'central': 'tapar', 'source': 'review'},
            }, out)
        self.report = self.data_file + '.csv'

    def tearDown(self):
        for path in (self.data_file, self.report):
            if os.path.exists(path):
                os.remove(path)
        varieties._cache.clear()
        super().tearDown()

    def _run(self, *args):
        pages = {
            'en': {'eixir': EN_EIXIR, 'hui': '==Catalan==\n===Adverb===\n# {{lb|ca|Valencia}} [[today]]\n'},
            'ca': {},
        }

        def fake_check(terms, editions, progress=None):
            return {t: {e: varieties.classify(pages[e].get(t), e) for e in editions} for t in terms}

        with mock.patch.object(varieties, 'DATA_FILE', self.data_file), \
                mock.patch.object(varieties.load, '__defaults__', (self.data_file,)), \
                mock.patch.object(varieties.save, '__defaults__', (self.data_file,)), \
                mock.patch.object(varieties, 'check', fake_check):
            if Word.query.filter_by(term='hui').first() is None:
                db.session.add(Word(term='hui', translation='сьогодні', slug='hui'))
                db.session.commit()
            return self.app.test_cli_runner().invoke(
                args=['vocabulary', 'check-dialects', '--report', self.report] + list(args)
            )

    def test_report_only_by_default(self):
        result = self._run()
        self.assertEqual(0, result.exit_code, result.output)
        with open(self.report, encoding='utf-8') as handle:
            rows = {row['term']: row for row in csv.DictReader(handle)}
        self.assertEqual('confirmed', rows['eixir']['action'])
        self.assertEqual('new', rows['hui']['action'])
        self.assertEqual('not-confirmed', rows['acotxar']['action'])
        with open(self.data_file, encoding='utf-8') as handle:
            self.assertNotIn('hui', json.load(handle))

    def test_verbs_option_adds_conjugator_verbs(self):
        result = self._run('--verbs', '--limit', '30')
        self.assertEqual(0, result.exit_code, result.output)
        with open(self.report, encoding='utf-8') as handle:
            self.assertEqual(30, len(list(csv.DictReader(handle))))
        result = self._run('--verbs')
        self.assertEqual(0, result.exit_code, result.output)
        with open(self.report, encoding='utf-8') as handle:
            checked = {row['term'] for row in csv.DictReader(handle)}
        self.assertIn('parlar', checked)
        self.assertGreater(len(checked), 8000)

    def test_apply_writes_confirmed_and_new_marks(self):
        result = self._run('--apply')
        self.assertEqual(0, result.exit_code, result.output)
        with open(self.data_file, encoding='utf-8') as handle:
            entries = json.load(handle)
        self.assertEqual('wiktionary-en', entries['eixir']['source'])
        self.assertEqual(['balearic', 'valencian'], entries['eixir']['variety'])
        self.assertEqual('sortir', entries['eixir']['central'])
        self.assertEqual(['valencian'], entries['hui']['variety'])
        # Not confirmed is kept as it was.
        self.assertEqual('review', entries['acotxar']['source'])
        self.assertEqual(('valencian',), Word.query.filter_by(term='hui').first().variety_codes)


if __name__ == '__main__':
    unittest.main()
