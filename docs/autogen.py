import os
import shutil
import typing as t
from pathlib import Path

from docs_utils import add_all_code_examples, add_links

from python_on_whales.utils import PROJECT_ROOT

AUTOGEN_PATTERN = "{{autogenerated}}"

# the key of pages is the template markdown file path
# the value of pages is the module path for auto-generating mkdocstring reference
# if the value is empty list, the function md_generate would just copy the template file to build directly

pages = {
    "docker_client.md": ["python_on_whales.docker_client.DockerClient"],
    "sub-commands/buildx.md": [
        "python_on_whales.components.buildx.cli_wrapper.BuildxCLI",
        "python_on_whales.components.buildx.imagetools.cli_wrapper.ImagetoolsCLI",
    ],
    "sub-commands/compose.md": [
        "python_on_whales.components.compose.cli_wrapper.ComposeCLI"
    ],
    "sub-commands/config.md": [
        "python_on_whales.components.config.cli_wrapper.ConfigCLI"
    ],
    "sub-commands/container.md": [
        "python_on_whales.components.container.cli_wrapper.ContainerCLI"
    ],
    "sub-commands/context.md": [
        "python_on_whales.components.context.cli_wrapper.ContextCLI"
    ],
    "sub-commands/image.md": ["python_on_whales.components.image.cli_wrapper.ImageCLI"],
    "sub-commands/manifest.md": [
        "python_on_whales.components.manifest.cli_wrapper.ManifestCLI"
    ],
    "sub-commands/network.md": [
        "python_on_whales.components.network.cli_wrapper.NetworkCLI"
    ],
    "sub-commands/node.md": ["python_on_whales.components.node.cli_wrapper.NodeCLI"],
    "sub-commands/plugin.md": [
        "python_on_whales.components.plugin.cli_wrapper.PluginCLI"
    ],
    "sub-commands/secret.md": [
        "python_on_whales.components.secret.cli_wrapper.SecretCLI"
    ],
    "sub-commands/service.md": [
        "python_on_whales.components.service.cli_wrapper.ServiceCLI"
    ],
    "sub-commands/stack.md": ["python_on_whales.components.stack.cli_wrapper.StackCLI"],
    "sub-commands/swarm.md": ["python_on_whales.components.swarm.cli_wrapper.SwarmCLI"],
    "sub-commands/system.md": [
        "python_on_whales.components.system.cli_wrapper.SystemCLI"
    ],
    "sub-commands/task.md": ["python_on_whales.components.task.cli_wrapper.TaskCLI"],
    "sub-commands/trust.md": ["python_on_whales.components.trust.cli_wrapper.TrustCLI"],
    "sub-commands/volume.md": [
        "python_on_whales.components.volume.cli_wrapper.VolumeCLI"
    ],
    "docker_objects/builders.md": ["python_on_whales.Builder"],
    "docker_objects/containers.md": ["python_on_whales.Container"],
    "docker_objects/configs.md": ["python_on_whales.Config"],
    "docker_objects/images.md": ["python_on_whales.Image"],
    "docker_objects/networks.md": ["python_on_whales.Network"],
    "docker_objects/nodes.md": ["python_on_whales.Node"],
    "docker_objects/plugins.md": ["python_on_whales.Plugin"],
    "docker_objects/services.md": ["python_on_whales.Service"],
    "docker_objects/secrets.md": ["python_on_whales.Secret"],
    "docker_objects/stacks.md": ["python_on_whales.Stack"],
    "docker_objects/volumes.md": ["python_on_whales.Volume"],
    "docker_objects/tasks.md": [],
    "user_guide/docker_run.md": [],
    "user_guide/generic_resources.md": [],
    "user_guide/running_python_on_whales_inside_a_container.md": [],
    "user_guide/exceptions.md": [],
    "index.md": [],
}


def md_generate(
    pages: t.Dict[str, list], template_path: str, destination_path: str
) -> None:
    for md_file in pages:
        template_file_path = f"{template_path}/{md_file}"
        target_file_path = f"{destination_path}/{md_file}"
        os.makedirs(Path(target_file_path).parent, exist_ok=True)

        if Path(template_file_path).exists():
            filedata = template_file_path.read_text()
        else:
            # if no template is found, the initial filedata
            # would be auto-generated by mkdocstrings
            filedata = AUTOGEN_PATTERN

        module_list = pages[md_file]

        for module in module_list:
            mkdocstring_output = f"""
## ::: {module}

"""
        filedata = filedata.replace(AUTOGEN_PATTERN, mkdocstring_output)

        with open(target_file_path, "w") as fout:
            fout.write(filedata)


def mkdoc_autogen():
    template_path = PROJECT_ROOT / "docs" / "template"
    destination_path = PROJECT_ROOT / "docs" / "generated_sources"
    md_generate(pages, template_path, destination_path)
    os.makedirs(destination_path / "img", exist_ok=True)
    shutil.copyfile(PROJECT_ROOT / "img/full.png", destination_path / "img/full.png")
    shutil.copyfile(
        PROJECT_ROOT / "img" / "docker_clients.png",
        destination_path / "img" / "docker_clients.png",
    )

    for file in destination_path.rglob("*.md"):
        file.write_text(add_links(file.read_text()))

    add_all_code_examples(destination_path)


if __name__ == "__main__":
    mkdoc_autogen()
