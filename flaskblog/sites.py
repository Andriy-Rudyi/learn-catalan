"""One site per language being learnt, all under one domain.

With BASE_DOMAIN set (e.g. ``langwave.app``):

* ``langwave.app`` shows the language picker (templates/sites_picker.html),
  with its own /robots.txt and /sitemap.xml; any other address there goes
  to the same address on the Catalan site;
* ``www.langwave.app`` goes to ``langwave.app``;
* ``catalan.langwave.app`` is the Catalan site, as it is today;
* the other sites in SITES (``english.``, ``french.``, ``german.``) are
  registered but switched off: their addresses answer 404 and the picker
  does not show them until ``enabled`` is True and they have material;
* an unknown subdomain goes to the picker;
* any other host (the old address of the app) goes, path and all, to the
  Catalan site, so old links keep working; localhost is served as the
  Catalan site, for development.

One account works on every site: the session, "remember me" and the
interface language cookies are set for the whole domain (they all share
the database and SECRET_KEY).

Without BASE_DOMAIN nothing of this happens: every host is the Catalan
site, as before.

Site addresses use the English names of the languages, so that they are
not mixed up with the language of the interface (``?lang=en``).
"""

from collections import namedtuple

from flask import abort, current_app, g, redirect, render_template, request, Response
from flask.sessions import SecureCookieSessionInterface

from flaskblog.i18n import lazy_gettext

Site = namedtuple('Site', 'slug code native name enabled')

# Order is the order of the picker. ``code`` is the ISO 639-1 code of the
# language the site teaches; ``name`` is its Ukrainian name (translated).
SITES = (
    Site('catalan', 'ca', 'Català', lazy_gettext('Каталанська'), True),
    Site('english', 'en', 'English', lazy_gettext('Англійська'), False),
    Site('french', 'fr', 'Français', lazy_gettext('Французька'), False),
    Site('german', 'de', 'Deutsch', lazy_gettext('Німецька'), False),
)
BY_SLUG = {site.slug: site for site in SITES}
DEFAULT = BY_SLUG['catalan']

LOCAL_HOSTS = ('localhost', '127.0.0.1', '::1', '[::1]')

# What the root domain answers itself; everything else goes to a site.
_ROOT_PATHS = ('/', '/robots.txt', '/sitemap.xml', '/favicon.ico')


def base_domain(app=None):
    """BASE_DOMAIN without scheme, ``www.`` or dots at the ends, or None."""
    value = (app or current_app).config.get('BASE_DOMAIN') or ''
    value = value.strip().lower().split('://')[-1].strip('/.')
    if value.startswith('www.'):
        value = value[4:]
    return value or None


def enabled_sites():
    return [site for site in SITES if site.enabled]


def _host():
    host = request.host.lower()
    if host.startswith('['):  # IPv6 literal
        return host.split(']')[0] + ']'
    return host.rsplit(':', 1)[0] if ':' in host else host


def _scheme():
    return request.headers.get('X-Forwarded-Proto', request.scheme).split(',')[0].strip()


def _port():
    """``:port`` of the request when it is not the default one (development)."""
    host = request.host
    if host.startswith('['):
        rest = host.split(']', 1)[1]
        return rest if rest.startswith(':') else ''
    return ':' + host.rsplit(':', 1)[1] if ':' in host else ''


def root_url():
    return '{}://{}{}'.format(_scheme(), base_domain(), _port())


def site_url(site=None):
    """Scheme and host of a site, without a trailing slash."""
    site = site or current()
    return '{}://{}.{}{}'.format(_scheme(), site.slug, base_domain(), _port())


def current():
    """The site of this request (the Catalan one without BASE_DOMAIN)."""
    return g.get('site') or DEFAULT


def is_root():
    return bool(g.get('site_root'))


def active():
    """True when the request came in through BASE_DOMAIN."""
    return bool(base_domain()) and bool(g.get('site_host'))


def _target(url):
    return url + request.full_path.rstrip('?') if request.query_string else url + request.path


def _moved(url):
    # 301 keeps search engines' links; 308 also keeps a form's POST.
    return redirect(url, code=301 if request.method in ('GET', 'HEAD') else 308)


def _root_robots():
    return Response('User-agent: *\nAllow: /\n\nSitemap: {}/sitemap.xml\n'.format(root_url()),
                    mimetype='text/plain')


def _root_sitemap():
    urls = [root_url() + '/'] + [site_url(site) + '/' for site in enabled_sites()]
    body = ''.join('<url><loc>{}</loc></url>'.format(url) for url in urls)
    return Response('<?xml version="1.0" encoding="UTF-8"?>\n'
                    '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
                    + body + '</urlset>\n', mimetype='application/xml')


def dispatch():
    """Before every request: find the site from the host."""
    base = base_domain()
    if not base:
        return None
    host = _host()
    static = request.path.startswith((current_app.static_url_path or '/static') + '/')

    if host == base:
        g.site_host = True
        if static:
            return None
        if request.path not in _ROOT_PATHS:
            return _moved(_target(site_url(DEFAULT)))
        g.site_root = True
        if request.path == '/robots.txt':
            return _root_robots()
        if request.path == '/sitemap.xml':
            return _root_sitemap()
        if request.path == '/favicon.ico':
            return current_app.send_static_file('favicon.ico')
        return render_template('sites_picker.html', sites=enabled_sites())

    if host == 'www.' + base:
        return _moved(_target(root_url()))

    if host.endswith('.' + base):
        site = BY_SLUG.get(host[:-len(base) - 1])
        if site is None:
            return redirect(root_url() + '/')
        if not site.enabled:
            abort(404)
        g.site = site
        g.site_host = True
        return None

    if host in LOCAL_HOSTS:
        return None
    return _moved(_target(site_url(DEFAULT)))


def cookie_domain():
    """Domain for the site's own cookies: the whole BASE_DOMAIN, when the
    request came in through it."""
    return base_domain() if active() else None


class _SessionInterface(SecureCookieSessionInterface):
    """The login session cookie, for the whole domain on its sites."""

    def get_cookie_domain(self, app):
        return cookie_domain() or super().get_cookie_domain(app)


def init_app(app):
    if base_domain(app):
        app.session_interface = _SessionInterface()
        # "Remember me" too (Flask-Login reads this when it sets the cookie).
        if not app.config.get('REMEMBER_COOKIE_DOMAIN'):
            app.config['REMEMBER_COOKIE_DOMAIN'] = base_domain(app)

    app.before_request(dispatch)

    @app.context_processor
    def inject_site():
        return {'current_site': current(), 'language_sites': enabled_sites(),
                'site_url': site_url, 'root_url': root_url}
