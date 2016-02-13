import unittest

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
    But I usually prefer to avoid Mock if I
    can and only use it for side effects related things (I/O, excpetions...)

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
    def f():
        return instance
    return f


class FakeProvider(AProvider):
    def __init__(self,
                 auth=('user', 'pw'),
                 send_url=(HttpMethod.post, 'http://google.fr'),
                 email_data=(DataFormat.form, Email().to_dict())):
        self._auth = auth
        self._send_url = send_url
        self._email_data = email_data

    @property
    def auth(self):
        return self._auth

    @property
    def send_url(self):
        return self._send_url

    def email_to_data(self, email):
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
            #FakeProvider(send_url=(HttpMethod.get, 'google.fr')), # bad url
            FakeProvider(send_url=('x', 'http://google.fr')), # bad method
            FakeProvider(send_url=('http://google.fr', )), # bad url tuple
            FakeProvider(email_data=('blah', {})), # bad data format
            FakeProvider(email_data=('blah',)), # bad data tuple
            #FakeProvider(email_data=(DataFormat.query, {})) # empty dict
        ]

    def test_bad_providers(self):
        self.assertRaises(
            InvalidProviderError,
            ProvidersManager._create_provider,
            InvalidProvider
        )
        for p in self.bad_providers:
            print(p)
            self.assertRaises(
                InvalidProviderError,
                ProvidersManager._prep_request,
                Email(),
                klass(p),
                fake_request_func
            )

    def test_smoke(self):
        req = ProvidersManager._prep_request(
            Email(), FakeProvider, fake_request_func
        )
        req = req()
        #self.assertEquals([], [req.auth])
        #with mock.patch('email_api.providers_manager'
