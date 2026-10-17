# Data in this folder

These files are not covered by the project's MIT License; each keeps its own.

## thesaurus.txt

Catalan thesaurus "sinonims-cat" by Jaume Ortolà Font and contributors,
Softcatalà: https://github.com/Softcatala/sinonims-cat

Licence: Creative Commons Attribution 4.0 International (CC BY 4.0),
https://creativecommons.org/licenses/by/4.0/

Taken in the compact form made by ReeeWriter
(https://github.com/neuronids/reeewriter, commit c35ab08, 2026-09-14): one
group of synonyms per line, `part of speech <TAB> gloss <TAB> words`, words
separated by `|`; `word^feminine`, `word~register`, a trailing `!` marks an
antonym. No entries were added.

## plural_exceptions.json

154 Catalan singular/plural pairs that the plural rule in `morphology.py`
gets wrong, found by checking that rule against the Softcatalà Catalan
dictionary (catalan-dict-tools, https://github.com/Softcatala/catalan-dict-tools).
Taken from ReeeWriter (same commit).

Licence: GNU Lesser General Public License v2.1, like the dictionary it was
derived from (https://www.gnu.org/licenses/old-licenses/lgpl-2.1.html).
