import json
import os
import shlex
import subprocess
import sys
from pathlib import Path

import requests

DEFAULT_UPLOAD_TARGET = os.environ.get(
    "DEFAULT_UPLOAD_TARGET", "ubuntu@130.56.247.160"
)
DEFAULT_IDENTITY_FILE = os.environ.get(
    "DEFAULT_IDENTITY_FILE", "~/.ssh/gplates-app-server-key.pem"
)
DEFAULT_REMOTE_PATH = os.environ.get("DEFAULT_REMOTE_PATH", "/mnt/2TB-Volume/webdav/pmm")
DEFAULT_COLLECT_MODELS_SOURCE = (
    Path(__file__).resolve().parents[3] / "config" / "collect_model_sources.json"
)


def _read_json(source):
    if source.startswith(("http://", "https://")):
        response = requests.get(source, timeout=30)
        response.raise_for_status()
        return response.json()
    with open(source, encoding="utf-8") as source_file:
        return json.load(source_file)


def load_collect_models(source):
    data = _read_json(source)
    models = data.get("models", data)
    if not isinstance(models, dict):
        raise ValueError("Collect model config must define a JSON object of models.")
    if not models:
        raise ValueError("Collect model config contains no models.")
    return models


def create_hex_hash_sidecar_files(model_path):
    script_path = Path(__file__).resolve().parents[3] / "scripts" / "create-hex-hash-file.sh"
    subprocess.run(
        ["bash", str(script_path), str(model_path)],
        check=True,
    )


def upload_model_folder(model_path, upload_target, identity_file, remote_path):
    create_hex_hash_sidecar_files(model_path)
    files_to_upload = sorted(path for path in Path(model_path).iterdir() if path.is_file())
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


def _resolve_collect_script(path):
    script_path = Path(path)
    if not script_path.is_absolute():
        script_path = Path(__file__).resolve().parents[3] / script_path
    if not script_path.is_file():
        raise ValueError(f"Collect script not found: {script_path}")
    return script_path


def _validate_remote_path(model_name, remote_path):
    if Path(remote_path.rstrip("/") or remote_path).name != model_name:
        raise ValueError(f"--remote-path must end with '/{model_name}'")


def collect_model_files(
    model_name,
    target_dir,
    source,
    upload=False,
    upload_target=DEFAULT_UPLOAD_TARGET,
    identity_file=DEFAULT_IDENTITY_FILE,
    remote_path=None,
):
    models = load_collect_models(source)
    selected_models = sorted(models.keys()) if model_name == "all" else [model_name]

    if model_name != "all" and model_name not in models:
        raise ValueError(f"Model '{model_name}' is not in the source config.")
    if model_name == "all" and remote_path:
        raise ValueError("--remote-path is only supported for a single model.")

    for selected_model in selected_models:
        script_path = _resolve_collect_script(models[selected_model])
        subprocess.run(
            [sys.executable, str(script_path), target_dir],
            check=True,
        )
        if upload:
            model_remote_path = remote_path or f"{DEFAULT_REMOTE_PATH}/{selected_model}"
            _validate_remote_path(selected_model, model_remote_path)
            upload_model_folder(
                Path(target_dir) / selected_model,
                upload_target,
                identity_file,
                model_remote_path,
            )
