from python_on_whales.client_config import DockerCLICaller


class TrustCLI(DockerCLICaller):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.key = None
        self.signer = None

    def inspect(self):
        """Not yet implemented"""
        raise NotImplementedError

    def revoke(self):
        """Not yet implemented"""
        raise NotImplementedError

    def sign(self):
        """Not yet implemented"""
        raise NotImplementedError
