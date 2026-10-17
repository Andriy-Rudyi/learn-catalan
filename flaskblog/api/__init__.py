"""Open read-only API for the dictionary and the conjugator (/api/v1).

Other sites and apps may use it freely: JSON over HTTPS, no key, CORS open
to every origin. Each client IP gets API_RATE_LIMIT requests a minute
(0 switches the limit off). The human-readable description is /developers,
the machine-readable one /api/v1/openapi.json.

Answers do not depend on the visitor's interface language: a word comes
with all its translations, or with the languages asked for in ?lang=.
"""

from flaskblog.api.routes import api, init_app  # noqa: F401
