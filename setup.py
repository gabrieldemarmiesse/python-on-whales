from pathlib import Path

from setuptools import find_packages, setup

CURRENT_DIR = Path(__file__).parent


def get_long_description() -> str:
    return (CURRENT_DIR / "README.md").read_text(encoding="utf8")


setup(
    name="python-on-whales",
    version="0.17.0",
    description="A Docker client for Python, designed to be fun and intuitive!",
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    install_requires=(CURRENT_DIR / "requirements.txt").read_text().splitlines(),
    packages=find_packages(),
    include_package_data=True,  # will read the MANIFEST.in
    license="MIT",
    python_requires=">=3.7, <4",
    entry_points={
        "console_scripts": [
            "python-on-whales=python_on_whales.command_line_entrypoint:main"
        ],
    },
)
