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
import yaml


_LOG = logging.getLogger()
PROVIDERS_KEY = "providers"


def _exit_if_no_providers(config):
    if PROVIDERS_KEY not in config:
        _LOG.critical(
            'The configuration must have a "%s" section. Exiting',
            PROVIDERS_KEY
        )
        exit(1)


def load_config(path):
    try:
        with open(path, 'r') as conf:
            return yaml.load(conf.read())
    except yaml.parser.ParserError:
        _LOG.error("Invalid YAML file: %s. Exiting", path)
        exit(1)


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
