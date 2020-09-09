from python_on_whales import docker
from python_on_whales.test_utils import random_name
from python_on_whales.components.network import NetworkInspectResult

def test_network_create_remove():
    my_name = random_name()
    my_network = docker.network.create(my_name)
    assert my_network.name == my_name
    docker.network.remove(my_name)


network_inspect_str = """
{
    "Name": "host",
    "Id": "ffb3f184cd0a2077f75a507320a9613eec135dc6cb234340ea924d576215e96e",
    "Created": "2020-05-04T17:50:40.0997657+02:00",
    "Scope": "local",
    "Driver": "host",
    "EnableIPv6": false,
    "IPAM": {
        "Driver": "default",
        "Options": null,
        "Config": []
    },
    "Internal": false,
    "Attachable": false,
    "Ingress": false,
    "ConfigFrom": {
        "Network": ""
    },
    "ConfigOnly": false,
    "Containers": {
        "a8d13ad9ac75a3343da098003e22052ac6ada63fa03a216e96f549f636b5ab56": {
            "Name": "gabriel_work_env",
            "EndpointID": "32b9e188395d7899599382ff4a08a4897475804a4bb8e9cf1fc51c8317180947",
            "MacAddress": "",
            "IPv4Address": "",
            "IPv6Address": ""
        }
    },
    "Options": {},
    "Labels": {}
}
"""

def test_parse_inspection():
    network_parsed = NetworkInspectResult.parse_raw(network_inspect_str)

    assert network_parsed.enable_I_pv6 is False
    assert network_parsed.driver == "host"
