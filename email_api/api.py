""" Web framework controller/routes
The glue is here.
"""
import logging

from bottle import route, run, request, abort

from email_api.message import (
    InvalidRecipientError,
    InvalidEmailError,
    build_email,
    build_recipients
)
from email_api.providers_manager import ProvidersManager
from email_api.sendgrid_provider import SendgridProvider
from email_api.mailgun_provider import MailgunProvider

_LOG = logging.getLogger()

# This could be done more dynamically, from config
# with dynamic imports
REGISTERED_PROVIDERS = [
    SendgridProvider,
    MailgunProvider
]


@route('/email', method='post')
def send_email():
    """ Validate and send an email.

    Accepts JSON or url encoded parameters
    """
    params = request.json or request.params

    recps = {
        'to': params.get('to', None),
        'cc': params.get('cc', None),
        'bcc': params.get('bcc', None)
    }
    subject = params.get('subject', None)
    body = params.get('body', None)

    print(recps, subject, body)
    try:
        recipients = build_recipients(recps)
        email = build_email(recipients, subject, body)
        manager = ProvidersManager(REGISTERED_PROVIDERS)
        sent = manager.send(email)

    except (InvalidRecipientError, InvalidEmailError) as e:
        _LOG.warning("%s", e)
        abort(400, e)

    return {"sent": sent}


if __name__ == '__main__':
    run(host='localhost', port=8080)
