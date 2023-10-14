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

### Adding Packages to `requirements.txt`

To add one or more packages to your project's `requirements.txt` file and install them, use the following command:

```
pirg install package_name1 package_name2 ...
```

### Removing Packages from `requirements.txt`

To remove one or more packages from your project's `requirements.txt` file and uninstall them, use the following command:

```
pirg uninstall package_name1 package_name2 ...
```

**Note:** Make sure to replace `package_name1`, `package_name2`, etc., with the actual names of the packages you want to add or remove.

### Additional Options

- You can specify a custom path for your `requirements.txt` file using the `--requirements-path` option. By default, it assumes `./requirements.txt`.

## Acknowledgments

This project makes use of the following third-party libraries, each with its own licensing terms:

- [Typer](https://github.com/tiangolo/typer)
  - **License**: [MIT License](./licenses/MIT.txt)

- [Requests](https://github.com/psf/requests)
  - **License**: [Apache License 2.0](./licenses/APACHE-2.0.txt)
 
- [Packaging](https://github.com/pypa/packaging)
  - **License**: [Apache License 2.0](./licenses/APACHE-2.0.txt)

Additionally, this project contains code under the GPL-2.0 License:

- **License**: [GPL-2.0 License](./licenses/GPL-2.0.txt)

## License

This project is licensed under the terms of the GNU General Public License, version 2.0. See the [GPL-2.0 License](./licenses/GPL-2.0.txt) file for details.

The third-party libraries Typer, Packaging and Requests are used in this project and have their own respective licenses. Please review their licenses in the [licenses](./licenses) directory for more information.


## Contributions

Contributions to **pirg** are welcome! If you encounter any issues or have suggestions for improvements, please open an issue or submit a pull request on the [GitHub repository](https://github.com/kokoteen/pirg).
