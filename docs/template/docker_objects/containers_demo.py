import sys

from python_on_whales import docker


def super_print(obj):
    print(f"type = {type(obj)}, value = {obj}")


def write_code(i: int, attribute_access: str):
    value = eval(attribute_access)
    string = f"""In [{i}]: super_print({attribute_access})
type = {type(value)}, value = {value}

"""
    sys.stdout.write(string)


container = docker.run("ubuntu", ["sleep", "infinity"], detach=True)


with container:

    to_evaluate = [
        "container.id",
        "container.created",
        "container.path",
        "container.args",
        "container.state",
        "container.image",
        "container.resolv_conf_path",
        "container.hostname_path",
        "container.hosts_path",
        "container.log_path",
        "container.node",
        "container.name",
        "container.restart_count",
        "container.driver",
        "container.platform",
        "container.mount_label",
        "container.process_label",
        "container.app_armor_profile",
        "container.exec_ids",
        "container.host_config",
        "container.graph_driver",
        "container.size_rw",
        "container.size_root_fs",
        "container.mounts",
        "container.config",
        "container.network_settings",
    ]

    for i, attribute_access in enumerate(to_evaluate):
        write_code(i + 4, attribute_access)

print("done")
