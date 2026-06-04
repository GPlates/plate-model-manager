#
#    Copyright (C) 2024-2026 The University of Sydney, Australia
#
#    This program is free software; you can redistribute it and/or modify it under
#    the terms of the GNU General Public License, version 2, as published by
#    the Free Software Foundation.
#
#    This program is distributed in the hope that it will be useful, but WITHOUT
#    ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
#    FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
#    for more details.
#
#    You should have received a copy of the GNU General Public License along
#    with this program; if not, write to Free Software Foundation, Inc.,
#    51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#
from datetime import datetime
from glob import glob
import hashlib
import io
import json, logging
import os
import shlex
import shutil
import subprocess
from pathlib import Path
import zipfile
import requests

from .download import FileDownloader
from ..zenodo import ZenodoRecord

DEFAULT_IDENTITY_FILE = os.environ.get(
    "DEFAULT_IDENTITY_FILE", "~/.ssh/gplates-app-server-key.pem"
)
DEFAULT_REMOTE_TARGET = os.environ.get(
    "DEFAULT_REMOTE_TARGET", "ubuntu@130.56.247.160:/mnt/2TB-Volume/webdav/pmm"
)
DEFAULT_COLLECT_MODELS_SOURCE = (
    "https://repo.gplates.org/webdav/pmm/config/model_sources.json"
)

logger = logging.getLogger("pmm")


def _zip_files(files, zip_filepath, zip_folder, log_fp=None):
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


def _zip_folder(folder, zip_filepath, zip_folder, log_fp=None):
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
        files = [f for f in glob(f"{folder}/**/*", recursive=True) if os.path.isfile(f)]
        rel_paths = [os.path.relpath(f, folder) for f in files]
        for f, rf in zip(files, rel_paths):
            f_zip.write(f, f"{zip_folder}/{rf}")
            if log_fp is not None:
                log_fp.write(f"\t{f}\n")


def _add_folder_to_zip(folder, zip_filepath, log_fp=None):
    """add all files and folders in a given folder to an existing zip file"""
    assert os.path.isdir(folder)
    with zipfile.ZipFile(
        zip_filepath,
        mode="a",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=9,
    ) as f_zip:
        if log_fp is not None:
            log_fp.write(f"Add {folder} to {zip_filepath}:\n")
        for root, dirs, files in os.walk(folder):
            for file in files:
                full_path = os.path.join(root, file)
                f_zip.write(full_path)  # preserves full relative path
                if log_fp is not None:
                    log_fp.write(f"\t{full_path}\n")


def _load_model_data_sources(source):
    if source.startswith(("http://", "https://")):
        response = requests.get(source, timeout=30)
        response.raise_for_status()
        return response.json()
    with open(source, encoding="utf-8") as source_file:
        return json.load(source_file)


def create_hex_hash_sidecar_files(model_path):
    """Create SHA256 hash sidecar files for all .zip files in the given directory."""
    model_path = Path(model_path)

    for zip_file in model_path.glob("*.zip"):
        # Calculate SHA256 hash
        sha256_hash = hashlib.sha256()
        with open(zip_file, "rb") as f:
            # Read file in chunks to handle large files efficiently
            for chunk in iter(lambda: f.read(8192), b""):
                sha256_hash.update(chunk)

        hex_digest = sha256_hash.hexdigest()

        # Create sidecar file with hash in filename
        sidecar_file = Path(f"{zip_file}.{hex_digest}")
        sidecar_file.touch()
        logger.info(f"Created: {sidecar_file}")


