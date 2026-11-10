# DACCO Catalan-English

`entries.jsonl` is the Catalan-to-English part of **DACCO: The Open Source
English-Catalan Dictionary** (edition 2012-01, http://www.catalandictionary.org),
read from the PDF the DACCO team published ("Catalan to English for English
Speakers") with `flask vocabulary dacco-parse <pdf>` (`flaskblog/vocabulary/dacco.py`).

Licence: **Creative Commons Attribution-ShareAlike 2.5**
(https://creativecommons.org/licenses/by-sa/2.5/). Credit DACCO wherever
this data or anything made from it is shown or shared, and share what is
made from it under the same licence.

16,540 entries, 22,028 meanings, 29,354 English translations, 1,026
example pairs, 2,508 expressions and 557 usage notes. The format is
described at the top of `flaskblog/vocabulary/dacco.py`. Changes made while
reading the PDF: running headers and page numbers removed, lines joined,
gender labels normalised (`m`, `f`, `m/f`, `m pl`, `f pl`). 901 expressions
were printed without a gender between the Catalan phrase and the English;
they were split by a guess and carry `"split_guess": true` until checked.
