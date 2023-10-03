from pathlib import Path

from setuptools import find_packages, setup

setup(
    name="pirc",
    version="0.0.4",
    packages=find_packages(),
    description="command-line tool that simplifies the management of project's `requirements.txt` file",
    long_description_content_type="text/markdown",
    long_description=Path("README.md").read_text(encoding="utf-8"),
    url="https://github.com/kokoteen/pirc",
    author="kokotin",
    entry_points={
        "console_scripts": [
            "pirc = pirc.pirc:main",
        ],
    },
    install_requires=["typer[all]==0.9.0", "requests==2.31.0", "packaging==23.1"],
    python_requires=">=3.8",
)
