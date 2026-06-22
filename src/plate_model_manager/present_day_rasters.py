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
import glob
import json
import logging
import os
from hashlib import sha256
from typing import Dict

import requests

from .network_requests import fetch_file
from .utils import download, misc
from .exceptions import RasterNameNotFound

DEFAULT_PRESENT_DAY_RASTERS_MANIFEST = (
    "https://repo.gplates.org/webdav/pmm/present_day_rasters.json"
)
logger = logging.getLogger("pmm")


class PresentDayRasterManager:
    """Manage present-day raster metadata retrieval and local raster access.

    .. note::

        You can use this class to do the things listed below.

        - Get a list of available present-day raster names.
        - Download a specific present-day raster.
    """

    def __init__(self, data_dir="present-day-rasters", raster_manifest=None):
        """Create a :class:`PresentDayRasterManager` instance.

        The raster manifest can be provided either as a local file path or as an
        HTTP(S) URL. If omitted, the default PMM raster manifest endpoint is used.

        :param data_dir: Directory where raster files and metadata are stored.
        :param raster_manifest: Local path or URL to a ``present_day_rasters.json``
            manifest. Provide this only when using a custom raster service.
        :raises Exception: If the manifest source is invalid or cannot be fetched.
        """
        if not raster_manifest:
            self.raster_manifest = DEFAULT_PRESENT_DAY_RASTERS_MANIFEST
        else:
            self.raster_manifest = raster_manifest
        self._rasters = None

        self.data_dir = data_dir

        # check if the model manifest file is a local file
        if os.path.isfile(self.raster_manifest):
            with open(self.raster_manifest) as f:
                self._rasters = json.load(f)
        elif self.raster_manifest.startswith(
            "http://"
        ) or self.raster_manifest.startswith("https://"):
            # try the http(s) url
            try:
                r = requests.get(self.raster_manifest)
                self._rasters = r.json()

            except requests.exceptions.ConnectionError:
                raise Exception(
                    f"Unable to fetch {self.raster_manifest}. "
                    + "No network connection or invalid URL!"
                )
        else:
            raise Exception(
                f"The model_manifest '{self.raster_manifest}' should be either a local file path or a http(s) URL."
            )

    @property
    def rasters(self) -> Dict:
        """Return raster metadata loaded from the configured manifest.

        :returns: Mapping of raster names to raster metadata.
        :rtype: Dict
        :raises Exception: If raster metadata is unexpectedly unavailable.
        """
        if self._rasters is not None:
            return self._rasters
        else:
            raise Exception(
                "The self._rasters is None. This should not happen. Something Extraordinary must have happened."
            )

    @rasters.setter
    def rasters(self, var) -> None:
        self._rasters = var

    def set_data_dir(self, data_dir):
        """Set the directory used to store downloaded raster files.

        :param data_dir: Directory path for local raster data.
        """
        self.data_dir = data_dir

    def list_present_day_rasters(self):
        """Return the list of available present-day raster names.

        :returns: Available raster names from the manifest.
        :rtype: list[str]
        """
        return [name for name in self.rasters]

    def _check_raster_avail(self, _name: str):
        """Validate that a raster name exists in the loaded manifest.

        :param _name: Raster name to validate.
        :returns: Lowercase raster name.
        :rtype: str
        :raises RasterNameNotFound: If the raster name is not defined.
        """
        name = _name.lower()
        if not name in self.rasters:
            raise RasterNameNotFound(f"Raster {name} is not found in {self.rasters}.")
        return name

    def is_wms(self, _name: str, check_raster_avail_flag=True):
        """Return whether a raster is served through WMS metadata.

        :param _name: The raster name of interest.
        :type _name: str
        :param check_raster_avail_flag: If ``True``, validate the raster name
            against the loaded manifest before checking service type.
        :type check_raster_avail_flag: bool
        :returns: ``True`` when the raster metadata marks the service as ``WMS``;
            otherwise ``False``.
        :rtype: bool
        """
        if check_raster_avail_flag:
            name = self._check_raster_avail(_name)
        else:
            name = _name.lower()
        if (
            isinstance(self.rasters[name], dict)
            and "service" in self.rasters[name]
            and self.rasters[name]["service"] == "WMS"
        ):
            return True
        else:
            return False

    def get_raster(
        self,
        _name: str,
        width=1800,
        height=800,
        bbox=[-180, -80, 180, 80],
        large_file_hint=True,
    ):
        """Download or fetch a raster and return its local file path.

        For file-based rasters, this method downloads and caches files under
        ``self.data_dir``. For WMS rasters, it requests a GeoTIFF with the given
        output dimensions and bounding box, and caches the result using a hash of
        the WMS request URL.

        Call :meth:`list_present_day_rasters` to inspect available raster names.

        :param _name: The raster name of interest.
        :type _name: str
        :param width: Output raster width in pixels for WMS requests.
        :type width: int
        :param height: Output raster height in pixels for WMS requests.
        :type height: int
        :param bbox: Geographic bounding box ``[min_lon, min_lat, max_lon, max_lat]``
            used for WMS requests.
        :type bbox: list[float]
        :param large_file_hint: Passed to file downloader to optimize large-file
            handling for non-WMS rasters.
        :type large_file_hint: bool

        :return: Local path to the downloaded or cached raster file.
        :rtype: str
        :raises RasterNameNotFound: If the raster name is not in the manifest.
        :raises Exception: If raster retrieval fails.
        """
        name = self._check_raster_avail(_name)
        is_wms_flag = self.is_wms(name, check_raster_avail_flag=False)

        if not is_wms_flag:
            downloader = download.FileDownloader(
                self.rasters[name],
                f"{self.data_dir}/{name}/.metadata.json",
                f"{self.data_dir}/{name}/",
                large_file_hint=large_file_hint,
            )
            # only re-download when necessary
            if downloader.check_if_file_need_update():
                downloader.download_file_and_update_metadata()
            else:
                if downloader.check_if_expire_date_need_update():
                    # update the expiry date
                    downloader.update_metadata()

                logger.debug(
                    f"The local raster file {self.data_dir}/{name} is still good. Will not download again at this moment."
                )

            files = glob.glob(f"{self.data_dir}/{name}/*")
            if len(files) == 0:
                raise Exception(f"Failed to get raster {name}")
            if len(files) > 1:
                misc.print_warning(
                    f"Multiple raster files have been detected.{files}. Return the first one found {files[0]}."
                )
            return files[0]
        else:
            server_url = self.rasters[name]["server_url"]
            version = self.rasters[name]["version"]
            layers = self.rasters[name]["layers"]
            if self.rasters[name]["hillshade_layer"]:
                layers.append(self.rasters[name]["hillshade_layer"])
            styles = self.rasters[name]["styles"]
            if self.rasters[name]["hillshade_style"]:
                styles.append(self.rasters[name]["hillshade_style"])
            format = "image/geotiff"
            url = (
                f"{server_url}/wms?service=WMS&version={version}&request=GetMap&layers={','.join(layers)}"
                + f"&bbox={bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}&width={width}&height={height}&srs=EPSG:4326"
                + f"&styles={','.join(styles)}&format={format}"
            )
            filepath = (
                f"{self.data_dir}/{name}/{sha256(url.encode('utf-8')).hexdigest()}"
            )
            if not os.path.isfile(f"{filepath}/{name}.tiff"):
                fetch_file(
                    url,
                    f"{self.data_dir}/{name}/{sha256(url.encode('utf-8')).hexdigest()}",
                    filename=f"{name}.tiff",
                )
            return f"{filepath}/{name}.tiff"
