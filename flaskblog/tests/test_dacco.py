# flaskblog/tests/test_dacco.py

import unittest

from flaskblog.vocabulary import dacco


class DaccoDataTests(unittest.TestCase):

    def test_numbers_match_the_title_page(self):
        numbers = dacco.stats()
        self.assertEqual(16540, numbers['entries'])
        self.assertEqual(557, numbers['notes'])
        self.assertGreater(numbers['senses'], 20000)
        self.assertGreater(numbers['translations'], 24000)

    def test_entry_with_two_parts_of_speech(self):
        entry = dacco.lookup('català')[0]
        self.assertEqual(['noun', 'adjective'], [block['pos'] for block in entry['blocks']])
        genders = [sense.get('gender') for sense in dacco.senses(entry)]
        self.assertEqual(['m', 'm/f', None], genders)

    def test_senses_examples_and_gloss(self):
        entry = dacco.lookup('a')[0]
        first = next(dacco.senses(entry))
        self.assertEqual(['to', 'into'], dacco.translations(first))
        self.assertIn({'ca': 'Anem a la platja?', 'en': 'Shall we go to the beach?'}, first['examples'])

    def test_pronominal_verbs_are_found_without_se(self):
        self.assertEqual('abalançar-se', dacco.lookup('abalançar')[0]['head'])

    def test_expressions(self):
        expressions = {x['ca']: x for x in dacco.lookup('casa')[0]['expressions']}
        self.assertEqual('summer camp', expressions['casa de colònies']['en'])
        self.assertEqual('f', expressions['casa de colònies']['gender'])

    def test_english_index(self):
        heads = {head for head, _pos, _n in dacco.english_index()['watermelon']}
        self.assertIn('síndria', heads)
        self.assertEqual('rush towards', dacco.english_key('to rush towards (someone)'))


if __name__ == '__main__':
    unittest.main()
