from flask import Blueprint, render_template

errors = Blueprint('errors', __name__)


def _api_error(status, code, message):
    """JSON instead of a page for addresses under the open API."""
    from flaskblog.api.routes import error, wants_json
    if wants_json():
        response, status = error(status, code, message)
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response, status
    return None


@errors.app_errorhandler(404)
def error_404(error):
    return _api_error(404, 'not-found', 'There is nothing at this address.') or \
        (render_template('errors/404.html'), 404)


@errors.app_errorhandler(403)
def error_403(error):
    return render_template('errors/403.html'), 403


@errors.app_errorhandler(500)
def error_500(error):
    return _api_error(500, 'internal', 'Something went wrong on our side.') or \
        (render_template('errors/500.html'), 500)
