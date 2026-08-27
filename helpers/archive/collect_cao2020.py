# This model is completely superfluous, as its content is entirely integrated into the Z22 model.
# It needs to be deleted.
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

# https://zenodo.org/doi/10.5281/zenodo.3854459
record = ZenodoRecord(3854459)
latest_id = record.get_latest_version_id()
print(f"The latest version ID is: {latest_id}.")
filenames = record.get_filenames(latest_id)
print(f"The file names in the latest version: {filenames}")
idx = 0
for i in range(len(filenames)):
    if filenames[i].startswith("1000Myr_synthetic_tectonic_reconstructions"):
        idx = i
        break
file_links = record.get_file_links(latest_id)
print(f"The file links in the latest version: {file_links}")

model_path = utils.get_model_path(sys.argv, "cao2020")
zip_path = "1000Myr_synthetic_tectonic_reconstructions"

info_fp = open(f"{model_path}/info.txt", "w+")
info_fp.write(f"{datetime.now()}\n")

# download the model zip file
zip_url = file_links[idx]
info_fp.write(f"Download zip file from {zip_url}\n")
r = requests.get(zip_url, allow_redirects=True, verify=True)
if r.status_code in [200]:
    z = zipfile.ZipFile(io.BytesIO(r.content))
    Path(model_path).mkdir(parents=True, exist_ok=True)
    z.extractall(f"{model_path}")


# zip Rotations
files = glob.glob(f"{model_path}/{zip_path}/*.rot")
utils.zip_files(files, f"{model_path}/Rotations.zip", "Rotations", info_fp)

# zip Coastlines
files = [
    f"{model_path}/{zip_path}/coastline_file_1000_250_new_valid_time.gpml",
    f"{model_path}/{zip_path}/coastline_file_250_0_new_valid_time.gpml",
]
utils.zip_files(files, f"{model_path}/Coastlines.zip", "Coastlines", info_fp)


# zip COBs
files = [
    f"{model_path}/{zip_path}/COBfile_1000_0_Toy_introversion.gpml",
]
utils.zip_files(files, f"{model_path}/COBs.zip", "COBs", info_fp)

# zip Topologies
files = [
    f"{model_path}/1000Myr_synthetic_tectonic_reconstructions/TopologyBuildingBlocks_AREPS.gpml",
    f"{model_path}/1000Myr_synthetic_tectonic_reconstructions/Toy_introversion_plate_boundaries_1000_410_new_valid_time.gpml",
    f"{model_path}/1000Myr_synthetic_tectonic_reconstructions/Toy_introversion_plate_boundaries_410_250_new_valid_time.gpml",
    f"{model_path}/1000Myr_synthetic_tectonic_reconstructions/Global_EarthByte_Mesozoic-Cenozoic_plate_boundaries_2016_v5.gpml",
]
utils.zip_files(files, f"{model_path}/Topologies.zip", "Topologies", info_fp)

shutil.rmtree(f"{model_path}/{zip_path}")
shutil.rmtree(f"{model_path}/__MACOSX")
info_fp.close()
