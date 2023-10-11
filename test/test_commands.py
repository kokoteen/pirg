import os.path
import sys
import requests
import pytest
from requests import HTTPError
from pirg.pirg import install, uninstall


def mock_get_name_version(package_name):
    status_code = 404
    response = requests.Response()
    response.status_code = status_code

    raise HTTPError(response=response)


def test_install(tmpdir, monkeypatch):
    test_dir = tmpdir.mkdir("test_dir")
    package_names = ["python-dotenv", "numpy"]
    requirements_file = test_dir.join("requirements.txt")

    monkeypatch.setattr("pirg.utils.load_requirements_file", lambda x: set())
    monkeypatch.setattr("pirg.utils.run_subprocess", lambda pkgs, cmd, args: None)

    # check if requirements exist
    install(package_names=package_names, requirements_path=requirements_file.strpath)
    assert requirements_file.exists()

    # installing already installed packages
    with pytest.raises(SystemExit) as excinfo:
        install(package_names=package_names, requirements_path=requirements_file.strpath)
    assert excinfo.value.code == 4000

    # test installing with no packages specified (nothing to install)
    with pytest.raises(SystemExit) as excinfo:
        install(package_names=[], requirements_path=requirements_file.strpath)
    assert excinfo.value.code == 4000

    # test installing with pip arguments but no packages specified
    monkeypatch.setattr(sys, "argv", ["--", "-U"])
    with pytest.raises(SystemExit) as excinfo:
        install(package_names=[], requirements_path=requirements_file.strpath)
    assert excinfo.value.code == 1
    monkeypatch.setattr(sys, "argv", [])

    # test wrong package name
    package_names = ["package1"]
    monkeypatch.setattr("pirg.utils.get_name_version", mock_get_name_version)
    with pytest.raises(SystemExit) as excinfo:
        install(package_names=package_names, requirements_path=requirements_file.strpath)
    assert excinfo.value.code == 404


def test_uninstall(tmpdir, monkeypatch):
    test_dir = tmpdir.mkdir("test_dir")
    package_names = ["python-dotenv", "numpy"]
    requirements_file = test_dir.join("requirements.txt")

    monkeypatch.setattr("pirg.utils.load_requirements_file", lambda x: set())
    monkeypatch.setattr("pirg.utils.run_subprocess", lambda pkgs, cmd, args: None)
    # FIXME: mock run_subprocess

    # create requirements file
    install(package_names=package_names, requirements_path=requirements_file.strpath)
    monkeypatch.setattr(sys, "argv", ["--", "-y"])

    # uninstalling already installed packages
    uninstall(package_names=package_names, requirements_path=requirements_file.strpath)
    assert os.path.getsize(requirements_file) == 0

    # uninstalling already uninstalled packages
    with pytest.raises(SystemExit) as excinfo:
        uninstall(package_names=package_names, requirements_path=requirements_file.strpath)
    assert excinfo.value.code == 4000

    # test uninstalling all from requirements
    monkeypatch.setattr(sys, "argv", [])
    install(package_names=package_names, requirements_path=requirements_file.strpath)
    monkeypatch.setattr(sys, "argv", ["--", "-y"])
    uninstall(package_names=[], requirements_path=requirements_file.strpath, delete_all=True)
    assert os.path.getsize(requirements_file) == 0

    # test uninstalling with no packages specified (nothing to uninstall)
    with pytest.raises(SystemExit) as excinfo:
        uninstall(package_names=[], requirements_path=requirements_file.strpath)
    assert excinfo.value.code == 4000

    # test uninstalling with pip disabled arguments but no packages specified
    monkeypatch.setattr(sys, "argv", ["--", "-r", f"{requirements_file.strpath}"])
    with pytest.raises(SystemExit) as excinfo:
        uninstall(package_names=[], requirements_path=requirements_file.strpath)
    assert excinfo.value.code == 4001
    monkeypatch.setattr(sys, "argv", [])

    # test wrong package name
    package_names = ["package1"]
    with pytest.raises(SystemExit) as excinfo:
        uninstall(package_names=package_names, requirements_path=requirements_file.strpath)
    assert excinfo.value.code == 4000
