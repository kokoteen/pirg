import os
import pytest
from pirc.pirc import (
    create_requirements,
    load_requirements_file,
    get_name_version,
)


@pytest.fixture
def temporary_requirements_file(tmpdir):
    requirements_path = os.path.join(tmpdir, "requirements.txt")
    with open(requirements_path, "w") as req_file:
        req_file.write("package1==1.0.0\n")

    yield requirements_path

    os.remove(requirements_path)


def test_create_requirements(temporary_requirements_file):
    package_names = {"package2==2.0.0", "package3==3.0.0"}
    create_requirements(package_names, temporary_requirements_file)

    with open(temporary_requirements_file, "r") as req_file:
        lines = req_file.readlines()
        assert "package1==1.0.0\n" in lines
        assert "package2==2.0.0\n" in lines
        assert "package3==3.0.0\n" in lines


def test_load_requirements_file(temporary_requirements_file):
    requirements = load_requirements_file(temporary_requirements_file)
    assert len(requirements) == 1
    assert "package1" in [pkg.name for pkg in requirements]


def test_get_name_version():
    package_names = {"numpy", "pandas"}
    installed_pkgs = get_name_version(package_names)

    for pkg, pkg_name in zip(installed_pkgs, package_names):
        assert pkg_name == pkg.name
