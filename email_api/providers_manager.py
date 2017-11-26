"""The module containing the Manager that handles the different
providers.

Its role is:
- To construct provider(s) while catching potential errors
- To Collect all information from the provider
- To do the actual I/O by sending http requests
- To Loop through providers until we successfully send an email

"""

import logging
from functools import partial

import requests

from email_api.abstract_provider import (
    DataFormat,
    InvalidProviderError,
    AProvider
)


_LOG = logging.getLogger()


class ProvidersManager:
    """Handles the different providers and exposes a facade to send
    an email easily.

    This class does the actual I/O.

    """

    def __init__(self, provider_classes, config):
        """
        Note:
           We take Classes as argument and not instances because we might
           need more control over how its built later, also we'd need to
           instanciate them all beforehand which is more costly than
           creating it only if we need.

        Args:
          provider_classes (list[AProvider]): List of
            `email_api.abstract_provider.AProvider` subclasses (!= objects)
          config (dict): Configuration that will be passed to providers

        """
        self.config = config
        self.provider_classes = provider_classes

    @staticmethod
    def _create_provider(provider_class, config):
        """ Instanciate and validate the provider.

        Args:
            provider_class (class:AProvider): An AProvider subclass

        Raises:
            InvalidProviderError: If provider_class is not:
              - Inheriting `AProvider`
              - Successfully passing `AProvider` validation

        Returns:
            AProvider: An AProvider speciliazation instance
        """
        try:
            provider = provider_class(config)
        except TypeError:
            raise InvalidProviderError("Provider must sub-class AProvider")

        if not isinstance(provider, AProvider):
            raise InvalidProviderError("Provider must sub-class AProvider")

        provider.validate()
        return provider

    @staticmethod
    def _get_serialized_data(provider, email):
        """Get the serialized email data that needs to be sent to the provider
        API and returns it.

        Makes sure the types are valid.

        Raises:
          InvalidProviderError: If the provider instance returned bad data
            formats

        Returns:
          tuple::

            (DataFormat, dict)

        """
        try:
            email = provider.fill_in_blanks(email)
            format_, mail_dict = provider.email_to_data(email)
        except ValueError:
            raise InvalidProviderError(
                "Provider.email_to_data must return tuple"
            )

        if not isinstance(format_, DataFormat) or \
           not isinstance(mail_dict, dict):
            raise InvalidProviderError(
                "Provider.email_to_data() returned unexpected types.\
                Must be ({}, {})".format(type(DataFormat), type(dict))
            )

        return format_, mail_dict

    def _prep_request(self, email, provider, request_func):
        """Prepare the request call by putting all the pieces together, and
        returns a (callable).


        This is a pure function (no I/O) which makes it easier to
        test.  Also serves as depency injection, in case we want to
        ditch/wrap the `requests` library later.

        Args:
          email (class:Email):
          provider_klass (class:AProvider): Class (to be instancianted)
          request_func (callable): A function pointer with the
             following signature::

               func(auth:tuple, method:str, url:str, json:dict,
                    data:dict, query:dict)

        Returns:
          callable: The request function with all the required parameters

        Raises:
          InvalidProviderError

        """
        format_, http_data = ProvidersManager._get_serialized_data(
            provider, email
        )
        method, url = provider.send_url
        auth = provider.auth
        # Build http request
        if auth:  # Add HTTP auth if provider needs it
            request_func = partial(request_func, auth=auth)

        return partial(
            request_func,
            method=method.value,
            url=url,
            # Below is: data=http_data or json=.. or params=..
            **{format_.value: http_data}
        )

    def send(self, email):
        """Send an email.

        Iterates on provider classes, contructing instances, gathering
        necessary data and catching potential errors.
        The loop stops as soon as we have sucessful call.

        Args:

          email (class:Email): The email structure to be
            sent

        Returns:
          bool: True if email was successfully sent

        """
        with requests.session() as sess:
            for klass in self.provider_classes:
                try:
                    # Prepare the request using the current provider
                    provider = self._create_provider(klass, self.config)
                    req = self._prep_request(email, provider, sess.request)
                    response = req()
                    if not provider.is_success(response):
                        _LOG.error(
                            "Failed to send with %s moving on",
                            klass.nickname
                        )
                        continue
                    # Reponse data is useless as it greatly varies
                    # from one provider to another.
                    # E.g sendgrid just replies: 'success'
                    # To keep track of email statuses webhooks need to be setup
                    return response, klass.nickname

                except (InvalidProviderError,
                        requests.exceptions.MissingSchema):
                    # Failing here means bad coding/config
                    _LOG.exception(
                        "%s is an invalid provider class", klass
                    )
                    continue
                except requests.HTTPError as e:
                    # If 4XX most likely because of unsanitized or bad
                    # data format
                    _LOG.warning(e)
                    continue
                except (requests.Timeout, requests.TooManyRedirects,
                        requests.ConnectionError) as e:
                    _LOG.warning(e)
                    continue

        # if we exit the loop it means no provider successfully worked
        return None, None

    def handle_callback(self, name, data):
        # Implement webhook callbacks here.
        # Dispatch to providers here and return structured data
        pass
