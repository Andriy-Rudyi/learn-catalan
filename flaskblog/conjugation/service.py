"""The conjugator the site serves.

Two things wrap verbecc here:

* **Validation.**  verbecc guesses a conjugation template with a machine
  learning model when a word is not in its verb list, so *qwertyuir* and
  the Spanish *hablar* both come back looking like real Catalan verbs.
  We switch that model off and refuse anything that is not in the list,
  offering close matches instead.
* **Corrections.**  Wrong templates and wrong verb-to-template
  assignments in verbecc's data are patched in memory; see
  :mod:`flaskblog.conjugation.corrections`.
"""

import difflib
import threading

import verbecc.config

# Must be set before the Conjugator is built: verbecc reads it while
# parsing the verb list and only then trains/loads its predictor.
verbecc.config.ml = False

from verbecc import Conjugator  # noqa: E402  (import after the flag)
from verbecc.inflector import Inflector  # noqa: E402

from flaskblog.conjugation import corrections as corrections_module  # noqa: E402
from flaskblog.conjugation.compound import add_compound_tenses  # noqa: E402
from flaskblog.conjugation.normalizer import (  # noqa: E402
    InvalidQueryError,
    normalize,
    strip_accents,
)
from flaskblog.conjugation.reference_ca import REFERENCE  # noqa: E402

# Error codes the view turns into messages.
ERR_EMPTY = "empty"
ERR_TOO_LONG = "too-long"
ERR_NOT_SINGLE_WORD = "not-a-single-word"
ERR_NOT_CATALAN = "not-catalan-letters"
ERR_UNKNOWN_VERB = "unknown-verb"
ERR_INTERNAL = "internal"

SOURCE_VERBECC = "verbecc"
SOURCE_CORRECTED = "corrected"


class ConjugationResult(object):
    """What the conjugator answers, successfully or not."""

    def __init__(
        self,
        query,
        ok=False,
        infinitive=None,
        display_infinitive=None,
        pronominal_suffix="",
        template=None,
        stem=None,
        moods=None,
        verified=False,
        source=SOURCE_VERBECC,
        error=None,
        suggestions=None,
    ):
        self.query = query
        self.ok = ok
        self.infinitive = infinitive
        self.display_infinitive = display_infinitive or infinitive
        self.pronominal_suffix = pronominal_suffix
        self.template = template
        self.stem = stem
        self.moods = moods or {}
        self.verified = verified
        self.source = source
        self.error = error
        self.suggestions = suggestions or []

    @property
    def is_pronominal(self):
        return bool(self.pronominal_suffix)

    def __repr__(self):
        return "ConjugationResult(query={!r}, ok={!r}, error={!r})".format(
            self.query, self.ok, self.error
        )


