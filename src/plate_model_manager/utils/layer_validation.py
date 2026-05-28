import json
import re
from html import unescape
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import urlopen

DEFAULT_SVR_BASE_URL = "https://repo.gplates.org/webdav/pmm"
ZIP_LINK_RE = re.compile(r'href="([^"]+\.zip)"', re.IGNORECASE)


def _is_url(source):
    if not isinstance(source, str):
        return False
    parsed = urlparse(source)
    return parsed.scheme in ("http", "https")


def load_models_config(source, timeout=30):
    if _is_url(source):
        try:
            with urlopen(source, timeout=timeout) as response:
                return json.loads(response.read().decode("utf-8", errors="replace"))
        except HTTPError as exc:
            raise RuntimeError(f"HTTP error for {source}: {exc.code}") from exc
        except URLError as exc:
            raise RuntimeError(f"URL error for {source}: {exc.reason}") from exc

    with Path(source).open(encoding="utf-8") as f:
        return json.load(f)


def normalize_svr_base_url(all_models):
    vars_cfg = all_models.get("vars", {})
    if isinstance(vars_cfg, dict):
        base_url = vars_cfg.get("SvrBaseURL")
        if isinstance(base_url, str) and base_url.strip():
            return base_url.rstrip("/")
    return DEFAULT_SVR_BASE_URL


def list_remote_zip_layers(model_name, base_url, timeout=30):
    model_url = f"{base_url.rstrip('/')}/{model_name}/"
    try:
        with urlopen(model_url, timeout=timeout) as response:
            html = response.read().decode("utf-8", errors="replace")
    except HTTPError as exc:
        raise RuntimeError(f"HTTP error for {model_url}: {exc.code}") from exc
    except URLError as exc:
        raise RuntimeError(f"URL error for {model_url}: {exc.reason}") from exc

    layers = set()
    for href in ZIP_LINK_RE.findall(html):
        name = unescape(href).split("?", 1)[0]
        if "/" in name:
            continue
        if name.endswith(".zip") and ".zip." not in name:
            layer = name[:-4]
            if layer != "Rotations":
                layers.add(layer)
    return sorted(layers)


def validate_layers_config(all_models, base_url=None, timeout=30):
    resolved_base_url = (
        base_url.rstrip("/") if base_url else normalize_svr_base_url(all_models)
    )
    issues = []
    checked_models = 0

    for model_name, model_cfg in all_models.items():
        if model_name in ("vars", "default"):
            continue

        if not isinstance(model_cfg, dict) or "Layers" not in model_cfg:
            continue

        if not isinstance(model_cfg["Layers"], dict):
            issues.append(f"{model_name}: Layers must be a JSON object")
            continue

        expected_layers = sorted(model_cfg["Layers"].keys())
        checked_models += 1

        try:
            remote_layers = list_remote_zip_layers(
                model_name, resolved_base_url, timeout=timeout
            )
        except RuntimeError as exc:
            issues.append(f"{model_name}: {exc}")
            continue

        if expected_layers != remote_layers:
            missing_layers = sorted(set(remote_layers) - set(expected_layers))
            extra_layers = sorted(set(expected_layers) - set(remote_layers))
            issue = f"{model_name}: remote={remote_layers}, config={expected_layers}"
            if missing_layers:
                issue += f", missing_in_config={missing_layers}"
            if extra_layers:
                issue += f", missing_on_server={extra_layers}"
            issues.append(issue)

    return checked_models, issues, resolved_base_url


def validate_layers_source(source, base_url=None, timeout=30):
    all_models = load_models_config(source, timeout=timeout)
    return validate_layers_config(all_models, base_url=base_url, timeout=timeout)
