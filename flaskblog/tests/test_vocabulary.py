"""Tests for the dictionary and for everyone's personal word list."""

import io
import unittest

from flaskblog import db
from flaskblog.models import UserWord, Word
from flaskblog.tests.helpers import AppTestCase
from flaskblog.vocabulary import service


def make_word(term='parlar', translation='говорити', **kwargs):
    word = Word(term=term, translation=translation, **kwargs)
    word.slug = service.unique_slug(term)
    db.session.add(word)
    db.session.commit()
    return word


class WordModelTests(AppTestCase):
    def test_slug_is_generated_from_the_term(self):
        word = make_word('bon dia', 'добрий день')
        self.assertEqual('bon-dia', word.slug)

    def test_slugs_stay_unique(self):
        make_word('cap', 'голова')
        second = make_word('cap', 'жоден')
        self.assertEqual('cap-1', second.slug)

    def test_accents_survive_in_the_term(self):
        word = make_word('àvia', 'бабуся')
        self.assertEqual('àvia', word.term)


class ImportTests(AppTestCase):
    def test_seed_file_imports(self):
        report = service.import_seed()
        db.session.commit()
        self.assertGreater(report.created, 150)
        self.assertEqual([], report.errors)
        self.assertEqual(report.created, Word.query.count())

    def test_importing_twice_does_not_duplicate(self):
        service.import_seed()
        db.session.commit()
        count = Word.query.count()
        second = service.import_seed()
        db.session.commit()
        self.assertEqual(0, second.created)
        self.assertEqual(count, second.skipped)
        self.assertEqual(count, Word.query.count())

    def test_update_existing_refreshes_translations(self):
        make_word('poma', 'старий переклад')
        report = service.import_rows(
            [{'term': 'poma', 'translation': 'яблуко'}], update_existing=True
        )
        db.session.commit()
        self.assertEqual(1, report.updated)
        self.assertEqual('яблуко', Word.query.filter_by(term='poma').first().translation)

    def test_rows_without_a_translation_are_reported(self):
        report = service.import_rows([{'term': 'poma', 'translation': ''}])
        db.session.commit()
        self.assertEqual(0, report.created)
        self.assertEqual(1, len(report.errors))

    def test_csv_text_is_read(self):
        rows = service.read_rows('term,translation\npoma,яблуко\n')
        self.assertEqual([{'term': 'poma', 'translation': 'яблуко'}], rows)

    def test_export_round_trips(self):
        make_word('poma', 'яблуко', topic='food', level='A1')
        csv_text = service.export_csv()
        self.assertIn('poma', csv_text)
        rows = service.read_rows(csv_text)
        self.assertEqual('яблуко', rows[0]['translation'])


class SeedQualityTests(unittest.TestCase):
    """Cheap guards on the bundled dictionary."""

    def setUp(self):
        self.rows = service.seed_rows()

    def test_terms_are_unique(self):
        terms = [row['term'] for row in self.rows]
        self.assertEqual(len(terms), len(set(terms)))

    def test_ukrainian_text_has_no_russian_only_letters(self):
        import re

        russian = re.compile('[ыэъё]', re.IGNORECASE)
        offenders = [
            (row['term'], field, row[field])
            for row in self.rows
            for field in ('translation', 'example_uk', 'notes')
            if russian.search(row[field])
        ]
        self.assertEqual([], offenders)

    def test_no_word_mixes_latin_and_cyrillic_letters(self):
        import re

        mixed = re.compile(r'[а-яіїєґ][a-zà-ú]|[a-zà-ú][а-яіїєґ]', re.IGNORECASE)
        offenders = [
            (row['term'], row['translation'])
            for row in self.rows
            if mixed.search(row['translation'])
        ]
        self.assertEqual([], offenders)

    def test_choices_are_valid(self):
        from flaskblog.vocabulary.constants import (GENDER_LABELS, LEVEL_LABELS,
                                                    PART_OF_SPEECH_LABELS,
                                                    TOPIC_LABELS)

        for row in self.rows:
            with self.subTest(term=row['term']):
                self.assertIn(row['part_of_speech'] or 'noun', PART_OF_SPEECH_LABELS)
                self.assertIn(row['topic'] or 'basics', TOPIC_LABELS)
                self.assertIn(row['level'] or 'A1', LEVEL_LABELS)
                if row['gender']:
                    self.assertIn(row['gender'], GENDER_LABELS)


class SearchTests(AppTestCase):
    def setUp(self):
        super(SearchTests, self).setUp()
        make_word('poma', 'яблуко', topic='food', level='A1', part_of_speech='noun')
        make_word('cotxe', 'машина', topic='city', level='A2', part_of_speech='noun')
        make_word('parlar', 'говорити', topic='basics', level='A1',
                  part_of_speech='verb', example_ca='Parlo català.')

    def test_search_by_catalan_term(self):
        self.assertEqual(['poma'], [w.term for w in service.search('pom').all()])

    def test_search_by_ukrainian_translation(self):
        self.assertEqual(['cotxe'], [w.term for w in service.search('машин').all()])

    def test_search_inside_examples(self):
        self.assertEqual(['parlar'], [w.term for w in service.search('català').all()])

    def test_filters_combine(self):
        found = service.search(topic='food', level='A1').all()
        self.assertEqual(['poma'], [w.term for w in found])
        self.assertEqual([], service.search(topic='food', level='A2').all())

    def test_results_are_sorted_by_term(self):
        self.assertEqual(
            ['cotxe', 'parlar', 'poma'], [w.term for w in service.search().all()]
        )


