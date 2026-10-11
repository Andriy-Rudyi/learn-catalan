# learn-catalan

A Flask-based blog platform for learning and teaching the Catalan language.

## Overview

**learn-catalan** is a blog-style language learning platform built with Flask and SQLAlchemy. It provides a clean, database-backed environment where Catalan language learners can access blog posts, lessons, vocabulary articles, and cultural content organized chronologically and by topic.

## Features

- Blog posts and articles for Catalan language learning
- Structured lessons organized by topic
- **Verb conjugator** with validated input and corrected conjugation data
  (see [Conjugator](#conjugator))
- **Catalan–Ukrainian dictionary** with search, filters, CSV import/export and
  a personal word list for every user (see [Dictionary](#dictionary))
- **Grammar course** of numbered units, each with an explanation, examples and
  exercises with answers (see [Grammar course](#grammar-course))
- Database-driven content management
- Chronological and category-based post navigation
- Responsive interface that works on phones, with a light/dark theme switch
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
│   │   ├── cli.py         # flask vocabulary ...
│   │   └── data/seed_words.csv
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

`/dictionary` is a Catalan–Ukrainian dictionary with search (Catalan term,
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
level, example_ca, example_uk, notes`. Only `term` and `translation` are
required. Importing is idempotent: a term already in the dictionary is skipped
unless `--update` is given.

The starter file `flaskblog/vocabulary/data/seed_words.csv` holds 3,228 words
across 21 topics (including Catalan cuisine and traditions), mostly A1–B1, including 2,210 verbs and C1 vocabulary such as discourse connectors and idioms. Verbs were chosen by how often their infinitive occurs in a Catalan subtitle corpus (OpenSubtitles 2018 frequency list), so the conjugator has a translation for nearly every verb people actually look up. The conjugator looks a
verb up here to show its translation, so dictionary entries double as the
conjugator's glossary.

## Grammar course

`/grammar` is a grammar course laid out like Raymond Murphy's grammar books:
each numbered unit holds a short explanation with examples and exercises whose
answers can be revealed. The course is written in Ukrainian about Catalan
grammar; only the format is borrowed.

Units live in `flaskblog/grammar/data/*.json` — one file per batch, each unit
holding `number`, `title`, `section`, `level`, `summary`, `explanation` (HTML),
`examples` and `exercises`. Loading is idempotent, so editing a file and
re-running the seed updates the units in place:

```bash
flask grammar seed     # load or refresh the units
flask grammar stats    # units, exercises and sections
```

The editor can also change a unit in the admin panel.

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
SHOW_FAQ=False               # set to True to bring back the FAQ page
TEST_DATABASE_URI=           # optional, tests default to in-memory SQLite
```

The application reads the database URL from `DATABASE_PUBLIC_URL`, falling
back to `DATABASE_URL` (the name Render, Heroku and Fly use). An old-style
`postgres://` URL is converted to `postgresql://` automatically
(see `flaskblog/config.py`).

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

### Railway (recommended)

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

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Author

[Andriy Rudyi](https://github.com/Andriy-Rudyi)

## Support

For issues, questions, or suggestions, open an issue on GitHub.

---

Last updated: October 2026
