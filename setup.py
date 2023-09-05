from setuptools import find_packages, setup

setup(
    name="pric",
    version="0.0.1",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "pric = pric.pric:main",
        ],
    },
    install_requires=[
        "typer",
    ],
    python_requires=">=3.8",
)
