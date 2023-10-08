import subprocess
import os
import sys
import responses
import requests
import pytest
from requests import HTTPError

from pirg.pirg import install
from pirg.custom_exceptions import NothingToDo
from pirg.utils import (
    PYPI_URL,
    check_for_pip_args,
    load_requirements_file,
    get_name_version,
    create_requirements,
    run_subprocess,
    find_requirements_file,
)


def mock_get_name_version(package_name):
    status_code = 404
    response = requests.Response()
    response.status_code = status_code

    raise HTTPError(response=response)


def test_install(tmpdir, monkeypatch):
    test_dir = tmpdir.mkdir("test_dir")
    package_names = ["requests", "numpy"]
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
