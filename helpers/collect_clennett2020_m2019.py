import glob
import io
import os
import shutil
import sys
import zipfile
from datetime import datetime

import requests
import utils

from plate_model_manager.zenodo import ZenodoRecord

# https://zenodo.org/doi/10.5281/zenodo.10348270
record = ZenodoRecord(10348270)
latest_id = record.get_latest_version_id()
print(f"The latest version ID is: {latest_id}.")
filenames = record.get_filenames(latest_id)
print(f"The file names in the latest version: {filenames}")
idx = 0
for i in range(len(filenames)):
    if filenames[i].startswith("Clennett_etal_2020_M2019"):
        idx = i
        break
file_links = record.get_file_links(latest_id)
print(f"The file links in the latest version: {file_links}")

model_path = utils.get_model_path(sys.argv, "clennett2020_m2019")
zip_path = "Clennett_etal_2020_M2019"

info_fp = open(f"{model_path}/info.txt", "w+")
info_fp.write(f"{datetime.now()}\n")

# download the model zip file
zip_url = file_links[idx]
info_fp.write(f"Download zip file from {zip_url}\n")
r = requests.get(zip_url, allow_redirects=True, verify=True)
if r.status_code in [200]:
    z = zipfile.ZipFile(io.BytesIO(r.content))
    z.extractall(f"{model_path}/{zip_path}")

# zip Rotations
with zipfile.ZipFile(
    f"{model_path}/Rotations.zip",
    mode="w",
    compression=zipfile.ZIP_DEFLATED,
    compresslevel=9,
) as f_zip:
    files = glob.glob(f"{model_path}/{zip_path}/Rotations/*.rot")
    files += glob.glob(f"{model_path}/{zip_path}/DeformingMeshes/*.rot")
    info_fp.write(f"Zip Rotations:\n")
    for f in files:
        f_zip.write(f, f"Rotations/{os.path.basename(f)}")
        info_fp.write(f"\t{f}\n")


# zip StaticPolygons
with zipfile.ZipFile(
    f"{model_path}/StaticPolygons.zip",
    mode="w",
    compression=zipfile.ZIP_DEFLATED,
    compresslevel=9,
) as f_zip:
    f = f"{model_path}/{zip_path}/StaticPolygons/Clennett_2020_StaticPolygons.gpml"
    info_fp.write(f"Zip StaticPolygons:\n")
    info_fp.write(f"\t{f}\n")
    f_zip.write(f, f"StaticPolygons/{os.path.basename(f)}")


# zip Coastlines
with zipfile.ZipFile(
    f"{model_path}/Coastlines.zip",
    mode="w",
    compression=zipfile.ZIP_DEFLATED,
    compresslevel=9,
) as f_zip:
    files = glob.glob(
        f"{model_path}/{zip_path}/Coastlines/Clennett_etal_2020_Coastlines.gpml"
    )
    info_fp.write(f"Zip Coastlines:\n")
    for f in files:
        f_zip.write(f, f"Coastlines/{os.path.basename(f)}")
        info_fp.write(f"\t{f}\n")

# zip Topologies
with zipfile.ZipFile(
    f"{model_path}/Topologies.zip",
    mode="w",
    compression=zipfile.ZIP_DEFLATED,
    compresslevel=9,
) as f_zip:
    files = glob.glob(f"{model_path}/{zip_path}/DeformingMeshes/*.gpml")
    files += glob.glob(f"{model_path}/{zip_path}/PlateBoundaries/*.gpml")
    info_fp.write(f"Zip Topologies:\n")
    for f in files:
        f_zip.write(f, f"Topologies/{os.path.basename(f)}")
        info_fp.write(f"\t{f}\n")

# zip Terranes
utils.zip_folder(
    f"{model_path}/{zip_path}/Terranes",
    f"{model_path}/Terranes.zip",
    "Terranes",
    log_fp=info_fp,
)

# zip COBs
utils.zip_folder(
    f"{model_path}/{zip_path}/COBs",
    f"{model_path}/COBs.zip",
    "COBs",
    log_fp=info_fp,
)

# zip ContinentalPolygons
utils.zip_folder(
    f"{model_path}/{zip_path}/ContinentalPolygons",
    f"{model_path}/ContinentalPolygons.zip",
    "ContinentalPolygons",
    log_fp=info_fp,
)

shutil.rmtree(f"{model_path}/{zip_path}")

info_fp.close()
