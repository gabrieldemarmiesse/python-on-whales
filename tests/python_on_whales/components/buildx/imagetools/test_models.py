import json

import pytest

from python_on_whales.components.buildx.imagetools.models import Manifest
from python_on_whales.test_utils import get_all_jsons


@pytest.mark.parametrize("json_file", get_all_jsons("manifests"))
def test_load_json(json_file):
    Manifest(**json.loads(json_file.read_text()))
