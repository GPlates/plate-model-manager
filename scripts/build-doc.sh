#!/bin/bash

source ./plate-model-manager-venv/bin/activate

pip-compile pyproject.toml
pip3 install .
pip3 install -U sphinx sphinx_rtd_theme

# Use module invocation so build does not depend on PATH-installed script wrappers.
python3 -m sphinx.ext.autosummary.generate -o doc/source/generated doc/source/*.rst
cd doc
python3 -m sphinx -b html source build/html