class DictionaryPageTests(AppTestCase):
    def setUp(self):
        super(DictionaryPageTests, self).setUp()
        self.word = make_word('poma', 'яблуко', topic='food', level='A1',
                              part_of_speech='noun')

    def test_dictionary_lists_words(self):
        response = self.client.get('/dictionary')
        self.assertEqual(200, response.status_code)
        self.assertIn('poma', response.data.decode())

    def test_dictionary_search(self):
        self.assertIn('poma', self.client.get('/dictionary?q=pom').data.decode())
        self.assertNotIn('poma', self.client.get('/dictionary?q=zzz').data.decode())

    def test_word_page(self):
        response = self.client.get('/dictionary/poma')
        self.assertEqual(200, response.status_code)
        self.assertIn('яблуко', response.data.decode())

    def test_missing_word_is_404(self):
        self.assertEqual(404, self.client.get('/dictionary/no-such-word').status_code)

    def test_verb_page_links_to_the_conjugator(self):
        make_word('parlar', 'говорити', part_of_speech='verb')
        response = self.client.get('/dictionary/parlar')
        self.assertIn('/conjugator?verb=parlar', response.data.decode())

    def test_export_is_csv(self):
        response = self.client.get('/dictionary/export.csv')
        self.assertEqual(200, response.status_code)
        self.assertIn('poma', response.data.decode('utf-8'))

    def test_editing_requires_login(self):
        response = self.client.get('/dictionary/new', follow_redirects=False)
        self.assertEqual(302, response.status_code)
        self.assertIn('/login', response.headers['Location'])

    def test_editing_is_refused_to_ordinary_users(self):
        user = self.create_user()
        self.login_as(user)
        self.assertEqual(403, self.client.get('/dictionary/new').status_code)
        self.assertEqual(
            403, self.client.post('/dictionary/poma/delete').status_code
        )

    def test_admin_can_add_a_word(self):
        self.login_as(self.create_admin())
        response = self.client.post(
            '/dictionary/new',
            data={'term': 'taronja', 'translation': 'апельсин', 'topic': 'food',
                  'level': 'A1', 'part_of_speech': 'noun', 'gender': 'f',
                  'pronunciation': '', 'example_ca': '', 'example_uk': '',
                  'notes': ''},
            follow_redirects=True,
        )
        self.assertEqual(200, response.status_code)
        self.assertIsNotNone(Word.query.filter_by(term='taronja').first())

    def test_admin_can_edit_and_delete(self):
        self.login_as(self.create_admin())
        self.client.post(
            '/dictionary/poma/edit',
            data={'term': 'poma', 'translation': 'яблуко (фрукт)', 'topic': 'food',
                  'level': 'A1', 'part_of_speech': 'noun', 'gender': 'f',
                  'pronunciation': '', 'example_ca': '', 'example_uk': '',
                  'notes': ''},
            follow_redirects=True,
        )
        self.assertEqual('яблуко (фрукт)', Word.query.first().translation)
        self.client.post('/dictionary/poma/delete', follow_redirects=True)
        self.assertEqual(0, Word.query.count())

    def test_admin_can_upload_a_csv(self):
        self.login_as(self.create_admin())
        data = {
            'file': (io.BytesIO('term,translation\nmar,море\n'.encode('utf-8')),
                     'words.csv'),
        }
        response = self.client.post(
            '/dictionary/import', data=data, follow_redirects=True,
            content_type='multipart/form-data',
        )
        self.assertEqual(200, response.status_code)
        self.assertIsNotNone(Word.query.filter_by(term='mar').first())


