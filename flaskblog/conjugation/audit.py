"""Compare what the conjugator serves against the reference forms.

Run it directly to see every difference::

    python -m flaskblog.conjugation.audit

The test suite calls :func:`run` and fails when anything is reported, so
a regression in verbecc's data - or in our corrections - shows up as a
failing test rather than as a wrong conjugation on the site.
"""

from __future__ import print_function

import sys

from flaskblog.conjugation.reference_ca import REFERENCE, matches, variants
from flaskblog.conjugation.service import get_service

PRONOUNS = ("jo", "tu", "ell", "ella", "nosaltres", "vosaltres", "ells", "elles")

# Words that must never be conjugated: invented, or from another language.
REJECTED_QUERIES = (
    "qwertyuir",
    "zzzzzar",
    "cantarr",
    "xyzir",
    "hablar",   # Spanish
    "comer",    # Spanish
    "manger",   # French
    "parlare",  # Italian
    "",
    "   ",
    "jo parlo",
    "anar a comprar",
    "parlar123",
)


class Difference(object):
    __slots__ = ("verb", "tense", "position", "expected", "actual")

    def __init__(self, verb, tense, position, expected, actual):
        self.verb = verb
        self.tense = tense
        self.position = position
        self.expected = expected
        self.actual = actual

    def __str__(self):
        return "{:<12} {:<22} [{}] expected {:<28} got {!r}".format(
            self.verb,
            self.tense,
            self.position,
            "/".join(variants(self.expected)),
            self.actual,
        )


def strip_pronoun(form):
    """Drop the pronoun verbecc prefixes to finite forms."""
    if not form:
        return form
    parts = form.split(" ", 1)
    if len(parts) == 2 and parts[0] in PRONOUNS:
        return parts[1]
    return form


def _lookup(moods, key):
    """Resolve a reference key such as ``indicatiu.present``."""
    mood_name, _, tense_name = key.partition(".")
    tense_name = tense_name or mood_name
    mood = moods.get(mood_name)
    if mood is None:
        return None
    return mood.get(tense_name)


def run(service=None):
    """Return the list of differences from the reference forms."""
    service = service or get_service()
    differences = []

    for verb in sorted(REFERENCE):
        result = service.conjugate(verb)
        if not result.ok:
            differences.append(
                Difference(verb, "-", "-", "a conjugation", "error: %s" % result.error)
            )
            continue
        for key, expected in sorted(REFERENCE[verb].items()):
            actual_forms = _lookup(result.moods, key)
            if actual_forms is None:
                differences.append(
                    Difference(verb, key, "-", "the tense to exist", None)
                )
                continue
            if isinstance(expected, str):
                expected = [expected]
            for index, expected_form in enumerate(expected):
                if index >= len(actual_forms):
                    differences.append(
                        Difference(verb, key, index, expected_form, None)
                    )
                    continue
                actual = strip_pronoun(actual_forms[index])
                if not matches(expected_form, actual):
                    differences.append(
                        Difference(verb, key, index, expected_form, actual)
                    )
    return differences


def run_rejections(service=None):
    """Return the queries that were conjugated although they are not verbs."""
    service = service or get_service()
    accepted = []
    for query in REJECTED_QUERIES:
        if service.conjugate(query).ok:
            accepted.append(query)
    return accepted


def main():
    service = get_service()
    differences = run(service)
    wrongly_accepted = run_rejections(service)

    print("reference verbs: {}".format(len(REFERENCE)))
    print("differences:     {}".format(len(differences)))
    for difference in differences:
        print("  " + str(difference))
    print("wrongly accepted: {}".format(len(wrongly_accepted)))
    for query in wrongly_accepted:
        print("  {!r}".format(query))
    return 1 if differences or wrongly_accepted else 0


if __name__ == "__main__":
    sys.exit(main())
