# Apertium spa-cat

`ca-es.jsonl` holds the common-word pairs of the bilingual dictionary of
**Apertium**, the open machine translation platform:
`apertium-spa-cat.spa-cat.metadix` from https://github.com/apertium/apertium-spa-cat
(commit `7635fe7`), converted with `flask vocabulary apertium-convert <clone>`
(`flaskblog/vocabulary/apertium.py`, where the format is described).

57,440 pairs: 49,777 Catalan and 52,084 Spanish lemmas. Proper names,
numbers, hours and Apertium's internal entries are left out.

Licence: **GNU GPL 2.0** (the repository's `COPYING`). Credit Apertium and
keep this file and anything made from it under the GPL.
