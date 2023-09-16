import pip
import subprocess
from requests.exceptions import HTTPError
import traceback
from typing import List, Optional, Tuple
import sys

from typing_extensions import Annotated

from .custom_exceptions import NothingToDo

import requests
import typer
from packaging.version import parse, Version
from packaging.specifiers import SpecifierSet
from .models import Package

PYPI_URL = lambda pkg_name: f"https://pypi.org/pypi/{pkg_name}/json"
PY_VERSION = Version(sys.version.split()[0])

main = typer.Typer()


def decorative_print(msg: str) -> None:
    num = 50
    num_end = num - 2
    # fmt: off
    print(f"{'-' * num}pirc log{'-' * num}\n\t{msg}\n{'-' * num_end}pirc log end{'-' * num_end}")
    # fmt: on


def parse_name(pkg: str) -> List[str]:
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
                name, version = parse_name(line)
                pkg = Package(name, version)
                requirements.add(pkg)
    except FileNotFoundError:
        decorative_print(f"{requirements_loc} file not found. Creating new one.")
    finally:
        return requirements


def get_name_version(package_names: set) -> set:
    installed_pkgs = set()
    for pkg_name in package_names:
        response = requests.get(PYPI_URL(pkg_name=pkg_name))
        response.raise_for_status()
        package_data = response.json()

        valid_versions = {
            rel
            for rel in package_data["releases"]
            for elem in package_data["releases"][rel]
            if elem["requires_python"] is not None
            and PY_VERSION in SpecifierSet(elem["requires_python"])
        }

        version = max(valid_versions, key=parse)
        version = Version(version)

        pkg_name_version = Package(pkg_name, version)
        installed_pkgs.add(pkg_name_version)
    return installed_pkgs


@main.command()
def install(
    package_names: Annotated[Optional[List[str]], typer.Argument()] = None,
    requirements_path: str = "./requirements.txt",
    pip_args: Annotated[Tuple[str, str], typer.Option()] = (None, None),
) -> None:
    package_names = set(package_names)

    try:
        current_pkgs = load_requirements_file(requirements_loc=requirements_path)
        new_pkgs = get_name_version(package_names=package_names)
        new_pkgs = new_pkgs - current_pkgs
        create_requirements(package_names=new_pkgs, requirements_loc=requirements_path)

        pip_args = [] if pip_args == (None, None) else list(pip_args)
        ins_pkgs = [p.name for p in new_pkgs]

        if not ins_pkgs and not pip_args:
            raise NothingToDo("Nothing to install")

        subprocess.run(["pip", "install"] + ins_pkgs + pip_args, check=True)
        decorative_print(f"Installed packages {ins_pkgs}")

    except HTTPError as e:
        pkg_name = e.args[0].split()[-1].split("/")[-2]
        decorative_print(f"Failed to find the latest version of {pkg_name} on PyPI")
        traceback.print_exc()
    except subprocess.CalledProcessError as e:
        decorative_print("Failed to install packages")
        traceback.print_exc()
    except NothingToDo as e:
        decorative_print(str(e))


@main.command()
def uninstall(
    package_names: Annotated[Optional[List[str]], typer.Argument()] = None,
    requirements_path: str = "./requirements.txt",
    pip_args: Annotated[Tuple[str, str], typer.Option()] = (None, None),
) -> None:
    try:
        new_pkgs = set([Package(name) for name in package_names])
        current_pkgs = load_requirements_file(requirements_loc=requirements_path)
        current_pkgs = current_pkgs - new_pkgs
        create_requirements(
            package_names=current_pkgs,
            requirements_loc=requirements_path,
            flag="w",
        )

        pip_args = [] if pip_args == (None, None) else list(pip_args)
        rm_pkgs = [p.name for p in new_pkgs]

        if not rm_pkgs and not pip_args:
            raise NothingToDo("Nothing to remove")

        subprocess.run(["pip", "uninstall"] + rm_pkgs + pip_args, check=True)
        decorative_print(f"Removed packages {rm_pkgs}")
    except HTTPError as e:
        pkg_name = e.args[0].split()[-1].split("/")[-2]
        decorative_print(f"Failed to find the latest version of {pkg_name} on PyPI")
        traceback.print_exc()
    except subprocess.CalledProcessError as e:
        decorative_print("Failed to remove packages")
        traceback.print_exc()
    except NothingToDo as e:
        decorative_print(str(e))


if __name__ == "__main__":
    main()
