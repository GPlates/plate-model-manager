#!/bin/bash

source ./plate-model-manager-venv/bin/activate

pip-compile pyproject.toml
pip3 install .
rm doc/source/plate_model_manager.rst
rm doc/source/modules.rst
rm doc/source/plate_model_manager.utils.rst
pip3 install -U sphinx sphinx_rtd_theme
sphinx-apidoc -f -o doc/source src/plate_model_manager/
cd doc
make html
