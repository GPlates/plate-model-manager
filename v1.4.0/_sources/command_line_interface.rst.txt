Command Line Interface (CLI)
============================

.. contents::
   :local:
   :depth: 2

.. note::

   To use the command line interface:
   
   * The ``plate model manager`` must have been installed. See `Installation page <installation.html>`_
   * There must be a working Internet connection.
   * The virtual environment containing ``plate model manager`` must be activated.

List available model names
--------------------------

This command will display a list of available plate model names on screen.

.. code:: console

   $ pmm ls

Show the details of a plate model
---------------------------------

This command will display the details of a plate model ``Cao2024``.

.. code:: console

   $ pmm ls Cao2024

.. note::

   Use ``pmm ls -h`` to see the details about the ``ls`` sub-command.

Download a plate model
----------------------

This command will download the plate model ``Cao2024`` into the folder ``plate-models-data-dir``.

.. code:: console

   $ pmm download Cao2024 plate-models-data-dir


Download all plate models
-------------------------

This command will download all available plate models into the current working directory.

.. code:: console

   $ pmm download all

.. note::

   Use ``pmm download -h`` to see the details about the ``download`` sub-command.
