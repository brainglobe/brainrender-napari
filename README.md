[![Docs](https://img.shields.io/badge/Docs-brainrender--napari-blue)](https://brainglobe.info/documentation/index.html)
[![Get in Touch](https://img.shields.io/badge/Get%20in%20Touch-BrainGlobe-blue)](https://brainglobe.info/contact.html)
[![License](https://img.shields.io/badge/License-BSD%203--Clause-blue.svg)](https://opensource.org/licenses/BSD-3-Clause)
[![Tests](https://github.com/brainglobe/brainrender-napari/actions/workflows/test_and_deploy.yml/badge.svg)](https://github.com/brainglobe/brainrender-napari/actions/workflows/test_and_deploy.yml)
[![Codecov](https://codecov.io/gh/brainglobe/brainrender-napari/graph/badge.svg)](https://codecov.io/gh/brainglobe/brainrender-napari)
[![Python Version](https://img.shields.io/pypi/pyversions/brainrender-napari.svg)](https://pypi.org/project/brainrender-napari)
[![PyPI](https://img.shields.io/pypi/v/brainrender-napari.svg)](https://pypi.org/project/brainrender-napari)
[![Conda](https://anaconda.org/conda-forge/brainrender-napari/badges/version.svg)](https://anaconda.org/conda-forge/brainrender-napari)
[![Napari Hub](https://img.shields.io/endpoint?url=https://api.napari-hub.org/shields/brainrender-napari)](https://www.napari-hub.org/plugins/brainrender-napari)
[![Downloads](https://static.pepy.tech/badge/brainrender-napari)](https://pepy.tech/project/brainrender-napari)
[![Code Style: Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/format.json)](https://github.com/astral-sh/ruff)
[![Pre-commit](https://img.shields.io/badge/pre--commit-enabled-green?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)
[![Contributions Welcome](https://img.shields.io/badge/Contributions-Welcome-green.svg)](https://brainglobe.info/community/developers/index.html)

# brainrender-napari

Visualisation and management of BrainGlobe atlases in napari.

----------------------------------

A napari plugin to visualise and manage BrainGlobe atlases. `brainrender-napari` aims to port the functionality of [`brainrender`](https://github.com/brainglobe/brainrender) to [`napari`](https://napari.org/stable/).
![add-region-brainrender-napari](https://github.com/brainglobe/brainrender-napari/assets/10500965/24fd3752-0ba7-4f47-aabf-5de22ff0f69b)

## Usage

Check out the ["Visualising an atlas in napari"](https://brainglobe.info/tutorials/visualise-atlas-napari.html) tutorial in the BrainGlobe documentation.

## Installation

We strongly recommend to use a virtual environment manager (like `conda` or `venv`). The installation instructions below will not specify the Qt backend for napari, and you will therefore need to install that separately. Please see [the `napari` installation instructions](https://napari.org/stable/tutorials/fundamentals/installation.html) for further advice on this.

You can install `brainrender-napari` via [pip]:

    pip install brainrender-napari

To install latest development version :

    pip install git+https://github.com/brainglobe/brainrender-napari.git

## Seeking help or contributing
We are always happy to help users of our tools, and welcome any contributions. If you would like to get in contact with us for any reason, please see the [contact page of our website](https://brainglobe.info/contact.html).

## License

Distributed under the terms of the [BSD-3] license,
"brainrender-napari" is free and open source software

## Acknowledgements

This [@napari] plugin was generated with [Cookiecutter] using [@napari]'s [cookiecutter-napari-plugin] template and the [Neuroinformatics Unit's template](https://github.com/neuroinformatics-unit/python-cookiecutter).

[Cookiecutter]: https://github.com/audreyr/cookiecutter
[@napari]: https://github.com/napari
[cookiecutter-napari-plugin]: https://github.com/napari/cookiecutter-napari-plugin
[BSD-3]: http://opensource.org/licenses/BSD-3-Clause
[file an issue]: https://github.com/brainglobe/brainrender-napari/issues
[tox]: https://tox.readthedocs.io/en/latest/
[pip]: https://pypi.org/project/pip/
[PyPI]: https://pypi.org/
