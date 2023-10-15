import os
import sys
import responses
import pytest
from packaging.specifiers import SpecifierSet
from pirg.custom_exceptions import DisabledPipFlag, WrongSpecifierSet, WrongPkgName
from pirg.models import Package
from pirg.utils import (
    PYPI_URL,
    check_for_pip_args,
    load_requirements_file,
    get_name_version,
    create_requirements,
    check_for_requirements_file,
    parse_package_name,
)


@pytest.fixture
def temporary_requirements_file(tmpdir):
    requirements_path = os.path.join(tmpdir, "requirements.txt")
    with open(requirements_path, "w") as req_file:
        req_file.write("package1==1.0.0\n")

    yield requirements_path

    os.remove(requirements_path)


def test_create_requirements(temporary_requirements_file):
    package_names = {
        Package(name="package2", specifier_set=SpecifierSet("==2.0.0")),
        Package(name="package3", specifier_set=SpecifierSet("==3.0.0")),
    }

    # test when there are packages and the file is provided
    create_requirements(package_names, temporary_requirements_file)
    with open(temporary_requirements_file, "r") as req_file:
        lines = req_file.readlines()
        assert "package1==1.0.0\n" not in lines
        assert "package2==2.0.0\n" in lines
        assert "package3==3.0.0\n" in lines

    # test if requirements file is empty when there are no packages
    create_requirements(set(), temporary_requirements_file)
    with open(temporary_requirements_file, "r") as req_file:
        lines = req_file.readlines()
        assert not lines

    # test when the file is not provided
    with pytest.raises(SystemExit) as excinfo:
        create_requirements(set(), "")
    assert excinfo.value.code == 2


def test_load_requirements_file(temporary_requirements_file):
    # test with file
    requirements = load_requirements_file(temporary_requirements_file)
    assert len(requirements) == 1
    assert "package1" in [pkg.name for pkg in requirements]

    # test empty file location
    requirements = load_requirements_file("")
    assert not requirements


def test_get_name_version():
    package_name = ["package1"]
    mock_response_body = {
        "releases": {
            "1.0.0": [{"requires_python": ">=3.8"}],
            "1.1.0": [{"requires_python": ">=3.8"}],
            "1.2.0": [{"requires_python": ">=3.8"}],
        }
    }

    for pkg in package_name:
        url = PYPI_URL(pkg)

        with responses.RequestsMock() as rsps:
            rsps.add(responses.GET, url, json=mock_response_body)
            result = get_name_version(pkg)

            assert result.name == pkg
            assert str(result.specifier_set) == "==1.2.0"


def test_check_for_requirements_file(tmpdir):
    root_dir = tmpdir.mkdir("project")
    sub_dir1 = root_dir.mkdir("subdirectory1")
    sub_dir2 = sub_dir1.mkdir("subdirectory2")

    sub_dir1.join("requirements.txt").write("Test requirements file content")

    # test if file is in sub_dir1
    os.chdir(str(sub_dir2))
    assert check_for_requirements_file() == sub_dir1.join("requirements.txt")

    # test if the current directory is default option if there is no file
    os.chdir(str(root_dir))
    assert check_for_requirements_file() == os.path.join(root_dir, "requirements.txt")


def test_check_for_pip_args(monkeypatch):
    test_argv = ["script_name", "arg1", "arg2", "--", "pip_arg1", "pip_arg2"]
    monkeypatch.setattr(sys, "argv", test_argv)
    result = check_for_pip_args()
    assert result == {"pip_arg1", "pip_arg2"}

    test_argv = ["script_name", "arg1", "arg2", "--"]
    monkeypatch.setattr(sys, "argv", test_argv)
    result = check_for_pip_args()
    assert not result

    test_argv = ["script_name", "arg1", "arg2"]
    monkeypatch.setattr(sys, "argv", test_argv)
    result = check_for_pip_args()
    assert not result

    test_argv = ["--"]
    monkeypatch.setattr(sys, "argv", test_argv)
    result = check_for_pip_args()
    assert not result

    test_argv = []
    monkeypatch.setattr(sys, "argv", test_argv)
    result = check_for_pip_args()
    assert not result

    test_argv = []
    monkeypatch.setattr(sys, "argv", test_argv)
    result = check_for_pip_args()
    assert not result

    test_argv = ["--", "-r", "requirements.txt"]
    monkeypatch.setattr(sys, "argv", test_argv)
    with pytest.raises(DisabledPipFlag):
        result = check_for_pip_args()


def test_parse_package_name():
    package_name = "SomePackage[suffix]>=2.0.0,<=1.0.0"
    pkg_name, pkg_suffix, pkg_specifier_set = parse_package_name(package_name)
    assert pkg_name == "SomePackage"
    assert pkg_suffix == "suffix"
    assert pkg_specifier_set == ">=2.0.0,<=1.0.0"

    package_name = "[suffix]>=2.0.0,<=1.0.0"
    with pytest.raises(WrongPkgName):
        _, _, _ = parse_package_name(package_name)

    package_name = "SomePackage>=2.0.0"
    pkg_name, pkg_suffix, pkg_specifier_set = parse_package_name(package_name)
    assert pkg_name == "SomePackage"
    assert not pkg_suffix
    assert pkg_specifier_set == ">=2.0.0"

    package_name = "SomePackage"
    pkg_name, pkg_suffix, pkg_specifier_set = parse_package_name(package_name)
    assert pkg_name == "SomePackage"
    assert not pkg_suffix
    assert not pkg_specifier_set
