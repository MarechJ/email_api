"""Web framework controller/routes
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
from email_api.sendgrid_provider import SendgridProvider
from email_api.mailgun_provider import MailgunProvider
from email_api.config import load_config, valid_config_or_exit, PROVIDERS_KEY

_LOG = logging.getLogger()

# We could load from config
REGISTERED_PROVIDERS = [
    SendgridProvider,
    MailgunProvider
]


@error(400)
def error400(err):
    response.content_type = 'application/json'

    return json.dumps({
        "error": str(err.body),
    })


@route('/email', method='post')
def send_email():
    """ Validates and send an email.

    Accepts JSON or url encoded parameters.

    """
    params = request.json or request.params

    recps = {
        'to': params.get('to', None),
        'cc': params.get('cc', None),
        'bcc': params.get('bcc', None)
    }
    subject = params.get('subject', None)
    body = params.get('body', None)
    from_ = params.get('from', None)
    reply_to = params.get('reply_to', None)

    try:
        # Init and validate data structures
        recipients = build_recipients(recps)
        email = build_email(recipients, subject, body, from_, reply_to)
        # Init Manager with registed providers
        manager = ProvidersManager(
            REGISTERED_PROVIDERS,
            app().config[PROVIDERS_KEY]
        )
        sent = manager.send(email)

    except (InvalidRecipientError, InvalidEmailError) as e:
        _LOG.warning("%s", e)
        abort(400, e)

    return {"sent": sent}


def start_app(argv):
    file_path = None
    if len(argv) >= 2:
        file_path = argv[1]

    config = load_config(file_path)
    valid_config_or_exit(config, REGISTERED_PROVIDERS)

    _app = default_app()
    _app.config.update(config)

    # TODO: Configure logger, WSGI server conf
    run(app=_app,
        host=config.get('host', 'localhost'),
        port=config.get('port', 8080))


if __name__ == '__main__':
    start_app(sys.argv)
