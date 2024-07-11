# brainrender-napari

[![License BSD-3](https://img.shields.io/pypi/l/brainrender-napari.svg?color=green)](https://github.com/brainglobe/brainrender-napari/raw/main/LICENSE)
[![PyPI](https://img.shields.io/pypi/v/brainrender-napari.svg?color=green)](https://pypi.org/project/brainrender-napari)
[![Python Version](https://img.shields.io/pypi/pyversions/brainrender-napari.svg?color=green)](https://python.org)
[![tests](https://github.com/brainglobe/brainrender-napari/workflows/tests/badge.svg)](https://github.com/brainglobe/brainrender-napari/actions)
[![codecov](https://codecov.io/gh/brainglobe/brainrender-napari/branch/main/graph/badge.svg)](https://codecov.io/gh/brainglobe/brainrender-napari)
[![napari hub](https://img.shields.io/endpoint?url=https://api.napari-hub.org/shields/brainrender-napari)](https://napari-hub.org/plugins/brainrender-napari)

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
