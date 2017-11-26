"""Concrete provider implementation for sendgrid

https://sendgrid.com/docs
"""
from email_api.abstract_provider import (
    AProvider,
    HttpMethod,
    DataFormat
)


class ElasticEmailProvider(AProvider):
    nickname = 'elasticemail'

    @property
    def send_url(self):
        return (  # Should come from conf
            HttpMethod.post,
            'https://api.elasticemail.com/v2/email/send'
        )

    @property
    def auth(self):
        return None

    def email_to_data(self, email):
        """onverts an `Email` to a `dict` of parameters specific to sendgrid

        Sendgrid is quite permissive and does not care about null fields
        so we don't filter.

        Args:
          email (class:Email): An Email instance

        Returns:
          tuple::

            (Dataformat.form, dict)

        """
        e = email.to_dict()
        mail = {}
        mail['msgTo'] = ';'.join([r.email for r in email.get_recipients('to')])
        mail['msgCC'] = ';'.join([r.email for r in email.get_recipients('cc')])
        mail['msgBcc'] = ';'.join([r.email for r in email.get_recipients('bcc')])
        mail['from'] = email.from_.email
        mail['fromName'] = email.from_.display_name
        mail['apiKey'] = self._key
        mail['charset'] = 'utf-8'
        mail['bodyText'] = e['text']
        mail['bodyHtml'] = e['html']
        mail['subject'] = e['subject']
        return DataFormat.form, mail

    def is_success(self, response):
        try:
            if response.status_code == 200 and response.json()['success']:
                return True
        except:
            return False

        return False
