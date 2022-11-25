from typing import Optional

import typer

from python_on_whales import docker
from python_on_whales.download_binaries import download_docker_cli

app = typer.Typer()


volume_app = typer.Typer()


@volume_app.command()
def copy(source: str, destination: str):
    if ":" in source:
        source_volume, source_path = source.split(":")
        docker.volume.copy((source_volume, source_path), destination)
    elif ":" in destination:
        destination_volume, destination_path = destination.split(":")
        docker.volume.copy(source, (destination_volume, destination_path))
    else:
        raise ValueError("No volume was specified. The format is 'volume:path'")


image_app = typer.Typer()


@image_app.command()
def copy_from(docker_image: str, source: str, destination: str, pull: str = "missing"):
    docker.image.copy_from(docker_image, source, destination, pull)


@image_app.command()
def copy_to(
    docker_image: str,
    source: str,
    destination: str,
    new_tag: Optional[str] = None,
    push: bool = False,
    pull: str = "missing",
):
    docker.image.copy_to(docker_image, source, destination, new_tag, pull)
    if push:
        docker.image.push(new_tag)


@app.command()
def download_cli():
    download_docker_cli()


@app.command()
def download_buildx():
    raise NotImplementedError("Downloading the buildx binary isn't supported yet.")


app.add_typer(volume_app, name="volume")
app.add_typer(image_app, name="image")


def main():
    app()
