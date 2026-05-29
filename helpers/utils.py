import glob
import argparse
import atexit
import os, io
import shlex
import shutil
import subprocess
import tempfile
import zipfile, sys
from pathlib import Path

import requests
from plate_model_manager.zenodo import ZenodoRecord
from datetime import datetime

DEFAULT_UPLOAD_TARGET = "ubuntu@130.56.247.160"
DEFAULT_IDENTITY_FILE = "~/.ssh/gplates-app-server-key.pem"
DEFAULT_REMOTE_PATH = "/mnt/2TB-Volume/webdav/pmm"
_REGISTERED_UPLOAD_PATHS = set()


def _add_collector_cli_args(parser, model_name):
    default_remote_path = f"{DEFAULT_REMOTE_PATH}/{model_name}"
    parser.add_argument(
        "target_dir",
        nargs="?",
        default=".",
        help=f"Base directory where the {model_name} model folder will be created.",
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
        default=default_remote_path,
        help=f"Remote directory for uploaded files. Default: {default_remote_path}",
    )
    return parser


def _validate_collector_remote_path(parser, args, model_name):
    remote_path = args.remote_path.rstrip("/") or args.remote_path
    if Path(remote_path).name != model_name:
        parser.error(f"--remote-path must end with '/{model_name}'")


def parse_collector_args(description, model_name, argv=None):
    parser = argparse.ArgumentParser(description=description)
    _add_collector_cli_args(parser, model_name)
    args = parser.parse_args(argv)
    _validate_collector_remote_path(parser, args, model_name)
    return args


def download_files_from_zenodo(
    rid: str, model_name: str, filename_prefix: str, dst_path: str = "files-from-zenodo"
):
    record = ZenodoRecord(rid)
    latest_id = record.get_latest_version_id()
    print(f"The latest version ID is: {latest_id}.")
    filenames = record.get_filenames(latest_id)
    print(f"The file names in the latest version: {filenames}")
    idx = 0
    for i in range(len(filenames)):
        if filenames[i].startswith(filename_prefix):
            idx = i
            break
    file_links = record.get_file_links(latest_id)
    print(f"The file links in the latest version: {file_links}")

    model_path = get_model_path(sys.argv, model_name)

    info_fp = open(f"{model_path}/info.txt", "w+")
    info_fp.write(f"{datetime.now()}\n")

    # download the model zip file
    zip_url = file_links[idx]
    info_fp.write(f"Download zip file from {zip_url}\n")
    r = requests.get(zip_url, allow_redirects=True, verify=True)
    if r.status_code in [200]:
        z = zipfile.ZipFile(io.BytesIO(r.content))
        Path(model_path).mkdir(parents=True, exist_ok=True)
        z.extractall(f"{model_path}/{dst_path}")
    return model_path, info_fp


def get_model_path(argv, name):
    """Resolve and prepare the local model folder path.

    This parses collector CLI arguments from ``argv``, builds the model path as
    ``<target_dir>/<name>``, and ensures the folder exists.

    If ``--upload`` is enabled, it also registers a one-time ``atexit`` upload
    callback for this model path so generated files are uploaded when the
    process exits successfully.

    Args:
        argv: Raw CLI argument list (typically ``sys.argv``).
        name: Model name used as the local folder name.

    Returns:
        The local model folder path as a string.
    """
    args = parse_collector_args(
        f"Collect the {name} model files and optionally upload them via SSH.",
        name,
        argv=argv[1:],
    )
    model_path = f"{args.target_dir}/{name}"

    Path(model_path).mkdir(parents=True, exist_ok=True)
    if args.upload and model_path not in _REGISTERED_UPLOAD_PATHS:
        _REGISTERED_UPLOAD_PATHS.add(model_path)
        atexit.register(
            upload_model_folder,
            model_path,
            args.upload_target,
            args.identity_file,
            args.remote_path,
        )
    return model_path


def prepare_model_dir(target_dir, model_name, script_name):
    model_path = get_model_path([script_name, target_dir], model_name)
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
        shutil.rmtree(model_dir)
        model_dir.mkdir(parents=True, exist_ok=True)
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
    files_to_upload = sorted(
        path for path in Path(model_path).iterdir() if path.is_file()
    )
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


def fetch_coastlines(url, model_path, file_name):
    """fetch coastlines"""
    r = requests.get(
        url,
        allow_redirects=True,
    )
    if r.status_code in [200]:
        with open(f"{model_path}/Coastlines.gpmlz", "wb+") as of:
            of.write(r.content)

        with zipfile.ZipFile(
            f"{model_path}/Coastlines.zip",
            mode="w",
            compression=zipfile.ZIP_DEFLATED,
            compresslevel=9,
        ) as f_zip:
            f_zip.write(
                f"{model_path}/Coastlines.gpmlz",
                f"Coastlines/{file_name}",
            )

        os.remove(f"{model_path}/Coastlines.gpmlz")