class ConjugationService(object):
    """Thread-safe, lazily initialised wrapper around verbecc."""

    def __init__(self, lang="ca"):
        self.lang = lang
        self._conjugator = None
        self._infinitives = ()
        self._infinitive_set = frozenset()
        self._infinitives_no_accents = {}
        self._corrections = None
        self._lock = threading.Lock()

    # -- initialisation ------------------------------------------------
    def _ensure_ready(self):
        if self._conjugator is not None:
            return
        with self._lock:
            if self._conjugator is not None:
                return
            conjugator = Conjugator(lang=self.lang)
            corrections = corrections_module.load()
            corrections_module.apply_to_inflector(conjugator._inflector, corrections)

            infinitives = tuple(conjugator.get_infinitives())
            no_accents = {}
            for infinitive in infinitives:
                no_accents.setdefault(strip_accents(infinitive), infinitive)

            self._corrections = corrections
            self._infinitives = infinitives
            self._infinitive_set = frozenset(infinitives)
            self._infinitives_no_accents = no_accents
            self._conjugator = conjugator

    @property
    def conjugator(self):
        self._ensure_ready()
        return self._conjugator

    @property
    def infinitives(self):
        self._ensure_ready()
        return self._infinitives

    # -- lookup --------------------------------------------------------
    def resolve(self, word):
        """Return the verb list entry matching *word*, or None.

        Matching is exact first, then diacritic-insensitive, so that
        "parlár" and "PARLAR" both find *parlar* - but *qwertyuir*
        finds nothing.
        """
        self._ensure_ready()
        if word in self._infinitive_set:
            return word
        return self._infinitives_no_accents.get(strip_accents(word))

    def is_known_verb(self, word):
        try:
            base, _ = normalize(word)
        except InvalidQueryError:
            return False
        return self.resolve(base) is not None

    def suggest(self, word, limit=6):
        """Close matches for a word that is not in the verb list."""
        self._ensure_ready()
        if not word:
            return []
        query = strip_accents(word)
        keys = list(self._infinitives_no_accents)
        # Verbs that start with what was typed are usually what the user
        # meant ("menj" -> "menjar"), so they come first, shortest first;
        # misspellings ("cantarr") are caught by the similarity search.
        prefixed = sorted(
            (key for key in keys if key.startswith(query)),
            key=lambda key: (len(key), key),
        )
        similar = difflib.get_close_matches(query, keys, n=limit, cutoff=0.72)
        ordered = prefixed[:limit] + [key for key in similar if key not in prefixed]
        seen = set()
        out = []
        for key in ordered:
            infinitive = self._infinitives_no_accents[key]
            if infinitive not in seen:
                seen.add(infinitive)
                out.append(infinitive)
        return out[:limit]

    def autocomplete(self, prefix, limit=10):
        """Infinitives starting with *prefix*, for the search box."""
        self._ensure_ready()
        try:
            base, _ = normalize(prefix)
        except InvalidQueryError:
            return []
        query = strip_accents(base)
        matches = [
            self._infinitives_no_accents[key]
            for key in self._infinitives_no_accents
            if key.startswith(query)
        ]
        matches.sort(key=lambda infinitive: (len(infinitive), infinitive))
        return matches[:limit]

    # -- conjugation ---------------------------------------------------
    def conjugate(self, raw_query):
        """Conjugate *raw_query*, or explain why we will not."""
        self._ensure_ready()
        query = "" if raw_query is None else str(raw_query).strip()
        try:
            base, suffix = normalize(raw_query)
        except InvalidQueryError as exc:
            return ConjugationResult(query=query, error=str(exc))

        infinitive = None
        if suffix:
            infinitive = self.resolve(base + suffix)
            if infinitive is not None:
                suffix = ""
        if infinitive is None:
            infinitive = self.resolve(base)
        if infinitive is None:
            return ConjugationResult(
                query=query,
                error=ERR_UNKNOWN_VERB,
                suggestions=self.suggest(base),
            )

        override = self._corrections.verb_overrides.get(infinitive)
        try:
            moods, template_name, stem = self._conjugate_verb(infinitive, override)
        except Exception:
            return ConjugationResult(query=query, error=ERR_INTERNAL)

        display = infinitive + suffix if suffix else infinitive
        return ConjugationResult(
            query=query,
            ok=True,
            infinitive=infinitive,
            display_infinitive=display,
            pronominal_suffix=suffix,
            template=template_name,
            stem=stem,
            moods=moods,
            verified=infinitive in REFERENCE,
            source=SOURCE_CORRECTED if override else SOURCE_VERBECC,
        )

    def _conjugate_verb(self, infinitive, override=None):
        """Build the conjugation tables for a verb in the verb list."""
        inflector = self._conjugator._inflector
        verb = inflector.find_verb_by_infinitive(infinitive)
        if getattr(verb, "predicted", False):
            # Defence in depth: verbecc should never predict now that its
            # model is off, and a predicted form is exactly what we refuse.
            raise ValueError("verbecc predicted a template for {!r}".format(infinitive))

        template_name = override.template if override else verb.template
        template = inflector.find_template(template_name)
        if override is not None and override.stem is not None:
            stem = override.stem
        else:
            stem = inflector._get_verb_stem_from_template_name(
                verb.infinitive, template.name
            )

        conj_objects = Inflector.ConjugationObjects(
            infinitive, verb, template, stem, False
        )
        moods = {}
        for mood_name in template.moods:
            moods[mood_name] = inflector._conjugate_mood(conj_objects, mood_name)
        moods = add_compound_tenses(moods, infinitive)
        return moods, template_name, stem


_service = None
_service_lock = threading.Lock()


def get_service():
    """The process-wide conjugation service."""
    global _service
    if _service is None:
        with _service_lock:
            if _service is None:
                _service = ConjugationService()
    return _service
