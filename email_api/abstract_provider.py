"""This module contains everything related to providers.

Third party provider's API implementation/definition must use the below.

The role of an AProvider subclass is just to take in core data struct,
shape and massage it to fit its specific API format.

It should not do any IOs or fancy side effects, the
`email_api.providers_manager.Manager` takes care of that.

"""

from enum import Enum
from abc import ABC, abstractproperty, abstractmethod


class InvalidProviderError(Exception):
    """Raise if you detect an invalid provider at runtime.

    Could happen if it's untested, because we have no way to enforce
    the return types with ABC or others (AFAIK)

    """
    pass


class DataFormat(Enum):
    """ Enum values map to `requests.request()` arguments for sending data.

    Use `form` for POST form parameters
    Use `query` for URL query parameters
    User `json` for... json
    """
    form = 'data'
    json = 'json'
    query = 'params'


class HttpMethod(Enum):
    """ Enum values map to HTTP Methods.
    """
    post = 'POST'
    get = 'GET'


class AProvider(ABC):
    """Third party providers must implement this abstract class

    Proper return types for subclasses are (to be) validated in the unit test

    `self._user` and `self._key` should be used in the subclass for auth.
    `config` is saved under `self._config` if need be
    """

    nickname = None
    """The name to be used for this provider in the configuration, and
    for the webhooks mapping.

    Subclasses should have their own
    """
    def __init__(self, config=None):
        """
        Args:
            config (Optionnal[dict]): Application config, should contain
              api username and key/password
        """
        self._user = ''
        self._key = ''
        self._config = config

        if not self.nickname:
            raise InvalidProviderError("Provider must define a nickname")
        if not config:
            return

        conf = config.get(self.nickname)
        self._user = conf.get('user', self._user)
        self._key = conf.get('key', self._key)

    @abstractproperty
    def auth(self):
        """Return None if the API does not use/need HTTP auth.

        Returns:
            tuple: containing (username:str, password:str) for http auth
        """
        pass

    @abstractproperty
    def send_url(self):
        """Returns the HTTP method and the API url to use for sending
        emails.

        Returns:
            A tuple containing, the http method to use and the url::

                (provider.HttpMethod, str)

        """
        pass

    @abstractmethod
    def email_to_data(self, email):
        """Format core data to API specific data format.

        This method takes an `email_api.message.Email` class and turns it
        into a (dict): adding API specific extra parameters, changing the
        structure, key names, etc... If need be.

        The provider sub class must also be aware of the email recipient
        data structure: `email_api.message.Recipient` and adapt it to its need.

        Files are currently not implemented in `email_api.message` but
        they should also be wrapped in a class such as `Attachment`

        Args:
            email (email_api.message.Email): The email to be serialized
              to API specific format

        Returns:
            A (tuple) containing the `email_api.provider.DataFormat` to
            use and the email as a (dict)::

                (email_api.provider.DataFormat, dict)

        """
        pass

    def validate(self):
        """Validates subclass implementation.

        This method just makes sure the Subclass is implemented
        properly, not to have random ValueError when unpacking values.

        Note:
            You must call it explicitly. We don't check that the url
            is valid, we delegate to the lib sending the requests.

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
