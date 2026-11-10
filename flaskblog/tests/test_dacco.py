# flaskblog/tests/test_dacco.py

import os
import tempfile
import textwrap
import unittest

from flaskblog.vocabulary import dacco


class DaccoDataTests(unittest.TestCase):

    def test_both_directions_are_there(self):
        self.assertEqual(18161, dacco.stats(direction='ca-en')['entries'])
        self.assertEqual(21443, dacco.stats(direction='en-ca')['entries'])

    def test_entry_with_two_parts_of_speech(self):
        entry = dacco.lookup('català')[0]
        self.assertEqual(['noun', 'adjective'], [part['pos'] for part in entry['parts']])
        noun, person, adjective = dacco.senses(entry)
        self.assertEqual(('m', 'language'), (noun['gender'], noun['category']))
        self.assertEqual('m/f', person['gender'])
        self.assertEqual(('catalana', 'catalans'), (adjective['fem'], adjective['plural']))
        self.assertGreater(entry['frequency'], 0)

    def test_senses_examples_and_gloss(self):
        first = next(dacco.senses(dacco.lookup('a')[0]))
        self.assertEqual(['to', 'into'], dacco.translations(first))
        self.assertIn({'ca': 'Anem a la platja?', 'en': 'Shall we go to the beach?'}, first['examples'])

    def test_pronominal_verbs_are_found_without_se(self):
        self.assertEqual('abalançar-se', dacco.lookup('abalançar')[0]['head'])

    def test_expressions(self):
        expressions = {x['text']: x for x in dacco.lookup('casa')[0]['expressions']}
        self.assertEqual('summer camp', expressions['casa de colònies']['senses'][0]['text'])

    def test_english_to_catalan(self):
        entry = dacco.lookup('watermelon', 'en-ca')[0]
        texts = [sense['text'] for sense in dacco.senses(entry)]
        self.assertIn('síndria', texts)


class ConvertTests(unittest.TestCase):

    def test_convert_a_small_file(self):
        xml = textwrap.dedent('''\
            <?xml version="1.0" encoding="UTF-8"?>
            <dictionary>
              <Entry frequency="10">gat<nouns><translations><date>0101</date>
                <translation catagory="animal" gender="m">cat<fems>gata</fems>
                  <catexamp>El gat dorm.</catexamp><engexamp>The cat is sleeping.</engexamp>
                  <example>Tinc un &lt;b&gt;gat&lt;/b&gt;.</example></translation>
                <grouptranslation catagory="slang"><translation gender="m">tomcat</translation></grouptranslation>
              </translations></nouns>
              <expressions>de nit tots els gats són negres
                <translations><translation>all cats are grey in the dark</translation></translations>
              </expressions></Entry>
            </dictionary>''')
        with tempfile.TemporaryDirectory() as folder:
            with open(os.path.join(folder, 'g.dic'), 'w', encoding='utf-8') as handle:
                handle.write(xml)
            entry, = dacco.convert_folder(folder)
        self.assertEqual('gat', entry['head'])
        self.assertEqual(10, entry['frequency'])
        cat, tomcat = entry['parts'][0]['senses']
        self.assertEqual({'text': 'cat', 'gender': 'm', 'category': 'animal', 'fem': 'gata',
                          'examples': [{'ca': 'El gat dorm.', 'en': 'The cat is sleeping.'}],
                          'sentences': ['Tinc un gat.']}, cat)
        self.assertEqual(('tomcat', 'slang', 1), (tomcat['text'], tomcat['category'], tomcat['group']))
        self.assertEqual('de nit tots els gats són negres', entry['expressions'][0]['text'])


if __name__ == '__main__':
    unittest.main()
