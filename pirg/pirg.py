import subprocess
import sys

from requests.exceptions import HTTPError
import traceback
from typing import List, Optional
from typing_extensions import Annotated
import typer
from .custom_exceptions import NothingToDo, DisabledPipFlag
from .models import Package
from .utils import (
    check_for_pip_args,
    check_for_requirements_file,
    load_requirements_file,
    decorative_print,
    create_requirements,
    get_name_version,
    parse_name,
    run_subprocess,
)


main = typer.Typer()


@main.command()
def install(
    package_names: Annotated[Optional[List[str]], typer.Argument(help="List of packages")] = None,
    requirements_path: Annotated[str, typer.Option()] = check_for_requirements_file(),
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
        new_pkgs = {get_name_version(package_name=pkg) for pkg in package_names}
        new_pkgs = new_pkgs - current_pkgs

        # fmt: off
        # check for update
        all_req_pkgs = {c for c in current_pkgs for n in new_pkgs if c.name != n.name}
        all_req_pkgs.update(new_pkgs)
        create_requirements(package_names=all_req_pkgs, requirements_loc=requirements_path)
        # fmt: on

        ins_pkgs = [f"{p.name}=={p.version}" for p in new_pkgs]

        if not ins_pkgs and not pip_args:
            raise NothingToDo("Nothing to install")

        run_subprocess(pkgs=ins_pkgs, pip_command="install", pip_args=list(pip_args))
    except HTTPError as e:
        pkg_name = e.args[0].split()[-1].split("/")[-2]
        decorative_print(f"Failed to find the latest version of {pkg_name} on PyPI")
        traceback.print_exc()
        sys.exit(e.response.status_code)
    except subprocess.CalledProcessError as e:
        decorative_print("Failed to install packages")
        traceback.print_exc()
        sys.exit(e.returncode)
    except NothingToDo as e:
        decorative_print(str(e))
        sys.exit(e.exit_code)


@main.command()
def uninstall(
    package_names: Annotated[Optional[List[str]], typer.Argument()] = None,
    requirements_path: Annotated[str, typer.Option()] = check_for_requirements_file(),
    delete_all: Annotated[bool, typer.Option()] = False,
) -> None:
    """
    Uninstalls [package_names] and removes them from the requirements file on [requirements_path] location

    You can pass additional `pip uninstall` arguments after "--".

    Example:
        `pirg uninstall torch -- -r requirements.txt --yes`

    """
    try:
        pip_args = check_for_pip_args()
        package_names = set(package_names) - pip_args

        package_names = [parse_name(val) for val in package_names]
        new_pkgs = set([Package(name, version) for name, version in package_names])
        current_pkgs = load_requirements_file(requirements_loc=requirements_path)

        if delete_all:
            new_pkgs.update(current_pkgs)

        # repopulate version from requirements.txt
        new_pkgs = {c for c in current_pkgs for n in new_pkgs if c.name == n.name}
        current_pkgs = current_pkgs - new_pkgs
        create_requirements(package_names=current_pkgs, requirements_loc=requirements_path)

        rm_pkgs = [p.name for p in new_pkgs]

        skip_pip_args = {"-h", "--help"}
        if not rm_pkgs and not delete_all and not bool(skip_pip_args & pip_args):
            raise NothingToDo("Nothing to remove")

        run_subprocess(pkgs=rm_pkgs, pip_command="uninstall", pip_args=list(pip_args))
    except HTTPError as e:
        pkg_name = e.args[0].split()[-1].split("/")[-2]
        decorative_print(f"Failed to find the latest version of {pkg_name} on PyPI")
        traceback.print_exc()
        sys.exit(e.response.status_code)
    except subprocess.CalledProcessError as e:
        decorative_print("Failed to remove packages")
        traceback.print_exc()
        sys.exit(e.returncode)
    except NothingToDo as e:
        decorative_print(str(e))
        sys.exit(e.exit_code)
    except DisabledPipFlag as e:
        decorative_print(str(e))
        sys.exit(e.exit_code)


if __name__ == "__main__":
    main()
