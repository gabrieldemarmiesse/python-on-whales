import shutil

from docs_utils import add_all_code_examples, add_links
from keras_autodoc import DocumentationGenerator, get_methods

from python_on_whales.utils import PROJECT_ROOT

pages = {
    "docker_client.md": ["python_on_whales.DockerClient"]
    + get_methods("python_on_whales.docker_client.DockerClient"),
    "sub-commands/app.md": get_methods("python_on_whales.components.app.AppCLI"),
    "sub-commands/buildx.md": get_methods(
        "python_on_whales.components.buildx.BuildxCLI"
    ),
    "sub-commands/compose.md": get_methods(
        "python_on_whales.components.compose.ComposeCLI"
    ),
    "sub-commands/config.md": get_methods(
        "python_on_whales.components.config.ConfigCLI"
    ),
    "sub-commands/container.md": get_methods(
        "python_on_whales.components.container.ContainerCLI"
    ),
    "sub-commands/context.md": get_methods(
        "python_on_whales.components.context.ContextCLI"
    ),
    "sub-commands/image.md": get_methods("python_on_whales.components.image.ImageCLI"),
    "sub-commands/manifest.md": get_methods(
        "python_on_whales.components.manifest.ManifestCLI"
    ),
    "sub-commands/network.md": get_methods(
        "python_on_whales.components.network.NetworkCLI"
    ),
    "sub-commands/node.md": get_methods("python_on_whales.components.node.NodeCLI"),
    "sub-commands/plugin.md": get_methods(
        "python_on_whales.components.plugin.PluginCLI"
    ),
    "sub-commands/secret.md": get_methods(
        "python_on_whales.components.secret.SecretCLI"
    ),
    "sub-commands/service.md": get_methods(
        "python_on_whales.components.service.ServiceCLI"
    ),
    "sub-commands/stack.md": get_methods("python_on_whales.components.stack.StackCLI"),
    "sub-commands/swarm.md": get_methods("python_on_whales.components.swarm.SwarmCLI"),
    "sub-commands/system.md": get_methods(
        "python_on_whales.components.system.SystemCLI"
    ),
    "sub-commands/task.md": get_methods("python_on_whales.components.task.TaskCLI"),
    "sub-commands/trust.md": get_methods("python_on_whales.components.trust.TrustCLI"),
    "sub-commands/volume.md": get_methods(
        "python_on_whales.components.volume.VolumeCLI"
    ),
    "docker_objects/builders.md": get_methods("python_on_whales.Builder"),
    "docker_objects/containers.md": get_methods("python_on_whales.Container"),
    "docker_objects/configs.md": get_methods("python_on_whales.Config"),
    "docker_objects/images.md": get_methods("python_on_whales.Image"),
    "docker_objects/networks.md": get_methods("python_on_whales.Network"),
    "docker_objects/nodes.md": get_methods("python_on_whales.Node"),
    "docker_objects/plugins.md": get_methods("python_on_whales.Plugin"),
    "docker_objects/services.md": get_methods("python_on_whales.Service"),
    "docker_objects/stacks.md": get_methods("python_on_whales.Stack"),
    "docker_objects/volumes.md": get_methods("python_on_whales.Volume"),
}


class MyDocumentationGenerator(DocumentationGenerator):
    def process_signature(self, signature):
        signature = signature.replace("DockerClient.", "docker.")
        signature = signature.replace("AppCLI.", "docker.app.")
        signature = signature.replace("BuildxCLI.", "docker.buildx.")
        signature = signature.replace("ComposeCLI.", "docker.compose.")
        signature = signature.replace("ConfigCLI.", "docker.config.")
        signature = signature.replace("ContextCLI.", "docker.context.")
        signature = signature.replace("ContainerCLI.", "docker.container.")
        signature = signature.replace("ImageCLI.", "docker.image.")
        signature = signature.replace("ManifestCLI.", "docker.manifest.")
        signature = signature.replace("NetworkCLI.", "docker.network.")
        signature = signature.replace("NodeCLI.", "docker.node.")
        signature = signature.replace("PluginCLI.", "docker.plugin.")
        signature = signature.replace("SecretCLI.", "docker.secret.")
        signature = signature.replace("ServiceCLI.", "docker.service.")
        signature = signature.replace("StackCLI.", "docker.stack.")
        signature = signature.replace("SwarmCLI.", "docker.swarm.")
        signature = signature.replace("SystemCLI.", "docker.system.")
        signature = signature.replace("TrustCLI.", "docker.trust.")
        signature = signature.replace("TaskCLI.", "docker.task.")
        signature = signature.replace("VolumeCLI.", "docker.volume.")
        return signature


doc_generator = MyDocumentationGenerator(
    pages,
    template_dir=PROJECT_ROOT / "docs/template",
    extra_aliases=[
        "python_on_whales.Builder",
        "python_on_whales.Container",
        "python_on_whales.Config",
        "python_on_whales.Image",
        "python_on_whales.Network",
        "python_on_whales.Node",
        "python_on_whales.Plugin",
        "python_on_whales.Service",
        "python_on_whales.Stack",
        "python_on_whales.Task",
        "python_on_whales.Volume",
    ],
    titles_size="##",
)


destination = PROJECT_ROOT / "docs" / "generated_sources"
doc_generator.generate(destination)
shutil.copyfile(PROJECT_ROOT / "README.md", destination / "index.md")
shutil.copyfile(PROJECT_ROOT / "img/full.png", destination / "img/full.png")
shutil.copyfile(
    PROJECT_ROOT / "img/docker_clients.png", destination / "img/docker_clients.png"
)


bb = destination / "sub-commands" / "container.md"


for file in destination.rglob("*.md"):
    file.write_text(add_links(file.read_text()))

add_all_code_examples(destination)
