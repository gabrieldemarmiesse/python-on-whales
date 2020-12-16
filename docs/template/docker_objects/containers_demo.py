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
        "container.state.status",
        "container.state.running",
        "container.state.paused",
        "container.state.restarting",
        "container.state.oom_killed",
        "container.state.dead",
        "container.state.pid",
        "container.state.exit_code",
        "container.state.error",
        "container.state.started_at",
        "container.state.finished_at",
        "container.state.health",
        "container.image",
        "container.resolv_conf_path",
    ]

    for i, attribute_access in enumerate(to_evaluate):
        write_code(i + 4, attribute_access)

print("done")
