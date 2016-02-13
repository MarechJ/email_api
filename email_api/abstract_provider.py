"""This module contains everything related to providers.
Third party provider API implementation/definition must use the below.
"""

from enum import Enum
from abc import ABC, abstractproperty, abstractmethod


class InvalidProviderError(Exception):
    """Raise if you detect an invalid provider at runtime

    Could happen if it's untested, because we have no way to enforce
    the return types with ABC or others (AFAIK)

    """
    pass


class DataFormat(Enum):
    """ Enum values map to
    requests.request() arguments for sending data

    Use form for POST form parameters
    Use query for URL query parameters
    User JSON for... json
    """
    form = 'data'
    json = 'json'
    query = 'params'


class HttpMethod(Enum):
    """ Enum values map to HTTP Methods
    """
    post = 'POST'
    get = 'GET'


class AProvider(ABC):
    """Third party provider must implement this abstract class

    Return types are not validate in anyway
    """

    @abstractproperty
    def auth(self):
        """
        Return None if the API does not use/need HTTP auth

        Returns:
          tuple: containing (username:str, password:str) for http auth
        """
        pass

    @abstractproperty
    def send_url(self):
        """
        Return the HTTP method and the API url to use for sending
        emails

        Returns:
          tuple: containing (provider.HttpMethod, http_url:str)

        """
        pass

    @abstractmethod
    def email_to_data(self, email):
        """This method takes an `email_api.message.Email` class and turns it
        into a dict, adding API specific extra parameters, changing
        structure, key names, etc... If need be.

        The provider sub class must also be aware of
        `email_api.message.Recipient` and adapt it to its need.

        Files are currently not implemented in email_api.message but
        they should also be wrap in a class such as Attachment

        Return of tuple with the `email_api.provider.DataFormat` to
        user and the email as a dict

        Args:
          email (email_api.message.Email): The email to be serialize
            to API specific format

        Returns:
          tuple: (email_api.provider.DataFormat, dict)

        """
        pass

    def validate(self):
        """This method just makes sure the Subclass is implemented
        properly, not to have random ValueError when unpacking values.

        Note: You must call it explicitly. We don't check that the url
        is valid, we delegate to the lib # sending the requests

        Raises:
          InvalidProviderError

        """
        if self.auth is not None:
            if not isinstance(self.auth, tuple) or len(self.auth) != 2:
                raise InvalidProviderError("Property auth must be a tuple")

        if not isinstance(self.send_url, tuple) or len(self.send_url) != 2:
            raise InvalidProviderError("Property send_url must be a tuple")

        try:
            method, _ = self.send_url
        except ValueError:
            raise InvalidProviderError(
                "send_url must return ({}, {})".format(
                    type(HttpMethod), type(str)
                )
            )

        if not isinstance(method, HttpMethod):
            raise InvalidProviderError(
                "send_url must return ({}, {})".format(
                    type(HttpMethod), type(str)
                )
            )
