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


_LOG = logging.getLogger()


@route('/email', method='post')
def send_email():
    """ Validate and send an email.

    Accepts JSON or url encoded parameters
    """
    params = request.json or request.params

    to = params.get('to', None)
    subject = params.get('subject', None)
    body = params.get('body', None)

    print(to, subject, body)
    try:
        if not isinstance(to, list):
            to = [to]
        recipients = build_recipients(to)
        build_email(recipients, subject, body)

    except (InvalidRecipientError, InvalidEmailError) as e:
        _LOG.warning("%s", e)
        abort(400, e)

    return 'ok'


if __name__ == '__main__':
    run(host='localhost', port=8080)
