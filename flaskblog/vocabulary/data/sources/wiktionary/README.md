# Wiktionary: Ukrainian-English and Ukrainian-Spanish

Made from **Wiktionary** (https://www.wiktionary.org, English and Spanish
editions) as extracted by wiktextract and published on https://kaikki.org
(downloads of 2026-11-11), with `flask vocabulary wiktionary-convert <folder>`
(`flaskblog/vocabulary/wiktionary.py`, where the formats are described).

| File | What | Rows |
| --- | --- | --- |
| `uk-en.jsonl` | Ukrainian headwords with English glosses, stress, gender, verb aspect (Ukrainian entries of the English Wiktionary) | 30,219 |
| `senses.jsonl` | One meaning of an English word with its Ukrainian, Spanish and Catalan translations (translation tables of the English Wiktionary that have a Ukrainian word) | 34,074 |
| `uk-es.jsonl` | Ukrainian words with their Spanish equivalents: from the Spanish Wiktionary (`direct`) and from the tables above, where both translate the same meaning of an English word | 31,941 |

Downloads the converter expects in its folder:

* `https://kaikki.org/dictionary/Ukrainian/kaikki.org-dictionary-Ukrainian.jsonl.gz`
* `https://kaikki.org/dictionary/English/kaikki.org-dictionary-English.jsonl.gz`
* `https://kaikki.org/eswiktionary/Español/kaikki.org-dictionary-Español.jsonl.gz`

Licence: **CC BY-SA 4.0** (Wiktionary text is also under the GFDL). Credit
Wiktionary and keep these files and what is made from them under CC BY-SA.
