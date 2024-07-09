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

# https://zenodo.org/doi/10.5281/zenodo.11392268
record = ZenodoRecord(11392268)
latest_id = record.get_latest_version_id()
print(f"The latest version ID is: {latest_id}.")
filenames = record.get_filenames(latest_id)
print(f"The file names in the latest version: {filenames}")
idx = 0
for i in range(len(filenames)):
    if filenames[i].startswith("Alfonso_etal_2024_modClennettMuller"):
        idx = i
        break
file_links = record.get_file_links(latest_id)
print(f"The file links in the latest version: {file_links}")

model_path = utils.get_model_path(sys.argv, "alfonso2024")

info_fp = open(f"{model_path}/info.txt", "w+")
info_fp.write(f"{datetime.now()}\n")

local_data_path = f"{model_path}/download-data"

zip_url = file_links[idx]
r = requests.get(
    zip_url,
    allow_redirects=True,
)
info_fp.write(f"Download zip file from {zip_url}\n")
Path(local_data_path).mkdir(parents=True, exist_ok=True)
if r.status_code in [200]:
    z = zipfile.ZipFile(io.BytesIO(r.content))
    z.extractall(local_data_path)


# zip rotations
files = glob.glob(f"{local_data_path}/Rotations/*.rot", recursive=True)
utils.zip_files(files, f"{model_path}/Rotations.zip", "Rotations", log_fp=info_fp)

# zip static polygons
files = glob.glob(
    f"{local_data_path}/StaticPolygons/Clennett_2020_StaticPolygons.gpml",
    recursive=True,
)
utils.zip_files(
    files, f"{model_path}/StaticPolygons.zip", "StaticPolygons", log_fp=info_fp
)

# zip topologies
files = glob.glob(f"{local_data_path}/PlateBoundaries/*.*", recursive=True)
utils.zip_files(files, f"{model_path}/Topologies.zip", "Topologies", log_fp=info_fp)

# zip coastlines
files = glob.glob(f"{local_data_path}/Coastlines/*", recursive=True)
utils.zip_files(files, f"{model_path}/Coastlines.zip", "Coastlines", log_fp=info_fp)


# zip Isochrons
files = glob.glob(f"{local_data_path}/Isochrons/*", recursive=True)
utils.zip_files(files, f"{model_path}/Isochrons.zip", "Isochrons", log_fp=info_fp)

# zip Terranes
utils.zip_folder(
    f"{local_data_path}/Terranes",
    f"{model_path}/Terranes.zip",
    "Terranes",
    log_fp=info_fp,
)

# zip DeformingMeshes
files = glob.glob(f"{local_data_path}/DeformingMeshes/*.*", recursive=True)
utils.zip_files(
    files, f"{model_path}/DeformingMeshes.zip", "DeformingMeshes", log_fp=info_fp
)

shutil.rmtree(f"{model_path}/download-data")
