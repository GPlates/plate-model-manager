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
