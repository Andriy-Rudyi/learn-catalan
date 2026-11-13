web: gunicorn run:app
release: FLASK_APP=run.py flask db upgrade && FLASK_APP=run.py flask vocabulary seed --update && FLASK_APP=run.py flask vocabulary dacco-import && FLASK_APP=run.py flask vocabulary apertium-words && FLASK_APP=run.py flask vocabulary apertium-import && FLASK_APP=run.py flask vocabulary pivot-import && FLASK_APP=run.py flask grammar seed
