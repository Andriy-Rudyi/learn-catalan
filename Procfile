web: gunicorn run:app
release: FLASK_APP=run.py flask db upgrade && FLASK_APP=run.py flask vocabulary seed && FLASK_APP=run.py flask grammar seed
