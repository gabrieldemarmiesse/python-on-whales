from keras_autodoc import DocumentationGenerator, get_methods

pages = {
    "docker_client.md": ["python_on_whales.DockerClient"]
    + get_methods("python_on_whales.docker_client.DockerClient"),
    "components/buildx.md": get_methods("python_on_whales.components.buildx.BuildxCLI"),
    "components/container.md": get_methods(
        "python_on_whales.components.container.ContainerCLI"
    ),
    "components/image.md": get_methods("python_on_whales.components.image.ImageCLI"),
    "components/network.md": get_methods(
        "python_on_whales.components.network.NetworkCLI"
    ),
    "components/volume.md": get_methods("python_on_whales.components.volume.VolumeCLI"),
    "docker_objects/image.md": get_methods("python_on_whales.Image"),
    "docker_objects/container.md": get_methods("python_on_whales.Container"),
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


doc_generator = MyDocumentationGenerator(pages, template_dir="./template")
doc_generator.generate("./generated_sources")
