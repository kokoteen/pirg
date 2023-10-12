import sys
import os
import re
from packaging.version import Version
from typing import Optional, Tuple, List, Set
import requests
from packaging.specifiers import SpecifierSet
import subprocess
from .models import Package
from .custom_exceptions import DisabledPipFlag, WrongPkgName

PYPI_URL = lambda pkg_name: f"https://pypi.org/pypi/{pkg_name}/json"
PY_VERSION = Version(sys.version.split()[0])
REQUIREMENTS = "requirements.txt"


def decorative_print(msg: str) -> None:
    num = 50
    num_end = num - 2
    print(f"{'-' * num}pirg log{'-' * num}\n\t{msg}\n{'-' * num_end}pirg log end{'-' * num_end}")


def parse_package_name(pkg: str) -> Tuple[str, Optional[str], Optional[str], Optional[str]]:
    pattern = r"^(?P<name>[a-zA-Z0-9_-]+)(\[(?P<suffix>[a-zA-Z0-9_-]+)\])?(?P<specifier>[<>=<=!>=]+)?(?P<version>(?:\d+(\.\d+){0,2}))?$"

    match = re.match(pattern, pkg)
    if not match:
        raise WrongPkgName(f"Package {pkg} does not match pattern")

    package_data = match.groupdict()

    name = package_data["name"]
    suffix = package_data["suffix"]
    specifier = package_data["specifier"]
    version = package_data["version"]

    return name, suffix, specifier, version


def create_requirements(
    package_names: set,
    requirements_loc: str,
    flag: str = "w",
) -> None:
    with open(requirements_loc, flag) as req_file:
        for pkg in package_names:
            req_file.write(f"{pkg}\n")


def load_requirements_file(requirements_loc: str) -> Set[Package]:
    requirements = set()
    try:
        with open(requirements_loc, "r") as req_file:
            for line in req_file:
                name, suffix, specifier, version = parse_package_name(line)
                pkg = Package(
                    name=name,
                    suffix=suffix,
                    specifier=specifier,
                    version=Version(version),
                )
                requirements.add(pkg)
    except FileNotFoundError:
        decorative_print(f"{requirements_loc} file not found. Creating new one.")
    finally:
        return requirements


def get_name_version(package_name: str) -> Package:
    pkg_name, pkg_suffix, pkg_specifier, pkg_version = parse_package_name(package_name)

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

    return Package(name=pkg_name, suffix=pkg_suffix, specifier=pkg_specifier, version=version)


def check_for_pip_args() -> Set[str]:
    try:
        dash_idx = sys.argv.index("--") + 1
        pip_args = set(sys.argv[dash_idx:])
    except ValueError:
        pip_args = set()

    disable = {"-r", "--requirements", "-U", "--upgrade"}
    disable = disable & pip_args
    if disable:
        raise DisabledPipFlag(f"{disable} is disabled")

    return pip_args


def check_for_requirements_file() -> str:
    current_dir = os.getcwd()
    while True:
        if REQUIREMENTS in os.listdir(current_dir):
            return os.path.join(current_dir, REQUIREMENTS)

        parent_dir = os.path.dirname(current_dir)
        if parent_dir == current_dir:
            break

        current_dir = parent_dir

    return os.path.join(os.getcwd(), REQUIREMENTS)


def run_subprocess(pkgs: List[str], pip_command: str, pip_args: List[str]):
    subprocess.run(["pip", pip_command] + pkgs + pip_args, check=True)
    decorative_print(f"{pip_command.capitalize()}ed packages: {pkgs}")
