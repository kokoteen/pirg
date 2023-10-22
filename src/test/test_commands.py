import logging
import os.path
import sys
import requests
import pytest
from requests import HTTPError
from pirg.pirg import initdb, install, uninstall, search
from pirg.pirg import TEMP_FILENAME

# TODO: test update all
# FIXME: try to mock packages
# FIXME: mock run_subprocess


def mock_get_package(package_name):
    status_code = 404
    response = requests.Response()
    response.status_code = status_code

    raise HTTPError(response=response)


def test_install(tmpdir, monkeypatch, caplog):
    test_dir = tmpdir.mkdir("test_dir")
    package_names = ["python-dotenv", "numpy"]
    requirements_file = test_dir.join("requirements.txt")
    caplog.set_level(logging.INFO)

    monkeypatch.setattr("pirg.utils.load_requirements_file", lambda x: set())
    monkeypatch.setattr("pirg.utils.run_subprocess", lambda pkgs, cmd, args: None)

    # check if requirements exist
    install(package_names=package_names, requirements_path=requirements_file.strpath)
    assert requirements_file.exists()

    # test installing already installed packages
    install(package_names=package_names, requirements_path=requirements_file.strpath)
    assert "Nothing to install" in [rec.message for rec in caplog.records]

    # test installing with no packages specified (nothing to install)
    install(package_names=[], requirements_path=requirements_file.strpath)
    assert "Nothing to install" in [rec.message for rec in caplog.records]

    # test installing with disabled pip arguments but no packages specified
    monkeypatch.setattr(sys, "argv", ["--", "-U"])
    with pytest.raises(SystemExit) as excinfo:
        install(package_names=[], requirements_path=requirements_file.strpath)
    assert excinfo.value.code == 4001
    monkeypatch.setattr(sys, "argv", [])

    # test wrong package name
    package_names = ["package1"]
    monkeypatch.setattr("pirg.utils.get_package", mock_get_package)
    with pytest.raises(SystemExit) as excinfo:
        install(package_names=package_names, requirements_path=requirements_file.strpath)
    assert excinfo.value.code == 404

    # test installing with no args
    install(package_names=[])
    assert "Nothing to install" in [rec.message for rec in caplog.records]


def test_uninstall(tmpdir, monkeypatch, caplog):
    test_dir = tmpdir.mkdir("test_dir")
    package_names = ["python-dotenv", "numpy"]
    requirements_file = test_dir.join("requirements.txt")
    caplog.set_level(logging.INFO)

    monkeypatch.setattr("pirg.utils.load_requirements_file", lambda x: set())
    monkeypatch.setattr("pirg.utils.run_subprocess", lambda pkgs, cmd, args: None)

    # create requirements file
    install(package_names=package_names, requirements_path=requirements_file.strpath)
    monkeypatch.setattr(sys, "argv", ["--", "-y"])

    # uninstalling already installed packages
    uninstall(package_names=package_names, requirements_path=requirements_file.strpath)
    assert os.path.getsize(requirements_file) == 0

    # uninstalling already uninstalled packages
    uninstall(package_names=package_names, requirements_path=requirements_file.strpath)
    assert "Nothing to remove" in [rec.message for rec in caplog.records]

    # test uninstalling all from requirements
    monkeypatch.setattr(sys, "argv", [])
    install(package_names=package_names, requirements_path=requirements_file.strpath)
    monkeypatch.setattr(sys, "argv", ["--", "-y"])
    uninstall(package_names=[], requirements_path=requirements_file.strpath, delete_all=True)
    assert os.path.getsize(requirements_file) == 0

    # test uninstalling with no packages specified (nothing to uninstall)
    uninstall(package_names=[], requirements_path=requirements_file.strpath)
    assert "Nothing to remove" in [rec.message for rec in caplog.records]

    # test uninstalling with pip disabled arguments but no packages specified
    monkeypatch.setattr(sys, "argv", ["--", "-r", f"{requirements_file.strpath}"])
    with pytest.raises(SystemExit) as excinfo:
        uninstall(package_names=[], requirements_path=requirements_file.strpath)
    assert excinfo.value.code == 4001
    monkeypatch.setattr(sys, "argv", [])

    # test wrong package name
    package_names = ["package1"]
    uninstall(package_names=package_names, requirements_path=requirements_file.strpath)
    assert "Nothing to remove" in [rec.message for rec in caplog.records]


def test_initdb(monkeypatch, tmpdir, caplog):
    def mock_data():
        return "package1\npackage2\npackage3"

    caplog.set_level(logging.INFO)

    monkeypatch.setattr("tempfile.gettempdir", lambda: tmpdir.strpath)
    monkeypatch.setattr(
        "pirg.utils.check_if_pypi_simple_is_modified.__code__",
        (lambda: False).__code__,
    )
    monkeypatch.setattr(
        "pirg.utils.get_pypi_simple_data.__code__",
        mock_data.__code__,
    )

    # default
    initdb()
    assert "Database initialized" in [rec.message for rec in caplog.records]

    # already initialized
    initdb()
    assert "Database already initialized" in [rec.message for rec in caplog.records]

    # update
    initdb(update=True)
    assert "Database is up-to-date" in [rec.message for rec in caplog.records]


def test_search(tmpdir, monkeypatch, caplog):
    package_names = ["package1", "paCKage2", "Package3"]
    filename = os.path.join(tmpdir.strpath, TEMP_FILENAME)
    with open(filename, "w") as file:
        for package in package_names:
            file.write(package + "\n")

    caplog.set_level(logging.INFO)

    monkeypatch.setattr("tempfile.gettempdir", lambda: tmpdir.strpath)
    monkeypatch.setattr(
        "pirg.utils.check_if_pypi_simple_is_modified.__code__",
        (lambda: False).__code__,
    )

    user_input = "package3"
    search(user_input)
    assert "Search result: ['Package3', 'paCKage2', 'package1']" in [
        rec.message for rec in caplog.records
    ]

    user_input = ""
    search(user_input)
    assert "Search result: []" in [rec.message for rec in caplog.records]

    with pytest.raises(TypeError):
        search()

    monkeypatch.setattr(
        "pirg.utils.check_if_pypi_simple_is_modified.__code__",
        (lambda: True).__code__,
    )
    user_input = ""
    search(user_input)
    assert (
        "Current list of package names is out of date. Please update with `initdb --update`"
        in [rec.message for rec in caplog.records]
    )

    filename = os.path.join(tmpdir.strpath, TEMP_FILENAME)
    with open(filename, "w") as file:
        file.write("")

    user_input = ""
    with pytest.raises(SystemExit) as excinfo:
        search(user_input)
    assert excinfo.value.code == 4004
