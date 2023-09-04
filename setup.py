from pathlib import Path

from setuptools import find_packages, setup

CURRENT_DIR = Path(__file__).parent


def get_long_description() -> str:
    return (CURRENT_DIR / "README.md").read_text(encoding="utf8")


setup(
    name="python-on-whales",
    version="0.64.3",
    description="A Docker client for Python, designed to be fun and intuitive!",
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    install_requires=(CURRENT_DIR / "requirements.txt").read_text().splitlines(),
    packages=find_packages(),
    include_package_data=True,  # will read the MANIFEST.in
    license="MIT",
    python_requires=">=3.8, <4",
    entry_points={
        "console_scripts": [
            "python-on-whales=python_on_whales.command_line_entrypoint:main"
        ],
    },
    project_urls={
        "Documentation": "https://gabrieldemarmiesse.github.io/python-on-whales/",
        "Source Code": "https://github.com/gabrieldemarmiesse/python-on-whales",
        "Bug Tracker": "https://github.com/gabrieldemarmiesse/python-on-whales/issues",
    },
)
