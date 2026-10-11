"""Tests for the conjugator.

The point of these is that a wrong conjugation fails the build: the
reference forms in :mod:`flaskblog.conjugation.reference_ca` are compared
against what the site actually serves, and invented words must be
refused rather than guessed at.
"""

import unittest

from flaskblog.conjugation import audit, get_service
from flaskblog.conjugation.compound import add_compound_tenses
from flaskblog.conjugation.corrections import load as load_corrections
from flaskblog.conjugation.normalizer import InvalidQueryError, normalize
from flaskblog.conjugation.reference_ca import REFERENCE
from flaskblog.tests.helpers import AppTestCase


class ReferenceFormsTests(unittest.TestCase):
    """Every verb we claim to have verified must conjugate correctly."""

    def test_no_differences_from_the_reference(self):
        differences = audit.run()
        self.assertEqual(
            [], differences, 'wrong forms:\n' + '\n'.join(str(d) for d in differences)
        )

    def test_reference_is_not_empty(self):
        self.assertGreater(len(REFERENCE), 100)


class ValidationTests(unittest.TestCase):
    def setUp(self):
        self.service = get_service()

    def test_invented_words_are_refused(self):
        self.assertEqual([], audit.run_rejections(self.service))

    def test_machine_learning_predictions_are_off(self):
        import verbecc.config

        self.assertFalse(verbecc.config.ml)

    def test_unknown_verb_gets_suggestions(self):
        result = self.service.conjugate('cantarr')
        self.assertFalse(result.ok)
        self.assertEqual('unknown-verb', result.error)
        self.assertIn('cantar', result.suggestions)

    def test_case_and_whitespace_are_ignored(self):
        for query in ('  PARLAR ', 'Parlar', 'parlar.'):
            result = self.service.conjugate(query)
            self.assertTrue(result.ok, query)
            self.assertEqual('parlar', result.infinitive)

    def test_missing_accent_still_finds_the_verb(self):
        self.assertEqual('ésser', self.service.conjugate('esser').infinitive)

    def test_pronominal_form_conjugates_the_base_verb(self):
        result = self.service.conjugate('rentar-se')
        self.assertTrue(result.ok)
        self.assertEqual('rentar', result.infinitive)
        self.assertEqual('-se', result.pronominal_suffix)
        self.assertEqual('rentar-se', result.display_infinitive)

    def test_pronominal_only_entry_is_found_as_typed(self):
        result = self.service.conjugate('adir-se')
        self.assertTrue(result.ok)
        self.assertEqual('adir-se', result.infinitive)

    def test_phrases_are_refused(self):
        self.assertEqual(
            'not-a-single-word', self.service.conjugate('jo parlo').error
        )

    def test_verified_flag_follows_the_reference(self):
        self.assertTrue(self.service.conjugate('saber').verified)
        self.assertFalse(self.service.conjugate('abadanar').verified)


class NormalizerTests(unittest.TestCase):
    def test_strips_and_lowercases(self):
        self.assertEqual(('parlar', ''), normalize('  PARLAR  '))

    def test_splits_pronominal_suffix(self):
        self.assertEqual(('rentar', '-se'), normalize('rentar-se'))
        self.assertEqual(('anar', "-se'n"), normalize("anar-se'n"))

    def test_short_verbs_are_not_split(self):
        self.assertEqual(('ser', ''), normalize('ser'))
        self.assertEqual(('dir', ''), normalize('dir'))

    def test_rejects_rubbish(self):
        for query in ('', '   ', None, 'parlar 123', 'jo parlo', 'x' * 60):
            with self.assertRaises(InvalidQueryError):
                normalize(query)


class CorrectionsTests(unittest.TestCase):
    def setUp(self):
        self.service = get_service()
        self.corrections = load_corrections()

    def test_every_overridden_verb_exists_in_verbecc(self):
        known = set(self.service.infinitives)
        missing = sorted(set(self.corrections.verb_overrides) - known)
        self.assertEqual([], missing)

    def test_every_overridden_verb_conjugates(self):
        for infinitive in self.corrections.verb_overrides:
            result = self.service.conjugate(infinitive)
            self.assertTrue(result.ok, infinitive)

    def test_corrections_are_actually_applied(self):
        # saber was filed under the perd:re template before the fix
        self.assertEqual('sab:er', self.service.conjugate('saber').template)

    def test_template_fixes_reach_verbs_sharing_the_template(self):
        # the mou:re participle fix, through beure and deure
        self.assertEqual(
            'begut', self.service.conjugate('beure').moods['particip']['particip'][0]
        )
        self.assertEqual(
            'degut', self.service.conjugate('deure').moods['particip']['particip'][0]
        )


class CompoundTenseTests(unittest.TestCase):
    def setUp(self):
        self.service = get_service()

    def test_perfect_and_periphrastic_past_are_built(self):
        moods = self.service.conjugate('parlar').moods
        self.assertEqual('jo he parlat', moods['indicatiu']['perfet'][0])
        self.assertEqual('jo vaig parlar', moods['indicatiu']['passat-perifrastic'][0])
        self.assertEqual('haver parlat', moods['infinitiu']['infinitiu-perfet'][0])

    def test_compound_tenses_use_the_corrected_participle(self):
        moods = self.service.conjugate('viure').moods
        self.assertEqual('jo he viscut', moods['indicatiu']['perfet'][0])

    def test_impersonal_verbs_stay_impersonal(self):
        moods = self.service.conjugate('caldre').moods
        self.assertEqual('-', moods['indicatiu']['perfet'][0])
        self.assertEqual('ell ha calgut', moods['indicatiu']['perfet'][2])

    def test_a_verb_without_a_participle_is_left_alone(self):
        moods = {'indicatiu': {'present': ['jo x'] * 6}}
        self.assertEqual(moods, add_compound_tenses(moods, 'x'))


class VerbeccApiTests(unittest.TestCase):
    """We use a few of verbecc's internals; fail loudly if they move."""

    def test_internals_we_depend_on_exist(self):
        from verbecc.inflector import Inflector

        service = get_service()
        inflector = service.conjugator._inflector
        for attribute in (
            '_conj_parser',
            '_conjugate_mood',
            '_get_verb_stem_from_template_name',
            'find_template',
            'find_verb_by_infinitive',
        ):
            self.assertTrue(hasattr(inflector, attribute), attribute)
        self.assertTrue(hasattr(Inflector, 'ConjugationObjects'))


class ConjugatorRouteTests(AppTestCase):
    def test_page_without_a_query(self):
        response = self.client.get('/conjugator')
        self.assertEqual(200, response.status_code)

    def test_conjugation_from_the_query_string(self):
        response = self.client.get('/conjugator?verb=saber')
        body = response.data.decode()
        self.assertEqual(200, response.status_code)
        self.assertIn('jo sé', body)
        self.assertIn('jo he sabut', body)

    def test_conjugation_from_the_form(self):
        response = self.client.post('/conjugator', data={'verb': 'parlar'})
        self.assertEqual(200, response.status_code)
        self.assertIn('jo parlo', response.data.decode())

    def test_unknown_verb_shows_a_message(self):
        response = self.client.get('/conjugator?verb=qwertyuir')
        self.assertIn('Такого дієслова немає', response.data.decode())

    def test_autocomplete_endpoint(self):
        response = self.client.get('/api/verbs?q=menj')
        self.assertEqual(200, response.status_code)
        self.assertIn('menjar', response.json['verbs'])

    def test_autocomplete_without_a_query(self):
        self.assertEqual([], self.client.get('/api/verbs').json['verbs'])


if __name__ == '__main__':
    unittest.main()
