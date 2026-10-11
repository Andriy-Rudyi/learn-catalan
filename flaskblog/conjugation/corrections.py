"""Corrections applied on top of verbecc's Catalan data.

verbecc 1.9.7 ships ``conjugations-ca.xml`` (templates) and ``verbs-ca.xml``
(verb -> template).  Both contain defects: templates with wrong endings
("mou:re" builds the participle *mouut* instead of *mogut*, "perd:re"
builds the future *perdé* instead of *perdré*) and verbs pointing at a
template that does not fit them (*saber* is filed under "perd:re", so it
conjugates as *sabo, sabs, sab*).

Rather than fork the library we patch the parsed objects in memory:

``<template>``  merges corrected tenses into an existing template, or
                registers a new one when ``new="true"``.  A new template
                may inherit every tense of another one with
                ``base="perd:re"`` and list only what differs.
``<verb>``      re-points one infinitive at another template, optionally
                with an explicit stem.

A template fix repairs every verb that uses the template at once, which
is why most entries live there.  Every correction is covered by the
reference forms in :mod:`flaskblog.conjugation.reference_ca`.
"""

import copy
import os
import threading

from lxml import etree
from verbecc import conjugation_template, tense_template

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
CORRECTIONS_FILE = os.path.join(DATA_DIR, "ca-corrections.xml")

_lock = threading.Lock()
_cache = None


class VerbOverride(object):
    """A verb that must not use the template verbecc assigned to it."""

    __slots__ = ("infinitive", "template", "stem", "note")

    def __init__(self, infinitive, template, stem=None, note=""):
        self.infinitive = infinitive
        self.template = template
        self.stem = stem
        self.note = note

    def __repr__(self):
        return "VerbOverride({!r} -> {!r}, stem={!r})".format(
            self.infinitive, self.template, self.stem
        )


class Corrections(object):
    def __init__(self, template_elems, verb_overrides):
        self.template_elems = template_elems
        self.verb_overrides = verb_overrides

    @property
    def verbs(self):
        return self.verb_overrides

    def applies_to(self, infinitive):
        return infinitive in self.verb_overrides


def load(path=None):
    """Parse the corrections file once and cache the result."""
    global _cache
    with _lock:
        if _cache is None or path is not None:
            parsed = _parse(path or CORRECTIONS_FILE)
            if path is not None:
                return parsed
            _cache = parsed
        return _cache


def _parse(path):
    parser = etree.XMLParser(remove_comments=True, encoding="utf-8")
    root = etree.parse(path, parser).getroot()
    if root.tag != "corrections":
        raise ValueError("unexpected root element {!r} in {}".format(root.tag, path))

    template_elems = []
    verb_overrides = {}
    for child in root:
        if child.tag == "template":
            template_elems.append(child)
        elif child.tag == "verb":
            infinitive = child.get("infinitive")
            template = child.get("template")
            if not infinitive or not template:
                raise ValueError("<verb> needs infinitive and template attributes")
            verb_overrides[infinitive] = VerbOverride(
                infinitive=infinitive,
                template=template,
                stem=child.get("stem"),
                note=child.get("note", ""),
            )
        else:
            raise ValueError("unexpected element {!r} in {}".format(child.tag, path))
    return Corrections(template_elems, verb_overrides)


def apply_to_inflector(inflector, corrections=None):
    """Merge the corrections into a verbecc inflector in place.

    Returns the number of (template, verb) corrections applied.
    """
    corrections = corrections or load()
    parser = inflector._conj_parser

    patched_templates = 0
    for elem in corrections.template_elems:
        name = elem.get("name")
        if not name:
            raise ValueError("<template> without a name attribute")
        if elem.get("new") == "true":
            _add_template(parser, elem)
        else:
            _merge_template(parser, name, elem)
        patched_templates += 1

    # A verb override must name a template that exists once patching is done.
    for override in corrections.verb_overrides.values():
        parser.find_template(override.template)

    return patched_templates + len(corrections.verb_overrides)


def _merge_template(parser, name, elem):
    template = parser.find_template(name)
    for mood_elem in elem:
        mood_name = mood_elem.tag.lower()
        mood = template.moods.get(mood_name)
        if mood is None:
            raise ValueError(
                "template {!r} has no mood {!r} to correct".format(name, mood_name)
            )
        for tense_elem in mood_elem:
            mood.tenses[tense_elem.tag] = tense_template.TenseTemplate(tense_elem)


def _add_template(parser, elem):
    name = elem.get("name")
    if _template_exists(parser, name):
        raise ValueError("template {!r} is marked new but already exists".format(name))

    base_name = elem.get("base")
    if base_name:
        # Inherit the base template and override only the listed tenses.
        template = copy.deepcopy(parser.find_template(base_name))
        template.name = name
        if elem.get("modify-stem") is not None:
            template.modify_stem = elem.get("modify-stem")
        for mood_elem in elem:
            mood_name = mood_elem.tag.lower()
            mood = template.moods.get(mood_name)
            if mood is None:
                raise ValueError(
                    "base template {!r} has no mood {!r}".format(base_name, mood_name)
                )
            for tense_elem in mood_elem:
                mood.tenses[tense_elem.tag] = tense_template.TenseTemplate(tense_elem)
    else:
        # ConjugationTemplate only reads 'name' and 'modify-stem', but keep
        # our bookkeeping attributes out of it all the same.
        clean = etree.fromstring(etree.tostring(elem))
        clean.attrib.pop("new", None)
        template = conjugation_template.ConjugationTemplate(clean)

    parser.templates.append(template)
    parser.templates.sort(key=lambda t: t.name)
    parser._keys = [t.name for t in parser.templates]


def _template_exists(parser, name):
    try:
        parser.find_template(name)
    except Exception:
        return False
    return True
