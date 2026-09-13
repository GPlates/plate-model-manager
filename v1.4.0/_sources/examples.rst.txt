Examples
========

.. contents::
   :local:
   :depth: 2

Use with pyGPlates 
------------------

The Python code snippet below demonstrates how to use PMM with pyGPlates to reconstruct a point feature at (0,0) to 140 Ma using the Zahirovic2022 plate model. The static polygon and rotation model files are automatically downloaded by PMM.

.. code-block:: python
    :linenos:
    :emphasize-lines: 14,15,24

    import pygplates

    from plate_model_manager import PlateModelManager

    pm_manager = PlateModelManager()
    model = pm_manager.get_model("Zahirovic2022")

    # create a point feature at (0,0)
    point_feature = pygplates.Feature()
    point_feature.set_geometry(pygplates.PointOnSphere(0, 0))

    # assign plate ID
    point_feature_with_PID = pygplates.partition_into_plates(
        model.get_static_polygons(),  # 👈👀 LOOK HERE
        model.get_rotation_model(),  # 👈👀 LOOK HERE
        [point_feature],
    )

    # Reconstruct the point features.
    reconstructed_feature_geometries = []
    time = 140
    pygplates.reconstruct(
        point_feature_with_PID,
        model.get_rotation_model(),  # 👈👀 LOOK HERE
        reconstructed_feature_geometries,
        time,
    )
    print(reconstructed_feature_geometries[0].get_reconstructed_geometry().to_lat_lon())

.. seealso::
    Example notebook of using PMM with pyGPlates:
    
    - `use PMM with pyGPlates`_

.. _use PMM with pyGPlates: https://github.com/GPlates/pygplates-tutorials/blob/master/notebooks/working-with-plate-model-manager.ipynb


Use with GPlately 
-----------------

The Python code snippet below demonstrates how to use PMM with GPlately to create a PlateReconstruction object and PlotTopologies object. It also shows how to get present-day and paleo rasters from PMM and create Raster objects.

.. code-block:: python
    :linenos:
    :emphasize-lines: 17,18,22,23

    from gplately import (
    PlateModelManager,
    PlateReconstruction,
    PlotTopologies,
    PresentDayRasterManager,
    Raster,
    )
    from plate_model_manager import ReferenceFrame, GenerationMethod

    model = PlateModelManager().get_model(
        "Zahirovic2022",  # model name
        data_dir="plate-model-repo",  # the folder to save the model files
    )

    recon_model = PlateReconstruction(
        model.get_rotation_model(),
        topology_features=model.get_layer("Topologies"),
        static_polygons=model.get_layer("StaticPolygons"),
    )
    gplot = PlotTopologies(
        recon_model,
        coastlines=model.get_layer("Coastlines"),
        COBs=model.get_layer("COBs", return_none_if_not_exist=True),
        time=55,
    )
    # get present-day topography raster
    raster = Raster(PresentDayRasterManager().get_raster("topography"))
    # get paleo-agegrid raster at 100Ma from Zahirovic2022 model
    agegrid = Raster(
        model.get_raster(
            "AgeGrids",
            time=100,
            reference_frame=ReferenceFrame.PmagReferenceFrame,
            generated_from=GenerationMethod.Topologies,
        )
    )

.. seealso::
    Examples of using PMM with GPlately: 

    - `introducing plate model manager`_
    - `working with plate model manager`_

.. _introducing plate model manager: https://github.com/GPlates/gplately/blob/master/Notebooks/Examples/introducing_plate_model_manager.py
.. _working with plate model manager: https://github.com/GPlates/gplately/blob/master/Notebooks/Examples/working_with_plate_model_manager.py


Use without Internet 
--------------------

The Python code snippet below assumes you have already downloaded the Zahirovic2022 model into the ``plate-model-repo`` folder while connected to the Internet. When you run the code snippet below without Internet connection, PMM will try to load the model files from the local ``plate-model-repo`` folder. If the model files are found, PMM will load them in readonly mode and print a warning message. If the model files are not found, PMM will raise an exception.

.. seealso::

    `How to download a plate model? <command_line_interface.html#download-a-plate-model>`__

.. code-block:: python
    :linenos:
    :emphasize-lines: 7,8,9

    from plate_model_manager import PlateModel

    try:
        model = PlateModelManager().get_model("Zahirovic2022", data_dir="plate-model-repo")
    except:
        # if unable to connect to the servers, try to use the local files
        model = PlateModel(
            model_name="Zahirovic2022", data_dir="plate-model-repo", readonly=True
        )
        print("Unable to connect to the servers. Using local files in readonly mode.")

    for layer in model.get_avail_layers():
        print(model.get_layer(layer))


Use with joblib 
---------------

For better performance, load static polygon files inside each worker process instead of loading them once in the main process and passing the loaded data to workers. `pygplates.FeatureCollection <https://www.gplates.org/docs/pygplates/generated/pygplates.featurecollection>`__ objects can take a long time to pickle and unpickle.

.. code-block:: python
    :linenos:
    :emphasize-lines: 7,8,9,14,15,16

    from joblib import Parallel, delayed
    import gplately
    from plate_model_manager import PlateModelManager


    def worker_task(index, static_polygons_files):
        static_polygons = gplately.gpml.load_feature_collection_from_files(
            static_polygons_files
        )
        print(f"Worker {index} is processing {len(static_polygons)} static polygons.")
        return


    static_polygons_files = (
        PlateModelManager().get_model("Zahirovic2022").get_static_polygons()
    )

    Parallel(n_jobs=4)(
        delayed(worker_task)(idx, static_polygons_files) for idx in range(10)
    )