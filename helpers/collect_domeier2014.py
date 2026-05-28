import argparse
import shlex
import subprocess
from pathlib import Path

import utils

MODEL_NAME = "domeier2014"
DEFAULT_UPLOAD_TARGET = "ubuntu@130.56.247.160"
DEFAULT_IDENTITY_FILE = "~/.ssh/gplates-app-server-key.pem"
DEFAULT_REMOTE_PATH = "/mnt/2TB-Volume/webdav/pmm/domeier2014"
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
    parser = argparse.ArgumentParser(
        description="Collect the Domeier 2014 model files and optionally upload them via SSH."
    )
    parser.add_argument(
        "target_dir",
        nargs="?",
        default=".",
        help="Base directory where the domeier2014 model folder will be created.",
    )
    parser.add_argument(
        "--upload",
        action="store_true",
        help=(
            "Upload files from the generated model folder to the remote server "
            "after archiving any existing remote contents into a timestamped subfolder."
        ),
    )
    parser.add_argument(
        "--upload-target",
        default=DEFAULT_UPLOAD_TARGET,
        help=(
            "SSH destination in the form user@host. "
            f"Default: {DEFAULT_UPLOAD_TARGET}"
        ),
    )
    parser.add_argument(
        "--identity-file",
        default=DEFAULT_IDENTITY_FILE,
        help=f"SSH private key to use for upload. Default: {DEFAULT_IDENTITY_FILE}",
    )
    parser.add_argument(
        "--remote-path",
        default=DEFAULT_REMOTE_PATH,
        help=f"Remote directory for uploaded files. Default: {DEFAULT_REMOTE_PATH}",
    )
    return parser.parse_args()


def collect_model(target_dir):
    model_path = utils.get_model_path(
        ["collect_domeier2014.py", target_dir], MODEL_NAME
    )
    model_dir = Path(model_path)
    if model_dir.exists() and any(model_dir.iterdir()):
        answer = (
            input(
                f"Local folder '{model_dir}' already exists and is not empty. "
                "Delete it and re-fetch? [y/N] "
            )
            .strip()
            .lower()
        )
        if answer != "y":
            print("Aborted.")
            raise SystemExit(0)
        import shutil

        shutil.rmtree(model_dir)
        model_dir.mkdir(parents=True, exist_ok=True)
    for archive_name, urls in DOWNLOADS.items():
        print(f"Fetching {archive_name}...")
        utils.fetch_and_zip_files(urls, model_path, archive_name)
    return model_dir


def create_hex_hash_sidecar_files(model_path):
    script_path = (
        Path(__file__).resolve().parents[1] / "scripts" / "create-hex-hash-file.sh"
    )
    subprocess.run(
        ["bash", str(script_path), str(model_path)],
        check=True,
    )


def upload_model_folder(model_path, upload_target, identity_file, remote_path):
    create_hex_hash_sidecar_files(model_path)
    files_to_upload = sorted(path for path in model_path.iterdir() if path.is_file())
    if not files_to_upload:
        raise RuntimeError(f"No files found in {model_path} to upload.")

    identity_path = str(Path(identity_file).expanduser())
    ssh_base_command = [
        "ssh",
        "-i",
        identity_path,
        upload_target,
    ]
    quoted_remote_path = shlex.quote(remote_path)
    remote_command = (
        f"remote_path={quoted_remote_path}; "
        "timestamp=$(date +%Y%m%d-%H%M%S); "
        'archive_path="$remote_path/$timestamp"; '
        'mkdir -p "$remote_path" "$archive_path"; '
        'find "$remote_path" -mindepth 1 -maxdepth 1 -type f '
        '-exec mv {} "$archive_path"/ \\;'
    )
    subprocess.run(
        [*ssh_base_command, remote_command],
        check=True,
    )
    subprocess.run(
        [
            "scp",
            "-i",
            identity_path,
            *[str(path) for path in files_to_upload],
            f"{upload_target}:{remote_path}/",
        ],
        check=True,
    )


def main():
    args = parse_args()
    model_path = collect_model(args.target_dir)
    if args.upload:
        upload_model_folder(
            model_path,
            args.upload_target,
            args.identity_file,
            args.remote_path,
        )


if __name__ == "__main__":
    main()
