import typer

from python_on_whales.download_binaries import download_docker_cli

app = typer.Typer()


@app.command()
def download_cli():
    download_docker_cli()


@app.command()
def download_buildx():
    raise NotImplementedError("Downloading the buildx binary isn't supported yet.")


def main():
    app()
