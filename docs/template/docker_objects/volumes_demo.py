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


volume = docker.volume.create()

with volume:
    to_evaluate = [
    "volume.name",
    "volume.driver",
    "volume.mountpoint",
    "volume.created_at",
    "volume.status",
    "volume.labels",
    "volume.scope",
    "volume.options",
    ]

    for i, attribute_access in enumerate(to_evaluate):
        write_code(i + 4, attribute_access)

print("done")
