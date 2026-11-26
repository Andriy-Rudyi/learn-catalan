"""The starter material of a language section's parts.

``langsites/data/<code>/content.json``::

    {"explained_in": "uk",
     "grammar": [{"title": "...", "level": "A1", "paragraphs": ["..."],
                  "examples": [["text in the language", "translation"]],
                  "table": {"head": ["...", "..."], "rows": [["...", "..."]]}}],
     "phonetics": [... the same ...],
     "conjugator": [... the same, a table of forms per verb ...],
     "course": [... the same ...],
     "text_example": "a short text for the Text page"}

``explained_in`` is the language the explanations are written in:
Ukrainian for the sections learnt from Ukrainian, English for the
Ukrainian section (learnt by people who do not speak it yet).
"""

import functools
import io
import json
import os

from flaskblog.langsites.dictionary import DATA_DIR


@functools.lru_cache(maxsize=8)
def load(code):
    try:
        with io.open(os.path.join(DATA_DIR, code, 'content.json'), encoding='utf-8') as handle:
            return json.load(handle)
    except (OSError, ValueError):
        return {}
