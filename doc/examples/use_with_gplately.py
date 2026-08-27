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
