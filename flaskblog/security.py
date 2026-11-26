"""Protection that every page gets.

* **Cookies.** The session and "remember me" cookies are HttpOnly and
  SameSite=Lax everywhere, and Secure (sent only over HTTPS) on the host
  (``config.is_hosted``) or with ``SECURE_COOKIES=True``.
* **Headers.** Every response says: do not guess content types
  (X-Content-Type-Options), the site may be framed only by itself
  (X-Frame-Options and CSP frame-ancestors), no plugins (object-src),
  no other base address (base-uri), send only the origin to other sites
  (Referrer-Policy), no camera or location, the microphone only for the
  site itself (the monologue trainer records). Over HTTPS also
  Strict-Transport-Security, so browsers keep to HTTPS. The policy does not
  restrict scripts: the pages use inline scripts and a CDN, and limiting
  them would need every page reworked.
* **Login attempts.** After ``LOGIN_MAX_FAILURES`` failed logins in
  ``LOGIN_WINDOW`` seconds from one address or for one email, logging in
  waits until the window has passed (``login_blocked`` / ``login_failed``
  / ``login_succeeded``). Kept in memory, per server process: enough to
  stop guessing passwords at speed.
* **Redirects after login** only go to addresses on the site
  (``safe_next``).
"""

import threading
import time
from urllib.parse import urlparse

from flaskblog.config import is_hosted

_lock = threading.Lock()
_failures = {}  # key -> [time, time...]


def _settings(app):
    return (int(app.config.get('LOGIN_MAX_FAILURES', 5)), int(app.config.get('LOGIN_WINDOW', 900)))


def _keys(address, email):
    keys = ['ip:' + (address or '?')]
    if email:
        keys.append('email:' + email.strip().lower())
    return keys


def _recent(key, now, window):
    times = [moment for moment in _failures.get(key, ()) if now - moment < window]
    if times:
        _failures[key] = times
    else:
        _failures.pop(key, None)
    return times


def login_blocked(app, address, email):
    """Seconds to wait before the next login attempt, or 0."""
    limit, window = _settings(app)
    now = time.time()
    wait = 0
    with _lock:
        for key in _keys(address, email):
            times = _recent(key, now, window)
            if len(times) >= limit:
                wait = max(wait, int(window - (now - times[-limit])) + 1)
    return wait


def login_failed(app, address, email):
    _limit, window = _settings(app)
    now = time.time()
    with _lock:
        for key in _keys(address, email):
            _recent(key, now, window)
            _failures.setdefault(key, []).append(now)
        if len(_failures) > 10000:  # keep memory bounded
            for key in list(_failures)[:5000]:
                _failures.pop(key, None)


def login_succeeded(address, email):
    with _lock:
        for key in _keys(address, email):
            _failures.pop(key, None)


def reset_attempts():
    with _lock:
        _failures.clear()


def safe_next(target):
    """*target* when it is an address on this site ("/grammar"), else None."""
    if not target:
        return None
    target = target.replace('\\', '/')
    parsed = urlparse(target)
    if parsed.scheme or parsed.netloc or not target.startswith('/') or target.startswith('//'):
        return None
    return target


def _headers(response):
    from flask import request

    headers = response.headers
    headers.setdefault('X-Content-Type-Options', 'nosniff')
    headers.setdefault('X-Frame-Options', 'SAMEORIGIN')
    headers.setdefault('Referrer-Policy', 'strict-origin-when-cross-origin')
    headers.setdefault('Permissions-Policy', 'camera=(), geolocation=(), microphone=(self)')
    headers.setdefault('Content-Security-Policy', "frame-ancestors 'self'; object-src 'none'; base-uri 'self'")
    forwarded = request.headers.get('X-Forwarded-Proto', request.scheme).split(',')[0].strip()
    if forwarded == 'https':
        headers.setdefault('Strict-Transport-Security', 'max-age=31536000; includeSubDomains')
    return response


def init_app(app):
    secure = is_hosted() or str(app.config.get('SECURE_COOKIES', '')).lower() == 'true'
    app.config.setdefault('SESSION_COOKIE_HTTPONLY', True)
    app.config.setdefault('REMEMBER_COOKIE_HTTPONLY', True)
    app.config['SESSION_COOKIE_SAMESITE'] = app.config.get('SESSION_COOKIE_SAMESITE') or 'Lax'
    app.config['REMEMBER_COOKIE_SAMESITE'] = app.config.get('REMEMBER_COOKIE_SAMESITE') or 'Lax'
    if secure:
        app.config['SESSION_COOKIE_SECURE'] = True
        app.config['REMEMBER_COOKIE_SECURE'] = True
    app.after_request(_headers)
