import logging.config
import os
import subprocess
import sys
import tempfile
import traceback
from importlib import metadata
from typing import List

import typer
from requests.exceptions import HTTPError
from typing_extensions import Annotated

from pirg.config import log_config
from pirg.exceptions import (
    DisabledPipFlag,
    EmptyDatabase,
    WrongPkgName,
    WrongSpecifierSet,
)
from .models import Package
from .utils import (
    check_for_pip_args,
    check_for_requirements_file,
    check_if_pypi_simple_is_modified,
    create_db,
    create_requirements,
    fuzzy_search,
    get_package,
    get_pypi_simple_data,
    load_requirements_file,
    parse_package_name,
    run_subprocess,
)

TEMP_FILENAME = "pirg_pkg_db.txt"
__version__ = metadata.version("pirg")
logging.config.dictConfig(log_config)

main = typer.Typer()


def version_callback(value: bool):
    if value:
        typer.echo(f"{__version__}")
        raise typer.Exit()


@main.callback()
def common(
    ctx: typer.Context,
    version: bool = typer.Option(
        None,
        "--version",
        help="Current version",
        callback=version_callback,
    ),
):
    pass


@main.command()
def install(
    package_names: Annotated[List[str], typer.Argument(help="List of packages")] = None,
    requirements_path: Annotated[str, typer.Option()] = check_for_requirements_file(),
    update_all: Annotated[bool, typer.Option()] = False,
    log_level: Annotated[str, typer.Option(help="Set the log level")] = "INFO",
) -> None:
    """
    Installs [package_names] and puts them in the requirements file on [requirements_path] location

    You can pass additional `pip install` arguments after "--".

    Example:
        `_pit install torch -- --index-url https://download.pytorch.org/whl/cu118`

    """
    log_level = log_level.upper()
    log_level = getattr(logging, log_level)
    logging.getLogger().setLevel(log_level)
    logging.debug(f"ARGV: {sys.argv}")

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
            logging.info("Nothing to install")
            return

        run_subprocess(pkgs=ins_pkgs, pip_command="install", pip_args=list(pip_args))
        create_requirements(package_names=update_current_pkgs, requirements_loc=requirements_path)
    except FileNotFoundError as e:
        traceback.print_exc()
        sys.exit(e.errno)
    except HTTPError as e:
        pkg_name = e.args[0].split()[-1].split("/")[-2]
        logging.error(f"Failed to find the latest version of {pkg_name} on PyPI")
        traceback.print_exc()
        sys.exit(e.response.status_code)
    except subprocess.CalledProcessError as e:
        logging.error("Failed to install packages")
        traceback.print_exc()
        sys.exit(e.returncode)
    except (DisabledPipFlag, WrongPkgName, WrongSpecifierSet) as e:
        logging.error(str(e))
        sys.exit(e.exit_code)


@main.command()
def uninstall(
    package_names: Annotated[List[str], typer.Argument()] = None,
    requirements_path: Annotated[str, typer.Option()] = check_for_requirements_file(),
    delete_all: Annotated[bool, typer.Option()] = False,
    log_level: Annotated[str, typer.Option(help="Set the log level")] = "INFO",
) -> None:
    """
    Uninstalls [package_names] and removes them from the requirements file on [requirements_path] location

    You can pass additional `pip uninstall` arguments after "--".

    Example:
        `_pit uninstall torch -- --yes`

    """
    log_level = log_level.upper()
    log_level = getattr(logging, log_level)
    logging.getLogger().setLevel(log_level)
    logging.debug(f"ARGV: {sys.argv}")

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
            logging.info("Nothing to remove")
            return

        run_subprocess(pkgs=rm_pkgs, pip_command="uninstall", pip_args=list(pip_args))
        create_requirements(package_names=current_pkgs, requirements_loc=requirements_path)
    except FileNotFoundError as e:
        traceback.print_exc()
        sys.exit(e.errno)
    except HTTPError as e:
        pkg_name = e.args[0].split()[-1].split("/")[-2]
        logging.error(f"Failed to find the latest version of {pkg_name} on PyPI")
        traceback.print_exc()
        sys.exit(e.response.status_code)
    except subprocess.CalledProcessError as e:
        logging.error("Failed to remove packages")
        traceback.print_exc()
        sys.exit(e.returncode)
    except (DisabledPipFlag, WrongPkgName, WrongSpecifierSet) as e:
        logging.error(str(e))
        sys.exit(e.exit_code)


@main.command()
def search(
    user_input: Annotated[str, typer.Argument()] = None,
    log_level: Annotated[str, typer.Option(help="Set the log level")] = "INFO",
) -> None:
    """
    Search for python package on PYPI

    Example:
        `_pit search sqlalchemy` -> Search result: ['SQLAlchemy', 'sqlalchemyp',...]
    """
    log_level = log_level.upper()
    log_level = getattr(logging, log_level)
    logging.getLogger().setLevel(log_level)
    logging.debug(f"ARGV: {sys.argv}")

    try:
        temp_dir = tempfile.gettempdir()
        filename = os.path.join(temp_dir, TEMP_FILENAME)

        if not os.path.exists(filename):
            raise FileNotFoundError("Package names file doesn't exist. Please run `initdb` first.")

        if check_if_pypi_simple_is_modified():
            # fmt: off
            logging.info("Current list of package names is out of date. Please update with `initdb --update`")
            # fmt: on

        with open(filename, "r") as file:
            package_names = [line.strip() for line in file]

        indexed_package_names = {name.lower(): name for name in package_names}
        search_output = fuzzy_search(user_input, indexed_package_names)
        logging.info(f"Search result: {search_output}")
    except EmptyDatabase as e:
        logging.error(str(e))
        sys.exit(e.exit_code)
    except FileNotFoundError as e:
        traceback.print_exc()
        sys.exit(e.errno)
    except HTTPError as e:
        logging.error(e)
        traceback.print_exc()
        sys.exit(e.response.status_code)


@main.command()
def initdb(
    update: Annotated[bool, typer.Option()] = False,
    log_level: Annotated[str, typer.Option(help="Set the log level")] = "INFO",
) -> None:
    """
    Initialize or update current package names list

    Example:
        `_pit initdb`
    """
    log_level = log_level.upper()
    log_level = getattr(logging, log_level)
    logging.getLogger().setLevel(log_level)
    logging.debug(f"ARGV: {sys.argv}")

    try:
        temp_dir = tempfile.gettempdir()
        filename = os.path.join(temp_dir, TEMP_FILENAME)
        logging.debug(f"Database location: {filename}")

        if not update and os.path.exists(filename):
            logging.info("Database already initialized")
            return

        new_version = check_if_pypi_simple_is_modified()
        if update and not new_version:
            logging.info("Database is up-to-date")
            return

        logging.info("Downloading data")
        data = get_pypi_simple_data()

        create_db(filename, data)
        logging.info("Database initialized")
    except FileNotFoundError as e:
        traceback.print_exc()
        sys.exit(e.errno)
    except HTTPError as e:
        logging.error(e)
        traceback.print_exc()
        sys.exit(e.response.status_code)


if __name__ == "__main__":
    main()