def upload_model(model_path, remote_target, identity_file):
    """Upload a plate model folder to a remote server via SCP.

    This function uploads all files in the specified model directory to a remote
    server. Before uploading, it creates SHA256 hash sidecar files for all .zip
    files in the directory. Existing files on the remote server are archived with
    a timestamp before the new files are uploaded.

    Args:
        model_path: Path to the local model directory containing files to upload.
        remote_target: Remote destination in the format 'user@host:path'.
                      The model name will be appended to the path automatically.
        identity_file: Path to the SSH private key file for authentication.

    Raises:
        RuntimeError: If no files are found in the model directory or if the
                     SSH connection to the remote host fails.
        AssertionError: If the remote_target format is invalid (must contain ':').

    Example:
        upload_model(
            "models/muller2022",
            "ubuntu@example.com:/data/models",
            "~/.ssh/id_rsa"
        )
    """
    create_hex_hash_sidecar_files(model_path)
    model_name = Path(model_path).name
    files_to_upload = sorted(
        path for path in Path(model_path).iterdir() if path.is_file()
    )
    if not files_to_upload:
        raise RuntimeError(f"No files found in {model_path} to upload.")

    identity_path = str(Path(identity_file).expanduser())
    remote_host_and_path = remote_target.split(":")
    assert (
        len(remote_host_and_path) == 2
    ), "Invalid remote target format. Expected 'host:path'"
    remote_host = remote_host_and_path[0]
    remote_path = Path(remote_host_and_path[1]) / model_name
    if remote_host:
        # Test SSH connection before proceeding
        try:
            subprocess.run(
                [
                    "ssh",
                    "-i",
                    identity_path,
                    remote_host,
                    "echo",
                    "SSH connection successful",
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(
                f"SSH connection to {remote_host} failed: {e.stderr.decode().strip()}"
            ) from e
    ssh_base_command = [
        "ssh",
        "-i",
        identity_path,
        remote_host,
    ]
    quoted_remote_path = shlex.quote(str(remote_path))
    remote_command = (
        f"remote_path={quoted_remote_path}; "
        "timestamp=$(date +%Y-%m-%d); "
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
            f"{remote_host}:{remote_path}/",
        ],
        check=True,
    )


def collect_model(
    model_name,
    target_dir=".",
    source=DEFAULT_COLLECT_MODELS_SOURCE,
):
    model_name = model_name.lower()
    models = _load_model_data_sources(source)

    if model_name not in models:
        raise ValueError(
            f"Model '{model_name}' is not in the data source configuration -- {source}."
        )

    model_data_source = models[model_name]

    model_dir = Path(target_dir) / model_name
    if model_dir.exists() and any(model_dir.iterdir()):
        answer = (
            input(
                f"Local folder '{model_dir}' already exists and is not empty. "
                "Delete it and re-fetch? [y/N] "
            )
            .strip()
            .lower()
        )
        if answer == "y":
            shutil.rmtree(model_dir)
    model_dir.mkdir(parents=True, exist_ok=True)
    local_data_path = Path(f"{model_dir}/download-data")

    redownload = True  # set to false to skip re-downloading from Zenodo if the files already exist locally
    if local_data_path.exists() and any(local_data_path.iterdir()):
        answer = (
            input(
                f"Local folder '{local_data_path}' already exists and is not empty. "
                "Delete it and re-fetch? [y/N] "
            )
            .strip()
            .lower()
        )
        if answer != "y":
            redownload = False
        else:
            redownload = True
            shutil.rmtree(model_dir)
    Path(local_data_path).mkdir(parents=True, exist_ok=True)

    info_fp = open(f"{model_dir}/info.txt", "w+")
    info_fp.write(f"{datetime.now()}\n")

    if "ZenodoID" in model_data_source and "ZenodoFiles" in model_data_source:
        zenodo_id = model_data_source["ZenodoID"]
        zenodo_files = model_data_source["ZenodoFiles"]
        record = ZenodoRecord(zenodo_id)
        latest_id = record.get_latest_version_id()
        logger.debug(f"The latest version ID is: {latest_id}.")
        file_names = record.get_filenames(latest_id)
        logger.debug(f"The file names in the latest version: {file_names}")
        file_links = record.get_file_links(latest_id)
        logger.debug(f"The file links in the latest version: {file_links}")

        for file_name, file_link in zip(file_names, file_links):
            if file_name in zenodo_files and redownload:
                r = requests.get(
                    file_link,
                    allow_redirects=True,
                )
                info_fp.write(f"Download zip file from {file_link}\n")

                if r.status_code in [200]:
                    z = zipfile.ZipFile(io.BytesIO(r.content))
                    z.extractall(local_data_path)
    if "URLs" in model_data_source:
        urls = model_data_source["URLs"]
        if not urls:
            raise ValueError(
                f"Model '{model_name}' has an empty 'URLs' list in the data source configuration."
            )
        for url in urls:
            url_hash = hashlib.sha1(url.encode("utf-8")).hexdigest()[:10]
            metadata_file = local_data_path / f".{url_hash}.metadata.json"
            downloader = FileDownloader(
                url,
                metadata_file,
                local_data_path,
            )
            downloader.download_file_and_update_metadata()
            info_fp.write(f"Download file from {url}\n")

    if "Rotations" not in model_data_source:
        raise ValueError(
            f"Model '{model_name}' must define 'Rotations' patterns in the data source configuration."
        )

    matched_files = []
    for pattern in model_data_source["Rotations"]:
        matched_files.extend(local_data_path.glob(pattern))
    if not matched_files:
        raise ValueError(
            f"No files found for pattern '{pattern}' in the downloaded data for model '{model_name}'."
        )
    # logger.debug(matched_files)
    _zip_files(matched_files, f"{model_dir}/Rotations.zip", "Rotations", info_fp)

    if "Layers" not in model_data_source:
        raise ValueError(
            f"Model '{model_name}' must define 'Layers' patterns in the data source configuration."
        )

    for layer_name, patterns in model_data_source["Layers"].items():
        matched_files = []
        matched_folders = []
        for pattern in patterns:
            for match in local_data_path.glob(pattern):
                if match.is_file():
                    matched_files.append(match)
                elif match.is_dir():
                    matched_folders.append(match)
        if not matched_files and not matched_folders:
            raise ValueError(
                f"No files or folders found for patterns '{patterns}' in the downloaded data for model '{model_name}' layer '{layer_name}'."
            )

        # logger.debug(matched_files)
        if matched_files:
            _zip_files(
                matched_files,
                f"{model_dir}/{layer_name}.zip",
                layer_name,
                info_fp,
            )
        if not Path(f"{model_dir}/{layer_name}.zip").exists() and matched_folders:
            _zip_folder(
                matched_folders[0],
                f"{model_dir}/{layer_name}.zip",
                layer_name,
                info_fp,
            )
            for folder in matched_folders[1:]:
                _add_folder_to_zip(
                    folder,
                    f"{model_dir}/{layer_name}.zip",
                    info_fp,
                )
        elif Path(f"{model_dir}/{layer_name}.zip").exists() and matched_folders:
            for folder in matched_folders:
                _add_folder_to_zip(
                    folder,
                    f"{model_dir}/{layer_name}.zip",
                    info_fp,
                )

    info_fp.close()
