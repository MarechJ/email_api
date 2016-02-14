"""This module contains the main data structures related to email and
its components. As well as utils functions to build them.

The web framework and the third party providers should be aware of this
core data structure, but not the other way around (to avoid coupling)

"""
import logging
import socket
from email import utils
from collections import namedtuple

# External dependency for validating email address
# Easily replacable
from email_validator import validate_email, EmailNotValidError

_LOG = logging.getLogger()


class InvalidRecipientError(Exception):
    """ Raise if the email address is improper
    """
    pass


class InvalidEmailError(Exception):
    """Raise if the email does not meet minimal requirements
    """
    pass


class Recipient(namedtuple('Recipient', ['email', 'display_name', 'type_'])):
    """ Structure for a recipient
    Provides a validation method and utils
    """

    @classmethod
    def from_string(cls, email_string, type_):
        """Builds instance from standard email string representation: E.g:

        "Display Name <actual@address.com>"

        Args:
            email_string (str): The email address as string
            type (str): One of to, cc, bcc, from
        """

        name, address = utils.parseaddr(email_string)

        return cls(address, name, type_)

    def __str__(self):
        if self.display_name:
            return '{} <{}>'.format(self.display_name, self.email)
        return self.email

    @staticmethod
    def check_email(email):
        try:
            validate_email(email, check_deliverability=False)
        except EmailNotValidError as e:
            # We re-raise with custom exception not to create dep on
            # the lib
            raise InvalidRecipientError(
                'Invalid email address format "{}"'.format(email)
            ) from e


    def validate(self):
        """ Checks if structure is valid

        Raises:
            InvalidRecipientError
        """
        if self.email is None:
            raise InvalidRecipientError('Email must be set')
        if self.type_ not in {'to', 'bcc', 'cc', 'from'}:
            raise InvalidRecipientError('Invalid recipient type')

        self.check_email(self.email)

        return True


class Email:
    """A minimal email structure.

    Enforces the 'From' recipient to be set appropriatly or defaults
    to hostname.
    Adds a default in case of empty subject

    Note: We disable two pylint warnings because it does not
    understand the setters & getters properly

    """
    default_subject = '(no subject)'
    default_from = "noreply@{}".format(socket.gethostname())

    def __init__(self, **kwargs):
        """
        Args:
          subject (str): Optionnal, Less that 79 chars
          replyto (str): Optionnal, email address (validity not enforced)
          text (str): Optionnal, text/plain email body
          html (str): Optionnal, text/html email body
          files (Attachment): Optionnal, not implemented
        """
        self._recipients = []
        self.from_ = kwargs.get(
            'from_',
            Recipient.from_string(Email.default_from, 'from')
        )
        self.subject = kwargs.get('subject', None)
        self.replyto = kwargs.get('replyto', None)
        self.text = kwargs.get('text', None)
        self.html = kwargs.get('html', None)
        self.files = kwargs.get('files', None)

    @property
    def from_(self):
        return self.__from

    @from_.setter
    def from_(self, recipient):
        """ Set the 'from' recipients

        Args:
          recipient (Recipient)

        Raises:
          TypeError: if arg is not `Recipient
          ValueError: If Recipient.type_ is not 'from'

        """
        self._check_recipient(recipient)
        if recipient.type_ != 'from':
            raise ValueError("Invalid Recipient.type_ must be 'from'")
        self.__from = recipient # pylint: disable=W0201

    @property
    def subject(self):
        return self.__subject or Email.default_subject

    @subject.setter
    def subject(self, subject):
        self.__subject = subject # pylint: disable=W0201

    def get_recipients(self, type_=None):
        """
        Args:
          type_ (str): Optionnal, if you want to filter by (to, cc...)

        Returns:
          list: list of `Recipients`
        """
        if not type_:
            return self._recipients
        return filter(lambda r: r.type_ == type_, self._recipients)

    def _check_recipient(self, recipient):
        if not isinstance(recipient, Recipient):
            raise TypeError("Invalid Recipient")
        return self

    def add_recipient(self, recipient):
        """ Append a recipient
        Args:
          recipient (Recipient): Only the `type()` is checked

        Raises:
          TypeError: If arg is not a `Recipient`
        """
        self._check_recipient(recipient)
        self._recipients.append(recipient)

    def add_recipients(self, recipients):
        """ Append a list or recipients
        Args:
          recipients (list): List of recipient

        Raises:
          TypeError: If arg is not a `Recipient`

        """
        for recp in recipients:
            self.add_recipient(recp)

    def to_dict(self):
        """Most providers follow the same name convention than the one we use.
        This method avoids a bit of boilerplate code in the providers' mapping.

        We leave out the recipients and the From, as the format often diverge

        """

        common_keys = {'replyto', 'text', 'html', 'files'}

        # build dict, ignoring None values if add_nones is False
        new_dict = {k: v for k, v in self.__dict__.items() if k in common_keys}
        new_dict['subject'] = self.subject
        # Most provider refuse to send a mail without html, but I
        # think it should be allowed
        if not self.text and not self.html:
            new_dict['text'] = ' '

        return new_dict

    def validate(self):
        if not len(self._recipients):
            raise InvalidEmailError("Email must have at least one Recipient")

        # RFC soft limit
        if len(self.subject) > 78:
            raise InvalidEmailError(
                "Subject must be less that 79 characters"
            )

        return True


def build_recipients(recp_dict):
    """Convenience function for building recipient struct and validate

    Args:
      recp_dict (dict): Containing type as key (to, cc, bcc), and
          email string or list of string as value, None is ignored

    """

    recipients = []
    for k, v in recp_dict.items():
        if not isinstance(v, (list, tuple, set)):
            v = [v]
        for email in v:
            if email is None:
                continue
            recp = Recipient.from_string(email, k)
            recp.validate()
            recipients.append(recp)

    return recipients


def build_email(recipients, subject, body, from_=None, replyto=None):
    """ Convenience function to construct an email and validate

    Args:
       recipients (list): List of `Recipient`
       subject (str): '' or None will default to (no subject)
       body (str): Can be empty or None. The body of the email (text/plain) only
       from_ (str): Optionnal, must be a valid recipient string
       reply_to (str): Optionnal, must be a valid email

    Raises:
       InvalidEmailError
       InvalidRecipientError
    """
    email = Email()
    try:
        email.add_recipients(recipients)
    except TypeError as e: # If a value is not `Recipient`
        # This is most likely a programming error
        _LOG.exception(e)
        raise InvalidRecipientError("Invalid recipent") from e

    email.subject = subject
    email.text = body
    if from_:
        from_ = Recipient.from_string(from_, 'from')
        from_.validate()
        email.from_ = from_

    if replyto:
        # Reply_to is not really a Recipient so we just check email
        # validity
        Recipient.check_email(replyto)
        email.replyto = replyto

    email.validate()

    return email
