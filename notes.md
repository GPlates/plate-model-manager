#### activate/deactivate the python virtual env

- `/opt/homebrew/bin/python3 -m venv pmm-venv` (macos system python is no good.)
- `source pmm-venv/bin/activate`
- `pip3 install -r plate-model-manager-venv.txt`
- `deactivate`

#### build and install the package

- `pip3 install pip-tools`
- `pip-compile pyproject.toml`
- `pip3 install .`

#### test

- The file .env must be in current working directory. Alternatively you can set the env variables instead.

#### doc

- `pip-compile pyproject.toml`
- `pip3 install .`
- `pip install -U sphinx sphinx_rtd_theme`
- `sphinx-apidoc -o doc/source src/plate_model_manager/`
- `make html`

⚠️You need to re-install the plate_model_manager, otherwise the sphinx will keep using the installed stable version(old code).

#### Publish to PyPI

- `pip install build twine`
- `python -m build`
- `twine check dist/*`
- `twine upload -r testpypi dist/*`
- `twine upload dist/*`
- username is \_\_token\_\_
- password is the API token. go to https://pypi.org/manage/account/token/ to get a one-time token

#### gh-pages branch

- `git clone https://github.com/gplates/plate-model-manager.git gh-pages.git`
- `git checkout --orphan gh-pages`
- `git rm -rf .`
- `cp -rf ../doc/build/html/* .`
- `touch .nojekyll`
- `git add .`
- `git commit -m"initial gh-pages checkin"`
- `git push --set-upstream origin gh-pages`

create GH_PAGE_COMMIT_TOKEN for the github workflow
