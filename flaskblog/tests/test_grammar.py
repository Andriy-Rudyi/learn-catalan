"""Tests for the grammar course."""

import unittest

from flaskblog import db
from flaskblog.grammar import service
from flaskblog.models import GrammarUnit
from flaskblog.tests.helpers import AppTestCase


class CourseDataTests(unittest.TestCase):
    """The bundled course files must be complete and consistent."""

    def setUp(self):
        self.units = service.load_units()

    def test_course_is_not_empty(self):
        self.assertGreater(len(self.units), 0)

    def test_numbers_are_unique_and_ordered(self):
        numbers = [unit['number'] for unit in self.units]
        self.assertEqual(sorted(set(numbers)), numbers)

    def test_titles_are_unique(self):
        titles = [unit['title'] for unit in self.units]
        self.assertEqual(len(set(titles)), len(titles))

    def test_slugs_are_unique(self):
        slugs = [
            service.unique_slug(unit['title'], unit['number']) for unit in self.units
        ]
        self.assertEqual(len(set(slugs)), len(slugs))

    def test_every_unit_has_examples_and_exercises(self):
        for unit in self.units:
            with self.subTest(unit=unit['number']):
                self.assertTrue(unit.get('examples'), 'no examples')
                self.assertTrue(unit.get('exercises'), 'no exercises')

    def test_examples_have_both_languages(self):
        for unit in self.units:
            for example in unit['examples']:
                with self.subTest(unit=unit['number'], ca=example.get('ca')):
                    self.assertTrue(example.get('ca'))
                    self.assertTrue(example.get('uk'))

    def test_every_exercise_item_has_a_question_and_an_answer(self):
        for unit in self.units:
            for block in unit['exercises']:
                self.assertTrue(block.get('instruction'))
                self.assertTrue(block.get('items'))
                for item in block['items']:
                    with self.subTest(unit=unit['number'], question=item.get('q')):
                        self.assertTrue(item.get('q'))
                        self.assertTrue(item.get('a'))

    def test_missing_required_field_is_rejected(self):
        import json
        import os
        import tempfile

        broken = [{'number': 1, 'title': 'No explanation', 'section': 'X'}]
        handle, path = tempfile.mkstemp(suffix='.json')
        try:
            with os.fdopen(handle, 'w', encoding='utf-8') as file_:
                json.dump(broken, file_)
            with self.assertRaises(ValueError):
                service.load_units([path])
        finally:
            os.unlink(path)


class SeedTests(AppTestCase):
    def test_seed_creates_the_units(self):
        report = service.seed()
        db.session.commit()
        self.assertEqual(len(service.load_units()), report.created)
        self.assertEqual(report.created, GrammarUnit.query.count())

    def test_seeding_twice_updates_instead_of_duplicating(self):
        service.seed()
        db.session.commit()
        count = GrammarUnit.query.count()
        second = service.seed()
        db.session.commit()
        self.assertEqual(0, second.created)
        self.assertEqual(count, second.updated)
        self.assertEqual(count, GrammarUnit.query.count())

    def test_examples_and_exercises_round_trip(self):
        service.seed()
        db.session.commit()
        unit = GrammarUnit.query.filter_by(number=1).one()
        self.assertTrue(unit.get_examples())
        self.assertTrue(unit.get_exercises())
        self.assertGreater(unit.exercise_count, 0)
        self.assertIn('ca', unit.get_examples()[0])

    def test_sections_keep_course_order(self):
        service.seed()
        db.session.commit()
        for units in service.sections().values():
            numbers = [unit.number for unit in units]
            self.assertEqual(sorted(numbers), numbers)

    def test_neighbours(self):
        service.seed()
        db.session.commit()
        first = GrammarUnit.query.order_by(GrammarUnit.number).first()
        previous, following = service.neighbours(first)
        self.assertIsNone(previous)
        self.assertIsNotNone(following)


class GrammarPageTests(AppTestCase):
    def setUp(self):
        super(GrammarPageTests, self).setUp()
        service.seed()
        db.session.commit()
        self.unit = GrammarUnit.query.filter_by(number=1).one()

    def test_index_lists_units(self):
        response = self.client.get('/grammar')
        self.assertEqual(200, response.status_code)
        self.assertIn(self.unit.title, response.data.decode())

    def test_unit_page_by_slug(self):
        response = self.client.get('/grammar/{}'.format(self.unit.slug))
        self.assertEqual(200, response.status_code)
        body = response.data.decode()
        self.assertIn('Вправи', body)
        self.assertIn('Приклади', body)

    def test_unit_page_by_number(self):
        response = self.client.get('/grammar/unit/1')
        self.assertEqual(200, response.status_code)
        self.assertIn(self.unit.title, response.data.decode())

    def test_unknown_unit_is_404(self):
        self.assertEqual(404, self.client.get('/grammar/unit/9999').status_code)
        self.assertEqual(404, self.client.get('/grammar/no-such-unit').status_code)

    def test_answers_are_hidden_by_default(self):
        body = self.client.get('/grammar/unit/1').data.decode()
        self.assertIn('exercise-answer d-none', body)

    def test_answers_can_be_shown_without_javascript(self):
        body = self.client.get('/grammar/unit/1?answers=1').data.decode()
        self.assertNotIn('exercise-answer d-none', body)

    def _numbers_in_order(self, body):
        import re
        return [int(n) for n in re.findall(r'<span class="unit-number">(\d+)</span>', body)]

    def test_index_is_in_course_order_by_default(self):
        numbers = self._numbers_in_order(self.client.get('/grammar').data.decode())
        self.assertEqual(sorted(numbers), numbers)
        self.assertEqual(GrammarUnit.query.count(), len(numbers))

    def test_index_by_number_shows_each_units_topic(self):
        body = self.client.get('/grammar?sort=number').data.decode()
        self.assertIn('unit-section', body)
        self.assertIn(self.unit.section, body)

    def test_index_by_topic_groups_units(self):
        body = self.client.get('/grammar?sort=topic').data.decode()
        for section in service.sections():
            self.assertIn('<h3>{} '.format(section), body)
        # every unit is listed exactly once
        numbers = self._numbers_in_order(body)
        self.assertEqual(GrammarUnit.query.count(), len(set(numbers)))
        self.assertEqual(len(numbers), len(set(numbers)))

    def test_topic_view_keeps_units_of_a_section_together(self):
        body = self.client.get('/grammar?sort=topic').data.decode()
        positions = {}
        for index, number in enumerate(self._numbers_in_order(body)):
            unit = GrammarUnit.query.filter_by(number=number).one()
            positions.setdefault(unit.section, []).append(index)
        for section, indexes in positions.items():
            self.assertEqual(list(range(indexes[0], indexes[0] + len(indexes))),
                             indexes, section)

    def test_unknown_sort_falls_back_to_number(self):
        body = self.client.get('/grammar?sort=nonsense').data.decode()
        numbers = self._numbers_in_order(body)
        self.assertEqual(sorted(numbers), numbers)

    def test_empty_course_shows_a_message(self):
        GrammarUnit.query.delete()
        db.session.commit()
        self.assertIn('ще не завантажено', self.client.get('/grammar').data.decode())


if __name__ == '__main__':
    unittest.main()
