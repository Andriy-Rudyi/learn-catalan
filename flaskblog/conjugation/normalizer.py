"""Normalisation of user input before it reaches verbecc.

verbecc happily conjugates whatever string it is given: leading spaces,
upper case, a pronominal suffix or an invented word all produce output.
Everything here runs *before* the verb is looked up, so that the lookup
only ever sees a bare, lower case infinitive.
"""

import re
import unicodedata

# Weak pronouns that may be attached to a Catalan infinitive, longest first
# so that "-se'n" is matched before "-se".
PRONOMINAL_SUFFIXES = (
    "-se'n", "-s'hi", "-s'ho", "-se-li", "-se-hi", "-se-ho", "-se-les",
    "-se-los", "-se-la", "-se-lo", "-se-li", "-se-ne", "-me'n", "-te'n",
    "-nos-en", "-vos-en", "-li'n", "-los-en", "-n'hi",
    "-se", "-me", "-te", "-nos", "-vos", "-li", "-los", "-les", "-la",
    "-lo", "-ho", "-hi", "-ne", "-ls", "-l", "-m", "-t", "-s", "-n",
    "'s", "'m", "'t", "'n", "'l", "'ls",
)

# Apostrophes and dashes people actually type, mapped to the ASCII ones
# used in the verb list.
_APOSTROPHES = {"’": "'", "ʼ": "'", "´": "'", "`": "'"}
_DASHES = {"‐": "-", "‑": "-", "‒": "-", "–": "-", "—": "-"}

MAX_QUERY_LENGTH = 40

# A Catalan infinitive: letters (with diacritics), optionally with an
# internal apostrophe or hyphen, nothing else.
_ALLOWED = re.compile(r"^[a-zçàáèéíïòóúüñ·'\-]+$")


class InvalidQueryError(ValueError):
    """The input cannot be a Catalan verb, whatever the verb list says."""


def strip_accents(text):
    """Return *text* without diacritics, matching verbecc's own helper."""
    return "".join(
        c for c in unicodedata.normalize("NFD", text)
        if unicodedata.category(c) != "Mn"
    )


def _translate(text, table):
    for src, dst in table.items():
        text = text.replace(src, dst)
    return text


def split_pronominal(infinitive):
    """Split a pronominal infinitive into (base verb, suffix).

    ``rentar-se`` -> ``("rentar", "-se")``; ``parlar`` -> ``("parlar", "")``.
    The suffix is only split off when something is left in front of it, so
    the verb ``ser`` is never read as ``s`` + ``er``.
    """
    for suffix in PRONOMINAL_SUFFIXES:
        if infinitive.endswith(suffix) and len(infinitive) > len(suffix) + 1:
            return infinitive[: -len(suffix)], suffix
    return infinitive, ""


def normalize(raw):
    """Clean up *raw* user input.

    Returns a ``(base, pronominal_suffix)`` tuple, both lower case.
    Raises :class:`InvalidQueryError` when the input cannot be a verb at
    all, so the caller never has to trust a conjugation of garbage.
    """
    if raw is None:
        raise InvalidQueryError("empty")

    text = unicodedata.normalize("NFC", str(raw))
    text = _translate(_translate(text, _APOSTROPHES), _DASHES)
    # Collapse any whitespace, including the non-breaking space that
    # comes with copy-pasted text, and drop surrounding punctuation.
    text = re.sub(r"[\s ]+", " ", text).strip()
    text = text.strip(".,;:!?\"()[]«»…")
    text = text.lower()

    if not text:
        raise InvalidQueryError("empty")
    if len(text) > MAX_QUERY_LENGTH:
        raise InvalidQueryError("too-long")
    if " " in text:
        # "anar a comprar", "jo parlo" - a phrase, not an infinitive.
        raise InvalidQueryError("not-a-single-word")
    if not _ALLOWED.match(text):
        raise InvalidQueryError("not-catalan-letters")

    base, suffix = split_pronominal(text)
    if not base:
        raise InvalidQueryError("empty")
    return base, suffix
