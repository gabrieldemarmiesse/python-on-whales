import shutil

from keras_autodoc import DocumentationGenerator, get_methods

from python_on_whales.utils import PROJECT_ROOT

pages = {
    "docker_client.md": ["python_on_whales.DockerClient"]
    + get_methods("python_on_whales.docker_client.DockerClient"),
    "sub-commands/buildx.md": get_methods(
        "python_on_whales.components.buildx.BuildxCLI"
    ),
    "sub-commands/container.md": get_methods(
        "python_on_whales.components.container.ContainerCLI"
    ),
    "sub-commands/image.md": get_methods("python_on_whales.components.image.ImageCLI"),
    "sub-commands/network.md": get_methods(
        "python_on_whales.components.network.NetworkCLI"
    ),
    "sub-commands/node.md": get_methods("python_on_whales.components.node.NodeCLI"),
    "sub-commands/service.md": get_methods(
        "python_on_whales.components.service.ServiceCLI"
    ),
    "sub-commands/system.md": get_methods(
        "python_on_whales.components.system.SystemCLI"
    ),
    "sub-commands/volume.md": get_methods(
        "python_on_whales.components.volume.VolumeCLI"
    ),
    "docker_objects/builders.md": get_methods("python_on_whales.Builder"),
    "docker_objects/containers.md": get_methods("python_on_whales.Container"),
    "docker_objects/images.md": get_methods("python_on_whales.Image"),
    "docker_objects/networks.md": get_methods("python_on_whales.Network"),
    "docker_objects/nodes.md": get_methods("python_on_whales.Node"),
    "docker_objects/services.md": get_methods("python_on_whales.Service"),
    "docker_objects/volumes.md": get_methods("python_on_whales.Volume"),
}


class MyDocumentationGenerator(DocumentationGenerator):
    def process_signature(self, signature):
        signature = signature.replace("DockerClient.", "docker.")
        signature = signature.replace("BuildxCLI.", "docker.buildx.")
        signature = signature.replace("ContainerCLI.", "docker.container.")
        signature = signature.replace("ImageCLI.", "docker.image.")
        signature = signature.replace("NetworkCLI.", "docker.network.")
        signature = signature.replace("VolumeCLI.", "docker.volume.")
        return signature


doc_generator = MyDocumentationGenerator(
    pages,
    template_dir="./template",
    extra_aliases=[
        "python_on_whales.Builder",
        "python_on_whales.Container",
        "python_on_whales.Image",
        "python_on_whales.Network",
        "python_on_whales.Node",
        "python_on_whales.Service",
        "python_on_whales.Volume",
    ],
    titles_size="##",
)
destination = PROJECT_ROOT / "docs" / "generated_sources"
doc_generator.generate(destination)
shutil.copyfile(PROJECT_ROOT / "README.md", destination / "index.md")
shutil.copyfile(PROJECT_ROOT / "logo.png", destination / "logo.png")
