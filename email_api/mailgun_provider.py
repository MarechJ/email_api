"""Concrete Provider for mailgun.

https://documentation.mailgun.com/user_manual.html
"""
from email_api.abstract_provider import (
    AProvider,
    DataFormat,
    HttpMethod
)


class MailgunProvider(AProvider):

    @property
    def send_url(self):
        return (
            HttpMethod.post,
            'https://api.mailgun.net/v3/\
            sandbox411449faf6304f7db8a5f923277e2437.mailgun.org/messages'
        )

    @property
    def auth(self):
        return "api", "" # add key

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

        mail['from'] = str(email.from_)

        return DataFormat.form, mail
