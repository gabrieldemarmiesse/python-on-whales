import random
import string
from contextlib import contextmanager
from pathlib import Path
from typing import List

from python_on_whales import client_config
from python_on_whales.utils import PROJECT_ROOT


def random_name() -> str:
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=20))


@contextmanager
def set_cache_validity_period(x: float):
    old = client_config.CACHE_VALIDITY_PERIOD
    client_config.CACHE_VALIDITY_PERIOD = x
    yield
    client_config.CACHE_VALIDITY_PERIOD = old


def get_all_jsons(object_types: str) -> List[Path]:
    jsons_directory = (
        PROJECT_ROOT / "tests/python_on_whales/components/jsons" / object_types
    )
    return sorted(list(jsons_directory.iterdir()), key=lambda x: int(x.stem))
