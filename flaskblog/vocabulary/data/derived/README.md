# Derived Ukrainian-Catalan dictionary

`uk-ca.jsonl` is made by `flask vocabulary pivot-export`
(`flaskblog/vocabulary/pivot.py`): for every word of the site's dictionary
(its own words and the ones imported from DACCO), the Ukrainian words that
two routes agree on: English (the word's English meanings, then Wiktionary's
English-Ukrainian tables and Ukrainian entries) and Spanish (Apertium's
Catalan-Spanish pairs, then Wiktionary's Spanish-Ukrainian pairs), or that
Wiktionary itself lists next to the Catalan word.

14,865 Ukrainian headwords. Each Catalan word carries the English meaning it
was found for and its `evidence` (`en`, `es`, `wikt`); `"unsure": true`
marks proposals with one route only. Nobody has checked the pairs by hand:
against the dictionary's 4,885 hand-translated words, the first proposal is
the very word the editor chose for 77% of the words, and one of the
proposals for 89% (the rest are mostly synonyms).

It is made from sources under different licences: Wiktionary (CC BY-SA
4.0), DACCO (LGPL-2.1 / CC BY-SA 2.5) and Apertium (GPL-2.0). Pairs whose
evidence does not include `es` owe nothing to Apertium. Credit all three
when sharing the file.
