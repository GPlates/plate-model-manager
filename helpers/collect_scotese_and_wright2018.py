import glob
import io
import shutil
import sys
import zipfile
from datetime import datetime
from pathlib import Path

import requests
import utils

model_path = utils.get_model_path(sys.argv, "scotese_and_wright2018")
zip_path = "Scotese_Wright_plate_model_2018"
zip_url = "https://earthbyte.org/webdav/ftp/incoming/mchin/plate-models/ScoteseAndWright2018/Scotese_Wright_plate_model_2018.zip"

info_fp = open(f"{model_path}/info.txt", "w+")
info_fp.write(f"{datetime.now()}\n")
info_fp.write(f"Download zip file from {zip_url}\n")

r = requests.get(zip_url, allow_redirects=True, verify=True)
if r.status_code in [200]:
    z = zipfile.ZipFile(io.BytesIO(r.content))
    Path(model_path).mkdir(parents=True, exist_ok=True)
    z.extractall(f"{model_path}/{zip_path}")

# zip Rotations
files = glob.glob(
    f"{model_path}/{zip_path}/**/Scotese_Wright_PlateModel.rot", recursive=True
)
utils.zip_files(files, f"{model_path}/Rotations.zip", "Rotations", info_fp)

# zip StaticPolygons
files = glob.glob(
    f"{model_path}/{zip_path}/**/Scotese_Wright_ContinentalPolygons.gpml",
    recursive=True,
)
utils.zip_files(files, f"{model_path}/StaticPolygons.zip", "StaticPolygons", info_fp)

# zip Topologies
files = glob.glob(
    f"{model_path}/{zip_path}/**/Scotese_Wright_PlateBoundaries.gpml", recursive=True
)
utils.zip_files(files, f"{model_path}/Topologies.zip", "Topologies", info_fp)

# zip ContinentalPolygons
files = glob.glob(
    f"{model_path}/{zip_path}/**/Scotese_Wright_ContinentalPolygons.gpml",
    recursive=True,
)
utils.zip_files(
    files, f"{model_path}/ContinentalPolygons.zip", "ContinentalPolygons", info_fp
)

shutil.rmtree(f"{model_path}/{zip_path}")
info_fp.close()
