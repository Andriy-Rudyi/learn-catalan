"""Who may edit the site's content.

The site has a single editor, identified by username.  It was spelled out
in every route that needed it; keeping it in one place means the name can
be changed with an environment variable instead of a code change.
"""

import os

from flask_login import current_user

DEFAULT_ADMIN_USERNAME = 'Andriy'


def admin_username():
    return os.getenv('ADMIN_USERNAME', DEFAULT_ADMIN_USERNAME)


def is_admin(user=None):
    """True when *user* (by default the logged in one) may edit content."""
    user = current_user if user is None else user
    return bool(
        user is not None
        and getattr(user, 'is_authenticated', False)
        and user.username == admin_username()
    )
