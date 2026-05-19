API Reference
=============

.. contents::
   :local:
   :depth: 2

PlateModelManager
-----------------

The :py:class:`plate_model_manager.PlateModelManager` class manages the plate reconstruction models. 
You can use this class to do the things listed below.

- Get a list of available model names.
- Get a :py:class:`plate_model_manager.PlateModel` object for a specific model name.
- Download all models into a folder.

.. autoclass:: plate_model_manager.PlateModelManager
    :members:
    :undoc-members:
    :special-members: __init__
    :exclude-members: models
    :no-index: 

PlateModel
----------

The :py:class:`plate_model_manager.PlateModel` class manages the files in a plate reconstruction model.
You can use this class to do the things listed below.

- Get a list of available layers in a plate model.
- Download the rotation file(s).
- Download the layer file(s) for a specific layer.
- Download time-dependent raster files.
- Download all files in a plate model.

.. autoclass:: plate_model_manager.PlateModel
    :members:
    :undoc-members:
    :special-members: __init__
    :exclude-members: model
    :no-index: 
    
PresentDayRasterManager
-----------------------

The :py:class:`plate_model_manager.PresentDayRasterManager` class manages the present-day rasters.
You can use this class to do the things listed below.

- Get a list of available present-day raster names.
- Download a specific present-day raster.

.. autoclass:: plate_model_manager.PresentDayRasterManager
    :members:
    :undoc-members:
    :special-members: __init__
    :exclude-members: rasters
    :no-index: 

Auxiliary Function
------------------

Auxiliary functon for users' convenience.

.. autofunction:: plate_model_manager.get_plate_model
    :no-index: 
    
