import glob
import shutil
import utils

# https://zenodo.org/doi/10.5281/zenodo.10596349
files_path = "z-files"
model_path, info_fp = utils.download_files_from_zenodo(
    "10596349", "gurnis2012", "Gurnis_etal_2012_CompGeosci", files_path
)

# zip Rotations
files = glob.glob(f"{model_path}/{files_path}/Rotations/*.rot")
utils.zip_files_ex(files, model_path, "Rotations", info_fp)

# zip StaticPolygons
files = glob.glob(f"{model_path}/{files_path}/StaticPolygons/*")
utils.zip_files_ex(files, model_path, "StaticPolygons", info_fp)

# zip Coastlines
files = glob.glob(f"{model_path}/{files_path}/Coastlines/*")
utils.zip_files_ex(files, model_path, "Coastlines", info_fp)

# zip Topologies
files = glob.glob(f"{model_path}/{files_path}/Topologies/*")
utils.zip_files_ex(files, model_path, "Topologies", info_fp)


shutil.rmtree(f"{model_path}/{files_path}")
print("Done")
