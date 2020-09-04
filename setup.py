from pathlib import Path

from setuptools import find_packages, setup

setup(
    name="python-on-whales",
    version=0.1,
    install_requires=Path("requirements.txt").read_text().splitlines(),
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "python-on-whales=python_on_whales.command_line_entrypoint:main"
        ],
    },
)