class PersonalDictionaryTests(AppTestCase):
    def setUp(self):
        super(PersonalDictionaryTests, self).setUp()
        self.word = make_word('poma', 'яблуко')
        self.user = self.create_user()
        self.login_as(self.user)

    def test_page_requires_login(self):
        self.client.get('/logout')
        response = self.client.get('/my-dictionary', follow_redirects=False)
        self.assertEqual(302, response.status_code)
        self.assertIn('/login', response.headers['Location'])

    def test_saving_a_shared_word(self):
        response = self.client.post('/dictionary/poma/save', follow_redirects=True)
        self.assertEqual(200, response.status_code)
        saved = UserWord.query.filter_by(user_id=self.user.id).all()
        self.assertEqual(1, len(saved))
        self.assertEqual('poma', saved[0].display_term)
        self.assertEqual('яблуко', saved[0].display_translation)

    def test_saving_the_same_word_twice_keeps_one_entry(self):
        self.client.post('/dictionary/poma/save', follow_redirects=True)
        self.client.post('/dictionary/poma/save', follow_redirects=True)
        self.assertEqual(1, UserWord.query.count())

    def test_adding_a_word_of_your_own(self):
        response = self.client.post(
            '/my-dictionary/add',
            data={'term': 'rodamón', 'translation': 'бродяга', 'note': 'з книжки'},
            follow_redirects=True,
        )
        self.assertEqual(200, response.status_code)
        item = UserWord.query.one()
        self.assertEqual('rodamón', item.display_term)
        self.assertEqual('бродяга', item.display_translation)
        self.assertIsNone(item.word_id)

    def test_an_own_word_links_to_the_shared_one_when_it_exists(self):
        self.client.post(
            '/my-dictionary/add',
            data={'term': 'poma', 'translation': 'яблучко'},
            follow_redirects=True,
        )
        item = UserWord.query.one()
        self.assertEqual(self.word.id, item.word_id)
        self.assertEqual('яблучко', item.display_translation)

    def test_status_toggles_between_learning_and_known(self):
        self.client.post('/dictionary/poma/save', follow_redirects=True)
        item = UserWord.query.one()
        self.assertEqual(UserWord.STATUS_LEARNING, item.status)
        self.client.post(
            '/my-dictionary/{}/status'.format(item.id), follow_redirects=True
        )
        self.assertEqual(UserWord.STATUS_KNOWN, UserWord.query.one().status)
        self.client.post(
            '/my-dictionary/{}/status'.format(item.id), follow_redirects=True
        )
        self.assertEqual(UserWord.STATUS_LEARNING, UserWord.query.one().status)

    def test_note_can_be_edited(self):
        self.client.post('/dictionary/poma/save', follow_redirects=True)
        item = UserWord.query.one()
        self.client.post(
            '/my-dictionary/{}/note'.format(item.id),
            data={'note': 'плід'},
            follow_redirects=True,
        )
        self.assertEqual('плід', UserWord.query.one().note)

    def test_removing_a_word(self):
        self.client.post('/dictionary/poma/save', follow_redirects=True)
        item = UserWord.query.one()
        self.client.post(
            '/my-dictionary/{}/remove'.format(item.id), follow_redirects=True
        )
        self.assertEqual(0, UserWord.query.count())

    def test_other_peoples_entries_are_untouchable(self):
        other = self.create_user(username='someone')
        item = UserWord(user_id=other.id, word_id=self.word.id)
        db.session.add(item)
        db.session.commit()
        self.assertEqual(
            403, self.client.post('/my-dictionary/{}/remove'.format(item.id)).status_code
        )
        self.assertEqual(
            403, self.client.post('/my-dictionary/{}/status'.format(item.id)).status_code
        )

    def test_filters_and_counts(self):
        self.client.post('/dictionary/poma/save', follow_redirects=True)
        response = self.client.get('/my-dictionary?status=learning')
        self.assertIn('poma', response.data.decode())
        self.assertNotIn(
            'poma', self.client.get('/my-dictionary?status=known').data.decode()
        )

    def test_export(self):
        self.client.post('/dictionary/poma/save', follow_redirects=True)
        response = self.client.get('/my-dictionary/export.csv')
        self.assertEqual(200, response.status_code)
        self.assertIn('poma', response.data.decode('utf-8'))

    def test_deleting_a_user_removes_their_words(self):
        self.client.post('/dictionary/poma/save', follow_redirects=True)
        db.session.delete(self.user)
        db.session.commit()
        self.assertEqual(0, UserWord.query.count())

    def test_deleting_a_shared_word_removes_it_from_personal_lists(self):
        self.client.post('/dictionary/poma/save', follow_redirects=True)
        db.session.delete(self.word)
        db.session.commit()
        self.assertEqual(0, UserWord.query.count())


if __name__ == '__main__':
    unittest.main()


class SearchRankingTests(AppTestCase):

    def setUp(self):
        super().setUp()
        for term, translation, example in (
            ('a la quinta forca', 'дуже далеко', 'La seva casa és lluny.'),
            ('casament', 'весілля', ''),
            ('casa', 'дім', ''),
            ('cases', 'будинки', ''),
            ('llar', 'домівка, casa', ''),
        ):
            db.session.add(Word(term=term, translation=translation, slug=term.replace(' ', '-'),
                                example_ca=example or None))
        db.session.commit()

    def test_exact_match_comes_first(self):
        terms = [w.term for w in service.search(query_text='casa')]
        self.assertEqual('casa', terms[0])
        self.assertEqual(['casa', 'casament', 'llar', 'a la quinta forca'], terms)

    def test_results_heading_and_filters(self):
        body = self.client.get('/dictionary?q=casa').data.decode()
        self.assertIn('Результати для «casa»', body)
        self.assertIn('id="dictFilters"', body)

    def test_suggestions_link_to_the_word(self):
        data = self.client.get('/api/words?q=cas').get_json()
        self.assertEqual('casa', data['words'][0]['term'])
        self.assertEqual('/dictionary/casa', data['words'][0]['url'])
        self.assertEqual([], self.client.get('/api/words?q=c').get_json()['words'])
