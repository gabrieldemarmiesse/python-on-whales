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


image = docker.image.inspect("ubuntu")

to_evaluate = [
    "image.id",
    "image.repo_tags",
    "image.repo_digests",
    "image.parent",
    "image.comment",
    "image.created",
    "image.container",
    "image.container_config",
    "image.docker_version",
    "image.author",
    "image.config",
    "image.architecture",
    "image.os",
    "image.os_version",
    "image.size",
    "image.virtual_size",
    "image.graph_driver.name",
    "image.graph_driver.data",
    "image.root_fs.type",
    "image.root_fs.layers",
    "image.root_fs.base_layer",
    "image.metadata",
]

for i, attribute_access in enumerate(to_evaluate):
    write_code(i + 4, attribute_access)

print("done")
