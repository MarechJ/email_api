"""It's questionnable whether or not the app should start without a
config, but it makes it much simpler to run it 'out of the
box' for now.

My API Keys are cyphered with a passphrase, not to push them 'in
clear' on Github. Probably not the most advanced security, but it
should keep script-kiddies away.

You can add you own user/pasword credential in the config.yaml
template at the root of the repo

Specify the path with argv:
E.g from the root of the repo:

python -m email_api.api config.yaml

"""
import logging
from getpass import getpass
from pathlib import Path

import yaml
from simplecrypt import decrypt, DecryptionException

_LOG = logging.getLogger()
PROVIDERS_KEY = "providers"

DEFAULT_CONF = {
    'host': 'localhost',
    'port': 8080,
    PROVIDERS_KEY: {
        'sendgrid': {
            'user': 'api_client',
            'key': b'sc\x00\x02\xbf\xa1\xa9Pn\xbd\xa9\xcfM\x95\xa9=2\x04\x13\xf6\x8b`\x91\x99\x81\xe5\x1b\x08\xc9\x14uU\x97FY\x04\xbd\xb7"\xdc\x1c\x98\xe89\xd8jF\xbe-x3\xbd\xafj\xee\xa2Z^\t\x07\xb1\xe6\x9a\xf1\x15\x0e\x1a\xec}\xda}\xae\xf83\xf1\xc99\xd2\x13'  # pylint: disable=C0301
        },
        'mailgun': {
            'user': 'api',
            'key': b"sc\x00\x02\xd6\xf0w)\xf7vy\x1c\x05\x10\xc1G6\xb1\x84A6\x1esa`\x9bL|\xe1jz\xd5J'\xd6\xe1:\xd2\x87a[a\x85\x81\xd8\xc1\xa8JXs_\xc1\xb7E\xea0h\xd4\xc0\xcc\x808\xda\x1b\x92\x86\x95e\xda\xc3\x99i\xedt\x07\xe9i\xf0D\xc2`D\xc8\xad$6\x10\x92\x1cM\x82\x87y\xf1\xd6\x1cK\xea|v\xb7\x9d\xf6\x15"  # pylint: disable=C0301
        }
    }
}


def _exit_if_no_providers(config):
    if PROVIDERS_KEY not in config:
        _LOG.critical(
            'The configuration must have a "%s" section. Exiting',
            PROVIDERS_KEY
        )
        exit(1)


def load_config(path):
    if path and Path(path).exists():
        try:
            with open(path, 'r') as conf:
                return yaml.load(conf.read())
        except yaml.parser.ParserError:
            _LOG.error("Invalid YAML file: %s. Exiting", path)
            exit(1)

    # Fallback on default conf
    _LOG.info(
        "No configuration found at: %s. Loading default...",
        path
    )
    _LOG.info(
        "You need to input your password to decypher providers API Key"
    )
    _exit_if_no_providers(DEFAULT_CONF)

    enc_key = getpass("Passphrase: ")  # I/O: prompt for passphrase
    # Below we loop thourgh the providers config and decrypt the api keys
    # It's kind of an hack so that we can push a 0 config app to github
    for _, prov_data in DEFAULT_CONF[PROVIDERS_KEY].items():
        for k, v in prov_data.items():
            if k == 'key':
                try:
                    clear = decrypt(enc_key, v)
                    if clear == prov_data[k]:
                        raise DecryptionException
                    prov_data[k] = clear.decode('utf-8')
                except (DecryptionException, UnicodeDecodeError) as e:
                    _LOG.critical(
                        "Invalid password. Can't decrypt api keys. %s", e
                    )
                    _LOG.info(
                        "You can provide your own by using a config file."
                    )
                    exit(1)

    return DEFAULT_CONF


def valid_config_or_exit(config, providers):
    _exit_if_no_providers(config)
    conf = config[PROVIDERS_KEY]

    for prov in providers:
        # Basically, if the provider is not found in the conf
        # or the user/key is missing or empty
        if prov.nickname not in conf \
           or not {'user', 'key'} <= conf[prov.nickname].keys() \
           or not conf[prov.nickname]['user'] \
           or not conf[prov.nickname]['key']:

            _LOG.critical(
                """'%s' provider not found or improperly configured. Exiting...
                Please add the following to the config:

                providers:
                \t%s:
                \t\tuser: "yourusername"
                \t\tkey: "yourkey"

                OR unregister this provider
                """, *(prov.nickname, ) * 2
            )
            exit(1)
