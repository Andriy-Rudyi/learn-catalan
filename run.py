import os
from flaskblog import create_app

app = create_app()

DEBUG_MODE = os.getenv('DEBUG_MODE') == 'True'

if __name__ == '__main__':
    app.run(DEBUG_MODE)
