"""Concrete provider implementation for sendgrid

https://sendgrid.com/docs
"""
from email_api.abstract_provider import (
    AProvider,
    HttpMethod,
    DataFormat
)


class SendgridProvider(AProvider):
    nickname = 'sendgrid'

    @property
    def send_url(self):
        return (  # Should come from conf
            HttpMethod.post,
            'https://api.sendgrid.com/api/mail.send.json'
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
        mail = dict(
            api_user=self._user,
            api_key=self._key,
            **{k: v for k, v in email.to_dict()
               if k in ['replyto', 'text', 'html', 'files']}
        )

        for type_ in ['to', 'cc', 'bcc']:
            for recp in email.get_recipients(type_):
                mail.setdefault(type_, []).append(recp.email)
                # Send grid does not allow a mix of empty and
                # populated display name (for some reason).
                # So instead of discarding them all (in case one is
                # empty) we default to the address
                name = recp.display_name or recp.email
                mail.setdefault("{}name".format(type_), []).append(name)

        mail['from'] = email.from_.email
        mail['fromname'] = email.from_.display_name

        return DataFormat.form, mail
