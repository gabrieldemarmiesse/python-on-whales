from pathlib import Path
from typing import List

import pytest

from python_on_whales.components.service import ServiceInspectResult


def get_all_services_jsons() -> List[Path]:
    jsons_directory = Path(__file__).parent / "services"
    return list(jsons_directory.iterdir())


@pytest.mark.parametrize("json_file", get_all_services_jsons())
def test_load_json(json_file):
    if json_file.name == "1.json":
        pytest.skip("TODO: FIXE!")
    json_as_txt = json_file.read_text()
    ServiceInspectResult.parse_raw(json_as_txt)
    # we could do more checks here if needed
