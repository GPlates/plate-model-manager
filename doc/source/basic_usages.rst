Basic Usages
============

.. contents::
   :local:
   :depth: 2

Download rotation files
-----------------------

The Python code below downloads the ``rotation`` files from the ``Muller2025`` model into a local folder ``plate-models-data-dir`` 
and displays the file paths on screen.

.. code-block:: python
    :linenos:
    :emphasize-lines: 4,6

    from plate_model_manager import PlateModelManager

    mgr = PlateModelManager()
    muller2025_model = mgr.get_model("Muller2025", data_dir="plate-models-data-dir")
    # download the rotation files and print their local paths
    print(muller2025_model.get_rotation_model())

.. seealso::
    See the :ref:`list-all-models` section for how to get a list of available models.

Download a layer
----------------

The Python code below downloads the ``Coastlines`` layer from the ``Muller2025`` model 
and displays the file paths on screen.

.. code-block:: python
    :linenos:
    :emphasize-lines: 4,6
   
    from plate_model_manager import PlateModelManager

    mgr = PlateModelManager()
    muller2025_model = mgr.get_model("Muller2025", data_dir="plate-models-data-dir")
    # download Coastlines from model Muller2025 and display the local path
    print(muller2025_model.get_layer("Coastlines"))

.. seealso::
    See the :ref:`list-all-layers` section for how to get a list of available layers.

.. _list-all-layers:

List all layer names
--------------------

The Python code below displays a list of available layers in the model **Muller2025** on the screen.

.. code-block:: python
    :linenos:
    :emphasize-lines: 4,6
   
    from plate_model_manager import PlateModelManager

    mgr = PlateModelManager()
    muller2025_model = mgr.get_model("Muller2025", data_dir="plate-models-data-dir")
    # display a list of available layers in model Muller2025
    print(muller2025_model.get_avail_layers())

.. _list-all-models:

List all available model names
------------------------------

The Python code below displays a list of available plate models.

.. code-block:: python
    :linenos:
    :emphasize-lines: 3

    from plate_model_manager import PlateModelManager

    print(PlateModelManager().get_available_model_names())