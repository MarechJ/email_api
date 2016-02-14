"""Concrete provider implementation

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
        return ( # This could be seeded from the conf But if they
            # change their API we might aswell revisit this class..
            HttpMethod.post,
            'https://api.sendgrid.com/api/mail.send.json'
        )

    @property
    def auth(self):
        return None

    def email_to_data(self, email):
        """Sendgrid is quite permissive and does not care about null fields
        so we don't filter

        """
        mail = dict(
            api_user=self._user,
            api_key=self._key,
            **email.to_dict(),
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
