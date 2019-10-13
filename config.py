import os.path
from typing import (
    List
)
import yaml
import inspect


def get_fcn_name() -> str:
    """ Magic function which inspects and returns the callers function name """
    call_stack = inspect.stack()
    parent_stack_frame = call_stack[1]
    return parent_stack_frame.function


class ConfigurationError(Exception):
    pass


class StorageConfiguration:

    def __init__(self, config: dict):
        self._config = config

    def _abs_path(self, filename: str) -> str:
        path = self._config["location_dir"]
        return os.path.join(path, filename)

    @property
    def hosts_filename(self) -> str:
        return self._abs_path(self._config[get_fcn_name()])

    @property
    def unix_accounts_filename(self) -> str:
        return self._abs_path(self._config[get_fcn_name()])

    @property
    def user_accounts_filename(self) -> str:
        return self._abs_path(self._config[get_fcn_name()])


class SSLConfiguration:

    def __init__(self, config: dict):
        self._config = config

    def _abs_path(self, filename: str) -> str:
        path = self._config["location_dir"]
        return os.path.join(path, filename)

    @property
    def cert(self) -> str:
        return self._abs_path(self._config[get_fcn_name()])

    @property
    def key(self) -> str:
        return self._abs_path(self._config[get_fcn_name()])

    @property
    def ca_cert(self) -> str:
        return self._abs_path(self._config[get_fcn_name()])


class ServiceConfiguration:

    def __init__(self, config: dict):
        self._config = config

    @property
    def host(self) -> str:
        return self._config[get_fcn_name()]

    @property
    def port(self) -> int:
        return self._config[get_fcn_name()]

    @property
    def ssl(self) -> SSLConfiguration:
        """ This configuration is optional """
        ssl_config = self._config.get(get_fcn_name())
        if ssl_config:
            return SSLConfiguration(ssl_config)
        else:
            return None


class WebserverConfiguration:

    def __init__(self, config: dict):
        self._config = config

    @property
    def external_url(self) -> str:
        return self._config[get_fcn_name()]

    @property
    def cookie_secret(self) -> str:
        return self._config[get_fcn_name()]

    def service(self, name: str) -> ServiceConfiguration:
        service_list = self._config[get_fcn_name()]
        try:
            return next(ServiceConfiguration(cfg) for cfg in service_list if cfg["name"] == name)
        except StopIteration:
            raise ConfigurationError("Webserver service '{name}' not found in config".format(name=name))


class OpenIDProviderConfiguration:

    def __init__(self, config: dict):
        self._config = config

    @property
    def name(self) -> str:
        return self._config[get_fcn_name()]

    @property
    def well_known(self) -> str:
        return self._config[get_fcn_name()]

    @property
    def client_id(self) -> str:
        return self._config[get_fcn_name()]

    @property
    def client_secret(self) -> str:
        return self._config[get_fcn_name()]


class OpenIDProviderConfigurationList:

    def __init__(self, config_list: list):
        self._config_list = config_list

    @property
    def all(self) -> List[OpenIDProviderConfiguration]:
        return list(OpenIDProviderConfiguration(cfg) for cfg in self._config_list)

    def has(self, name: str) -> bool:
        return any(cfg["name"] == name for cfg in self._config_list)

    def provider(self, name: str) -> OpenIDProviderConfiguration:
        try:
            return next(OpenIDProviderConfiguration(cfg) for cfg in self._config_list if cfg["name"] == name)
        except StopIteration:
            raise ConfigurationError("OpenID openid_client_cfg '{name}' not found in config".format(name=name))


class BootstrapConfiguration:

    def __init__(self, bootstrap_types):
        self._bootstrap_types = bootstrap_types

    def type(self, type_name: str) -> List[dict]:
        return list(cfg for cfg in self._bootstrap_types if cfg["type"] == type_name)


class Configuration:

    """ This class is the main entrypoint for loading and navigating through the configuration file """

    def __init__(self, filename: str):
        with open(filename, "r") as stream:
            config = yaml.safe_load(stream)
        self._config = config["application"]

    @property
    def storage(self) -> StorageConfiguration:
        return StorageConfiguration(self._config[get_fcn_name()])

    @property
    def webserver(self):
        return WebserverConfiguration(self._config[get_fcn_name()])

    @property
    def openid_provider(self) -> OpenIDProviderConfigurationList:
        return OpenIDProviderConfigurationList(self._config[get_fcn_name()])

    @property
    def bootstrap(self) -> BootstrapConfiguration:
        return BootstrapConfiguration(self._config[get_fcn_name()])
