from setuptools import find_packages, setup

setup(
    name="docker-cli-wrapper",
    version=0.1,
    install_requires=["typeguard", "pydantic", "requests", "tqdm"],
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "docker-cli-wrapper=docker_cli_wrapper.command_line_entrypoint:main"
        ],
    },
)
