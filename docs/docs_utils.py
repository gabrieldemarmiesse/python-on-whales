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


def generate_code_demo_images() -> str:
    result = []

    image = docker.pull("ubuntu")
    print(f"Generating example for {image.repo_tags}")
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
        value = eval(attribute_access)
        result.append(write_code(i + 4, attribute_access, value))

    return "\n".join(result)


def add_links(text):
    text = text.replace(
        "`python_on_whales.Container`",
        "[`python_on_whales.Container`](/docker_objects/containers/)",
    )

    return text
