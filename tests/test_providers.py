import unittest

from email_api.abstract_provider import AProvider
from email_api.message import (
    build_recipients,
    Email,
    Recipient
)
from email_api.mailgun_provider import MailgunProvider
from email_api.sendgrid_provider import SendgridProvider
from email_api.api import REGISTERED_PROVIDERS


class TestProviders(unittest.TestCase):

    def setUp(self):
        self.registered_providers = REGISTERED_PROVIDERS

        self.recps = build_recipients({
            'to': "a b <a@b.com>",
            'cc': ["c d <c@d.com>", "g@blah.com", "           h@space.com"],
            'bcc': "hey <hey@hey.com"  # should pass
        })
        self.from_ = Recipient.from_string("unittest <noreply@unitest", 'from')

        complete = Email(
            subject="a",
            text='hey',
            html="<p>hey</p>",
            replyto="a@b.com"
        )
        complete.add_recipients(self.recps)
        complete.from_ = self.from_

        self.emails = [
            Email(),
            complete
        ]
        self.key_config = {'user': 'me', 'key': 'blah'}

    def test_smoke(self):
        assert len(self.registered_providers), \
            "NO REGISTERED THIRD PARTY PROVIDERS"

        for prov in self.registered_providers:
            assert prov.nickname and len(prov.nickname)
            inst = prov({prov.nickname: self.key_config})
            assert isinstance(inst, AProvider), str(prov)
            inst.validate()

    def test_mailgun_serialize(self):
        """ Testing mailgun's specific format
        """
        nick = MailgunProvider.nickname
        user, key = MailgunProvider({nick: self.key_config}).auth

        assert len(user) and len(key), "No auth provided"
        assert user == self.key_config['user'] and \
            key == self.key_config['key'], "Auth does not match"

        for email in self.emails:
            _, data = MailgunProvider().email_to_data(email)
            self.assertEqual(data['h:Reply-To'], email.replyto)

            for type_ in ['to', 'cc', 'bcc']:
                self.assertEqual(
                    data.get(type_, []),
                    [str(r) for r in email.get_recipients(type_)]
                )

            self.assertEqual(data['from'], str(email.from_))

    def test_sendgrid_serialize(self):
        """ Testing sendgrid's specific format
        """
        nick = SendgridProvider.nickname
        conf = {nick: self.key_config}

        for email in self.emails:
            _, data = SendgridProvider(conf).email_to_data(email)

            assert len(data['api_user']) and len(data['api_key']), \
                "No auth provided"

            for type_ in ['to', 'cc', 'bcc']:
                self.assertEqual(
                    data.get(type_, []),
                    [r.email for r in email.get_recipients(type_)]
                )
                name_key = '{}name'.format(type_)
                self.assertEqual(
                    data.get(name_key, []),
                    [r.display_name or r.email
                     for r in email.get_recipients(type_)]
                )
                # Sendmail refuses to send if to and toname don't have
                # same length. Same goes for cc, bcc
                assert len(data.get(type_, [])) == len(data.get(name_key, []))

            self.assertEqual(data['from'], email.from_.email)
            self.assertEqual(data['fromname'], email.from_.display_name)
