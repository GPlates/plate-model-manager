import glob
import io
import shutil
import sys
import zipfile
from datetime import datetime
from pathlib import Path

import requests
import utils

from plate_model_manager.zenodo import ZenodoRecord

# https://zenodo.org/doi/10.5281/zenodo.10346399
record = ZenodoRecord(10346399)
latest_id = record.get_latest_version_id()
print(f"The latest version ID is: {latest_id}.")
filenames = record.get_filenames(latest_id)
print(f"The file names in the latest version: {filenames}")
idx = 0
for i in range(len(filenames)):
    if filenames[i].startswith("Merdith_etal_2021_ESR"):
        idx = i
        break
file_links = record.get_file_links(latest_id)
print(f"The file links in the latest version: {file_links}")

model_path = utils.get_model_path(sys.argv, "merdith2021")
zip_path = "Merdith_etal_2021_ESR"

info_fp = open(f"{model_path}/info.txt", "w+")
info_fp.write(f"{datetime.now()}\n")

zip_url = file_links[idx]
r = requests.get(
    zip_url,
    allow_redirects=True,
)
info_fp.write(f"Download zip file from {zip_url}\n")
if r.status_code in [200]:
    z = zipfile.ZipFile(io.BytesIO(r.content))
    z.extractall(f"{model_path}/{zip_path}")

# zip topologies
files = glob.glob(f"{model_path}/{zip_path}/Topologies/*.gpml", recursive=True)
utils.zip_files(files, f"{model_path}/Topologies.zip", "Topologies", log_fp=info_fp)

# zip coastlines
files = [
    f"{model_path}/{zip_path}/Coastlines/shapes_coastlines_Merdith_et_al_v2.gpmlz",
]
utils.zip_files(files, f"{model_path}/Coastlines.zip", "Coastlines", log_fp=info_fp)


# zip static polygons
files = [
    f"{model_path}/{zip_path}/StaticPolygons/shapes_static_polygons_Merdith_etal.gpml"
]

utils.zip_files(
    files, f"{model_path}/StaticPolygons.zip", "StaticPolygons", log_fp=info_fp
)

# zip rotations
files = [f"{model_path}/{zip_path}/Rotations/1000_0_rotfile_Merdith_etal.rot"]
utils.zip_files(files, f"{model_path}/Rotations.zip", "Rotations", log_fp=info_fp)

# zip ContinentalPolygons
files = [f"{model_path}/{zip_path}/Continents/shapes_continents.gpml"]
utils.zip_files(
    files,
    f"{model_path}/ContinentalPolygons.zip",
    "ContinentalPolygons",
    log_fp=info_fp,
)

# zip COBs. this model does not provide COBs, use the continental polygons as COBs
files = [f"{model_path}/{zip_path}/Continents/shapes_continents.gpml"]
utils.zip_files(
    files,
    f"{model_path}/COBs.zip",
    "COBs",
    log_fp=info_fp,
)

# zip Cratons
files = [f"{model_path}/{zip_path}/Cratons/shapes_cratons_Merdith_etal.gpml"]

utils.zip_files(files, f"{model_path}/Cratons.zip", "Cratons", log_fp=info_fp)

shutil.rmtree(f"{model_path}/{zip_path}")

info_fp.close()
