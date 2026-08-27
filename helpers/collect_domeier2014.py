import utils

MODEL_NAME = "domeier2014"
DOWNLOADS = {
    "Rotations": [
        "https://www.earthbyte.org/webdav/ftp/incoming/mchin/plate-models/DOMEIER2014/LP_TPW.rot"
    ],
    "Coastlines": [
        "https://www.earthbyte.org/webdav/ftp/incoming/mchin/plate-models/DOMEIER2014/LP_land.shp",
        "https://www.earthbyte.org/webdav/ftp/incoming/mchin/plate-models/DOMEIER2014/LP_land.dbf",
        "https://www.earthbyte.org/webdav/ftp/incoming/mchin/plate-models/DOMEIER2014/LP_land.prj",
        "https://www.earthbyte.org/webdav/ftp/incoming/mchin/plate-models/DOMEIER2014/LP_land.shx",
        "https://www.earthbyte.org/webdav/ftp/incoming/mchin/plate-models/DOMEIER2014/LP_land.shp.gplates.xml",
    ],
    "StaticPolygons": [
        "https://www.earthbyte.org/webdav/ftp/incoming/mchin/plate-models/DOMEIER2014/LP_land.shp",
        "https://www.earthbyte.org/webdav/ftp/incoming/mchin/plate-models/DOMEIER2014/LP_land.dbf",
        "https://www.earthbyte.org/webdav/ftp/incoming/mchin/plate-models/DOMEIER2014/LP_land.prj",
        "https://www.earthbyte.org/webdav/ftp/incoming/mchin/plate-models/DOMEIER2014/LP_land.shx",
        "https://www.earthbyte.org/webdav/ftp/incoming/mchin/plate-models/DOMEIER2014/LP_land.shp.gplates.xml",
    ],
    "Topologies": [
        "https://www.earthbyte.org/webdav/ftp/incoming/mchin/plate-models/DOMEIER2014/LP_topos.gpml",
        "https://www.earthbyte.org/webdav/ftp/incoming/mchin/plate-models/DOMEIER2014/LP_transform.gpml",
        "https://www.earthbyte.org/webdav/ftp/incoming/mchin/plate-models/DOMEIER2014/LP_ridge.gpml",
        "https://www.earthbyte.org/webdav/ftp/incoming/mchin/plate-models/DOMEIER2014/LP_subduction.gpml",
    ],
}


def parse_args():
    return utils.parse_collector_args(
        "Collect the Domeier 2014 model files and optionally upload them via SSH.",
        MODEL_NAME,
    )


def collect_model(target_dir):
    model_dir = utils.prepare_model_dir(
        target_dir, MODEL_NAME, "collect_domeier2014.py"
    )
    for archive_name, urls in DOWNLOADS.items():
        print(f"Fetching {archive_name}...")
        utils.fetch_and_zip_files(urls, str(model_dir), archive_name)
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
