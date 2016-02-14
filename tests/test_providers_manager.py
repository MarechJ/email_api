import unittest
from unittest import mock

import requests

from email_api.providers_manager import ProvidersManager
from email_api.abstract_provider import (
    AProvider,
    HttpMethod,
    DataFormat,
    InvalidProviderError
)
from email_api.message import Email



class fake_request_func:
    """Could use Mock assert_called_with.

    But I usually prefer to avoid Mock it if I can and only use it for
    side effects related things (I/O, excpetions...)

    """
    def __init__(self, method, url, auth=None,
                 json=None, data=None, params=None):
        self.method = method
        self.url = url
        self.auth = auth
        self.json = json
        self.data = data
        self.params = params


class InvalidProvider:
    pass

def klass(instance):
    "fake class constructor"
    def f(*args, **kwargs):
        return instance
    return f


class FakeProvider(AProvider):
    def __init__(self,
                 auth=('user', 'pw'),
                 send_url=(HttpMethod.post, 'http://google.fr'),
                 email_data=(DataFormat.form, Email().to_dict()),
                 raises=None):
        self._auth = auth
        self._send_url = send_url
        self._email_data = email_data
        self._raises = raises

    @property
    def auth(self):
        return self._auth

    @property
    def send_url(self):
        return self._send_url

    def email_to_data(self, email):
        if self._raises:
            raise self._raises
        return self._email_data

    def __str__(self):
        return '{},{},{}'.format(
            self.auth, self._send_url, self._email_data
        )


class TestProvidersManager(unittest.TestCase):

    def setUp(self):
        self.good = FakeProvider()

        self.bad_providers = [
            FakeProvider(auth=''), # bad auth
            FakeProvider(auth=('user',)), # bad auth
            FakeProvider(send_url=('x', 'http://google.fr')), # bad method
            FakeProvider(send_url=('http://google.fr', )), # bad url tuple
            FakeProvider(email_data=('blah', {})), # bad data format
            FakeProvider(email_data=('blah',)), # bad data tuple
        ]

    def _get_manager(self, provider=None, config=None):
        return ProvidersManager(provider, config)

    def test_bad_providers(self):
        self.assertRaises(
            InvalidProviderError,
            ProvidersManager._create_provider,
            InvalidProvider,
            {}
        )
        for p in self.bad_providers:
            self.assertRaises(
                InvalidProviderError,
                self._get_manager()._prep_request,
                Email(),
                klass(p),
                fake_request_func
            )

    def test_smoke(self):
        req = self._get_manager()._prep_request(
            Email(), klass(FakeProvider()), fake_request_func
        )
        req = req()
        prov = FakeProvider()
        method, url = prov._send_url
        # Check if the request paramters match those of the provider
        self.assertEqual([req.method, req.url], [method.value, url])
        self.assertEqual(req.auth, prov.auth)
        format_, data = prov._email_data
        self.assertEqual(getattr(req, format_.value), data)

    def test_fallack(self):
        exceptions = [
            requests.HTTPError,
            requests.Timeout,
            requests.TooManyRedirects,
            requests.ConnectionError,
            requests.exceptions.MissingSchema,
            InvalidProviderError
        ]

        with mock.patch( # Stop I/O
            'email_api.providers_manager.requests.session',
            auto_spec=True
        ):
            for excp in exceptions:
                providers = [klass(FakeProvider(raises=excp))] * 2
                mng = self._get_manager(providers)
                assert mng.send(Email()) == False
                mng = self._get_manager(providers + [klass(self.good)])
                assert mng.send(Email()) == True