def fetch_static_polygons(url, model_path, file_name):
    """fetch static polygons"""
    r = requests.get(
        url,
        allow_redirects=True,
    )
    if r.status_code in [200]:
        with open(f"{model_path}/StaticPolygons.gpmlz", "wb+") as of:
            of.write(r.content)

        with zipfile.ZipFile(
            f"{model_path}/StaticPolygons.zip",
            mode="w",
            compression=zipfile.ZIP_DEFLATED,
            compresslevel=9,
        ) as f_zip:
            f_zip.write(
                f"{model_path}/StaticPolygons.gpmlz",
                f"StaticPolygons/{file_name}",
            )

        os.remove(f"{model_path}/StaticPolygons.gpmlz")


def fetch_rotations(url, model_path, file_name):
    """fetch rotations"""
    r = requests.get(
        url,
        allow_redirects=True,
    )
    if r.status_code in [200]:
        with open(f"{model_path}/rotations.rot", "wb+") as of:
            of.write(r.content)

        with zipfile.ZipFile(
            f"{model_path}/Rotations.zip",
            mode="w",
            compression=zipfile.ZIP_DEFLATED,
            compresslevel=9,
        ) as f_zip:
            f_zip.write(
                f"{model_path}/rotations.rot",
                f"Rotations/{file_name}",
            )

        os.remove(f"{model_path}/rotations.rot")


def fetch_COBs(url, model_path, file_name):
    """fetch COBs"""
    r = requests.get(
        url,
        allow_redirects=True,
    )
    if r.status_code in [200]:
        with open(f"{model_path}/COBs", "wb+") as of:
            of.write(r.content)

        with zipfile.ZipFile(
            f"{model_path}/COBs.zip",
            mode="w",
            compression=zipfile.ZIP_DEFLATED,
            compresslevel=9,
        ) as f_zip:
            f_zip.write(
                f"{model_path}/COBs",
                f"COBs/{file_name}",
            )

        os.remove(f"{model_path}/COBs")


def fetch_continental_polygons(url, model_path, file_name):
    """fetch continental polygons"""
    r = requests.get(
        url,
        allow_redirects=True,
    )
    if r.status_code in [200]:
        with open(f"{model_path}/continental_polygons", "wb+") as of:
            of.write(r.content)

        with zipfile.ZipFile(
            f"{model_path}/ContinentalPolygons.zip",
            mode="w",
            compression=zipfile.ZIP_DEFLATED,
            compresslevel=9,
        ) as f_zip:
            f_zip.write(
                f"{model_path}/continental_polygons",
                f"ContinentalPolygons/{file_name}",
            )

        os.remove(f"{model_path}/continental_polygons")


def fetch_file(url, model_path):
    """fetch one file"""
    r = requests.get(
        url,
        allow_redirects=True,
    )
    if r.status_code in [200]:
        file_name = url.split("/")[-1]
        file_path = f"{model_path}/{file_name}"
        with open(file_path, "wb+") as of:
            of.write(r.content)
        return file_path
    else:
        return None


def zip_files_ex(files, model_path, name, log_fp=None):
    zip_files(files, f"{model_path}/{name}.zip", name, log_fp)


def zip_files(files, zip_filepath, zip_folder, log_fp=None):
    """zip a bunch of files"""
    if not len(files) > 0:
        raise Exception("You are trying to zip nothing. We don't allow that.")
    with zipfile.ZipFile(
        zip_filepath,
        mode="w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=9,
    ) as f_zip:
        if log_fp is not None:
            log_fp.write(f"Zip {zip_folder}:\n")
        for f in files:
            f_zip.write(f, f"{zip_folder}/{os.path.basename(f)}")
            if log_fp is not None:
                log_fp.write(f"\t{f}\n")


def zip_folder(folder, zip_filepath, zip_folder, log_fp=None):
    """zip all files and folders in a given folder"""
    assert os.path.isdir(folder)
    with zipfile.ZipFile(
        zip_filepath,
        mode="w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=9,
    ) as f_zip:
        if log_fp is not None:
            log_fp.write(f"Zip {zip_folder}:\n")
        files = [
            f for f in glob.glob(f"{folder}/**/*", recursive=True) if os.path.isfile(f)
        ]
        rel_paths = [os.path.relpath(f, folder) for f in files]
        for f, rf in zip(files, rel_paths):
            f_zip.write(f, f"{zip_folder}/{rf}")
            if log_fp is not None:
                log_fp.write(f"\t{f}\n")


def fetch_and_zip_files(urls, model_path, zip_name):
    """fetch files and zip them"""
    files = []
    tmp_path = tempfile.mkdtemp(dir=model_path)
    for url in urls:
        files.append(
            fetch_file(
                url,
                tmp_path,
            )
        )

    zip_files(
        [f for f in files if f is not None], f"{model_path}/{zip_name}.zip", zip_name
    )

    shutil.rmtree(tmp_path)
