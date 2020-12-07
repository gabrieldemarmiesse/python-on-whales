from contextlib import contextmanager

from python_on_whales import client_config


@contextmanager
def set_cache_validity_period(x: float):
    old = client_config.CACHE_VALIDITY_PERIOD
    client_config.CACHE_VALIDITY_PERIOD = x
    yield
    client_config.CACHE_VALIDITY_PERIOD = old
