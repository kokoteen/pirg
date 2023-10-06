import subprocess
from requests.exceptions import HTTPError
import traceback
from typing import List, Optional
from typing_extensions import Annotated
from .custom_exceptions import NothingToDo
import typer
from .models import Package
from .utils import (
    check_for_pip_args,
    find_requirements_file,
    load_requirements_file,
    decorative_print,
    create_requirements,
    get_name_version,
)


main = typer.Typer()


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
    except subprocess.CalledProcessError:
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
    except subprocess.CalledProcessError:
        decorative_print("Failed to remove packages")
        traceback.print_exc()
    except NothingToDo as e:
        decorative_print(str(e))


if __name__ == "__main__":
    main()
