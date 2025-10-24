# plate-model-manager

![unittest](https://github.com/gplates/plate-model-manager/actions/workflows/unittest.yml/badge.svg)
![unittest-win](https://github.com/gplates/plate-model-manager/actions/workflows/unittest-win.yml/badge.svg)
![build-doc](https://github.com/gplates/plate-model-manager/actions/workflows/build-doc-update-gh-pages.yml/badge.svg)
[![PyPI version](https://badge.fury.io/py/plate-model-manager.svg)](https://badge.fury.io/py/plate-model-manager)
![anaconda_badge](https://anaconda.org/conda-forge/plate-model-manager/badges/version.svg)
![platforms](https://anaconda.org/conda-forge/plate-model-manager/badges/platforms.svg)
![downloads](https://anaconda.org/conda-forge/plate-model-manager/badges/downloads.svg)

Originally the `plate-model-manager` was designed for [GPlately](https://github.com/GPlates/gplately). Later, it was found also useful in other scenarios and contexts. The `plate-model-manager` downloads and manages the plate reconstruction model files. It is a dataset manager for plate tectonic reconstruction models, similar to [NPM](https://www.npmjs.com/) or [Conda](https://anaconda.org/anaconda/conda) for software packages.

Have you ever wondered where to get the plate tectonic reconstruction models for your research? Are you tired of downloading files from Internet manually and specify file paths when calling [PyGPlates](https://www.gplates.org/docs/pygplates/) functions? If the answer is yes, you probably want to check out this `plate-model-manager` Python module.

### How to install

`pip install plate-model-manager`

or

`conda install conda-forge::plate-model-manager`

For more information regarding installation, visit [this page](https://gplates.github.io/plate-model-manager/latest/installation.html)

### How to use the Python module

Visit [this page](https://gplates.github.io/plate-model-manager/latest/basic_usages.html) to see how to use the `plate-model-manager` package in assorted scenarios.

### How to use the command line

Visit [this page](https://gplates.github.io/plate-model-manager/latest/command_line_interface.html) to see how to use the `plate-model-manager` command lines.

### Documentation

- [latest dev](https://gplates.github.io/plate-model-manager/latest/)
- [latest stable](https://gplates.github.io/plate-model-manager/stable/)
- [v1.3.0](https://gplates.github.io/plate-model-manager/v1.3.0/)
- [v1.2.0](https://gplates.github.io/plate-model-manager/v1.2.0/)

### Software adoption

Here are some software applications that make use of `the plate-model-manager` module:

- [GPlately](https://github.com/GPlates/gplately)
- [GPlates Web Service](https://github.com/GPlates/gplates-web-service)
- [PyGPlates Tutorials](https://github.com/GPlates/pygplates-tutorials)
- [GWS Python Wrapper](https://github.com/michaelchin/gwspy)

The `plate-model-manager` can also be used with the GPlates desktop application. To do so, use the `plate-model-manager` command-line tool to download the plate model files, then open them in GPlates. This provides a convenient alternative to manually downloading files from the internet.

### Dependencies

- aiohttp
- requests
- nest_asyncio

### Event loop RuntimeError

For Jupyter Notebook, Web Server or GUI application users, you need the following two lines to workaround the event loop RuntimeError.
If you do not add these two lines, the PlateModelManager still works. But you will see a warning message. You can ignore the warning message safely.
If the warning message bothers you, add the two lines before calling PlateModelManager.

https://anaconda.org/conda-forge/nest-asyncio/

```python
import nest_asyncio
nest_asyncio.apply()
```
