class ImageCLI(DockerCLICaller):
    def __init__(self, client_config: ClientConfig):
        super().__init__(client_config)
        self.build = python_on_whales.components.buildx.BuildxCLI(client_config).build
