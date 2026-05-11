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
    """Manage a set of publicly available plate reconstruction models.
    The model files are hosted on EarthByte servers.
    You need Internet connection to use this class and download the files.
    """

    # Load a models.json file and manage plate models.
    # See an example models.json file at PlateModelManager.get_default_repo_url().

    def __init__(self, model_manifest: str = "", timeout=(None, None)):
        """Constructor. Create a :class:`PlateModelManager` instance.
        You need Internet connection to create an instance of this class.
        If you don't have Internet connection, use :class:`PlateModel` class directly in ``readonly`` mode.
        Visit `this page <examples.html#use-without-internet>`__ to see an example.

        :param model_manifest: The URL to a ``models.json`` metadata file.
                               Normally you don't need to provide this parameter unless
                               you would like to setup your own plate model server.

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
        """The metadata for all the models."""
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
        """Replace the variables in `json_obj` with the real values. The variables are defined in `var_dict`."""
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
        """Resolve model configuration, handling alias chains with recursion protection.

        :param model_name: The model name (case-insensitive)
        :param data_dir: The folder to save model files
        :param visited: Set of already visited model names to detect circular aliases
        :param max_depth: Maximum recursion depth to prevent infinite loops
        :returns: The resolved model configuration dict or None if not found
        :raises InvalidConfigFile: If circular alias or max depth exceeded
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
        """Retrieve a :class:`PlateModel` object for a given plate model name.

        This method resolves model aliases and creates a PlateModel instance configured
        with the model's metadata. Alias resolution follows chains and detects circular
        references to prevent infinite loops.

        Call :meth:`get_available_model_names()` to see a list of available model names
        and valid aliases.

        :param model_name: The name of the plate model to retrieve. Case-insensitive.
                          Can be a direct model name, an alias, or a variant with
                          reference frame suffix (e.g., "model_pmag_ref").
                          Defaults to "default".
        :param data_dir: The folder path to save downloaded plate model files.
                        Defaults to the current directory (".");
                        This path can be changed later with :meth:`PlateModel.set_data_dir()`.
        :param reference_frame: Optional reference frame for the plate model. If set to
                               :attr:`ReferenceFrame.PmagReferenceFrame` and a "_pmag_ref"
                               variant exists, that variant will be loaded automatically.

        :returns: A :class:`PlateModel` object if the model is found and successfully created,
                 ``None`` if the model name is not found in the manifest.

        :raises InvalidConfigFile: If a circular alias chain is detected or if the maximum
                                  alias resolution depth is exceeded, indicating an error
                                  in the model manifest.

        :example:
            >>> pmm = PlateModelManager()
            >>> model = pmm.get_model("muller2016", data_dir="./models")
            >>> if model:
            ...     model.download_all_layers()

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
        """Return the names of available models as a list."""
        return list(self.models.keys())

    @staticmethod
    def get_local_available_model_names(local_dir: str):
        """Return a list of model names in a local folder.

        :param local_dir: The local folder containing models.
        :type local_dir: str
        """
        models = []
        for file in os.listdir(local_dir):
            d = os.path.join(local_dir, file)
            if os.path.isdir(d) and os.path.isfile(f"{d}/.metadata.json"):
                models.append(file)
        return models

    @staticmethod
    def get_default_repo_url():
        """Return the URL to the configuration data of models."""
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
        """Download all available models into the ``data_dir``.

        :param data_dir: The folder to save the model files.
        :type data_dir: str
        """
        for name in self.get_available_model_names():
            print(f"download {name}")
            model = self.get_model(name)
            if model is not None:
                model.set_data_dir(data_dir)
                model.download_all_layers()
