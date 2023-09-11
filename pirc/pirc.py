import os
import subprocess
import traceback
from typing import List
import sys

import requests
import typer
from packaging.version import parse
from .models import Package

REQUIREMENTS_TXT = "requirements.txt"
PYPI_URL = lambda pkg_name: f"https://pypi.org/pypi/{pkg_name}/json"
PY_VERSION = sys.version

main = typer.Typer()


def decorative_print(msg: str) -> None:
    num = 50
    num_end = num - 2
    # fmt: off
    print(f"{'-' * num}pirc log{'-' * num}\n\t{msg}\n{'-' * num_end}pirc log end{'-' * num_end}")
    # fmt: on


def name_parse(pkg: str) -> List[str, str]:
    return pkg.strip().split("==")


def create_requirements(
    package_names: set,
    requirements_loc: str,
    flag: str = "a",
) -> None:
    with open(requirements_loc, flag) as req_file:
        for pkg in package_names:
            req_file.write(f"{pkg}\n")


def load_requirements_file(requirements_loc: str) -> set:
    requirements = set()
    try:
        with open(requirements_loc, "r") as req_file:
            for line in req_file:
                name, version = name_parse(line)
                pkg = Package(name, version)
                requirements.add(pkg)
    except FileNotFoundError:
        decorative_print(f"{requirements_loc} file not found. Creating new one.")
    finally:
        return requirements


def get_name_version(package_names: set) -> set:
    installed_pkgs = set()
    for pkg_name in package_names:
        try:
            response = requests.get(PYPI_URL(pkg_name=pkg_name))
            response.raise_for_status()
            package_data = response.json()
            version = package_data["info"]["version"]

            pkg_name_version = Package(pkg_name, version)
            installed_pkgs.add(pkg_name_version)
        except Exception as e:
            decorative_print(f"Failed to find the latest version of {pkg_name} on PyPI")
            traceback.print_exc(e)
    return installed_pkgs


@main.command()
def install(package_names: List[str], requirements_loc: str = ".") -> None:
    requirements_txt = os.path.join(requirements_loc, REQUIREMENTS_TXT)

    current_pkgs = load_requirements_file(requirements_loc=requirements_txt)
    new_pkgs = get_name_version(package_names=package_names)
    new_pkgs = new_pkgs - current_pkgs
    create_requirements(package_names=new_pkgs, requirements_loc=requirements_txt)

    try:
        subprocess.run(["pip", "install", "-r", requirements_txt], check=True)
        decorative_print(f"Installed packages from {requirements_txt}")
    except subprocess.CalledProcessError as e:
        decorative_print("Failed to install packages: ")
        traceback.print_exc(e)


@main.command()
def uninstall(package_names: List[str], requirements_loc: str = ".") -> None:
    requirements_txt = os.path.join(requirements_loc, REQUIREMENTS_TXT)

    new_pkgs = set([Package(name) for name in package_names])
    current_pkgs = load_requirements_file(requirements_loc=requirements_txt)

    current_pkgs = current_pkgs - new_pkgs
    create_requirements(
        package_names=current_pkgs,
        requirements_loc=requirements_txt,
        flag="w",
    )

    try:
        rm_pkgs = [p.name for p in new_pkgs]
        subprocess.run(["pip", "uninstall"] + rm_pkgs, check=True)
        decorative_print(f"Removed packages {rm_pkgs}")
    except subprocess.CalledProcessError as e:
        decorative_print("Failed to remove packages: ")
        traceback.print_exc(e)


if __name__ == "__main__":
    main()
