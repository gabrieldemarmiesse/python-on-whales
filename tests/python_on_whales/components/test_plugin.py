from python_on_whales import docker

test_plugin_name = "vieux/sshfs:latest"


def test_install_plugin_disable_enable():
    with docker.plugin.install(test_plugin_name) as my_plugin:
        my_plugin.disable()
        my_plugin.enable()


def test_plugin_upgrade():
    with docker.plugin.install(test_plugin_name) as my_plugin:
        my_plugin.disable()
        my_plugin.upgrade()
