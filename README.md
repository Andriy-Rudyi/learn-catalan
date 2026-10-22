# learn-catalan

A Flask-based blog platform for learning and teaching the Catalan language.

## Overview

**learn-catalan** is a blog-style language learning platform built with Flask and SQLAlchemy. It provides a clean, database-backed environment where Catalan language learners can access blog posts, lessons, vocabulary articles, and cultural content organized chronologically and by topic.

## Features

- Blog posts and articles for Catalan language learning
- Structured lessons organized by topic
- **Verb conjugator** with validated input and corrected conjugation data
  (see [Conjugator](#conjugator))
- **Catalan-Ukrainian dictionary** with search, filters, CSV import/export and
  a personal word list for every user (see [Dictionary](#dictionary))
- **Grammar course** of numbered units, each with an explanation, examples and
  exercises with answers (see [Grammar course](#grammar-course))
- **Phonetics** lessons (`/phonetics`): sounds with IPA, Ukrainian
  approximations, practice words and exercises; 🔊 buttons read Catalan aloud
  with the device's own Catalan voice (also on dictionary, conjugator and
  grammar pages). Lessons live in `flaskblog/phonetics/data/lessons.json`,
  so no database step is needed.
- Database-driven content management
- Chronological and category-based post navigation
- **Three interface languages: English (the default), Ukrainian and French**
  (language menu in the header; first visit follows the browser language).
  English learners get an adapted course, not a word-for-word translation:
  grammar units and pronunciation lessons are rewritten around English (false
  friends, “do”, aspirated p/t/k…), and every dictionary entry has an English
  translation. French has its own interface and dictionary translations; the
  courses are shown in English until they get a French version.
  See [Languages](#languages)
- **Meanings**: a dictionary translation is attached to a meaning of the word,
  not to the word (“tocar”: 1. touch, 2. play an instrument), with English
  as the pivot. `SENSES=False` goes back to one line per language. See
  [Meanings](#meanings)
- **Translator** at `/translator`: Catalan ↔ Ukrainian, English, French with
  the site's own engine; translation memory first, word by word otherwise,
  and every approved correction makes it better. See [Translator](#translator)
- **Reading**: Shakespeare's *Othello* in full in Catalan, every word
  clickable. See [Reading](#reading)
- **Transcription**: every dictionary word shows how it sounds, in IPA and (on
  the Ukrainian site) in Ukrainian letters with the stress marked:
  casa [ˈkazə] ка́зə. See [Transcription](#transcription)
- **Translation platform** at `/translate`: anyone logged in suggests
  translations of the dictionary and of the interface, translators of a
  language accept them and check machine translations, every change can be
  undone. See [Translation platform](#translation-platform)
- **Text page** at `/text`: paste a Catalan text and click any word for its
  base form (convingueren → convenir, simple past, 3rd person plural), its
  translation and synonyms already put into the same form; a synonym can
  replace the word, with a history to go back through. See
  [Text page](#text-page)
- Responsive interface that works on phones, with a light/dark theme switch
- Two looks: a modern design (default; the menu is pinned to
  the left edge) and the earlier classic one. There is no button for it:
  opening any page with `?design=classic` switches that browser back
  (`?design=modern` returns), and `DESIGN=classic` rolls everyone back. The
  modern look lives entirely in `flaskblog/static/modern.css`, so deleting
  that file (and its `<link>` in `layout.html`) removes it for good
- FAQ (`/faq`) with contents, links to every question and a search box,
  including step-by-step instructions for turning on audio in the
  pronunciation lessons on Android, iPhone, Mac and Windows. The questions
  live in `flaskblog/main/faq.py`
- Search engine optimisation (`flaskblog/seo.py`): page descriptions,
  canonical links, Ukrainian/English versions (hreflang), link previews
  (Open Graph image `static/og-image.png`), structured data (site search,
  FAQ), `noindex` on private pages and search results, `/robots.txt` and
  `/sitemap.xml` (every unit, lesson, word and verb in both languages).
  `SEO=False` switches all of it off and brings back the earlier page heads
  (follows the system setting until the user picks one)
- Production-ready deployment configuration
- Database migrations for schema management

## Tech Stack

- **Backend**: Python 3, Flask, Flask-SQLAlchemy
- **Frontend**: HTML5, CSS3
- **Database**: SQLAlchemy ORM with Alembic migrations
- **Deployment**: WSGI-compatible (Procfile included for Heroku)

## Prerequisites

- Python 3.7+
- pip

## Installation

1. Clone the repository:
```bash
git clone https://github.com/Andriy-Rudyi/learn-catalan.git
cd learn-catalan
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Initialize the database:
```bash
flask db upgrade
```

5. Run the application:
```bash
python run.py
```

The application will be available at `http://localhost:5000`

## Project Structure

```
learn-catalan/
├── flaskblog/              # Main Flask application package
│   ├── __init__.py        # Application factory
│   ├── config.py          # Config and TestConfig
│   ├── models.py          # User, Post, Comment, Word, UserWord, admin views
│   ├── permissions.py     # Who may edit content
│   ├── main/              # Home, lessons, FAQ, conjugator routes
│   ├── posts/             # Lesson CRUD and comments
│   ├── users/             # Registration, login, account
│   ├── admin/             # Flask-Admin panel
│   ├── errors/            # 403/404/500 handlers
│   ├── conjugation/       # Verb conjugator (see below)
│   │   ├── service.py     # Validation and conjugation
│   │   ├── corrections.py # Patches for verbecc's Catalan data
│   │   ├── compound.py    # Compound tenses (he parlat, vaig parlar)
│   │   ├── reference_ca.py# Reference forms used as the test oracle
│   │   ├── audit.py       # Compares what we serve against the reference
│   │   └── data/ca-corrections.xml
│   ├── grammar/           # Grammar course (see below)
│   │   ├── routes.py      # Unit index and unit pages
│   │   ├── service.py     # Loading and seeding units
│   │   ├── cli.py         # flask grammar ...
│   │   └── data/*.json    # The units themselves
│   ├── vocabulary/        # Dictionary (see below)
│   │   ├── routes.py      # Dictionary and personal word list
│   │   ├── service.py     # Search, CSV import/export
│   │   ├── senses.py      # Meanings of words, kept in step with the translations
│   │   ├── cli.py         # flask vocabulary ...
│   │   └── data/words.csv, data/translations/<lang>.csv
│   ├── translate/         # Translation platform /translate, flask translations ...
│   ├── reader/            # Text page /text: word forms and synonyms (data/ has its own licences)
│   ├── api/               # Open API /api/v1 and the /developers page
│   ├── languages.py       # Languages the dictionary is translated into
│   ├── tests/             # Test suite
│   ├── templates/         # Jinja templates
│   └── static/            # CSS and assets
├── migrations/             # Database migrations
├── run.py                 # Application entry point
├── requirements.txt       # Python dependencies
├── Procfile              # Deployment configuration
├── .gitignore            # Git ignore rules
├── LICENSE               # MIT License
└── README.md             # This file
```

## Conjugator

`/conjugator` conjugates Catalan verbs. The conjugation engine is
[verbecc](https://github.com/bretttolbert/verbecc), wrapped in two layers that
`flaskblog/conjugation/` adds.

**Validation.** verbecc guesses a conjugation template with a machine learning
model whenever a word is not in its verb list, so invented words
(*qwertyuir*) and words from other languages (*hablar*) came back looking like
real Catalan verbs. The model is switched off (`verbecc.config.ml = False`) and
a word must be in the verb list to be conjugated; otherwise the page shows
close matches. Input is normalised first: case, accents, surrounding
punctuation and attached weak pronouns (*rentar-se*) are handled, and phrases
such as *jo parlo* are refused.

**Corrections.** verbecc's Catalan data contains wrong endings, which affected
about 1,700 of its 8,616 verbs. Examples: *saber* conjugated as *sabo, sabs,
sab*; the participles of *moure*, *beure*, *conèixer* and *créixer* came out as
*mouut*, *beuut*, *coneixut*, *creixut*; the future of the whole `perd:re`
group read *perdé* instead of *perdré*; *estar* had the Spanish gerund
*estando*. These are fixed in `flaskblog/conjugation/data/ca-corrections.xml`,
which patches the templates in memory (a template fix repairs every verb using
it) and re-points verbs filed under the wrong template. Compound tenses
(*he parlat*, *vaig parlar*), which verbecc does not generate for Catalan, are
built from the corrected participle.

Every correction is covered by reference forms in
`flaskblog/conjugation/reference_ca.py`, written from grammar references rather
than from verbecc's output. The audit compares the two:

```bash
flask conjugation audit          # must report no differences
flask conjugation check saber    # print one verb's conjugation
```

The audit also runs as part of the test suite, so a regression in the data
fails the build. Verbs covered by the reference are marked «перевірено» on the
page; the rest are served as verbecc has them and marked accordingly.

## Dictionary

`/dictionary` is a Catalan-Ukrainian dictionary with search (Catalan term,
Ukrainian translation or example), filters by topic, level and part of speech,
and CSV export. Verb entries link to their conjugation.

Logged-in users keep a personal list at `/my-dictionary`: words saved from the
shared dictionary or typed in themselves, each with a note, a
learning/known status and CSV export.

The dictionary is filled by the site editor, in the admin panel, through
`/dictionary/new`, by uploading a CSV at `/dictionary/import`, or from the
command line:

```bash
flask vocabulary seed              # load the bundled starter vocabulary
flask vocabulary import words.csv  # import your own CSV
flask vocabulary import words.csv --update   # also refresh existing entries
flask vocabulary export words.csv  # write the dictionary out
flask vocabulary stats             # counts by topic and level
```

CSV columns: `term, translation, part_of_speech, gender, pronunciation, topic,
level, example_ca, example_uk, notes, translation_en, example_en, notes_en`,
and for any other language `translation_<code>`, `example_<code>`,
`notes_<code>` (`translation_fr`, `example_fr`…). Only `term` and a translation
in some language are required. Importing is idempotent: a term already in the
dictionary is skipped unless `--update` is given, and then only the columns in
the file change.

### Many languages

A dictionary word is one Catalan entry (`Word`: term, part of speech, level,
topic, Catalan example, regional marks) plus one `WordTranslation` row per
language (translation, example in that language, notes). Adding a language
therefore needs no database change:

1. Add it to `flaskblog/languages.py` if it is not there (French, Italian,
   Spanish, Polish, German, Arabic and Chinese already are).
2. Put its translations in `flaskblog/vocabulary/data/translations/<code>.csv`
   with the columns `term, translation, example, notes` and optionally
   `reviewed` (rows matched to `data/words.csv` by `term`), or import a CSV with `translation_<code>`
   columns, or add them one by one in the admin panel (Word Translation).
3. `flask vocabulary seed --update` loads them; Render runs it on every deploy.

Where a word has no translation in the language asked for, English and then
Ukrainian are shown.

Every translation has a `reviewed` flag. A file or CSV column `reviewed`
(`reviewed_<code>` in an import) set to `0` marks drafts such as machine
translations: the word page then says the translation has not been checked
yet, and the API returns `"reviewed": false`. Translators mark it checked on
`/translate` (or the editor in the admin panel, Word Translation). The
interface itself (menus, buttons) is translated separately, see
[Languages](#languages).

A translation changed on the site (the editor's form, the admin panel, a CSV
upload, `/translate`) is marked `edited`: from then on the bundled files no
longer overwrite it when `flask vocabulary seed --update` runs on deploy. To
keep such work in the repository, `flask translations export <code>` writes
it back into `data/translations/<code>.csv`.

The bundled dictionary lives in `flaskblog/vocabulary/data/words.csv` (the
Catalan side) and `data/translations/uk.csv`, `data/translations/en.csv`,
`data/translations/fr.csv`. It holds 3,572 words
across 21 topics (including Catalan cuisine and traditions), mostly A1-B1, including 2,210 verbs and C1 vocabulary such as discourse connectors and idioms. Verbs were chosen by how often their infinitive occurs in a Catalan subtitle corpus (OpenSubtitles 2018 frequency list), so the conjugator has a translation for nearly every verb people actually look up. The conjugator looks a
verb up here to show its translation, so dictionary entries double as the
conjugator's glossary.

### Meanings

Translations are attached to the meanings of a word (`WordSense`, with one
`SenseTranslation` per language) rather than to the word: “tocar” has two
meanings, *touch* and *play (an instrument)*, and each language translates
each of them. English is the pivot: the meanings of a word are the parts of
its English translation separated by `;`. The word page lists them
numbered, the API returns them as `senses`, and `/translate` asks for them
one by one with the English next to each.

Each language also keeps its meanings joined with `;` in
`WordTranslation.translation`: that is what the CSV files, imports and the
editor's form use, and `flaskblog/vocabulary/senses.py` keeps the two in
step. A language with fewer parts than English is spread over the meanings
(French “batterie” is both *battery* and *drums*, shown with the English to
tell them apart); one with more puts the extra parts into the last meaning.

Rolling back:

- `SENSES=False` shows one translation line per language on the word pages
  and leaves `senses` out of the API. Nothing in the database changes, so
  `SENSES=True` brings the meanings back.
- Removing the feature: revert the commit and run `flask db downgrade`
  (migration `c7e2d4a9f1b6`). The joined strings were kept all along, so
  no translation is lost; tested on PostgreSQL 16 and SQLite.
- `flask vocabulary senses` rebuilds every word's meanings from the strings.

### Transcription

`flaskblog/vocabulary/transcription.py` gives each word a transcription in
Central Catalan, in the broad IPA of the pronunciation lessons, and the same
in Ukrainian letters (ə for the neutral vowel, an acute on the stressed vowel).
It comes from, most reliable first:

1. the editor's "Вимова" field (`Word.pronunciation`);
2. the words transcribed in the pronunciation lessons;
3. our own reading rules: stress, vowel reduction (a/e → ə, o → u), voiced s,
   ll/ny/tx/tg/ix, silent final r/t/c in the usual places.

The rules agree with every lesson word except whether a stressed e/o is open
or closed, which the spelling does not show. Such words, and a final -r
outside verbs, are marked `certain: false` and shown with ≈. Nothing is taken
from Wiktionary or other dictionaries, so there is no licence to follow.

- The word page shows it under the term; `/text` shows it for the clicked word.
- The API gives `transcription: {ipa, cyrillic, certain, source}`.
- `TRANSCRIPTION=False` goes back to showing only what an editor typed in;
  nothing is stored, so there is nothing to migrate.

### Regional words

The course teaches Central Catalan. Words that are Valencian, Balearic,
North-Western… or archaic (*eixir*, *acotxar*, *tindre*) carry a mark with the
Central equivalent (*sortir*); the dictionary can filter them out, and the
conjugator warns about them. The marks live in
`flaskblog/vocabulary/data/varieties.json` and are copied onto the words by
`flask vocabulary seed`.

To verify them against Wiktionary (public MediaWiki API of the English and
Catalan editions, which label senses *Valencia*, *Balearic*, *valencià*…):

```bash
flask vocabulary check-dialects                 # report only → dialect_report.csv
flask vocabulary check-dialects --apply         # write confirmed and new marks
flask vocabulary check-dialects --verbs --apply # also every conjugator verb
```

The check also runs by itself every Monday in GitHub Actions
(`.github/workflows/check-dialects.yml`, or *Actions → Check regional words →
Run workflow*): when the marks change it opens a pull request into `dev`, and
merging it redeploys the site. For that, enable *Settings → Actions → General →
Workflow permissions → Allow GitHub Actions to create and approve pull
requests*.

Run locally, it needs internet access and takes a few minutes (50 words per request, one
request per second). A word without regional labels is *not* treated as
proof that it is Central (normative dictionaries list many Valencian words
without a mark), so existing marks are only ever confirmed or added, never
removed automatically; the report lists the ones Wiktionary did not confirm.

## Open API

The dictionary and the conjugator are open for other sites and apps:
read-only JSON at `/api/v1`, no key, CORS open to every origin. A page for
developers is at `/developers`, the OpenAPI description at
`/api/v1/openapi.json`.

| Endpoint | What it returns |
| --- | --- |
| `GET /api/v1/words?q=&lang=&topic=&level=&part_of_speech=&variety=&page=&per_page=` | Search, 20 words a page (up to 100) |
| `GET /api/v1/words/<slug or term>?lang=fr,uk` | One word with its translations |
| `GET /api/v1/conjugations/<verb>` | Every tense and mood, forms by person (`1s`…`3p`) |
| `GET /api/v1/verbs?q=par` | Infinitives for autocomplete |
| `GET /api/v1/languages` | Translation languages and word counts |
| `GET /api/v1/dictionary.csv` | The whole dictionary, every language |

Each client address may make `API_RATE_LIMIT` requests a minute (120 by
default, `0` for no limit); beyond that the answer is 429 with `Retry-After`.
The limit is counted per server process. Errors are
`{"error": {"code", "message"}}`. The code is in `flaskblog/api/`.

## Translation platform

`/translate` (linked at the bottom of the menu as “Help translate”) is the
site's own translation tool, in the same database. For every language in
`flaskblog/languages.py` it shows how much of the dictionary and of the
interface is translated and checked, and has three pages:

- **Dictionary**: each word as a card, every meaning with its English and
  Ukrainian, plus the example and notes; filters for what needs work, no
  translation, drafts, suggestions; search.
- **Interface**: the strings of `flaskblog/i18n`, with the Ukrainian source
  and the English. A string saved here overrides the catalogue file at once.
- **History**: every change with the text before and after, and an undo
  button.

Who does what:

- Anyone logged in **suggests** a translation. It waits under the field,
  visible to everyone, so nobody translates the same thing twice.
- A **translator** of a language (granted in the admin panel, Translator, or
  `flask translations grant <username> <code>`, `*` for every language)
  saves directly, accepts or rejects suggestions and marks drafts such as
  machine translations as checked. The editor (`ADMIN_USERNAME`) is a
  translator of every language. Without any translators, every suggestion
  goes through the editor.
- A save is refused if someone else changed the same field after the page
  was opened; the message shows their text.

Checks: a meaning may not contain `;` (it separates meanings); an interface
string must keep the `{placeholders}` and HTML tags of the original, so a
translation can neither break a page nor add markup to it.

`flask translations export <code>` writes a language back into the project:
the dictionary into `vocabulary/data/translations/<code>.csv`, the interface
into `flaskblog/i18n/<code>.py`. A new interface language also has to be
added to `LANGUAGES` in `flaskblog/i18n/__init__.py` to appear in the
language menu.

## Text page

`/text` (“Text” in the menu) takes a pasted Catalan text and makes every word
clickable. A click shows:

- what the word is: the infinitive with mood, tense and person for a verb form
  (`convingueren` → *convenir*, simple past, 3rd plural), the singular and
  masculine for a noun or adjective (`boniques` → *bonic*), after taking off
  punctuation, an elided article (`l'home`) and clitics (`fes-ho`, `dona'm`);
- its translation from the dictionary, with links to the word and the
  conjugator and a button to add it to “My dictionary”;
- synonyms from the Softcatalà thesaurus put into the same form: conjugated
  into the same slot for verbs (*acordaren*, *pactaren*), plural and feminine
  for nouns and adjectives. Hovering one previews it in the sentence; a
  click replaces the word. Every replacement goes into a history you can
  go back through. The word before decides whether noun or verb readings
  come first (“les obres” / “ells obren”).

The text and its history stay in the visitor's browser. The page asks the
server one word at a time (`/text/word?w=&prev=`). Verb forms come from
the conjugator's own data (verbecc with this project's corrections): the
forms of the verbs that start with the same three letters are built when
first needed, and forms that start differently from their infinitive
(*vaig*, *sóc*, *puc*) are indexed once per process, which takes a couple of
seconds on the first click. The approach, the plural rule and the list of
singular candidates come from [ReeeWriter](https://github.com/neuronids/reeewriter)
(MIT); the data is in `flaskblog/reader/data/` (see its `SOURCES.md`).
`READER=False` removes the page and its menu item.

## Reading

`/reading` is a small library of whole works in Catalan, read in the same
way as `/text`: every word of the text can be clicked for its form,
translation, transcription and synonyms (the panel does not replace words
here: the text is the author's).

- The first work is Shakespeare's *Othello*, in full, in a new Catalan
  translation made for this site from the English play text (public
  domain). Only the play itself was translated: no notes or other
  translations were used.
- The second is Jack London's novel *Martin Eden* (1909), also in full and
  in a new translation made for this site, from a scan of the 1916 printing
  (public domain). The scan's OCR text was corrected by hand; a few
  passages it had mixed up beyond reading were rebuilt. The English is kept
  beside the translation, paragraph for paragraph, in
  `martin-eden/original/en/`, so the novel can later be translated into
  other languages; the site does not load it.
- A work is a folder in `flaskblog/reader/data/works/` with `work.json`
  (title, author, level, kind, characters). A play has one file per scene,
  `a{act}s{scene}.json`; a novel (`"kind": "novel"`) one file per chapter,
  `c{NN}.json` (see `flaskblog/reader/works.py` for the formats). Adding a
  work needs no code or migration.
- `/reading/<work>` is the contents page; `/reading/<work>/<act>/<scene>` a
  scene of a play and `/reading/<work>/<chapter>` a chapter of a novel, with
  links to the previous and next one. All are in the sitemap.
- `READING=False` removes the section and its menu item (so does
  `READER=False`).
- The dictionary covers the play: its words that were missing (1,313:
  everyday words, function words such as "el", "de", "meu", and the play's
  literary vocabulary) were added with Ukrainian, English and French
  translations. Each entry was written, then checked by a second,
  independent pass; anything either pass was unsure about was left out.
  A new part of speech, "article", is used for "el".

## Translator

`/translator` translates between Catalan and Ukrainian, English or French
with the site's own engine (`flaskblog/translator/engine.py`), built to get
better as it is used:

1. **Translation memory.** A sentence that people have translated comes out
   exactly as they translated it: the dictionary's example sentences, the
   grammar course's examples, and every correction approved on the site
   (table `translation_memory`). A close sentence from the memory is shown
   next to the result.
2. **Word by word.** Anything else is glossed: the dictionary's fixed
   expressions, contractions (del, al), articles as the target language uses
   them, clitics (l', d', -ho), "va" + infinitive and "ha" + participle, and
   the reader's analysis of forms (decidiren → decidir). It is marked as an
   approximate translation; words the dictionary lacks are highlighted.
3. **Corrections.** Anyone logged in can suggest a better translation of a
   sentence. A translator of that language (the same role as on
   `/translate`) approves it on `/translator/review`, or it goes straight in
   when they wrote it. From then on the sentence is translated from memory.

The Catalan side of every translation can be clicked word by word (the
`/text` panel), listened to, and the last 20 translations stay in the
browser. `TRANSLATOR=False` removes the page and its menu item; migration
`d5a8c3e1f907` adds the table (downgrade drops it).

## Grammar course

`/grammar` is a grammar course laid out like Raymond Murphy's grammar books:
each numbered unit holds a short explanation with examples and exercises whose
answers can be revealed. The course is written in Ukrainian about Catalan
grammar; only the format is borrowed.

Units live in `flaskblog/grammar/data/*.json`, one file per batch, each unit
holding `number`, `title`, `section`, `level`, `summary`, `explanation` (HTML),
`examples` and `exercises`. Loading is idempotent, so editing a file and
re-running the seed updates the units in place:

```bash
flask grammar seed     # load or refresh the units
flask grammar stats    # units, exercises and sections
```

The editor can also change a unit in the admin panel.

## Languages

Interface strings are written in Ukrainian and wrapped in `_()` (templates and
Python); English and French text live in `flaskblog/i18n/en.py` and
`flaskblog/i18n/fr.py`, keyed by the Ukrainian original. A string missing from a
catalogue falls back to English. The language comes from `?lang=en|uk|fr`
(stored in a cookie), then the cookie, then the browser's `Accept-Language`,
and otherwise `DEFAULT_LANGUAGE` (environment variable, `en` by default).

English is the main language of the site: whatever has no version in the
language asked for (a course, an FAQ answer, a dictionary translation) is
shown in English.

Course content has separate English versions:

| Content | Ukrainian | English |
| --- | --- | --- |
| Grammar units | `flaskblog/grammar/data/units_*.json` | `flaskblog/grammar/data/en/units_*.json` (loaded by `flask grammar seed` into `GrammarUnit.translations`) |
| Phonetics | `flaskblog/phonetics/data/lessons.json` | `flaskblog/phonetics/data/lessons_en.json` |
| Dictionary | `flaskblog/vocabulary/data/translations/uk.csv` | `flaskblog/vocabulary/data/translations/en.csv` (one file per language, see [Many languages](#many-languages)) |

French has no course versions yet; its dictionary file
`data/translations/fr.csv` is a machine translation marked `reviewed=0`.

`flaskblog/tests/test_i18n.py` renders the English pages and fails if any of
them still shows Cyrillic, so a missing translation is caught by the tests.

## Testing

```bash
python -m unittest discover -s flaskblog/tests -t .
```

The suite uses an in-memory SQLite database through `TestConfig`, so it never
touches the real one. It covers the conjugator (reference forms, validation,
corrections, routes), the dictionary (models, import/export, search, pages,
permissions), the grammar course (data consistency, seeding, pages) and the
existing models, forms and routes.

## Usage

### Development

Start the development server:
```bash
python run.py
```

### Database Migrations

Create a new migration after model changes:
```bash
flask db migrate -m "Description of changes"
flask db upgrade
```

### Production Deployment

Use a production WSGI server like Gunicorn:
```bash
gunicorn run:app
```

For Heroku deployment, the `Procfile` is already configured.

## Configuration

Environment variables can be set in a `.env` file or system environment:

```bash
FLASK_APP=run.py
DEBUG_MODE=False
SECRET_KEY=your-secret-key-here
DATABASE_PUBLIC_URL=postgresql://user:password@localhost/learn_catalan
EMAIL_USER=your-smtp-user
EMAIL_PASS=your-smtp-password
ADMIN_USERNAME=Andriy        # the account allowed to edit content
SHOW_FAQ=True                # set to False to hide the FAQ page
DESIGN=modern                # set to classic to bring back the earlier look for everyone
SEO=True                     # set to False to switch off the search engine tags, robots.txt and sitemap.xml
SITE_URL=https://example.com # public address for canonical links and the sitemap (optional)
API_RATE_LIMIT=120           # open API requests a minute per client address; 0 = no limit
SENSES=True                  # set to False to show one translation line per language instead of meanings
READER=True                  # set to False to take away the /text page
READING=True                 # set to False to take away the /reading section
TRANSLATOR=True              # set to False to take away the /translator page
TRANSCRIPTION=True           # set to False to show only pronunciations typed in by an editor
TEST_DATABASE_URI=           # optional, tests default to in-memory SQLite
```

The application reads the database URL from `DATABASE_PUBLIC_URL`, falling
back to `DATABASE_URL` (the name Render, Heroku and Fly use). An old-style
`postgres://` URL is converted to `postgresql://` automatically
(see `flaskblog/config.py`).

**Local development needs no variables at all.** Without a database URL the
app uses `instance/learn_catalan.db` (SQLite) and a random secret key made
fresh on every start (so you are logged out after a restart),
and `wsgi.py` lets `flask` find the app without `FLASK_APP`:

```bash
flask db upgrade
flask vocabulary seed --update
flask grammar seed
python run.py
```

On a hosting platform (Render, Railway, Heroku, Fly) these fallbacks are
switched off, so a missing `DATABASE_URL` or `SECRET_KEY` stops the app
instead of silently using a throwaway database.

## Database

The application uses SQLAlchemy as the ORM with Alembic for migrations. Database schema is version-controlled in the `migrations/` directory.

To reset the database:
```bash
flask db downgrade base
flask db upgrade
```

## Deployment

The app needs Python 3.11 (pinned in `.python-version`), a PostgreSQL
database and these environment variables: `SECRET_KEY`,
`DATABASE_PUBLIC_URL` or `DATABASE_URL`, `DEBUG_MODE=False`, and optionally
`EMAIL_USER` / `EMAIL_PASS` for password reset mails.

After every deploy run the migrations and the idempotent seeds:

```bash
flask db upgrade
flask vocabulary seed --update
flask grammar seed
```

The `Procfile` starts the site with `gunicorn run:app` and declares the same
steps as a `release` command (Heroku runs it automatically).

### Free: Render + Neon

Both have free plans with no time limit. The site sleeps after 15 minutes
without visitors and takes about a minute to wake up.

1. **Database**: sign up at [neon.tech](https://neon.tech), create a project
   (region: Frankfurt) and copy the connection string
   (`postgresql://…neon.tech/neondb?sslmode=require…`).
2. **Site**: sign up at [render.com](https://render.com) with GitHub, then
   *New → Blueprint* → choose this repository. Render reads `render.yaml`
   and asks only for `DATABASE_URL`: paste the Neon string.
3. Wait for the first build: it installs the packages, runs the migrations and
   loads the dictionary and the course. The site appears at
   `https://learn-catalan.onrender.com` (or similar).

Every merge into `dev` redeploys automatically.

### Railway

1. New Project → Deploy from GitHub repo → choose this repository, branch `dev`.
2. Add a PostgreSQL service; Railway exposes `DATABASE_PUBLIC_URL`
   (reference it from the web service's variables).
3. Set `SECRET_KEY`, `FLASK_APP=run.py`, `DEBUG_MODE=False`.
4. Settings → Deploy → *Pre-deploy command*:
   `flask db upgrade && flask vocabulary seed --update && flask grammar seed`.
5. Settings → Networking → *Generate domain* (or attach your own domain).

### Render

1. New → PostgreSQL (copy the *Internal Database URL*).
2. New → Web Service from the repository; build command
   `pip install -r requirements.txt`, start command `gunicorn run:app`.
3. Environment: `DATABASE_URL`, `SECRET_KEY`, `FLASK_APP=run.py`,
   `DEBUG_MODE=False`, `PYTHON_VERSION=3.11.9`.
4. Pre-deploy command (paid plans) or a one-off shell:
   `flask db upgrade && flask vocabulary seed --update && flask grammar seed`.

### Heroku / Fly.io

```bash
heroku create your-app-name
heroku addons:create heroku-postgresql
heroku config:set SECRET_KEY=... FLASK_APP=run.py DEBUG_MODE=False
git push heroku dev:main          # the release step runs migrations and seeds
```

Fly.io works the same way with `fly launch` (it detects the Procfile) and
`fly postgres create`.

## Development Workflow

### VS Code

Workspace configuration is included in `.vscode/`. Recommended extensions:
- Python
- Flask Snippets
- SQLAlchemy

### Code Style

Follow PEP 8 standards. Consider using:
- `black` for code formatting
- `flake8` for linting
- `mypy` for type checking

## Contributing

1. Create a feature branch: `git checkout -b feature/description`
2. Make your changes and commit: `git commit -m 'Add feature'`
3. Push to the branch: `git push origin feature/description`
4. Open a pull request

## Troubleshooting

**ImportError when running the app:**
```bash
# Ensure virtual environment is activated
source venv/bin/activate
pip install -r requirements.txt
```

**Database migration errors:**
```bash
# Check migration history
flask db current
flask db history

# Rollback if needed
flask db downgrade -1
```

**Port already in use:**
```bash
# Change the port in run.py or use
python run.py --port 5001
```

## License

The code is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

### Data sources and licences

Most of the content was written for this project: the dictionary
(`words.csv`, the translations), the grammar units, the pronunciation lessons
and the FAQ. The French dictionary translations are a machine translation
made with an AI model and are marked `reviewed=0` until a translator checks
them. Third-party material:

| Data | Source | Licence | What it asks for |
| --- | --- | --- | --- |
| Regional labels (`vocabulary/data/varieties.json`, entries with source `wiktionary-en` / `wiktionary-ca`) | Wiktionary, English and Catalan editions, via `flask vocabulary check-dialects` | CC BY-SA 4.0 | Credit Wiktionary; the labels stay under CC BY-SA |
| Which words and verbs are included | Chosen by frequency with FrequencyWords (Hermit Dave), from OpenSubtitles 2018 (OPUS); the list itself is not in the project | CC BY-SA 4.0 | Nothing is copied; credited as a courtesy |
| Synonyms on `/text` (`reader/data/thesaurus.txt`) | sinonims-cat thesaurus by Jaume Ortolà Font and contributors, Softcatalà, in the compact form made by ReeeWriter | CC BY 4.0 | Credit Softcatalà (done on the page, `/developers` and the API index); commercial use allowed |
| Plural exceptions (`reader/data/plural_exceptions.json`) | 154 pairs found against Softcatalà's catalan-dict-tools, via ReeeWriter | LGPL-2.1 | Keep the file under LGPL; not for a book sold under other terms |
| Plural rule and singular candidates (`reader/morphology.py`) | Ported from ReeeWriter (neuronids) | MIT | Copyright notice kept in the file |
| Verb conjugations | The verbecc library (LGPL-3.0); its Catalan data comes from Verbiste (Pierre Sarrazin) and catverbs (Neil Roberts) | GPL-2.0-or-later | `conjugation/data/ca-corrections.xml` changes that data, so it is under GPL-2.0-or-later too (see its header). A bulk export of conjugations would have to be GPL as well |
| Bootstrap, Bootstrap Icons (the search icon in the CSS) | CDN / inlined | MIT | — |

The same list is on `/developers` and in the API index (`/api/v1/`,
`sources`). No licence has been declared for the dictionary itself yet;
nothing in it stands in the way of an open one such as CC BY-SA 4.0.

## Author

[Andriy Rudyi](https://github.com/Andriy-Rudyi)

## Support

For issues, questions, or suggestions, open an issue on GitHub.

---

Last updated: October 2026
