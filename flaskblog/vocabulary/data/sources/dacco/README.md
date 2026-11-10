# DACCO

**DACCO** (Diccionari Obert Català de Codi Obert), the open
Catalan-English / English-Catalan dictionary started in 2004 by Dr Linda
Oxnard; contributing editors Prof Max Wheeler, Lou Hevly, Carles Pina i
Estany, Prof Jonathan Kaye, Gill Martin, Josep M. Lopez Besora and
Margarita Castañón. Web: http://www.catalandictionary.org

Source: https://github.com/cpina/dacco, commit `f36744f` (2025-07-29),
folders `dictionaries/cateng` and `dictionaries/engcat`, converted with
`flask vocabulary dacco-convert <clone>` (`flaskblog/vocabulary/dacco.py`,
where the format is described).

| File | Direction | Entries | Meanings | Translations |
| --- | --- | --- | --- | --- |
| `ca-en.jsonl` | Catalan → English | 18,161 | 24,858 | 33,124 |
| `en-ca.jsonl` | English → Catalan | 21,443 | 31,360 | 38,902 |

Licence: the repository is distributed under the **GNU LGPL 2.1** (its
`LICENSE` file); the PDF edition DACCO published states **Creative Commons
Attribution-ShareAlike 2.5**. Either way: credit DACCO wherever this data
or anything made from it is shown or shared, and share what is made from it
under the same terms.

The conversion keeps everything in the XML except the editing dates; HTML
in the Catalan sample sentences (`<b>`) is removed.
