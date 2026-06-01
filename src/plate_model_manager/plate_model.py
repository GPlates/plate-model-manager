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
import asyncio
import concurrent.futures
import functools
import glob
import json
import logging
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Union

from plate_model_manager.utils.enums import GenerationMethod, ReferenceFrame

from .exceptions import LayerNotFoundInModel
from .utils import download

METADATA_FILENAME = ".metadata.json"
README_FILENAME = "readme.txt"

FILE_EXT = [
    "gpml",
    "gpmlz",
    "gpml.gz",
    "dat",
    "pla",
    "shp",
    "geojson",
    "json",
    ".gpkg",
    "gmt",
    "vgp",
]

logger = logging.getLogger("pmm")


class PlateModel:
    """Download and manage files for a plate reconstruction model.

    In most workflows, create instances through
    :py:meth:`PlateModelManager.get_model` so model configuration and metadata
    are resolved automatically. Direct instantiation is primarily intended for
    advanced or offline use (for example, ``readonly=True`` with pre-downloaded
    local files).

    .. seealso::

        `Use PlateModel class in readonly mode. <examples.html#use-without-internet>`__
    """

    def __init__(
        self,
        model_name: str,
        model_cfg=None,
        data_dir: str = ".",
        reference_frame: Union[ReferenceFrame, None] = None,
        readonly=False,
        timeout=(None, None),
    ):
        """Create a :class:`PlateModel` instance.

        :param model_name: Model name to load.
        :type model_name: str
        :param model_cfg: Model configuration dictionary. This is typically
            provided by :py:meth:`PlateModelManager.get_model`, or loaded from
            local metadata in readonly mode.
        :param data_dir: Parent directory used to store model files.
        :type data_dir: str, default="."
        :param reference_frame: Default reference frame associated with this
            instance.
        :type reference_frame: ReferenceFrame or None
        :param readonly: If ``True``, use only local files and do not perform
            downloads or updates.
        :type readonly: bool, default=False
        :param timeout: Network timeout tuple passed to file downloads.
        :raises Exception: If ``readonly=True`` and the local model directory is
            invalid.
        """
        self.model_name = model_name.lower()
        self.meta_filename = METADATA_FILENAME
        self._model = model_cfg
        self._reference_frame = reference_frame
        self.readonly = readonly
        self.timeout = timeout

        self.data_dir = data_dir

        if readonly:
            if not PlateModel.is_model_dir(self.model_dir):
                raise Exception(
                    f"{self.model_dir} must be valid model dir in readonly mode."
                )
            else:
                with open(f"{self.model_dir}/{self.meta_filename}", "r") as f:
                    self._model = json.load(f)

        if not readonly:
            # async and concurrent things
            self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=15)
            self.loop = asyncio.new_event_loop()
            self.run = functools.partial(self.loop.run_in_executor, self.executor)
            asyncio.set_event_loop(self.loop)

        if self._model is None:
            logger.warning(
                "Creating a PlateModel instance with the 'model configuration' is None. Normally this should not happen. I allow this just in case some genius is doing something extraordinarily smart."
            )

    @property
    def model(self) -> Dict:
        """Return model metadata for this instance.

        :returns: Model configuration dictionary.
        :rtype: Dict
        :raises Exception: If model configuration is unexpectedly unavailable.
        """
        if self._model is not None:
            return self._model
        else:
            raise Exception(
                "The 'model configuration' is None. This should not happen. Something extraordinary must have happened. Think carefully what you have done!!!"
            )

    @model.setter
    def model(self, var) -> None:
        if var is None:
            logger.warning(
                "You are trying to set the 'model configuration' to None. I will allow this. But I hope you know what you are doing!!!"
            )
        self._model = var

    def __getstate__(self):
        """Return picklable instance state without executor or event loop."""
        attributes = self.__dict__.copy()
        attributes.pop("executor", None)
        attributes.pop("loop", None)
        attributes.pop("run", None)
        return attributes

    def __setstate__(self, state):
        """Restore instance state and recreate async helpers when writable."""
        self.__dict__ = state
        if not self.readonly:
            # async and concurrent things
            self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=15)
            self.loop = asyncio.new_event_loop()
            self.run = functools.partial(self.loop.run_in_executor, self.executor)
            asyncio.set_event_loop(self.loop)

    def __del__(self):
        """Close the event loop when the instance is garbage collected."""
        if not self.readonly:
            try:
                self.loop.close()
            except:
                pass  # ignore the exception when closing the loop if any

    def get_cfg(self):
        """Return the model configuration dictionary.

        :returns: Model metadata dictionary.
        :rtype: Dict
        """
        return self.model

    def get_model_dir(self):
        """Return the local directory path for this model.

        In writable mode, the model directory is created when missing.

        :returns: Absolute or relative path to this model folder.
        :rtype: str
        :raises Exception: If the folder is missing in readonly mode.
        """
        _model_dir = f"{self.data_dir}/{self.model_name}"
        if PlateModel.is_model_dir(_model_dir):
            return _model_dir
        elif not self.readonly:
            return self.create_model_dir()
        else:
            raise Exception(
                f"The model dir {_model_dir} is invalid and could not create it (in readonly mode)."
            )

    def get_data_dir(self):
        """Return the parent directory containing downloaded models.

        :returns: Data directory path.
        :rtype: str
        """
        return self.data_dir

    @property
    def model_dir(self):
        """Return the model folder path under ``data_dir``."""
        return self.get_model_dir()

    def set_data_dir(self, new_dir):
        """Set a new parent directory for this model.

        :param new_dir: New data directory path.
        """
        self.data_dir = new_dir

    def get_big_time(self):
        """Return the maximum reconstruction time in Ma."""
        return self.model["BigTime"]

    def get_small_time(self):
        """Return the minimum reconstruction time in Ma."""
        return self.model["SmallTime"]

    def get_avail_layers(self):
        """Return all available geometry layer names in this model.

        :returns: Layer names.
        :rtype: list[str]
        :raises Exception: If model configuration is missing.
        """
        if not self.model:
            raise Exception("Fatal: No model configuration found!")
        return list(self.model["Layers"].keys())

    def get_rotation_model(
        self,
        reference_frame: Union[ReferenceFrame, None] = None,
    ):
        """Return rotation files, and optionally a PMAG anchor plate ID.

        Rotation files are read from the local model directory in ``readonly``
        mode, or downloaded/updated first in writable mode.

        When ``reference_frame`` is
        :attr:`ReferenceFrame.PmagReferenceFrame`, this method also returns the
        anchor plate ID required by consumers that need PMAG reference frame rotations.
        The anchor ID is read from
        ``model["Attributes"]["PmagReferenceFrameAnchorPID"]`` when present.
        If that value is missing but this model is
        already under PMAG reference frame, set the anchor ID to ``0``,
        such as ``matthews2016_pmag_ref`` model.

        :param reference_frame: Optional reference frame for
                                the returned rotation model. (since version 1.4.0)

        :returns: If ``reference_frame`` is PMAG, returns
                  ``(rotation_files, anchor_pid)`` where ``rotation_files`` is
                  a list of ``.rot``/``.grot`` file paths and ``anchor_pid`` is
                  an integer. Otherwise returns only ``rotation_files``.

        :raises Exception: If PMAG is requested but the model is not PMAG and
                           ``Attributes.PmagReferenceFrameAnchorPID`` is not
                           defined.
        """
        if not self.readonly:
            rotation_folder = self._download_layer_files("Rotations")
        else:
            logger.debug(
                f"Getting rotation files from local folder {self.model_dir}/Rotations since we are in readonly mode."
            )
            rotation_folder = f"{self.model_dir}/Rotations"
        rotation_files = glob.glob(f"{rotation_folder}/*.rot")
        rotation_files.extend(glob.glob(f"{rotation_folder}/*.grot"))
        # print(rotation_files)
        if reference_frame is None:
            reference_frame = self._reference_frame
        if reference_frame == ReferenceFrame.PmagReferenceFrame:
            attrs = self.model.get("Attributes", None)
            pmag_ref_frame_anchor_pid = (
                attrs.get("PmagReferenceFrameAnchorPID", None) if attrs else None
            )
            if pmag_ref_frame_anchor_pid is None:
                if self._reference_frame == ReferenceFrame.PmagReferenceFrame:
                    # if the model is already in PMAG reference frame, we can just set the anchor PID to 0
                    pmag_ref_frame_anchor_pid = 0
                else:
                    raise Exception(
                        f"The model '{self.model_name}' is not a PMAG reference frame model and does not have 'Attributes.PmagReferenceFrameAnchorPID' defined. Cannot get rotation model for PMAG reference frame."
                    )
            return rotation_files, pmag_ref_frame_anchor_pid
        else:
            # for mantle reference frame, we don't need to know the anchor PID
            return rotation_files

    def get_coastlines(
        self, return_none_if_not_exist: bool = False
    ) -> Union[List[str], None]:
        """Return local file paths for the ``Coastlines`` layer."""
        return self.get_layer(
            "Coastlines", return_none_if_not_exist=return_none_if_not_exist
        )

    def get_static_polygons(
        self, return_none_if_not_exist: bool = False
    ) -> Union[List[str], None]:
        """Return local file paths for the ``StaticPolygons`` layer."""
        return self.get_layer(
            "StaticPolygons", return_none_if_not_exist=return_none_if_not_exist
        )

    def get_continental_polygons(
        self, return_none_if_not_exist: bool = False
    ) -> Union[List[str], None]:
        """Return local file paths for the ``ContinentalPolygons`` layer."""
        return self.get_layer(
            "ContinentalPolygons", return_none_if_not_exist=return_none_if_not_exist
        )

    def get_topologies(
        self, return_none_if_not_exist: bool = False
    ) -> Union[List[str], None]:
        """Return local file paths for the ``Topologies`` layer."""
        return self.get_layer(
            "Topologies", return_none_if_not_exist=return_none_if_not_exist
        )

    def get_COBs(
        self, return_none_if_not_exist: bool = False
    ) -> Union[List[str], None]:
        """Return local file paths for the ``COBs`` layer."""
        return self.get_layer("COBs", return_none_if_not_exist=return_none_if_not_exist)

    def get_layer(
        self, layer_name: str, return_none_if_not_exist: bool = False
    ) -> Union[List[str], None]:
        """Return local file paths for a geometry layer.

        In writable mode, layer data are downloaded or updated before paths are
        returned. In readonly mode, paths are resolved from the local model
        folder.

        :param layer_name: Layer name. Call :meth:`get_avail_layers` to list
            valid names.
        :param return_none_if_not_exist: If ``True``, return ``None`` instead
            of raising when the layer is missing.
        :returns: List of matching layer file paths, or ``None`` when
            ``return_none_if_not_exist=True`` and the layer is missing.
        :raises LayerNotFoundInModel: If the layer does not exist and
            ``return_none_if_not_exist`` is ``False``.
        """
        try:
            if not self.readonly:
                layer_folder = self._download_layer_files(layer_name)
            else:
                layer_folder = f"{self.model_dir}/{layer_name}"
            files = []
            for ext in FILE_EXT:
                files.extend(glob.glob(f"{layer_folder}/*.{ext}"))

            return files
        except LayerNotFoundInModel as e:
            logger.warning(e)
            if return_none_if_not_exist:
                logger.warning(
                    f"The layer({layer_name}) does not exist in model({self.model_name})."
                )
                return None
            else:
                raise e

    def get_layer_metadata(
        self, layer_name: str, return_none_if_not_exist: bool = False
    ) -> Union[Dict, None]:
        """Return metadata for a layer as a dictionary.

        In writable mode, this method ensures the layer is downloaded/updated
        before reading metadata. In readonly mode, it reads from the local
        layer folder directly.

        :param layer_name: The layer name of interest.

        :param return_none_if_not_exist: If set to ``True``, return ``None``
                                         when the layer does not exist in the
                                         model.

        :returns: Layer metadata dictionary, or ``None`` if
                  ``return_none_if_not_exist`` is set to ``True`` and the layer
                  is not found.

        :raises LayerNotFoundInModel: Raise this exception if the layer name
                          does not exist in this model.
        :raises Exception: If the layer metadata file is missing.

        """
        try:
            if not self.readonly:
                layer_folder = self._download_layer_files(layer_name)
            else:
                layer_folder = f"{self.model_dir}/{layer_name}"

            metadata_file = f"{layer_folder}/{self.meta_filename}"
            if not os.path.isfile(metadata_file):
                raise Exception(
                    f"Layer metadata file not found for layer({layer_name}) in model({self.model_name}): {metadata_file}"
                )

            with open(metadata_file, "r") as f:
                return json.load(f)
        except LayerNotFoundInModel as e:
            logger.warning(e)
            if return_none_if_not_exist:
                logger.warning(
                    f"The layer({layer_name}) does not exist in model({self.model_name})."
                )
                return None
            else:
                raise e

    def _best_effort_to_get_raster_name_from_config(self, raster_name):
        if raster_name in self.model.get("TimeDepRasters", {}):
            return raster_name
        else:
            for name in self.model.get("TimeDepRasters", {}):
                if name.lower() == raster_name.lower():
                    logger.warning(
                        f"Raster '{raster_name}' not found in this model '{self.model_name}', but '{name}' exists. Will use '{name}' for now."
                    )
                    return name
        return None

    def _resolve_raster_name(self, raster_name, reference_frame, generated_from):
        """Resolve a canonical time-dependent raster key from optional suffixes.

        :param raster_name: Base raster name.
        :param reference_frame: Optional reference frame suffix.
        :param generated_from: Optional generation method suffix.
        :returns: Raster key present in ``model["TimeDepRasters"]``.
        :rtype: str
        :raises Exception: If the model has no time-dependent rasters or the
            resolved name cannot be matched.
        """
        if not "TimeDepRasters" in self.model:
            raise Exception(
                f"No time-dependent rasters found in this model '{self.model_name}'."
            )

        if reference_frame is None:
            reference_frame = self._reference_frame

        if reference_frame is None and generated_from is None:
            name_in_config = self._best_effort_to_get_raster_name_from_config(
                raster_name
            )
            if name_in_config is not None:
                return name_in_config
            else:
                # try the best to deduce the raster name
                guessed_name = f"{raster_name}{GenerationMethod.Isochrons.value}{ReferenceFrame.MantleReferenceFrame.value}"
                name_in_config = self._best_effort_to_get_raster_name_from_config(
                    guessed_name
                )
                if name_in_config is not None:
                    return name_in_config
        else:
            resolved_raster_name = raster_name
            if generated_from is not None:
                resolved_raster_name = f"{raster_name}{generated_from.value}"
            name_without_reference_frame = resolved_raster_name
            if reference_frame is not None:
                resolved_raster_name = f"{resolved_raster_name}{reference_frame.value}"

            name_in_config = self._best_effort_to_get_raster_name_from_config(
                resolved_raster_name
            )
            if name_in_config is not None:
                return name_in_config
            else:
                name_in_config = self._best_effort_to_get_raster_name_from_config(
                    name_without_reference_frame
                )
                if name_in_config is not None:
                    logger.warning(
                        f"Raster '{resolved_raster_name}' not found in this model '{self.model_name}', but '{name_in_config}' exists. Will use '{name_in_config}' for now."
                    )
                    return name_in_config

        raise Exception(
            f"Time-dependent rasters ({resolved_raster_name}) were not found in this model '{self.model_name}'.\n"
            + f"Available time-dependent rasters in '{self.model_name}':\n"
            + "\n".join(self.model.get("TimeDepRasters", {}).keys())
        )

    def get_raster(
        self,
        raster_name: str,
        time: Union[int, float],
        reference_frame: Union[ReferenceFrame, None] = None,
        generated_from: Union[GenerationMethod, None] = None,
    ) -> str:
        """Return a local path for a single time-dependent raster.

        The final raster key is built from ``raster_name`` and optional suffixes
        from ``generated_from`` and ``reference_frame`` (in that order), matching
        the naming convention used in ``model[\"TimeDepRasters\"]``.

        :param raster_name: Base raster name in ``TimeDepRasters`` (for example,
                            ``\"AgeGrids\"``).
        :param time: Reconstruction time (Ma) to fetch.
        :param reference_frame: Optional reference-frame suffix to append to the
                                raster name.
        :param generated_from: Optional generation-method suffix to append to the
                               raster name.

        :returns: Local file path for the requested raster at ``time``.

        :raises Exception: If this model has no ``TimeDepRasters`` entry, if the
                           constructed raster name is not configured, if the file
                           is missing in readonly mode, or if a download fails in
                           writable mode.
        """
        raster_name = self._resolve_raster_name(
            raster_name, reference_frame, generated_from
        )
        url = self.model["TimeDepRasters"][raster_name].format(time)

        if not self.readonly:
            self._download_raster(url, f"{self.get_model_dir()}/Rasters/{raster_name}")
        file_name = url.split("/")[-1]
        local_path = f"{self.get_model_dir()}/Rasters/{raster_name}/{file_name}"
        if os.path.isfile(local_path):
            return local_path
        elif self.readonly:
            raise Exception(
                f"You are in readonly mode and the raster {url} has not been downloaded yet."
            )
        else:
            raise Exception(f"Failed to download {url}")

    def get_rasters(
        self,
        raster_name: str,
        times: List[Union[int, float]],
        reference_frame: Union[ReferenceFrame, None] = None,
        generated_from: Union[GenerationMethod, None] = None,
    ) -> List[str]:
        """Return local paths for a sequence of time-dependent rasters.

        The final raster key is built from ``raster_name`` and optional suffixes
        from ``generated_from`` and ``reference_frame`` (in that order), matching
        the naming convention used in ``model[\"TimeDepRasters\"]``.

        :param raster_name: Base raster name in ``TimeDepRasters`` (for example,
                            ``\"AgeGrids\"``).
        :param times: Reconstruction times (Ma) to fetch.
        :param reference_frame: Optional reference-frame suffix to append to the
                                raster name.
        :param generated_from: Optional generation-method suffix to append to the
                               raster name.

        :returns: Local file paths for the requested times, in the same order as
                  ``times``.

        :raises Exception: If this model has no ``TimeDepRasters`` entry, if the
                           constructed raster name is not configured, if a
                           requested file is missing in readonly mode, or if a
                           download fails in writable mode.
        """
        raster_name = self._resolve_raster_name(
            raster_name, reference_frame, generated_from
        )
        if not self.readonly:
            self.download_time_dependent_rasters(raster_name, times)

        paths = []
        for time in times:
            url = self.model["TimeDepRasters"][raster_name].format(time)
            file_name = url.split("/")[-1]
            local_path = f"{self.get_model_dir()}/Rasters/{raster_name}/{file_name}"
            if os.path.isfile(local_path):
                paths.append(local_path)
            elif self.readonly:
                raise Exception(
                    f"You are in readonly mode and the raster {url} has not been downloaded yet."
                )
            else:
                raise Exception(f"Failed to download {url}")
        return paths

    def get_age_grid(
        self,
        time: Union[int, float],
        reference_frame: Union[ReferenceFrame, None] = None,
        generated_from: Union[GenerationMethod, None] = None,
    ) -> str:
        """Return a local path for an ``AgeGrids`` raster at ``time`` Ma."""
        return self.get_raster("AgeGrids", time, reference_frame, generated_from)

    def get_age_grids(
        self,
        times: List[Union[int, float]],
        reference_frame: Union[ReferenceFrame, None] = None,
        generated_from: Union[GenerationMethod, None] = None,
    ) -> List[str]:
        """Return local paths for ``AgeGrids`` rasters at multiple times."""
        return self.get_rasters("AgeGrids", times, reference_frame, generated_from)

    def get_spreading_rate_grid(
        self,
        time: Union[int, float],
        reference_frame: Union[ReferenceFrame, None] = None,
        generated_from: Union[GenerationMethod, None] = None,
    ) -> str:
        """Return a local path for a ``SpreadingRate`` raster at ``time`` Ma."""
        return self.get_raster("SpreadingRate", time, reference_frame, generated_from)

    def get_spreading_rate_grids(
        self,
        times: List[Union[int, float]],
        reference_frame: Union[ReferenceFrame, None] = None,
        generated_from: Union[GenerationMethod, None] = None,
    ) -> List[str]:
        """Return local paths for ``SpreadingRate`` rasters at multiple times."""
        return self.get_rasters("SpreadingRate", times, reference_frame, generated_from)

    def _create_readme_content(self) -> str:
        """Return a human-readable string summarising the model metadata for readme.txt."""
        lines = []
        lines.append(f"Model: {self.model_name}")
        lines.append("")

        if "Description" in self.model:
            lines.append(f"Description: {self.model['Description']}")
            lines.append("")

        if "BigTime" in self.model and "SmallTime" in self.model:
            lines.append(
                f"Reconstruction time range: {self.model['SmallTime']} - {self.model['BigTime']} Ma"
            )
            lines.append("")

        if "Layers" in self.model and self.model["Layers"]:
            lines.append("Layers:")
            for layer in self.model["Layers"]:
                lines.append(f"  - {layer}")
            lines.append("")

        if "TimeDepRasters" in self.model and self.model["TimeDepRasters"]:
            lines.append("Time-dependent rasters:")
            for raster in self.model["TimeDepRasters"]:
                lines.append(f"  - {raster}")
            lines.append("")

        if "URL" in self.model:
            lines.append(f"URL: {self.model['URL']}")

        if "Version" in self.model:
            lines.append(f"Version: {self.model['Version']}")

        return "\n".join(lines) + "\n"

    def create_model_dir(self):
        """Ensure the model folder exists and refresh local metadata files.

        This method creates ``self.model_dir`` when missing, then always rewrites
        ``.metadata.json`` and ``readme.txt`` from the current in-memory model
        configuration, even if the folder already exists.

        :returns: The model folder path.
        :rtype: str

        :raises Exception: If running in readonly mode, if ``self.model_dir`` is
                           invalid/empty, or if the model path exists as a file.
        """
        model_path = f"{self.data_dir}/{self.model_name}"
        if self.readonly:
            raise Exception("Unable to create model folder in readonly mode.")
        if not model_path:
            raise Exception(f"Error: Invalid model folder {model_path}")

        if os.path.isfile(model_path):
            raise Exception(
                f"Fatal: The model folder {model_path} already exists and is a file!! Remove the file or use another folder to download the model."
            )

        Path(model_path).mkdir(parents=True, exist_ok=True)

        metadata_file = f"{model_path}/{self.meta_filename}"
        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(self.model, f)

        readme_file = f"{model_path}/{README_FILENAME}"
        with open(readme_file, "w", encoding="utf-8") as f:
            f.write(self._create_readme_content())

        return model_path

    @staticmethod
    def is_model_dir(folder_path: str):
        """Return whether ``folder_path`` looks like a local model directory."""
        return os.path.isdir(folder_path) and os.path.isfile(
            f"{folder_path}/.metadata.json"
        )

    def purge(self):
        """Delete the model directory and all files under it, if present."""
        if os.path.isdir(self.model_dir):
            shutil.rmtree(self.model_dir)

    def purge_layer(self, layer_name):
        """Delete a local layer directory for ``layer_name``, if present."""
        layer_path = f"{self.model_dir}/{layer_name}"
        if os.path.isdir(layer_path):
            shutil.rmtree(layer_path)

    def purge_time_dependent_rasters(self, raster_name):
        """Delete local cached rasters for ``raster_name``, if present."""
        raster_path = f"{self.model_dir}/{raster_name}"
        if os.path.isdir(raster_path):
            shutil.rmtree(raster_path)

    def _download_layer_files(self, layer_name):
        """Download and cache files for one layer, then return its folder path.

        Prefer :meth:`get_layer` for normal usage. This lower-level helper is
        used internally and handles update checks and historical backups of
        replaced layer folders.

        :param layer_name: Layer name such as ``Rotations`` or ``Coastlines``.
        :returns: Path to the local layer folder.
        :rtype: str
        :raises Exception: If called in readonly mode.
        :raises LayerNotFoundInModel: If the layer is not configured in this
            model.
        """
        if self.readonly:
            raise Exception("Unable to download layer files in readonly mode.")

        layer_file_url = self._get_layer_file_url(layer_name)

        model_folder = self.create_model_dir()
        layer_folder = f"{model_folder}/{layer_name}"
        metadata_file = f"{layer_folder}/{self.meta_filename}"

        downloader = download.FileDownloader(
            layer_file_url, metadata_file, model_folder, timeout=self.timeout
        )
        # only re-download when necessary
        if downloader.check_if_file_need_update():
            if os.path.isdir(layer_folder):
                # move the old layer files into "history" folder
                timestamp_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                history_dir = f"{model_folder}/history/{layer_name}_{timestamp_str}"
                Path(history_dir).mkdir(parents=True, exist_ok=True)
                shutil.move(layer_folder, history_dir)

            downloader.download_file_and_update_metadata()
        else:
            if downloader.check_if_expire_date_need_update():
                # update the expiry date
                logger.debug(
                    f"The local files in {layer_folder} are still good but the expiry date needs to be updated. Will update the expiry date in metadata."
                )
                downloader.update_metadata()
            else:
                logger.debug(
                    f"The local files in {layer_folder} are still good. Will not download again at this moment."
                )

        return layer_folder

    def download_all_layers(self):
        """Download all configured layers for this model.

        This includes ``Rotations`` when available, plus every entry under
        ``model["Layers"]``.
        """
        if self.readonly:
            raise Exception("Unable to download all layers in readonly mode.")

        async def f():
            tasks = []
            if "Rotations" in self.model:
                tasks.append(self.run(self._download_layer_files, "Rotations"))
            if "Layers" in self.model:
                for layer in self.model["Layers"]:
                    tasks.append(self.run(self._download_layer_files, layer))

            # print(tasks)
            await asyncio.wait(tasks)

        try:
            self.loop.run_until_complete(f())
        except RuntimeError:
            import nest_asyncio

            nest_asyncio.apply()
            self.loop.run_until_complete(f())

    def get_avail_time_dependent_raster_names(self):
        """Return configured names of time-dependent rasters.

        :returns: Raster names from ``TimeDepRasters``, or an empty list when
            the model defines none.
        :rtype: list[str]
        """
        if not "TimeDepRasters" in self.model:
            return []
        else:
            return [name for name in self.model["TimeDepRasters"]]

    def download_time_dependent_rasters(self, raster_name, times=None):
        """Download and cache a time series of rasters for ``raster_name``.

        :param raster_name: Raster key in ``model["TimeDepRasters"]``.
        :param times: Iterable of reconstruction times (Ma). If omitted, download
            every integer time from ``SmallTime`` to ``BigTime`` inclusive.
        :raises Exception: If called in readonly mode or raster configuration is
            missing.
        """
        if self.readonly:
            raise Exception(
                "Unable to download time dependent rasters in readonly mode."
            )

        if (
            "TimeDepRasters" in self.model
            and raster_name in self.model["TimeDepRasters"]
        ):

            async def f():
                nonlocal times
                tasks = []

                dst_path = f"{self.get_model_dir()}/Rasters/{raster_name}"
                if not times:
                    times = range(self.model["SmallTime"], self.model["BigTime"] + 1)
                for time in times:
                    tasks.append(
                        self.run(
                            self._download_raster,
                            self.model["TimeDepRasters"][raster_name].format(time),
                            dst_path,
                        )
                    )

                # print(tasks)
                await asyncio.wait(tasks)

            try:
                self.loop.run_until_complete(f())
            except RuntimeError:
                import nest_asyncio

                nest_asyncio.apply()
                self.loop.run_until_complete(f())

        else:
            raise Exception(
                f"Unable to find {raster_name} configuration in this model {self.model_name}."
            )

    def _download_raster(self, url, dst_path):
        """Download one raster file to ``dst_path`` with metadata tracking.

        A per-file metadata JSON is stored under ``{dst_path}/.metadata`` and
        used to decide whether updates are required on subsequent calls.

        :param url: Source URL of the raster file.
        :param dst_path: Destination folder path for the downloaded file.
        :raises Exception: If called in readonly mode.
        """
        if self.readonly:
            raise Exception("Unable to download raster in readonly mode.")
        filename = url.split("/")[-1]
        metadata_folder = f"{dst_path}/.metadata"
        metadata_file = f"{metadata_folder}/{filename}.json"

        downloader = download.FileDownloader(
            url, metadata_file, dst_path, timeout=self.timeout
        )
        # only re-download when necessary
        if downloader.check_if_file_need_update():
            downloader.download_file_and_update_metadata()
        else:
            if downloader.check_if_expire_date_need_update():
                # update the expiry date
                downloader.update_metadata()

            logger.debug(
                f"The local raster file {dst_path}/{filename} is still good. Will not download again at this moment."
            )

    def download_all(self):
        """Download all layers and all configured time-dependent rasters."""
        if self.readonly:
            raise Exception("Unable to download all in readonly mode.")
        self.download_all_layers()
        if "TimeDepRasters" in self.model:
            for raster in self.model["TimeDepRasters"]:
                self.download_time_dependent_rasters(raster)

    def _get_layer_file_url(self, layer_name: str):
        """Return the download URL for a configured layer.

        ``Rotations`` is stored as a top-level model entry, while geometry
        layers are stored under ``model["Layers"]``.

        :param layer_name: Layer name to resolve.
        :returns: Layer archive URL.
        :rtype: str
        :raises LayerNotFoundInModel: If ``layer_name`` is not configured.
        """
        # find the layer file url. two parts. one is the rotation, the other is all other geometry layers
        if layer_name == "Rotations":
            # for Rotations
            return self.model[layer_name]
        elif "Layers" in self.model and layer_name in self.model["Layers"]:
            # for other geometry layers
            return self.model["Layers"][layer_name]
        else:
            logger.debug(f"{json.dumps(self.model, indent=4)}")
            raise LayerNotFoundInModel(
                f"The layer({layer_name}) was not found in model({self.model_name})."
            )
