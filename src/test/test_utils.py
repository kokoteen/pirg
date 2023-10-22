import os
import sys
import responses
import pytest
from packaging.specifiers import Version
from pirg.exceptions import DisabledPipFlag, EmptyDatabase, WrongSpecifierSet, WrongPkgName
from pirg.utils import (
    PYPI_URL,
    check_for_pip_args,
    fuzzy_search,
    load_requirements_file,
    get_package,
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


def test_load_requirements_file(temporary_requirements_file):
    # test with file
    requirements = load_requirements_file(temporary_requirements_file)
    assert len(requirements) == 1
    assert "package1" in [pkg.name for pkg in requirements]

    # test empty file location
    requirements = load_requirements_file("")
    assert not requirements


def test_get_package():
    package_name = [
        "package1",
        "package2",
        "package3",
        "package4",
    ]

    specifier_set = ["", "", ">1.1", ">1.1"]
    mock_response_body = [
        {
            "releases": {
                "1.0.0": [{"requires_python": ">=3.8"}],
                "1.1.0": [{"requires_python": ">=3.8"}],
                "1.2.0": [{"requires_python": ">=3.8"}],
            }
        },
        {
            "releases": {
                "1.0.0": [{"requires_python": None}],
                "1.1.0": [{"requires_python": None}],
                "1.2.0": [{"requires_python": None}],
            }
        },
        {
            "releases": {
                "1.0.0": [{"requires_python": ">=3.8"}],
                "1.1.0": [{"requires_python": ">=3.8"}],
                "1.2.0": [{"requires_python": ">=3.8"}],
            }
        },
        {
            "releases": {
                "1.0.0": [{"requires_python": None}],
                "1.1.0": [{"requires_python": None}],
                "1.2.0": [{"requires_python": None}],
            }
        },
    ]

    for pkg, ss, mres in zip(package_name, specifier_set, mock_response_body):
        url = PYPI_URL(pkg)

        with responses.RequestsMock() as rsps:
            rsps.add(responses.GET, url, json=mres)
            result = get_package(pkg + ss)

            assert result.name == pkg
            assert Version("1.2.0") in result.specifier_set

    package_name = "package5"
    specifier_set = "==3.0"
    mock_response_body = {
        "releases": {
            "1.0.0": [{"requires_python": ">=3.8"}],
            "1.1.0": [{"requires_python": ">=3.8"}],
            "1.2.0": [{"requires_python": ">=3.8"}],
        }
    }
    url = PYPI_URL(package_name)

    with pytest.raises(WrongSpecifierSet):
        with responses.RequestsMock() as rsps:
            rsps.add(responses.GET, url, json=mock_response_body)
            _ = get_package(package_name + specifier_set)


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
        _ = check_for_pip_args()


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


def test_fuzzy_search():
    test_db = {
        "package1": "Package1",
        "package2": "Package2",
        "package3": "Package3",
    }

    search_term = "Package1"

    output = fuzzy_search(search_term, test_db)
    assert search_term in output

    search_term = ""
    output = fuzzy_search(search_term, test_db)
    assert not output

    search_term = "ASdwe"
    output = fuzzy_search(search_term, test_db)
    assert not output

    with pytest.raises(EmptyDatabase):
        _ = fuzzy_search(search_term, {})
