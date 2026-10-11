"""Compound tenses, which verbecc does not generate for Catalan.

verbecc's Catalan templates only hold simple tenses, so *he parlat* and
*vaig parlar* - the two past tenses a learner meets first - were missing
from the conjugator.  They are fully regular: an auxiliary form plus the
participle (or, for the periphrastic past, plus the infinitive), so we
build them from the corrected participle rather than storing them.
"""

PRONOUNS = ("jo", "tu", "ell", "nosaltres", "vosaltres", "ells")

# Auxiliary paradigms: haver for the perfect tenses, anar for the
# periphrastic past.
HAVER = {
    "perfet": ("he", "has", "ha", "hem", "heu", "han"),
    "plusquamperfet": ("havia", "havies", "havia", "havíem", "havíeu", "havien"),
    "passat-anterior": (
        "haguí", "hagueres", "hagué", "haguérem", "haguéreu", "hagueren",
    ),
    "futur-perfet": ("hauré", "hauràs", "haurà", "haurem", "haureu", "hauran"),
    "condicional-perfet": (
        "hauria", "hauries", "hauria", "hauríem", "hauríeu", "haurien",
    ),
    "subjuntiu-perfet": ("hagi", "hagis", "hagi", "hàgim", "hàgiu", "hagin"),
    "subjuntiu-plusquamperfet": (
        "hagués", "haguessis", "hagués", "haguéssim", "haguéssiu", "haguessin",
    ),
}
ANAR = ("vaig", "vas", "va", "vam", "vau", "van")

# Where each compound tense belongs, and the order tenses are shown in.
INDICATIU_ORDER = (
    "present",
    "perfet",
    "imperfet",
    "plusquamperfet",
    "passat-simple",
    "passat-anterior",
    "passat-perifrastic",
    "futur",
    "futur-perfet",
)
SUBJUNTIU_ORDER = ("present", "perfet", "imperfet", "plusquamperfet")
CONDICIONAL_ORDER = ("present", "perfet")
INFINITIU_ORDER = ("infinitiu-present", "infinitiu-perfet")
GERUNDI_ORDER = ("gerundi", "gerundi-compost")

MISSING = "-"


def _participle(moods):
    """The masculine singular participle, or None when there is none."""
    forms = moods.get("particip", {}).get("particip") or []
    if not forms:
        return None
    participle = forms[0]
    return None if not participle or participle == MISSING else participle


def _available_persons(moods):
    """Which persons the verb actually has.

    Impersonal verbs such as *caldre* only exist in the third person, and
    *cal* must not become *jo he calgut*.
    """
    present = moods.get("indicatiu", {}).get("present") or []
    if len(present) != len(PRONOUNS):
        return [True] * len(PRONOUNS)
    return [form != MISSING for form in present]


def _build(aux_forms, tail, available):
    forms = []
    for index, aux in enumerate(aux_forms):
        if not available[index]:
            forms.append(MISSING)
        else:
            forms.append("{} {} {}".format(PRONOUNS[index], aux, tail))
    return forms


def _ordered(tenses, order):
    """Reorder a mood's tenses, keeping anything not named in *order*."""
    ordered = {}
    for name in order:
        if name in tenses:
            ordered[name] = tenses[name]
    for name, forms in tenses.items():
        if name not in ordered:
            ordered[name] = forms
    return ordered


def add_compound_tenses(moods, infinitive):
    """Return *moods* with the compound tenses added.

    The input is not modified.  When the verb has no participle the
    moods come back untouched.
    """
    participle = _participle(moods)
    result = {mood: dict(tenses) for mood, tenses in moods.items()}
    if participle is None:
        return result

    available = _available_persons(moods)

    indicatiu = result.setdefault("indicatiu", {})
    indicatiu["perfet"] = _build(HAVER["perfet"], participle, available)
    indicatiu["plusquamperfet"] = _build(
        HAVER["plusquamperfet"], participle, available
    )
    indicatiu["passat-anterior"] = _build(
        HAVER["passat-anterior"], participle, available
    )
    indicatiu["futur-perfet"] = _build(HAVER["futur-perfet"], participle, available)
    indicatiu["passat-perifrastic"] = _build(ANAR, infinitive, available)

    subjuntiu = result.setdefault("subjuntiu", {})
    subjuntiu["perfet"] = _build(HAVER["subjuntiu-perfet"], participle, available)
    subjuntiu["plusquamperfet"] = _build(
        HAVER["subjuntiu-plusquamperfet"], participle, available
    )

    condicional = result.setdefault("condicional", {})
    condicional["perfet"] = _build(
        HAVER["condicional-perfet"], participle, available
    )

    infinitiu = result.setdefault("infinitiu", {})
    infinitiu["infinitiu-perfet"] = ["haver {}".format(participle)]

    gerundi = result.setdefault("gerundi", {})
    gerundi["gerundi-compost"] = ["havent {}".format(participle)]

    result["indicatiu"] = _ordered(indicatiu, INDICATIU_ORDER)
    result["subjuntiu"] = _ordered(subjuntiu, SUBJUNTIU_ORDER)
    result["condicional"] = _ordered(condicional, CONDICIONAL_ORDER)
    result["infinitiu"] = _ordered(infinitiu, INFINITIU_ORDER)
    result["gerundi"] = _ordered(gerundi, GERUNDI_ORDER)
    return result
