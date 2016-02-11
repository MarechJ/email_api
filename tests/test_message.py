import unittest

from email_api.message import Email, Recipient, InvalidEmailError, InvalidRecipientError


class TestRecipient(unittest.TestCase):

    def setUp(self):
        self.bad_emails = [
            '',
            None,
            '\0\0\0\0a@blah.com',
            'a@gmail',
            '\xff'
        ]
        self.valid_emails = [
            'julien.marechal35@gmail.com',
            'a@b.us',
            '\xff@abroad.rus'
        ]
        self.display_names = [
            'Bonjour blah',
            'foo bar',
            None
        ]

    def test_bad_email_recipient(self):
        for e in self.bad_emails:
            r = Recipient(e, None)
            self.assertRaises(InvalidRecipientError, r.validate)

    def test_valid_email_recipient(self):
        for e in self.valid_emails:
            r = Recipient(e, None)
            self.assertEqual(r.email, e)
            self.assertEqual(r.validate(), True)

    def test_smoke(self):
        for e in self.valid_emails:
            for n in self.display_names:
                r = Recipient(e, n)
                self.assertEqual([r.email, r.display_name], [e, n])


class TestEmail(unittest.TestCase):

    def setUp(self):
        self.bad_recipients = [
            None,
            [],
            1,
            object(),
            'blah'
        ]
        self.recipients = [
            Recipient('me@blah.com', 'My Name')
        ]
        self.bad_subject = [
            'a' * 90
        ]
        self.subject = [
            'bonjour',
            'a'
        ]
        self.bodies = [
            None,
            '',
            'I talk a lot' * 42
        ]

    def get_new_mail(self, *args, **kwargs):
        return Email(*args, **kwargs)

    def test_default_subject(self):
        email = self.get_new_mail()
        email.set_subject('')
        self.assertEqual(email.subject, Email.default_subject)
        email.set_subject(None)
        self.assertEqual(email.subject, Email.default_subject)

    def test_bad_recipient_type(self):
        email = self.get_new_mail()

        for r in self.bad_recipients:
            self.assertRaises(TypeError, email.add_recipient, r)
        self.assertRaises(TypeError, email.add_recipients, self.bad_recipients)

    def test_invalid_email(self):
        email = self.get_new_mail()

        self.assertRaises(InvalidEmailError, email.validate)

        for subj in self.bad_subject:
            email = self.get_new_mail()
            email.add_recipients(self.recipients)
            email.set_subject(subj)
            self.assertRaises(InvalidEmailError, email.validate)

    def test_smoke_email(self):
        email = self.get_new_mail()
        email.add_recipient(self.recipients[0])
        for s in self.subject:
            for b in self.bodies:
                email.set_subject(s)
                email.set_body(b)
                if not b:
                    b = email.default_body
                self.assertEqual([email.subject, email.body], [s, b])
                self.assertEqual(email.validate(), True)
