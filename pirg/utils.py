import sys
import os
import re
from packaging.version import Version
from typing import Optional, Tuple, List, Set
import requests
from packaging.specifiers import SpecifierSet, Specifier
import subprocess
from .models import Package
from .custom_exceptions import DisabledPipFlag, WrongPkgName, WrongSpecifierSet

PYPI_URL = lambda pkg_name: f"https://pypi.org/pypi/{pkg_name}/json"
PY_VERSION = Version(sys.version.split()[0])
PARSE_PATTERN = r"^(?P<name>[a-zA-Z0-9_-]+)(\[(?P<suffix>[a-zA-Z0-9_-]+)\])?(?P<specifier_set>.*)"
REQUIREMENTS = "requirements.txt"


def decorative_print(msg: str) -> None:
    num = 50
    num_end = num - 2
    print(f"{'-' * num}pirg log{'-' * num}\n\t{msg}\n{'-' * num_end}pirg log end{'-' * num_end}")


def parse_package_name(pkg: str) -> Tuple[str, Optional[str], Optional[str]]:
    pattern = PARSE_PATTERN

    match = re.match(pattern, pkg)
    if not match:
        raise WrongPkgName(f"Package {pkg} does not match pattern")

    package_data = match.groupdict()

    name = package_data["name"]
    suffix = package_data["suffix"]
    specifier_set = package_data["specifier_set"]

    return name, suffix, specifier_set


def create_requirements(
    package_names: Set[Package],
    requirements_loc: str,
    flag: str = "w",
) -> None:
    try:
        with open(requirements_loc, flag) as req_file:
            for pkg in package_names:
                req_file.write(f"{str(pkg)}\n")
    except FileNotFoundError as e:
        decorative_print(f"File '{requirements_loc}' not found")
        sys.exit(e.errno)


def load_requirements_file(requirements_loc: str) -> Set[Package]:
    requirements = set()
    try:
        with open(requirements_loc, "r") as req_file:
            for line in req_file:
                name, suffix, specifier_set = parse_package_name(line)
                pkg = Package(
                    name=name,
                    suffix=suffix,
                    specifier_set=specifier_set,
                )
                requirements.add(pkg)
    except FileNotFoundError:
        decorative_print(f"File '{requirements_loc}' not found. Creating new one")
    finally:
        return requirements


def get_name_version(package_name: str) -> Package:
    pkg_name, pkg_suffix, pkg_specifier_set = parse_package_name(package_name)

    response = requests.get(PYPI_URL(pkg_name=pkg_name))
    response.raise_for_status()
    package_data = response.json()

    valid_versions = {
        Specifier(f"=={rel}")
        for rel in package_data["releases"]
        for elem in package_data["releases"][rel]
        if elem["requires_python"] is not None
        and PY_VERSION in SpecifierSet(elem["requires_python"])
    }

    pkg_specifier_set = SpecifierSet(pkg_specifier_set) if pkg_specifier_set else None
    if pkg_specifier_set:
        specifier_set = {
            pkg_specifier_set for vv in valid_versions if vv.version in pkg_specifier_set
        }.pop()
        if not specifier_set:
            raise WrongSpecifierSet(f"Not valid specifier set: {pkg_specifier_set}")
    else:
        specifier_set = max(valid_versions, key=str)

    return Package(name=pkg_name, suffix=pkg_suffix, specifier_set=specifier_set)


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
