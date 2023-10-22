import logging
import os
import re
import subprocess
import sys
from datetime import datetime, timedelta
from difflib import get_close_matches
from typing import Dict, List, Optional, Set, Tuple

import requests
from bs4 import BeautifulSoup
from fuzzywuzzy import fuzz, process
from packaging.specifiers import Specifier, SpecifierSet
from packaging.version import Version

from .exceptions import DisabledPipFlag, WrongPkgName, WrongSpecifierSet, EmptyDatabase
from .models import Package

PYPI_URL = lambda pkg_name: f"https://pypi.org/pypi/{pkg_name}/json"
PYPI_SIMPLE_URL = "https://pypi.org/simple/"
PY_VERSION = Version(sys.version.split()[0])
PARSE_PATTERN = r"^(?P<name>[a-zA-Z0-9_-]+)(\[(?P<suffix>[a-zA-Z0-9_-]+)\])?(?P<specifier_set>.*)"
REQUIREMENTS = "requirements.txt"


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
    with open(requirements_loc, flag) as req_file:
        for pkg in package_names:
            req_file.write(f"{str(pkg)}\n")


def load_requirements_file(requirements_loc: str) -> Set[Package]:
    requirements = set()

    if not os.path.exists(requirements_loc):
        return requirements

    with open(requirements_loc, "r") as req_file:
        for line in req_file:
            name, suffix, specifier_set = parse_package_name(line)
            pkg = Package(
                name=name,
                suffix=suffix,
                specifier_set=specifier_set,
            )
            requirements.add(pkg)

    return requirements


def get_package(package_name: str) -> Package:
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

    logging.debug(f"valid_versions: {valid_versions}")
    if not valid_versions:
        # when `requires_python = None` for all pkgs
        valid_versions = {Specifier(f"=={rel}") for rel in package_data["releases"]}

    pkg_specifier_set = SpecifierSet(pkg_specifier_set) if pkg_specifier_set else None

    if pkg_specifier_set:
        specifier_set = {
            pkg_specifier_set for vv in valid_versions if vv.version in pkg_specifier_set
        }

        if not specifier_set:
            # if the specifier is wrong we get from packaging lib Invalid specifier
            # this means, here can only be empty specifier set
            # which can happen if valid version is not in provided specifier set
            raise WrongSpecifierSet(f"Not valid specifier set: {pkg_specifier_set}")

        specifier_set = max(specifier_set, key=str)
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


def get_pypi_simple_data(url: str = PYPI_SIMPLE_URL) -> str:
    response = requests.get(url)
    response.raise_for_status()
    return response.text


def check_if_pypi_simple_is_modified(days: int = 3, url: str = PYPI_SIMPLE_URL) -> bool:
    current_date = datetime.now()
    last_modified_date = current_date - timedelta(days=days)
    if_modified_since = last_modified_date.strftime("%a, %d %b %Y %H:%M:%S GMT")

    headers = {"If-Modified-Since": if_modified_since}

    response = requests.head(url, headers=headers)
    response.raise_for_status()

    if response.status_code == 200:
        return True
    elif response.status_code == 304:
        return False


def create_db(filename: str, data: str) -> None:
    soup = BeautifulSoup(data, "html.parser")
    links = soup.find_all("a")
    package_names = [link.text.strip() for link in links if link.text.strip()]

    with open(filename, "w") as file:
        for package in package_names:
            file.write(package + "\n")


def fuzzy_search(search_input: str, indexed_pkg_names: Dict[str, str]) -> List[str]:
    if not indexed_pkg_names:
        raise EmptyDatabase("Empty DB")

    matches = get_close_matches(search_input, indexed_pkg_names, n=7, cutoff=0.6)
    search_results = process.extract(search_input, matches, scorer=fuzz.ratio)

    org_names = [indexed_pkg_names[result] for result, _ in search_results]
    return org_names


def run_subprocess(pkgs: List[str], pip_command: str, pip_args: List[str]):
    subprocess.run(["pip", pip_command] + pkgs + pip_args, check=True)
    logging.info(f"{pip_command.capitalize()}ed packages: {pkgs}")
