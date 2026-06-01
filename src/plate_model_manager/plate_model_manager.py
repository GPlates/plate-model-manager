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
import json
import logging
import os
import re
from typing import Dict, Union

import requests

from .utils.enums import ReferenceFrame

from .exceptions import InvalidConfigFile, ServerUnavailable
from .plate_model import PlateModel

logger = logging.getLogger("pmm")


class PlateModelManager:
    """Manage discovery and loading of plate reconstruction model metadata.

    Model manifests can be loaded from a local file or an HTTP(S) endpoint.
    Retrieved model configurations are used to construct :class:`PlateModel`
    instances.
    """

    # Load a models.json file and manage plate models.
    # See an example models.json file at PlateModelManager.get_default_repo_url().

    def __init__(self, model_manifest: str = "", timeout=(None, None)):
        """Create a :class:`PlateModelManager` instance.

        If ``model_manifest`` is omitted, the manager probes known PMM manifest
        endpoints and uses the first reachable URL.

        :param model_manifest: Local path or HTTP(S) URL for a ``models.json``
            manifest. Use this when hosting a custom model repository.
        :param timeout: Timeout tuple passed to HTTP requests.
        :raises InvalidConfigFile: If the manifest path/URL is invalid or does
            not contain valid JSON.
        :raises ServerUnavailable: If the manifest URL cannot be reached.
        """
        if not model_manifest:
            self.model_manifest = PlateModelManager.get_default_repo_url()
        else:
            self.model_manifest = model_manifest

        self._models = None
        self.timeout = timeout

        if not isinstance(self.model_manifest, str):
            raise InvalidConfigFile(
                f"The model_manifest '{type(self.model_manifest)}' must be a string. It is either a local file path or a http(s) URL."
            )

        # check if the model manifest file is a local file
        if os.path.isfile(self.model_manifest):
            with open(self.model_manifest) as f:
                self._models = json.load(f)
        elif self.model_manifest.startswith(
            "http://"
        ) or self.model_manifest.startswith("https://"):
            # try the http(s) url
            try:
                r = requests.get(self.model_manifest, timeout=timeout)
                if r.status_code != 200:
                    raise InvalidConfigFile(
                        f"Unable to get valid JSON data from '{self.model_manifest}'. Http request return code: {r.status_code}"
                    )
                else:
                    self._models = r.json()

            except (
                requests.exceptions.ConnectionError,
                requests.exceptions.ConnectTimeout,
                requests.exceptions.ReadTimeout,
            ):
                raise ServerUnavailable(
                    f"Unable to fetch {self.model_manifest}. No network connection, server unavailable or invalid URL!"
                )
            except requests.exceptions.JSONDecodeError:
                raise InvalidConfigFile(
                    f"Unable to get valid JSON data from '{self.model_manifest}'."
                )
        else:
            raise InvalidConfigFile(
                f"The model_manifest '{self.model_manifest}' must be either a local file path or a http(s) URL."
            )

        if "vars" in self.models:
            self._replace_vars_with_values(self.models["vars"], self.models)
            del self.models["vars"]

    @property
    def models(self) -> Dict:
        """Return metadata for all configured models.

        :returns: Mapping from model names to model entries.
        :rtype: Dict
        :raises Exception: If model metadata is unavailable.
        """
        if self._models is not None:
            return self._models
        else:
            raise Exception(
                f"No model found. Check the model manifest {self.model_manifest} for errors."
            )

    @models.setter
    def models(self, var) -> None:
        self._models = var

    def _replace_vars_with_values(self, var_dict, json_obj):
        """Expand template variables in-place within a manifest dictionary.

        Variables use the marker format ``@<<name>>@`` and are resolved from
        ``var_dict``.

        :param var_dict: Variable name/value mapping.
        :param json_obj: JSON-like dictionary to mutate in place.
        """
        for key, value in json_obj.items():
            if key == "vars":
                continue
            if isinstance(value, dict):
                self._replace_vars_with_values(var_dict, value)
            elif isinstance(value, str):
                matches = re.findall("@<<(.*)>>@", value)
                for m in matches:
                    if m in var_dict:
                        value = value.replace(f"@<<{m}>>@", var_dict[m])
                json_obj[key] = value
            else:
                continue

    def _resolve_model_config(
        self,
        model_name: str,
        data_dir: str,
        visited: set = None,
        max_depth: int = 10,
    ) -> Union[dict, None]:
        """Resolve a model entry to its final configuration dictionary.

        Alias chains are resolved recursively with cycle/depth protection.

        :param model_name: Model name to resolve (case-insensitive).
        :param data_dir: Reserved for compatibility with existing call sites.
        :param visited: Set of previously visited model names.
        :param max_depth: Maximum alias-chain depth.
        :returns: Resolved model configuration dictionary, or ``None`` when the
            model name is not present.
        :raises InvalidConfigFile: If alias resolution exceeds ``max_depth``.
        """
        if visited is None:
            visited = set()

        if len(visited) >= max_depth:
            raise InvalidConfigFile(
                f"Maximum alias resolution depth ({max_depth}) exceeded. "
                f"Possible circular alias in model manifest {self.model_manifest}. "
                f"Resolution chain: {' -> '.join(visited)} -> {model_name}"
            )

        model_name = model_name.lower()
        if model_name not in self.models:
            return None

        model_entry = self.models[model_name]
        visited_copy = visited.copy()
        visited_copy.add(model_name)

        # If entry is a string, it's an alias reference
        if isinstance(model_entry, str):
            # Remove optional '@' prefix that marks aliases
            target_model_name = (
                model_entry[1:] if model_entry.startswith("@") else model_entry
            )

            # Recursively resolve the target
            return self._resolve_model_config(
                target_model_name, data_dir, visited_copy, max_depth
            )

        # Entry is a dict, return it as the configuration
        return model_entry if isinstance(model_entry, dict) else None

    def get_model(
        self,
        model_name: str = "default",
        data_dir: str = ".",
        reference_frame: Union[ReferenceFrame, None] = None,
    ) -> Union[PlateModel, None]:
        """Return a :class:`PlateModel` for ``model_name``.

        The method resolves aliases, applies optional reference-frame handling,
        and instantiates :class:`PlateModel` with the resolved configuration.

        :param model_name: Model name or alias (case-insensitive). Defaults to
            ``"default"``.
        :param data_dir: Parent directory for model downloads and cache files.
        :param reference_frame: Optional reference frame. When PMAG is requested
            and a ``_pmag_ref`` variant exists, that variant is selected
            automatically.
        :returns: A configured :class:`PlateModel`, or ``None`` if the model is
            unavailable or incompatible with the requested reference frame.
        :raises InvalidConfigFile: If alias resolution detects an invalid alias
            chain.
        """
        model_name_lower = model_name.lower()
        if reference_frame == ReferenceFrame.PmagReferenceFrame:
            if f"{model_name_lower}_pmag_ref" in self.models:
                model_name_lower += "_pmag_ref"

        try:
            model_cfg = self._resolve_model_config(model_name_lower, data_dir)
        except InvalidConfigFile:
            raise

        if model_cfg is None:
            logger.error(f"Model '{model_name}' is not available.")
            return None

        if (
            reference_frame == ReferenceFrame.PmagReferenceFrame
            and not model_name_lower.endswith("_pmag_ref")
        ):
            if (
                model_cfg.get("Attributes", {}).get("PmagReferenceFrameAnchorPID")
                is None
            ):
                logger.error(
                    f"Model '{model_name}' does not have a PMAG reference frame version available."
                )
                return None

        return PlateModel(
            model_name_lower,
            model_cfg=model_cfg,
            data_dir=data_dir,
            reference_frame=reference_frame,
        )

    def get_available_model_names(self):
        """Return all model keys from the loaded manifest.

        :returns: Available model names and aliases.
        :rtype: list[str]
        """
        return list(self.models.keys())

    @staticmethod
    def get_local_available_model_names(local_dir: str):
        """Return locally available model names from ``local_dir``.

        :param local_dir: The local folder containing models.
        :type local_dir: str
        :returns: Names of subdirectories that look like valid local PMM models
            (contain ``.metadata.json``).
        :rtype: list[str]
        """
        models = []
        for file in os.listdir(local_dir):
            d = os.path.join(local_dir, file)
            if os.path.isdir(d) and os.path.isfile(f"{d}/.metadata.json"):
                models.append(file)
        return models

    @staticmethod
    def get_default_repo_url():
        """Return the first reachable default model-manifest URL.

        Endpoints are probed in order using HTTP ``HEAD`` requests.

        :returns: Reachable manifest URL.
        :rtype: str
        :raises ServerUnavailable: If none of the default endpoints are
            reachable.
        """
        default_repo_url_list = [
            "https://repo.gplates.org/webdav/pmm/config/models_v2.json",
            "https://www.earthbyte.org/webdav/pmm/config/models_v2_eb.json",
            "https://portal.gplates.org/static/pmm/config/models_v2_gp.json",
        ]
        for url in default_repo_url_list:
            try:
                response = requests.head(url, timeout=(5, 5))
                if response.status_code == 200:
                    return url
                else:
                    logger.warning(
                        f"Unable to fetch {url}. status_code={response.status_code}"
                    )
                    continue
            except:
                logger.warning(f"Unable to fetch {url}.")
                continue
        raise ServerUnavailable(
            """Cannot connect to the servers. Either the servers are currently unavailable, or there is a problem with your internet connection."""
        )

    def download_all_models(self, data_dir: str = "./") -> None:
        """Download layer data for all available models into ``data_dir``.

        :param data_dir: Destination directory for downloaded model data.
        :type data_dir: str
        """
        for name in self.get_available_model_names():
            print(f"download {name}")
            model = self.get_model(name)
            if model is not None:
                model.set_data_dir(data_dir)
                model.download_all_layers()
