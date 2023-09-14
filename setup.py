from setuptools import find_packages, setup

setup(
    name="pirc",
    version="0.0.1",
    packages=find_packages(),
    description="command-line that simplifies the management of project's `requirements.txt` file",
    long_description=open('README.md').read(),
    entry_points={
        "console_scripts": [
            "pirc = pirc.pirc:main",
        ],
    },
    install_requires=["typer[all]==0.9.0", "requests==2.31.0", "packaging==23.1"],
    python_requires=">=3.8",
)
