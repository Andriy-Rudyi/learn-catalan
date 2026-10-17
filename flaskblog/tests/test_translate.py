# flaskblog/tests/test_translate.py

import re
import unittest

from flaskblog import db
from flaskblog.i18n import source_key
from flaskblog.i18n.fr import MESSAGES as FR
from flaskblog.models import (TranslationChange, TranslationSuggestion, Translator,
                              UiTranslation, Word)
from flaskblog.tests.helpers import AppTestCase
from flaskblog.translate import service
from flaskblog.vocabulary import service as vocabulary_service

MENU_STRING = 'Мій словник'


class TranslatePlatformTests(AppTestCase):

    def setUp(self):
        super().setUp()
        vocabulary_service.import_rows(vocabulary_service.read_rows(
            'term,translation,translation_en,translation_fr,reviewed_fr,example_ca,example_en\n'
            'tocar,торкатися; грати,touch; play (an instrument),toucher ; jouer,0,Toca el piano.,He plays the piano.\n'
            'casa,дім,house,,,,\n'
        ))
        # As if it came with the bundled files, not edited on the site.
        for word in Word.query:
            for entry in word.translations.values():
                entry.edited = False
        db.session.commit()
        self.user = self.create_user('olena')
        self.translator = self.create_user('marie')
        db.session.add(Translator(user_id=self.translator.id, lang='fr'))
        db.session.commit()

    def word(self, term):
        return Word.query.filter_by(term=term).first()

    def post_sense(self, sense, text, action='save', base=None, lang='fr'):
        current = sense.translations.get(lang)
        return self.client.post('/translate/{}/dictionary/{}'.format(lang, sense.word_id), data={
            'kind': 'sense', 'sense_id': sense.id, 'text': text, 'action': action,
            'base': (current.text if current else '') if base is None else base,
        }, follow_redirects=True)

    # -- pages --------------------------------------------------------------------

    def test_pages_open_without_login(self):
        for url in ('/translate/', '/translate/fr/dictionary', '/translate/fr/interface',
                    '/translate/fr/history', '/translate/it/dictionary?status=missing'):
            self.assertEqual(200, self.client.get(url).status_code, url)
        self.assertEqual(404, self.client.get('/translate/xx/dictionary').status_code)
        # Ukrainian is the language the interface is written in.
        self.assertEqual(404, self.client.get('/translate/uk/interface').status_code)
        body = self.client.get('/translate/?lang=en').data.decode()
        self.assertIn('Help translate', body)
        self.assertIn('Français', body)
        self.assertIn('noindex', body)
        self.assertIn('Disallow: /translate/', self.client.get('/robots.txt').data.decode())

    def test_dictionary_page_lists_what_needs_work(self):
        body = self.client.get('/translate/fr/dictionary').data.decode()
        self.assertIn('tocar', body)   # machine drafts
        self.assertIn('casa', body)    # no French at all
        body = self.client.get('/translate/fr/dictionary?status=missing').data.decode()
        self.assertNotIn('>tocar<', body)
        self.assertIn('>casa<', body)
        body = self.client.get('/translate/fr/dictionary?status=all&q=toc').data.decode()
        self.assertIn('touch', body)
        self.assertIn('play (an instrument)', body)

    # -- suggestions ---------------------------------------------------------------

    def test_anonymous_visitors_cannot_post(self):
        sense = self.word('tocar').senses[0]
        response = self.client.post('/translate/fr/dictionary/{}'.format(sense.word_id),
                                    data={'kind': 'sense', 'sense_id': sense.id, 'text': 'x'})
        self.assertEqual(302, response.status_code)
        self.assertIn('/login', response.headers['Location'])

    def test_a_user_suggests_and_a_translator_accepts(self):
        self.login_as(self.user)
        sense = self.word('tocar').senses[0]
        body = self.post_sense(sense, 'toucher, effleurer', action='save').data.decode()
        # Without translator rights a save is a suggestion.
        self.assertIn('Пропозицію перевірить', body)
        self.assertEqual('toucher', self.word('tocar').senses[0].translations['fr'].text)
        suggestion = TranslationSuggestion.query.one()
        self.assertEqual(('sense', 'open'), (suggestion.kind, suggestion.status))
        # Everybody sees it, so the work is not done twice.
        self.assertIn('toucher, effleurer', self.client.get('/translate/fr/dictionary?status=suggestions').data.decode())
        # Only a translator of the language decides.
        self.assertEqual(403, self.client.post('/translate/suggestions/{}/accept'.format(suggestion.id)).status_code)

        self.client.get('/logout')
        self.login_as(self.translator)
        self.client.post('/translate/suggestions/{}/accept'.format(suggestion.id), follow_redirects=True)
        word = self.word('tocar')
        self.assertEqual('toucher, effleurer', word.senses[0].translations['fr'].text)
        self.assertTrue(word.senses[0].translations['fr'].reviewed)
        self.assertEqual('toucher, effleurer ; jouer', word.translations['fr'].translation)
        self.assertTrue(word.translations['fr'].edited)
        self.assertEqual('accepted', db.session.get(TranslationSuggestion, suggestion.id).status)
        self.assertEqual(['accept'], [change.action for change in TranslationChange.query])

    def test_reject(self):
        suggestion = service.suggest(service.Target('sense', 'fr', sense=self.word('tocar').senses[1]),
                                     'jouer de', self.user)
        db.session.commit()
        self.login_as(self.translator)
        self.client.post('/translate/suggestions/{}/reject'.format(suggestion.id))
        self.assertEqual('rejected', db.session.get(TranslationSuggestion, suggestion.id).status)
        self.assertEqual('jouer', self.word('tocar').senses[1].translations['fr'].text)

    # -- translators --------------------------------------------------------------------

    def test_translator_saves_only_their_language(self):
        self.login_as(self.translator)
        sense = self.word('casa').senses[0]
        self.post_sense(sense, 'maison')
        word = self.word('casa')
        self.assertEqual('maison', word.translations['fr'].translation)
        self.assertTrue(word.senses[0].translations['fr'].reviewed)
        change = TranslationChange.query.one()
        self.assertEqual((None, 'maison', 'edit'), (change.old_text, change.new_text, change.action))
        # Italian: not theirs, so it becomes a suggestion.
        self.post_sense(sense, 'casa', lang='it')
        self.assertNotIn('it', self.word('casa').translations)
        self.assertEqual(1, TranslationSuggestion.query.filter_by(lang='it').count())

    def test_someone_else_changed_it_meanwhile(self):
        self.login_as(self.translator)
        sense = self.word('tocar').senses[0]
        body = self.post_sense(sense, 'palper', base='old text').data.decode()
        self.assertIn('хтось уже змінив', body)
        self.assertEqual('toucher', self.word('tocar').senses[0].translations['fr'].text)

    def test_checks(self):
        self.login_as(self.translator)
        sense = self.word('tocar').senses[0]
        self.assertIn('Крапка з комою', self.post_sense(sense, 'toucher; palper').data.decode())
        self.assertEqual('toucher', self.word('tocar').senses[0].translations['fr'].text)

    def test_mark_checked_and_revert(self):
        self.login_as(self.translator)
        word = self.word('tocar')
        self.client.post('/translate/fr/dictionary/{}'.format(word.id), data={'action': 'check'})
        word = self.word('tocar')
        self.assertTrue(all(sense.translations['fr'].reviewed for sense in word.senses))
        self.assertFalse(service.is_draft(word, 'fr'))
        # Undo checking the first meaning.
        change = TranslationChange.query.filter_by(kind='sense').order_by(TranslationChange.id).first()
        self.client.post('/translate/changes/{}/revert'.format(change.id))
        self.assertFalse(self.word('tocar').senses[0].translations['fr'].reviewed)

    def test_revert_an_edit(self):
        self.login_as(self.translator)
        self.post_sense(self.word('tocar').senses[1], 'jouer (d’un instrument)')
        change = TranslationChange.query.one()
        body = self.client.get('/translate/fr/history').data.decode()
        self.assertIn('jouer (d’un instrument)', body)
        self.client.post('/translate/changes/{}/revert'.format(change.id))
        word = self.word('tocar')
        self.assertEqual('jouer', word.senses[1].translations['fr'].text)
        self.assertFalse(word.senses[1].translations['fr'].reviewed)  # it was a draft
        self.assertEqual('toucher ; jouer', word.translations['fr'].translation)

    def test_example_translation(self):
        self.login_as(self.translator)
        word = self.word('tocar')
        self.client.post('/translate/fr/dictionary/{}'.format(word.id), data={
            'kind': 'example', 'text': 'Il joue du piano.', 'base': '', 'action': 'save'})
        self.assertEqual('Il joue du piano.', self.word('tocar').translations['fr'].example)

    def test_admin_translates_every_language(self):
        self.login_as(self.create_admin())
        self.post_sense(self.word('casa').senses[0], 'casa', lang='it')
        self.assertEqual('casa', self.word('casa').translations['it'].translation)

    def test_deploy_seed_keeps_platform_work(self):
        self.login_as(self.translator)
        self.post_sense(self.word('casa').senses[0], 'maison')
        vocabulary_service.import_rows(
            [{'term': 'casa', 'translation': 'дім', 'translation_fr': 'logement'}],
            update_existing=True, seed=True)
        db.session.commit()
        self.assertEqual('maison', self.word('casa').translations['fr'].translation)

    # -- interface ------------------------------------------------------------------------

    def post_ui(self, source, text, base=None):
        return self.client.post('/translate/fr/interface', data={
            'key': source_key(source), 'text': text, 'action': 'save',
            'base': FR.get(source, '') if base is None else base,
        }, follow_redirects=True)

    def test_interface_translation_shows_on_the_site(self):
        self.login_as(self.translator)
        self.post_ui(MENU_STRING, 'Mon lexique')
        self.assertEqual('Mon lexique', UiTranslation.query.one().text)
        body = self.client.get('/?lang=fr').data.decode()
        self.assertIn('Mon lexique', body)
        # Emptying it brings back the catalogue's text.
        self.post_ui(MENU_STRING, '', base='Mon lexique')
        self.assertEqual(0, UiTranslation.query.count())
        self.assertIn(FR[MENU_STRING], self.client.get('/?lang=fr').data.decode())

    def test_interface_checks_placeholders_and_tags(self):
        self.login_as(self.translator)
        source = next(key for key in FR if '{' in key and '<' not in key)
        body = self.post_ui(source, 'sans espace réservé').data.decode()
        self.assertIn('заповнювачі', body)
        source = next(key for key in FR if '<code>' in key)
        broken = re.sub(r'<[^>]+>', '', FR[source]) + '<script>alert(1)</script>'
        body = self.post_ui(source, broken).data.decode()
        self.assertIn('HTML-теги', body)
        # A tag left open, or format fields that read attributes.
        self.assertIsNotNone(service.check_interface(source, FR[source] + ' <img src=x onerror=alert(1) '))
        placeholder = next(key for key in FR if '{term}' in key)
        self.assertIsNotNone(service.check_interface(
            placeholder, FR[placeholder] + ' {term.__class__}'))
        self.assertIsNone(service.check_interface(placeholder, FR[placeholder]))
        self.assertEqual(0, UiTranslation.query.count())

    def test_unknown_string(self):
        self.login_as(self.translator)
        response = self.client.post('/translate/fr/interface', data={'key': 'nope', 'text': 'x'})
        self.assertEqual(404, response.status_code)

    def test_progress_and_export(self):
        rows = {row['language'].code: row for row in service.progress()}
        self.assertEqual(3, rows['fr']['senses_total'])
        self.assertEqual((2, 0), (rows['fr']['senses'], rows['fr']['checked']))
        self.assertIsNone(rows['uk']['interface'])
        exported = service.export_dictionary('fr')
        self.assertEqual([('tocar', 'toucher ; jouer', '0')],
                         [(row['term'], row['translation'], row['reviewed']) for row in exported])
        db.session.add(UiTranslation(lang='fr', key=source_key(MENU_STRING), source=MENU_STRING, text='Mon lexique'))
        db.session.commit()
        from flaskblog.i18n import forget_overrides
        forget_overrides()
        self.assertIn((MENU_STRING, 'Mon lexique'), service.export_interface('fr'))

    def test_grant_command(self):
        runner = self.app.test_cli_runner()
        result = runner.invoke(args=['translations', 'grant', 'olena', 'it'])
        self.assertEqual(0, result.exit_code, result.output)
        self.assertTrue(service.can_translate('it', self.user))
        runner.invoke(args=['translations', 'revoke', 'olena', 'it'])
        self.assertFalse(service.can_translate('it', self.user))
        self.assertNotEqual(0, runner.invoke(args=['translations', 'grant', 'olena', 'xx']).exit_code)


if __name__ == '__main__':
    unittest.main()
