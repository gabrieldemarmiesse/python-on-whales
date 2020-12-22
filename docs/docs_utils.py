from python_on_whales import docker


def write_code(i: int, attribute_access: str, value) -> str:
    string = f"""In [{i}]: super_print({attribute_access})
type = {type(value)}, value = {value}
"""
    return string


def generate_code_demo_volumes() -> str:
    result = []

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
            value = eval(attribute_access)
            result.append(write_code(i + 4, attribute_access, value))

    return "\n".join(result)


def add_links(text):
    text = text.replace(
        "`python_on_whales.Container`",
        "[`python_on_whales.Container`](/docker_objects/containers/)",
    )

    return text
