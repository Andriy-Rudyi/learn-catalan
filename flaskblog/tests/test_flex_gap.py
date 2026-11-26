# flaskblog/tests/test_flex_gap.py

import importlib.util
import os
import unittest

SCRIPT = os.path.join(os.path.dirname(__file__), '..', '..', 'scripts', 'flex_gap_fallback.py')


class FlexGapFallbackTests(unittest.TestCase):
    """static/flex-gap.css follows the flex gaps of main.css and modern.css."""

    def test_up_to_date(self):
        spec = importlib.util.spec_from_file_location('flex_gap_fallback', SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with open(module.OUTPUT, encoding='utf-8') as handle:
            self.assertEqual(module.fallback_css(), handle.read(),
                             'run: python scripts/flex_gap_fallback.py')

    def test_menu_link(self):
        with open(os.path.join(os.path.dirname(SCRIPT), '..', 'flaskblog', 'static', 'flex-gap.css')) as handle:
            css = handle.read()
        self.assertIn('html.no-flex-gap[data-design="modern"] .lc-menu-link > :not(:last-child)', css)
        self.assertNotIn('.lc-page >', css)
