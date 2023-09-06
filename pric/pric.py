import subprocess
import traceback
from typing import List

import requests
import typer
from packaging.version import parse

REQUIREMENTS_TXT = "requirements.txt"
PYPI_URL = lambda pkg_name: f"https://pypi.org/pypi/{pkg_name}/json"


def decorative_print(msg: str) -> None:
    num = 50
    num_end = num - 2
    # fmt: off
    print(f"{'-'*num}pyinstall log{'-'*num}\n\t{msg}\n{'-'*num_end}pyinstall log end{'-'*num_end}")
    # fmt: on


def create_requirements(package_names: set) -> None:
    for pkg in package_names:
        with open(REQUIREMENTS_TXT, "a") as req_file:
            req_file.write(f"{pkg}\n")


def load_requirements_file() -> set:
    requirements = set()
    try:
        with open(REQUIREMENTS_TXT, "r") as req_file:
            for line in req_file:
                stripped_line = line.strip()
                if stripped_line:
                    requirements.add(stripped_line)
    except FileNotFoundError:
        decorative_print("requirements.txt file not found. Creating new one.")
    finally:
        return requirements


def get_name_version(package_names: set) -> set:
    installed_pkgs = set()
    for pkg_name in package_names:
        try:
            response = requests.get(PYPI_URL(pkg_name=pkg_name))
            response.raise_for_status()
            package_data = response.json()
            releases = package_data["releases"].keys()
            latest_version = max(releases, key=parse)

            pkg_name_version = f"{pkg_name}=={latest_version}"
            installed_pkgs.add(pkg_name_version)
        except Exception as e:
            decorative_print(f"Failed to find the latest version of {pkg_name} on PyPI")
            traceback.print_exc(e)
    return installed_pkgs


def install_package(package_names: List[str]) -> None:
    if not package_names:
        decorative_print("No packages provided for installation.")
        return

    current_pkgs = load_requirements_file()
    new_pkgs = get_name_version(package_names=package_names)
    new_pkgs = new_pkgs - current_pkgs
    create_requirements(package_names=new_pkgs)

    try:
        subprocess.run(["pip", "install", "-r", REQUIREMENTS_TXT], check=True)
        decorative_print(f"Installed packages from {REQUIREMENTS_TXT}")
    except subprocess.CalledProcessError as e:
        decorative_print("Failed to install packages: ")
        traceback.print_exc(e)


def main():
    typer.run(install_package)


if __name__ == "__main__":
    typer.run(install_package)
