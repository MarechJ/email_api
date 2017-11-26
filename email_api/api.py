"""Web framework controller/routes.
Bottle: http://bottlepy.org/docs/dev/index.html

The glue is here.

TODO:

- Save the email to persistent storage (SQLAlchemy + sqlite), adding
an ID and status

- Provide GET endpoint to fetch by ID, or ALL with pagination

- Provide a POST /hook/<providername> endpoint (for status update)
that uses the ProvidersManager to handle API specific data and
standardize it, then update Email records status

- Add rate limiting or auth, or both

- Add HATEOAS links in endpoints' return data

"""
import logging
import json
import sys
import re
import os

import bottle
bottle.BaseRequest.MEMFILE_MAX = 1024 * 1024

from bottle import (
    route,
    run,
    request,
    response,
    abort,
    default_app,
    app,
    error
)

from email_api.message import (
    InvalidRecipientError,
    InvalidEmailError,
    build_email,
    build_recipients
)
from email_api.providers_manager import ProvidersManager
from email_api.mailgun_provider import MailgunProvider
from email_api.elasticemail_provider import ElasticEmailProvider
from email_api.config import load_config, valid_config_or_exit, PROVIDERS_KEY

_LOG = logging.getLogger()

# We could load from config
REGISTERED_PROVIDERS = [
    MailgunProvider,
    ElasticEmailProvider
]

PROVIDER_BY_NICK = {
    p.nickname: p for p in REGISTERED_PROVIDERS
}


@error(400)
def error400(err):
    response.content_type = 'application/json'

    return json.dumps({
        "error": str(err.body),
    })


def _order(nicks):
    return [PROVIDER_BY_NICK[n] for n in nicks]


class UnconfiguredRouteError(Exception):
    pass


def get_route(config, email, routing_type=None):
    routes = config['routes']
    if not routing_type:
        return REGISTERED_PROVIDERS

    joined = ';'.join([rec.email for rec in email.get_recipients('to')])

    for rule in routes[routing_type]:
        r = re.compile(rule['regex'])
        res = r.match(joined)
        if res and res.group(0):
            print(res, res.group(0))
            return _order(rule['providers'])

    return _order(routes['default'])


@route('/email', method='post')
def send_email():
    """ Validates and send an email.

    Accepts JSON or url encoded parameters.

    """
    params = request.json or request.params

    recps = {
        'to': params.get('to'),
        'cc': params.get('cc'),
        'bcc': params.get('bcc')
    }
    subject = params.get('subject')
    text = params.get('text')
    html = params.get('html')
    from_ = params.get('from')
    reply_to = params.get('reply_to')
    route = params.get('route')

    try:
        # Init and validate data structures
        recipients = build_recipients(recps)
        email = build_email(recipients, subject, text, html, from_, reply_to)
        # Init Manager with registed providers
        try:
            providers = get_route(app().config, email, route)
            print(providers)
        except Exception as e: # TODO change this
            _LOG.exception("Routing error")
            raise InvalidEmailError
        #
        manager = ProvidersManager(
            providers,
            app().config[PROVIDERS_KEY]
        )
        res, provider = manager.send(email)

    except (InvalidRecipientError, InvalidEmailError) as e:
        _LOG.warning("%s", e)
        abort(400, e)
    print(res.text)
    return {"sent": bool(res), "provider": provider}


def start_app(argv):
    file_path = os.getenv('EMAIL_API_CONFIG')

    config = load_config(file_path)
    valid_config_or_exit(config, REGISTERED_PROVIDERS)

    _app = default_app()
    _app.config.update(config)

    extra = config.get('server_extra') or {}
    # TODO: Configure logger, WSGI server conf
    run(app=_app,
        host=config.get('host', 'localhost'),
        port=config.get('port', 8080),
        server=config.get('server', 'wsgiref'),
        **extra
    )


if __name__ == '__main__':
    start_app(sys.argv)
