"""The module containing the Manager that handles the different
providers.

Its role is:
- To construct providers while catching potential errors,
one by one until it succeeds
- To Collect all information from the
provider
- To do the actual I/O by sending http requests

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
    """This class does the actual I/O

    It handles the different providers and provides a facade to send
    emails easily

    """

    def __init__(self, provider_classes, config):
        """
        Note:

        We take Classes as argument and not instances because we might
        need more control over how it's built later, also we'd need to
        instanciate them all beforehand which is more costly than
        creating it only if we need.

        Args:
          provider_classes (list): List of AProvider sub-class (not instances)

        """
        self.config = config
        self.provider_classes = provider_classes


    @staticmethod
    def _create_provider(provider_class, config):
        """ Instanciate and validate the provider

        Raises:
          InvalidProviderError

        Returns:
          AProvider
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
        """ Get the serialize data that need to be sent to the provider API
        Makes sure the types are valid

        Raises:
          InvalidProviderError

        Returns:
          tuple: DataFormat, dict

        """
        try:
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

    def _prep_request(self, email, provider_klass, request_func):
        """ *Pure function*
        Easier for testing, we prepare the request function and return the
        callable, no I/O.  Also serves as depency injection, in case
        we want to ditch/wrap the requests library later

        Args:
          email (email_api.message.Email):
          provider_klass (AProvider): Class (to be instancianted)

          request_func (function): A function pointer with the
             following signature:
             func(auth:tuple, method:str, url:str, json:dict,
                  data:dict, query:dict)

        Returns:
          callable function

        Raises:
          InvalidProviderError

        """
        provider = self._create_provider(provider_klass, self.config)
        format_, http_data = ProvidersManager._get_serialized_data(
            provider, email
        )
        method, url = provider.send_url
        auth = provider.auth
        # Build http request
        if auth: # Add HTTP auth if provider needs it
            request_func = partial(request_func, auth=auth)

        return partial(
            request_func,
            method=method.value,
            url=url,
            # data=http_data or json=.. or params=..
            **{format_.value: http_data}
        )



    def send(self, email):
        """Iterate on provider, gathering necessary data and catching
        potential errors.

        The loop stops as soon as we have sucessful call.

        Args:

          email (email_api.message.Email): The email structure to be
             sent

        Returns:
          bool: True if email was successfully sent
        """
        with requests.session() as sess:
            for klass in self.provider_classes:
                try:
                    # Get the data from the provider
                    req = self._prep_request(email, klass, sess.request)
                    response = req()
                    response.raise_for_status() # We only care about 2XX

                    # Reponse data is useless as it greatly varies
                    # from one provider to another.
                    # E.g sendgrid just replies: 'success'
                    return True

                except (InvalidProviderError,
                        requests.exceptions.MissingSchema):
                    # Failing here means bad coding/config
                    _LOG.error(
                        "%s is an invalid provider class", klass
                    )
                    continue
                except requests.HTTPError as e:
                    # If 4XX most likely because of unsanitized data
                    _LOG.warning(e)
                    continue
                except (requests.Timeout, requests.TooManyRedirects,
                        requests.ConnectionError) as e:
                    _LOG.warning(e)
                    continue

        # if we exit the loop it means no provider successfully worked
        return False

    def handle_callback(self, name, data):
        # Implement webhook callback.
        # Dispatch to providers here and return structured data
        pass
