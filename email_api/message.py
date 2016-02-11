"""This module contains the main data structures related to email As
well as utils function to build them

"""
from email import utils
from collections import namedtuple

# External dependency for validating email address
# Easily replacable
from email_validator import validate_email, EmailNotValidError


class InvalidRecipientError(Exception):
    """ Raise email address is improper
    """
    pass


class InvalidEmailError(Exception):
    """Raise if the email does not meet minimal requirements
    """
    pass


class Recipient(namedtuple('Recipient', ['email', 'display_name'])):
    """ Structure for a recipient
    Provides a validation method and utils
    """

    @classmethod
    def from_string(cls, email_string):
        """Builds instance from standard email string representation: E.g:

        <Display Name actual@address.com>

        Args:
            email_string (str): The email address as string

        """

        name, address = utils.parseaddr(email_string)

        return cls(address, name)

    def __str__(self):
        if self.display_name:
            return "{} <{}>".format(self.display_name, self.email)
        return self.email

    def validate(self):
        """ Checks if structure is valid

        Raises:
            InvalidRecipientError
        """
        if self.email is None:
            raise InvalidRecipientError("Email must be set")

        try:
            validate_email(self.email, check_deliverability=False)
        except EmailNotValidError as e:
            # We re-raise with custom exception not to create dep on
            # the lib
            raise InvalidRecipientError(
                "Invalid email address format {}".format(self.email)
            ) from e

        return True


class Email:
    """ A minimal email structure
    """
    default_subject = '(no subject)'
    default_body = ''

    def __init__(self):
        self._to = []
        self._subject = self.default_subject
        self._body = ''

    @property
    def subject(self):
        return self._subject

    @property
    def to(self):
        return self._to

    @property
    def body(self):
        return self._body

    def add_recipient(self, recipient):
        if not isinstance(recipient, Recipient):
            raise TypeError("Invalid Recipient")
        self._to.append(recipient)

    def add_recipients(self, recipients):
        for recp in recipients:
            self.add_recipient(recp)

    def set_subject(self, subject):
        if not subject:
            subject = self.default_subject

        self._subject = str(subject)

    def set_body(self, body):
        if not body:
            body = self.default_body

        self._body = str(body)

    def validate(self):
        if not len(self._to):
            raise InvalidEmailError("Email must have at least one Recipient")
        # RFC soft limit
        if len(self._subject) > 78:
            raise InvalidEmailError(
                "Subject must be less that 79 characters"
            )

        return True


def build_recipients(to):
    """ Facade for building recipient struct and validate
    Args:
        to (list): list or recipients as "address@domain.com"
    """
    recipients = []

    for s in to:
        recp = Recipient.from_string(s)
        recp.validate()

    return recipients


def build_email(recipients, subject, body):
    """Facade to construct an email and validate

    Args:
       recipients (list): List of `Recipient`
       subject (str): '' or None will default to (no subject)
       body (str): Can be empty or None
    """

    email = Email()
    email.add_recipients(recipients)
    email.set_subject(subject)
    email.set_body(body)

    email.validate()

    return email
