#!/bin/bash

source ./plate-model-manager-venv/bin/activate

pip-compile pyproject.toml
pip3 install .
pip3 install -U sphinx sphinx_rtd_theme
sphinx-autogen -o doc/source/generated doc/source/*.rst
cd doc
make html
