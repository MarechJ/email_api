"""Concrete Provider for mailgun.

https://documentation.mailgun.com/user_manual.html
"""
from email_api.abstract_provider import (
    AProvider,
    DataFormat,
    HttpMethod
)


class MailgunProvider(AProvider):
    nickname = "mailgun"

    @property
    def send_url(self):
        return (# This could be seeded from the conf But if they
            # change their API we might aswell revisit this class..
            HttpMethod.post,
            'https://api.mailgun.net/v3/\
            sandbox411449faf6304f7db8a5f923277e2437.mailgun.org/messages'
        )

    @property
    def auth(self):
        return self._user, self._key

    def email_to_data(self, email):
        """ Mailgun is quite permissive and does not care about null fields
        So we don't do any filtering
        """
        mail = dict(
            **email.to_dict()
        )
        # Orgnize recipients by type (to,cc,bcc)
        # Store a list of standard email strings such as:
        # {'to':['my name <my@name.com>', 'my@address.com'], 'cc': [...], ...}
        for recp in email.get_recipients():
            mail.setdefault(recp.type_, []).append(str(recp))

        # Remap replyto
        mail['h:Reply-To'] = mail['replyto']
        del mail['replyto'] # Mailgun actually ignores this key otherwise
        mail['from'] = str(email.from_)

        return DataFormat.form, mail
