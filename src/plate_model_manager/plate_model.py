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
    """Download and manage files required for a plate reconstruction model.

    👀👇 **LOOK HERE!!!** 👀👇

    Normally you should always use :py:meth:`PlateModelManager.get_model()` to get a :class:`PlateModel` object.
    Create a :class:`PlateModel` object directly only when you don't have Internet connection and would like
    to use the local model files in ``readonly`` mode.
    Do not create a :class:`PlateModel` object directly if you have no idea what's going on.

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
        """Constructor. Create a :class:`PlateModel` instance.

        :param model_name: The model name of interest.
        :type model_name: str
        :param model_cfg: The model configuration in JSON format.
                          The configuration is either downloaded from the server or
                          loaded from a local file ``.metadata.json``. If you are confused by this parameter,
                          use :py:meth:`PlateModelManager.get_model()` to get a :class:`PlateModel` object instead.
        :param data_dir: The folder path to save the model data.
        :type data_dir: str, default="."
        :param readonly: If this flag is set to ``True``, The :class:`PlateModel` object will use
                         the files in the local folder and will not attempt to
                         download/update the files from the server.
        :type readonly: bool, default=False
        :param timeout: Network connection `timeout parameter <https://requests.readthedocs.io/en/latest/user/advanced/#timeouts>`__.
        """
        self.model_name = model_name.lower()
        self.meta_filename = METADATA_FILENAME
        self._model = model_cfg
        self.reference_frame = reference_frame
        self.readonly = readonly
        self.timeout = timeout

        self.data_dir = data_dir

        self.model_dir = f"{self.data_dir}/{self.model_name}"

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
        """The model metadata."""
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
        attributes = self.__dict__.copy()
        attributes.pop("executor", None)
        attributes.pop("loop", None)
        attributes.pop("run", None)
        return attributes

    def __setstate__(self, state):
        self.__dict__ = state
        if not self.readonly:
            # async and concurrent things
            self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=15)
            self.loop = asyncio.new_event_loop()
            self.run = functools.partial(self.loop.run_in_executor, self.executor)
            asyncio.set_event_loop(self.loop)

    def __del__(self):
        if not self.readonly:
            try:
                self.loop.close()
            except:
                pass  # ignore the exception when closing the loop if any

    def get_cfg(self):
        """Return the model configuration."""
        return self.model

    def get_model_dir(self):
        """Return the path to a folder containing the model files."""
        if PlateModel.is_model_dir(self.model_dir):
            return self.model_dir
        elif not self.readonly:
            return self.create_model_dir()
        else:
            raise Exception(
                f"The model dir {self.model_dir} is invalid and could not create it (in readonly mode)."
            )

    def get_data_dir(self):
        """Return the path to a folder (parent folder of the ``model dir``) containing a set of downloaded models."""
        return self.data_dir

    def set_data_dir(self, new_dir):
        """Change the folder (parent folder of the ``model dir``) in which you would like to save your model."""
        self.data_dir = new_dir
        self.model_dir = f"{self.data_dir}/{self.model_name}/"

    def get_big_time(self):
        """The max (big number in Ma) reconstruction time in the model."""
        return self.model["BigTime"]

    def get_small_time(self):
        """The min (small number in Ma) reconstruction time in the model."""
        return self.model["SmallTime"]

    def get_avail_layers(self):
        """Get all available layers in this plate model."""
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
            rotation_folder = f"{self.model_dir}/Rotations"
        rotation_files = glob.glob(f"{rotation_folder}/*.rot")
        rotation_files.extend(glob.glob(f"{rotation_folder}/*.grot"))
        # print(rotation_files)
        if reference_frame is None:
            reference_frame = self.reference_frame
        if reference_frame == ReferenceFrame.PmagReferenceFrame:
            attrs = self.model.get("Attributes", None)
            pmag_ref_frame_anchor_pid = (
                attrs.get("PmagReferenceFrameAnchorPID", None) if attrs else None
            )
            if pmag_ref_frame_anchor_pid is None:
                if self.reference_frame == ReferenceFrame.PmagReferenceFrame:
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
        """Return a list of ``coastlines`` files."""
        return self.get_layer(
            "Coastlines", return_none_if_not_exist=return_none_if_not_exist
        )

    def get_static_polygons(
        self, return_none_if_not_exist: bool = False
    ) -> Union[List[str], None]:
        """Return a list of ``static polygons`` files."""
        return self.get_layer(
            "StaticPolygons", return_none_if_not_exist=return_none_if_not_exist
        )

    def get_continental_polygons(
        self, return_none_if_not_exist: bool = False
    ) -> Union[List[str], None]:
        """Return a list of ``continental polygons`` files."""
        return self.get_layer(
            "ContinentalPolygons", return_none_if_not_exist=return_none_if_not_exist
        )

    def get_topologies(
        self, return_none_if_not_exist: bool = False
    ) -> Union[List[str], None]:
        """Return a list of ``topologies`` files."""
        return self.get_layer(
            "Topologies", return_none_if_not_exist=return_none_if_not_exist
        )

    def get_COBs(
        self, return_none_if_not_exist: bool = False
    ) -> Union[List[str], None]:
        """Return a list of ``Continent-Ocean Boundaries`` files."""
        return self.get_layer("COBs", return_none_if_not_exist=return_none_if_not_exist)

    def get_layer(
        self, layer_name: str, return_none_if_not_exist: bool = False
    ) -> Union[List[str], None]:
        """Get a list of layer files by a layer name. Call :meth:`get_avail_layers` to get all the available layer names.

        Raise :class:`LayerNotFoundInModel` exception to get user's attention by default.
        Set ``return_none_if_not_exist`` to ``True`` if you don't want to see the :class:`LayerNotFoundInModel` exception.

        :param layer_name: The layer name of interest.
        :param return_none_if_not_exist: If set to ``True``, return ``None`` when the layer does not exist in the model.

        :returns: A list of file names or ``None`` if ``return_none_if_not_exist`` is set to ``True``.

        :raises :class:`LayerNotFoundInModel`: Raise this exception if the layer name does not exist in this model.

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

    def _resolve_raster_name(self, raster_name, reference_frame, generated_from):
        resolved_raster_name = raster_name
        if reference_frame is None:
            reference_frame = self.reference_frame
        if generated_from is not None:
            resolved_raster_name = f"{raster_name}{generated_from.value}"
        name_without_reference_frame = resolved_raster_name
        if reference_frame is not None:
            resolved_raster_name = f"{resolved_raster_name}{reference_frame.value}"
        if not "TimeDepRasters" in self.model:
            raise Exception(
                f"No time-dependent rasters found in this model '{self.model_name}'."
            )
        if not resolved_raster_name in self.model["TimeDepRasters"]:
            if name_without_reference_frame in self.model["TimeDepRasters"]:
                logger.warning(
                    f"Raster '{resolved_raster_name}' not found in this model '{self.model_name}', but '{name_without_reference_frame}' exists. This may be because the model does not have different reference frame versions of this raster. Will use '{name_without_reference_frame}' for now."
                )
                return name_without_reference_frame
            else:
                raise Exception(
                    f"Time-dependent rasters ({resolved_raster_name}) not found in this model '{self.model_name}'. "
                    + f"The raster name is constructed as: {raster_name}+{generated_from.value}+{reference_frame.value}."
                    + f"Available: {self.model['TimeDepRasters']}"
                )
        return resolved_raster_name

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
        """Return a local path for the age grid raster file at a given time."""
        return self.get_raster("AgeGrids", time, reference_frame, generated_from)

    def get_age_grids(
        self,
        times: List[Union[int, float]],
        reference_frame: Union[ReferenceFrame, None] = None,
        generated_from: Union[GenerationMethod, None] = None,
    ) -> List[str]:
        """Return local paths for the age grid raster files at given times."""
        return self.get_rasters("AgeGrids", times, reference_frame, generated_from)

    def get_spreading_rate_grid(
        self,
        time: Union[int, float],
        reference_frame: Union[ReferenceFrame, None] = None,
        generated_from: Union[GenerationMethod, None] = None,
    ) -> str:
        """Return a local path for the spreading rate grid raster file at a given time."""
        return self.get_raster("SpreadingRate", time, reference_frame, generated_from)

    def get_spreading_rate_grids(
        self,
        times: List[Union[int, float]],
        reference_frame: Union[ReferenceFrame, None] = None,
        generated_from: Union[GenerationMethod, None] = None,
    ) -> List[str]:
        """Return local paths for the spreading rate grid raster files at given times."""
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
        if self.readonly:
            raise Exception("Unable to create model folder in readonly mode.")
        if not self.model_dir:
            raise Exception(f"Error: Invalid model folder {self.model_dir}")

        model_path = self.model_dir
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
        """Return ``True`` if the folder contains files of a plate model, otherwise ``False``."""
        return os.path.isdir(folder_path) and os.path.isfile(
            f"{folder_path}/.metadata.json"
        )

    def purge(self):
        """Remove the model folder and everything inside the folder."""
        if os.path.isdir(self.model_dir):
            shutil.rmtree(self.model_dir)

    def purge_layer(self, layer_name):
        """Remove the layer folder of the given layer name."""
        layer_path = f"{self.model_dir}/{layer_name}"
        if os.path.isdir(layer_path):
            shutil.rmtree(layer_path)

    def purge_time_dependent_rasters(self, raster_name):
        """Remove the raster folder of the given raster name."""
        raster_path = f"{self.model_dir}/{raster_name}"
        if os.path.isdir(raster_path):
            shutil.rmtree(raster_path)

    def _download_layer_files(self, layer_name):
        """Download layer files for a given layer name. You should use :meth:`get_layer`, instead of this one, whenever possible.

        The layer files are in a ".zip" file. This function will download and unzip it.

        :param layer_name: the layer name, such as "Rotations","Coastlines", "StaticPolygons", "ContinentalPolygons", "Topologies", etc.
                           Call :meth:`get_avail_layers` to get all the available layer names.

        :returns: the folder path which contains the layer files

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
                downloader.update_metadata()

            logger.debug(
                f"The local files in {layer_folder} are still good. Will not download again at this moment."
            )

        return layer_folder

    def download_all_layers(self):
        """Download all layers. This function calls :meth:`download_layer_files()` on every available layer."""
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
        """Return all time-dependent raster names in this plate model."""
        if not "TimeDepRasters" in self.model:
            return []
        else:
            return [name for name in self.model["TimeDepRasters"]]

    def download_time_dependent_rasters(self, raster_name, times=None):
        """Download time-dependent rasters for a given raster name.

        Call :meth:`get_avail_time_dependent_raster_names()` to see all the available raster names in this model.

        :param raster_name: the raster name of interest
        :param times: if not given, download from begin to end with 1My interval
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
        """Download a single raster file from ``url`` and save the file in ``dst_path``.

        A metadata file will also be created for the raster file in folder ``f"{dst_path}/metadata"``

        :param url: the url to the raster file
        :param dst_path: the folder path to save the raster file

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
        """Download everything in this plate model."""
        if self.readonly:
            raise Exception("Unable to download all in readonly mode.")
        self.download_all_layers()
        if "TimeDepRasters" in self.model:
            for raster in self.model["TimeDepRasters"]:
                self.download_time_dependent_rasters(raster)

    def _get_layer_file_url(self, layer_name: str):
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
