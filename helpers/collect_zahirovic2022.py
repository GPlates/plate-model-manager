import glob
import io
import shutil
import zipfile
from datetime import datetime

import requests
import utils

from plate_model_manager.zenodo import ZenodoRecord

MODEL_NAME = "zahirovic2022"
ZENODO_RECORD_ID = 4729045
ZENODO_FILENAME_PREFIX = "PlateMotionModel_and_GeometryFiles"
ZIP_PATH = "PlateMotionModel_and_GeometryFiles/Zahirovic_etal_2022_GDJ"


def parse_args():
    return utils.parse_collector_args(
        "Collect the Zahirovic 2022 model files and optionally upload them via SSH.",
        MODEL_NAME,
    )


def collect_model(target_dir):
    model_dir = utils.prepare_model_dir(
        target_dir, MODEL_NAME, "collect_zahirovic2022.py"
    )

    record = ZenodoRecord(ZENODO_RECORD_ID)
    latest_id = record.get_latest_version_id()
    print(f"The latest version ID is: {latest_id}.")
    filenames = record.get_filenames(latest_id)
    print(f"The file names in the latest version: {filenames}")

    idx = 0
    for i, filename in enumerate(filenames):
        if filename.startswith(ZENODO_FILENAME_PREFIX):
            idx = i
            break

    file_links = record.get_file_links(latest_id)
    print(f"The file links in the latest version: {file_links}")

    with open(model_dir / "info.txt", "w+") as info_fp:
        info_fp.write(f"{datetime.now()}\n")

        zip_url = file_links[idx]
        info_fp.write(f"Download zip file from {zip_url}\n")
        response = requests.get(
            zip_url,
            allow_redirects=True,
        )
        if response.status_code not in [200]:
            raise RuntimeError(
                f"Failed to download model zip file: HTTP {response.status_code}"
            )

        zipfile.ZipFile(io.BytesIO(response.content)).extractall(model_dir)

        zip_root = model_dir / ZIP_PATH

        files = glob.glob(f"{zip_root}/CombinedRotations.rot")
        utils.zip_files(files, f"{model_dir}/Rotations.zip", "Rotations", info_fp)

        files = glob.glob(f"{zip_root}/StaticGeometries/StaticPolygons/*")
        utils.zip_files(
            files, f"{model_dir}/StaticPolygons.zip", "StaticPolygons", info_fp
        )

        files = glob.glob(f"{zip_root}/StaticGeometries/Coastlines/*")
        utils.zip_files(files, f"{model_dir}/Coastlines.zip", "Coastlines", info_fp)

        files = [
            f"{zip_root}/Plate_Boundaries.gpml",
            f"{zip_root}/Feature_Geometries.gpml",
            f"{zip_root}/Deforming_Networks_Inactive.gpml",
            f"{zip_root}/Deforming_Networks_Active.gpml",
        ]
        utils.zip_files(files, f"{model_dir}/Topologies.zip", "Topologies", info_fp)

        files = glob.glob(f"{zip_root}/StaticGeometries/ContinentalPolygons/*")
        utils.zip_files(
            files,
            f"{model_dir}/ContinentalPolygons.zip",
            "ContinentalPolygons",
            info_fp,
        )

        # Use ContinentalPolygons as COBs since the model doesn't ship explicit COB files.
        files = glob.glob(f"{zip_root}/StaticGeometries/ContinentalPolygons/*")
        utils.zip_files(files, f"{model_dir}/COBs.zip", "COBs", info_fp)

    shutil.rmtree(model_dir / ZENODO_FILENAME_PREFIX)
    return model_dir


def main():
    args = parse_args()
    model_path = collect_model(args.target_dir)
    if args.upload:
        utils.upload_model_folder(
            model_path,
            args.upload_target,
            args.identity_file,
            args.remote_path,
        )


if __name__ == "__main__":
    main()
