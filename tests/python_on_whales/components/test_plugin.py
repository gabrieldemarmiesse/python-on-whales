import json
from pathlib import Path
from typing import List

import pytest

from python_on_whales import docker
from python_on_whales.components.plugin.models import PluginInspectResult
from python_on_whales.test_utils import get_all_jsons

test_plugin_name = "vieux/sshfs:latest"


def get_all_plugins_jsons() -> List[Path]:
    jsons_directory = Path(__file__).parent / "plugins"
    return sorted(list(jsons_directory.iterdir()))


@pytest.mark.parametrize("json_file", get_all_jsons("plugins"))
def test_load_json(json_file):
    json_as_txt = json_file.read_text()
    PluginInspectResult(**json.loads(json_as_txt))
    # we could do more checks here if needed


def test_install_plugin_disable_enable():
    with docker.plugin.install(test_plugin_name) as my_plugin:
        my_plugin.disable()
        my_plugin.enable()
        assert my_plugin in docker.plugin.list()
        assert "name='vieux/sshfs:latest'" in repr(my_plugin)


def test_plugin_upgrade():
    with docker.plugin.install(test_plugin_name) as my_plugin:
        my_plugin.disable()
        my_plugin.upgrade()


def test_remove_empty_plugin_list():
    with docker.plugin.install(test_plugin_name) as my_plugin:
        plugins_set = set(docker.plugin.list())
        assert my_plugin in plugins_set
        docker.plugin.remove([])
        assert set(docker.plugin.list()) == plugins_set
