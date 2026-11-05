# flaskblog/tests/test_course.py

import unittest

from flaskblog.course import content, phrases
from flaskblog.tests.helpers import AppTestCase

FIELDS = ('ca', 'type', 'theme', 'level', 'meaning_ca', 'uk', 'en', 'fr',
          'example_ca', 'example_uk', 'example_en', 'register')


class PhrasesDataTests(unittest.TestCase):

    def test_every_phrase_is_complete(self):
        items = phrases.load()
        self.assertGreaterEqual(len(items), 150)
        themes = {key for key, _name in phrases.THEMES}
        seen = set()
        for item in items:
            for field in FIELDS:
                self.assertTrue(item.get(field), (item['ca'], field))
            self.assertIn(item['theme'], themes, item['ca'])
            self.assertIn(item['level'], ('B2', 'C1', 'C2'), item['ca'])
            self.assertIn(item['type'], ('frase feta', 'refrany'), item['ca'])
            self.assertNotIn(item['ca'].lower(), seen)
            seen.add(item['ca'].lower())
            self.assertFalse(item['ca'].endswith('.'), item['ca'])

    def test_themes_and_meanings(self):
        self.assertEqual(len(phrases.THEMES), len(phrases.themes()))
        item = phrases.load()[0]
        self.assertEqual(item['uk'], phrases.meaning(item, 'uk'))
        self.assertEqual(item['fr'], phrases.meaning(item, 'fr'))
        self.assertEqual(item['en'], phrases.meaning({'en': item['en']}, 'fr'))


class CoursePagesTests(AppTestCase):

    def test_hub(self):
        body = self.client.get('/c1').data.decode()
        self.assertIn('href="/c1/frases-fetes"', body)
        self.assertIn('href="/c1/article"', body)
        self.assertIn('href="/c1/monologue"', body)
        self.assertIn('Морфологія', body)
        self.assertIn('href="/c1"', self.client.get('/').data.decode())    # menu

    def test_hub_links_existing_units(self):
        from flaskblog import db
        from flaskblog.models import GrammarUnit
        db.session.add(GrammarUnit(number=31, slug='relatius', title='Відносні займенники',
                                   section='Будова речення', explanation='…'))
        db.session.commit()
        body = self.client.get('/c1').data.decode()
        self.assertIn('href="/grammar/relatius"', body)

    def test_phrases_page(self):
        body = self.client.get('/c1/frases-fetes').data.decode()
        self.assertIn('ploure a bots i barrals', body)
        self.assertIn('id="phrases-config"', body)
        self.assertIn('course-phrases.js', body)
        english = self.client.get('/c1/frases-fetes?lang=en').data.decode()
        self.assertIn('Set phrases (frases fetes)', english)

    def test_article_and_monologue(self):
        body = self.client.get('/c1/article').data.decode()
        self.assertIn('id="article-text"', body)
        self.assertIn(content.ARTICLE_TOPICS[0], body)
        self.assertIn('data-insert="Tanmateix"', body)
        body = self.client.get('/c1/monologue').data.decode()
        self.assertIn('id="mono-start"', body)
        self.assertIn('%d:00' % content.MONOLOGUE_MINUTES, body)

    def test_sitemap_and_switch(self):
        self.assertIn('/c1/frases-fetes', self.client.get('/sitemap.xml').data.decode())
        self.app.config['COURSE_C1'] = False
        self.assertEqual(404, self.client.get('/c1').status_code)
        self.assertNotIn('href="/c1"', self.client.get('/').data.decode())


if __name__ == '__main__':
    unittest.main()
