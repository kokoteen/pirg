import subprocess
import sys
import typer
import traceback

from importlib import metadata
from requests.exceptions import HTTPError
from typing import List, Optional
from typing_extensions import Annotated
from .custom_exceptions import NothingToDo, DisabledPipFlag, WrongPkgName, WrongSpecifierSet
from .models import Package
from .utils import (
    check_for_pip_args,
    check_for_requirements_file,
    load_requirements_file,
    decorative_print,
    create_requirements,
    get_package,
    parse_package_name,
    run_subprocess,
)

__version__ = metadata.version("pirg")

main = typer.Typer()


def version_callback(value: bool):
    if value:
        typer.echo(f"{__version__}")
        raise typer.Exit()


@main.callback()
def common(
    ctx: typer.Context,
    version: bool = typer.Option(None, "--version", callback=version_callback),
):
    pass


@main.command()
def install(
    package_names: Annotated[List[str], typer.Argument(help="List of packages")] = None,
    requirements_path: Annotated[str, typer.Option()] = check_for_requirements_file(),
    update_all: Annotated[bool, typer.Option()] = False,
) -> None:
    """
    Installs [package_names] and puts them in the requirements file on [requirements_path] location

    You can pass additional `pip install` arguments after "--".

    Example:
        `pirg install torch -- --index-url https://download.pytorch.org/whl/cu118`

    """
    try:
        pip_args = check_for_pip_args()
        package_names = set(package_names) - pip_args

        current_pkgs = load_requirements_file(requirements_loc=requirements_path)
        new_pkgs = {get_package(package_name=pkg) for pkg in package_names}
        new_pkgs = new_pkgs - current_pkgs

        if update_all:
            # all pkgs update
            update_current_pkgs = {get_package(package_name=pkg.name) for pkg in current_pkgs}
            update_current_pkgs = new_pkgs.union(update_current_pkgs)
            new_pkgs = update_current_pkgs
        else:
            # one pkg update
            # check if it has same name but different version
            update_current_pkgs = {c for c in current_pkgs for n in new_pkgs if c.name != n.name}
            update_current_pkgs.update(new_pkgs)

        ins_pkgs = [f"{str(p)}" for p in new_pkgs]

        skip_pip_args = {"-h", "--help"}
        if not ins_pkgs and not update_all and not bool(skip_pip_args & pip_args):
            raise NothingToDo("Nothing to install")

        run_subprocess(pkgs=ins_pkgs, pip_command="install", pip_args=list(pip_args))
        create_requirements(package_names=update_current_pkgs, requirements_loc=requirements_path)
    except HTTPError as e:
        pkg_name = e.args[0].split()[-1].split("/")[-2]
        decorative_print(f"Failed to find the latest version of {pkg_name} on PyPI")
        traceback.print_exc()
        sys.exit(e.response.status_code)
    except subprocess.CalledProcessError as e:
        decorative_print("Failed to install packages")
        traceback.print_exc()
        sys.exit(e.returncode)
    except (NothingToDo, DisabledPipFlag, WrongPkgName, WrongSpecifierSet) as e:
        decorative_print(str(e))
        sys.exit(e.exit_code)


@main.command()
def uninstall(
    package_names: Annotated[List[str], typer.Argument()] = None,
    requirements_path: Annotated[str, typer.Option()] = check_for_requirements_file(),
    delete_all: Annotated[bool, typer.Option()] = False,
) -> None:
    """
    Uninstalls [package_names] and removes them from the requirements file on [requirements_path] location

    You can pass additional `pip uninstall` arguments after "--".

    Example:
        `pirg uninstall torch -- --yes`

    """
    try:
        pip_args = check_for_pip_args()
        package_names = set(package_names) - pip_args

        package_names = [parse_package_name(val) for val in package_names]
        new_pkgs = set([Package(n, sf, ss) for n, sf, ss in package_names])
        current_pkgs = load_requirements_file(requirements_loc=requirements_path)

        if delete_all:
            new_pkgs.update(current_pkgs)

        # repopulate version from requirements.txt
        new_pkgs = {c for c in current_pkgs for n in new_pkgs if c.name == n.name}
        current_pkgs = current_pkgs - new_pkgs

        rm_pkgs = [p.name for p in new_pkgs]

        skip_pip_args = {"-h", "--help"}
        if not rm_pkgs and not delete_all and not bool(skip_pip_args & pip_args):
            raise NothingToDo("Nothing to remove")

        run_subprocess(pkgs=rm_pkgs, pip_command="uninstall", pip_args=list(pip_args))
        create_requirements(package_names=current_pkgs, requirements_loc=requirements_path)
    except HTTPError as e:
        pkg_name = e.args[0].split()[-1].split("/")[-2]
        decorative_print(f"Failed to find the latest version of {pkg_name} on PyPI")
        traceback.print_exc()
        sys.exit(e.response.status_code)
    except subprocess.CalledProcessError as e:
        decorative_print("Failed to remove packages")
        traceback.print_exc()
        sys.exit(e.returncode)
    except (NothingToDo, DisabledPipFlag, WrongPkgName, WrongSpecifierSet) as e:
        decorative_print(str(e))
        sys.exit(e.exit_code)


if __name__ == "__main__":
    main()
