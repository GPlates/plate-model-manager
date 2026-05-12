Plate Model Manager Documentation Development
=============================================

Originally the ``plate-model-manager`` was designed for GPlately_. 
Later, it was found also useful in other scenarios and contexts. 
The ``plate-model-manager`` downloads and manages the plate reconstruction model files. 
It is a dataset manager for plate tectonic reconstruction models, similar to NPM_ or Conda_ for software packages.

Have you ever wondered where to get the plate tectonic reconstruction models for your research? 
Are you tired of downloading files from Internet manually and specify file paths when calling PyGPlates_ functions? 
If the answer is yes, you probably want to check out this ``plate-model-manager`` Python module.



.. toctree::
   :caption: User Guide
   :maxdepth: 3

   installation
   basic_usages
   examples
   command_line_interface
   api
   plate_models

.. Hidden TOCs

.. toctree::
   :caption: everything under the hood 
   :maxdepth: 2
   :hidden:

   modules

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`

.. _GPlately: https://github.com/GPlates/gplately
.. _NPM: https://www.npmjs.com/
.. _Conda: https://anaconda.org/anaconda/conda
.. _PyGPlates: https://www.gplates.org/docs/pygplates/