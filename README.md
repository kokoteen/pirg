# PiRG - Pip Requirements Generator

***

[![License: GPL-2.0](https://img.shields.io/badge/License-GPL%20v2-blue.svg)](https://www.gnu.org/licenses/gpl-2.0.html)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)

## Description

**PiRG** (Pip Requirements Generator) is a minimalist command-line tool designed for Python developers who prefer a simple approach to managing project dependencies. Unlike traditional requirements files that include all installed packages and their dependencies, PiRG focuses on capturing only the primary packages you install using `pip install`. This makes your `requirements.txt` file concise and easier to manage.

With PiRG, you can also pass additional `pip install` or `pip uninstall` options to customize package installation and removal.

### Philosophy
Instead of looking back and searching through project files which packages are needed for project, with PiRG you record each installed package. If you don't want to put some package into `requirements.txt` just use `pip`.
## Installation

### Prerequisites

Before using **pirg**, make sure you have Python 3.8 or higher installed on your system.

### Installation Steps

1. Install **pirg** using pip:

    ```
    pip install pirg
    ```

2. Verify the installation by running:

    ```
    pirg --help
    ```

3. You're ready to use **pirg**!

## Usage

- install - Add package to environment and `requirements.txt`
- uninstall - Remove package from environment and `requirements.txt`
- search - Search PyPI for package

## Acknowledgments & License

This project makes use of the following third-party libraries, each with its own licensing terms:

- [Typer](https://github.com/tiangolo/typer) ([MIT License](./licenses/MIT.txt))
- [Requests](https://github.com/psf/requests) ([Apache License 2.0](./licenses/APACHE-2.0.txt))
- [packaging](https://github.com/pypa/packaging) ([Apache License 2.0](./licenses/APACHE-2.0.txt))
- [fuzzywuzzy](https://github.com/seatgeek/fuzzywuzzy) ([GPL-2.0 License](./licenses/GPL-2.0.txt))
- [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/) ([MIT License](./licenses/MIT.txt))

Additionally, this project contains code under the [GPL-2.0 License](./licenses/GPL-2.0.txt)

## Contributions

Contributions to **pirg** are welcome! If you encounter any issues or have suggestions for improvements, please open an issue or submit a pull request on the [GitHub repository](https://github.com/kokoteen/pirg).
