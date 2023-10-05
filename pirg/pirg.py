import os
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

REQUIREMENTS = "requirements.txt"
PYPI_URL = lambda pkg_name: f"https://pypi.org/pypi/{pkg_name}/json"
PY_VERSION = Version(sys.version.split()[0])

main = typer.Typer()


def decorative_print(msg: str) -> None:
    num = 50
    num_end = num - 2
    print(f"{'-' * num}pirg log{'-' * num}\n\t{msg}\n{'-' * num_end}pirg log end{'-' * num_end}")


def parse_name(pkg: str) -> Tuple[str, Optional[str]]:
    tmp_lst = pkg.strip().split("==")
    name = tmp_lst.pop(0)
    version = tmp_lst.pop() if tmp_lst else None
    return name, version


def create_requirements(
    package_names: set,
    requirements_loc: str,
    flag: str = "w",
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
                pkg = Package(name, Version(version))
                requirements.add(pkg)
    except FileNotFoundError:
        decorative_print(f"{requirements_loc} file not found. Creating new one.")
    finally:
        return requirements


def get_name_version(package_names: set) -> set:
    installed_pkgs = set()
    for pkg in package_names:
        pkg_name, pkg_version = parse_name(pkg)

        response = requests.get(PYPI_URL(pkg_name=pkg_name))
        response.raise_for_status()
        package_data = response.json()

        valid_versions = {
            Version(rel)
            for rel in package_data["releases"]
            for elem in package_data["releases"][rel]
            if elem["requires_python"] is not None
            and PY_VERSION in SpecifierSet(elem["requires_python"])
        }

        pkg_version = Version(pkg_version) if pkg_version else None
        if pkg_version in valid_versions:
            version = pkg_version
        else:
            version = max(valid_versions)

        pkg_name_version = Package(pkg_name, version)
        installed_pkgs.add(pkg_name_version)
    return installed_pkgs


def check_for_pip_args() -> set:
    try:
        dash_idx = sys.argv.index("--") + 1
        pip_args = set(sys.argv[dash_idx:])
    except ValueError:
        pip_args = set()

    return pip_args


def find_requirements_file() -> Optional[str]:
    current_dir = os.getcwd()
    while True:
        if REQUIREMENTS in os.listdir(current_dir):
            return os.path.join(current_dir, REQUIREMENTS)

        parent_dir = os.path.dirname(current_dir)
        if parent_dir == current_dir:
            break

        current_dir = parent_dir
    return None


@main.command()
def install(
    package_names: Annotated[Optional[List[str]], typer.Argument(help="List of packages")] = None,
    requirements_path: Annotated[str, typer.Option()] = find_requirements_file(),
) -> None:
    """
    Installs [package_names] and puts them in the requirements file on [requirements_path] location

    You can pass additional `pip install` arguments after "--".

    Example:
        `pirg install torch -- --index-url https://download.pytorch.org/whl/cu118`

    """
    pip_args = check_for_pip_args()
    package_names = set(package_names) - pip_args

    try:
        current_pkgs = load_requirements_file(requirements_loc=requirements_path)
        new_pkgs = get_name_version(package_names=package_names)
        new_pkgs = new_pkgs - current_pkgs

        # fmt: off
        # check for update
        current_pkgs = {c for c in current_pkgs for n in new_pkgs if c.name != n.name}
        current_pkgs.update(new_pkgs)
        # fmt: on

        create_requirements(package_names=current_pkgs, requirements_loc=requirements_path)

        ins_pkgs = [f"{p.name}=={p.version}" for p in new_pkgs]

        if not ins_pkgs and not pip_args:
            raise NothingToDo("Nothing to install")

        subprocess.run(["pip", "install"] + ins_pkgs + list(pip_args), check=True)
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
    requirements_path: Annotated[str, typer.Option()] = find_requirements_file(),
) -> None:
    """
    Uninstalls [package_names] and removes them from the requirements file on [requirements_path] location

    You can pass additional `pip uninstall` arguments after "--".

    Example:
        `pirg uninstall torch -- -r requirements.txt --yes`

    """
    pip_args = check_for_pip_args()
    package_names = set(package_names) - pip_args

    try:
        new_pkgs = set([Package(name) for name in package_names])
        current_pkgs = load_requirements_file(requirements_loc=requirements_path)
        current_pkgs = current_pkgs - new_pkgs
        create_requirements(package_names=current_pkgs, requirements_loc=requirements_path)

        rm_pkgs = [p.name for p in new_pkgs]

        if not rm_pkgs and not pip_args:
            raise NothingToDo("Nothing to remove")

        subprocess.run(["pip", "uninstall"] + rm_pkgs + list(pip_args), check=True)
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
