# learn-catalan

A Flask-based blog platform for learning and teaching the Catalan language.

## Overview

**learn-catalan** is a blog-style language learning platform built with Flask and SQLAlchemy. It provides a clean, database-backed environment where Catalan language learners can access blog posts, lessons, vocabulary articles, and cultural content organized chronologically and by topic.

## Features

- Blog posts and articles for Catalan language learning
- Structured lessons organized by topic
- Database-driven content management
- Chronological and category-based post navigation
- User-friendly web interface
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
├── flaskblog/              # Main Flask blog application package
│   ├── __init__.py        # Flask app initialization
│   ├── models.py          # Blog post and user models
│   ├── routes.py          # Blog routes (posts, categories, etc.)
│   └── templates/         # HTML blog templates
│       └── static/        # CSS, JavaScript, assets
├── migrations/             # Database migrations
├── run.py                 # Application entry point
├── requirements.txt       # Python dependencies
├── Procfile              # Deployment configuration
├── .gitignore            # Git ignore rules
├── LICENSE               # MIT License
└── README.md             # This file
```

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
FLASK_ENV=production
FLASK_APP=run.py
DATABASE_URL=postgresql://user:password@localhost/learn_catalan
SECRET_KEY=your-secret-key-here
```

## Database

The application uses SQLAlchemy as the ORM with Alembic for migrations. Database schema is version-controlled in the `migrations/` directory.

To reset the database:
```bash
flask db downgrade base
flask db upgrade
```

## Deployment

### Heroku

```bash
heroku create your-app-name
git push heroku dev:main
heroku run flask db upgrade
```

### Docker

Create a `Dockerfile` for containerized deployment. Ensure the Flask app is properly configured for the container environment.

### Other Platforms

1. Ensure Python and pip are installed
2. Install dependencies: `pip install -r requirements.txt`
3. Run migrations: `flask db upgrade`
4. Start with Gunicorn or similar WSGI server

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

Last updated: March 2026
