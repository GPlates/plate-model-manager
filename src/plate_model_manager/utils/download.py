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
from datetime import datetime, timedelta
from pathlib import Path
from typing import Union

from .. import network_aiohttp, network_requests
from . import network

EXPIRY_TIME_FORMAT = "%Y/%m/%d, %H:%M:%S"
EXPIRE_HOURS = 12

logger = logging.getLogger("pmm")

# {url:{new-etag:"xxxx", file-size:12345, meta-etag:"uuuuu"}}
etag_and_file_size_cache = {}

from enum import Enum


class HttpClient(Enum):
    REQUESTS = 1
    AIOHTTP = 2


class FileDownloader:
    """Class for managing single file download"""

    def __init__(
        self,
        file_url: str,
        meta_filepath: str,
        dst_dir: str,
        filename: Union[str, None] = None,
        auto_unzip: bool = True,
        expire_hours=EXPIRE_HOURS,
        expiry_time_format=EXPIRY_TIME_FORMAT,
        large_file_hint=False,
        timeout=(None, None),
        http_client: HttpClient = HttpClient.REQUESTS,
    ) -> None:
        """Initialize a downloader for one remote file and its metadata.

        :param file_url:
            Source URL for the target file.
        :param meta_filepath:
            Path to the JSON metadata file used to store cache fields such as
            URL, expiry, ETag, and SHA-256.
        :param dst_dir:
            Local destination directory where the downloaded file is stored.
        :param filename:
            Optional output filename. If ``None``, the client chooses a name
            (typically derived from the URL).
        :param auto_unzip:
            If ``True`` (default), unzip compressed downloads when supported by
            the active HTTP client.
        :param expire_hours:
            Number of hours to add to ``datetime.now()`` when writing metadata
            ``expiry``.
        :param expiry_time_format:
            ``datetime.strftime``/``strptime`` format used for metadata
            ``expiry`` values.
        :param large_file_hint:
            If ``True``, fetch headers early to estimate file size and prefer
            large-file transfer logic for big downloads.
        :param timeout:
            Network timeout tuple passed to helper requests. Conventionally
            ``(connect_timeout, read_timeout)``.
        :param http_client:
            HTTP backend selection, either ``HttpClient.REQUESTS`` or
            ``HttpClient.AIOHTTP``.
        """
        self.file_url = file_url
        self.meta_filepath = meta_filepath
        self.dst_dir = dst_dir
        self.filename = filename
        self.expire_hours = expire_hours
        self.expiry_time_format = expiry_time_format
        self.meta_etag = None
        self.new_etag = None
        self.meta_sha256 = None
        self.new_sha256 = None
        self.file_size = None
        self.large_file_hint = large_file_hint
        self.timeout = timeout
        self.auto_unzip = auto_unzip
        self.http_client = http_client

    def check_if_file_need_update(self):
        """Decide whether the target file should be downloaded again.

        Returns:
            bool: ``True`` when the file should be downloaded/re-downloaded,
            ``False`` when the existing local file can be reused.

        Decision flow:
            1. If the metadata file is missing, return ``True``.
            2. If the stored ``url`` differs from ``self.file_url`` (or is
               missing), return ``True``.
            3. If the metadata ``expiry`` is still valid, return ``False``.
            4. If expired (or expiry is invalid/missing), compare remote
               content state:
               - Prefer SHA-256 comparison when available.
               - Fall back to ETag comparison if SHA-256 cannot be obtained.
               - If neither reliable value is available, return ``True``.
        """

        #
        # first check if the metadata file exists
        # since metadata file is inside the layer folder, this check will also confirm the existence of the layer folder
        #
        if not os.path.isfile(self.meta_filepath):
            logger.debug(
                f"the metadata file({self.meta_filepath}) does not exist, need to download the file({self.file_url})"
            )
            return True

        with open(self.meta_filepath, "r") as f:
            meta = json.load(f)
            #
            # check if the "url" in the metafile matches the "layer file url"
            #
            if "url" in meta:
                meta_url = meta["url"]
                if meta_url != self.file_url:
                    logger.debug(
                        "the layer url has changed, re-download the file({file_url})"
                    )
                    return True
            else:
                logger.debug(
                    "no url found in the metafile. to be on the safe side, re-download the file({file_url})"
                )
                return True
            #
            # now check the layer file's expiry date
            #
            need_check_etag = False
            if "expiry" in meta:
                try:
                    meta_expiry = meta["expiry"]
                    expiry_date = datetime.strptime(
                        meta_expiry, self.expiry_time_format
                    )
                    now = datetime.now()
                    if now > expiry_date:
                        logger.debug("The file expired. Check sha256 or etag.")
                        need_check_etag = (
                            True  # expired, need to check sha256 or etag to decide
                        )
                    else:
                        # layer file has not expired yet, no need to check update
                        logger.debug(
                            f"The file has not expired yet (expiry date: {expiry_date}, now: {now}). No need to check sha256 or etag. Will use the local file."
                        )
                        return False
                except ValueError:
                    need_check_etag = True  # invalid expiry date, need to check sha256 or etag to decide
            else:
                need_check_etag = True  # no expiry date in metafile, need to check sha256 or etag to make sure

            if need_check_etag:
                self.meta_sha256 = meta.get("sha256")
                self.new_sha256 = network.get_sha256(
                    self.file_url, timeout=self.timeout
                )

                if self.new_sha256:
                    if self.meta_sha256 == self.new_sha256:
                        logger.debug(
                            f"SHA-256 unchanged: {self.meta_sha256} matches {self.new_sha256}"
                        )
                        return False
                    logger.debug(
                        f"SHA-256 has changed or is missing in metadata. re-download the file({self.file_url})"
                    )
                    return True

                if "etag" in meta:
                    meta_etag = meta["etag"]
                    headers = network.get_headers(self.file_url)
                    self.file_size = network.get_content_length(headers)
                    self.new_etag = network.get_etag(headers)

                    if meta_etag == self.new_etag:
                        logger.debug(f"{meta_etag} -- {self.new_etag}")
                        return False
                    else:
                        logger.debug(
                            f"etag has been changed. re-download the file({self.file_url})"
                        )
                        return True

                else:
                    logger.debug(
                        f"no etag found in the metadata file, to be safe, re-download the file({self.file_url})"
                    )
                    return True

            logger.debug("This line and below should not be reached!!!!")
            return True

    def download_file_and_update_metadata(self):
        """Download the target file and refresh its metadata cache.

        The method selects an HTTP backend from ``self.http_client`` and then
        chooses download strategy based on size:

        - If ``self.large_file_hint`` is ``True``, it first retrieves response
          headers and stores ``self.file_size``.
        - If ``self.file_size`` is known and greater than 20 MB, it uses
          ``fetch_large_file``.
        - Otherwise, it uses ``fetch_file``.

        After a successful download call, ``self.new_etag`` is updated from the
        client response and :meth:`update_metadata` is called to write metadata
        fields (URL, expiry, ETag, SHA-256) to ``self.meta_filepath``.

        :raises Exception:
            Propagates exceptions raised by network/header retrieval, download
            client calls, or metadata writing.
        """
        if self.large_file_hint:
            headers = network.get_headers(self.file_url)
            self.file_size = network.get_content_length(headers)

        if self.http_client == HttpClient.REQUESTS:
            client = network_requests
        else:
            client = network_aiohttp

        if self.file_size and self.file_size > 20 * 1000 * 1000:
            self.new_etag = client.fetch_large_file(
                self.file_url,
                self.dst_dir,
                filename=self.filename,
                filesize=self.file_size,
                etag=None,
                auto_unzip=self.auto_unzip,
                check_etag=False,
            )

        else:
            self.new_etag = client.fetch_file(
                self.file_url,
                self.dst_dir,
                filename=self.filename,
                etag=self.meta_etag,
                auto_unzip=self.auto_unzip,
            )

        # update metadata file
        self.update_metadata()

    def update_metadata(self):
        """Write or refresh the JSON metadata file for the current download.

        The metadata file at ``self.meta_filepath`` is created (including
        parent directories) and overwritten with these fields:

        - ``url``: ``self.file_url``
        - ``expiry``: current time plus ``self.expire_hours`` formatted with
          ``self.expiry_time_format``
        - ``etag``: ``self.new_etag``
        - ``sha256``: ``self.new_sha256``

        If ``self.new_sha256`` is not already populated, SHA-256 is retrieved
        from the remote resource before writing metadata.

        :raises Exception:
            Propagates exceptions raised while fetching SHA-256, creating
            directories, or writing the metadata file.
        """
        if self.new_sha256 is None:
            self.new_sha256 = network.get_sha256(self.file_url, timeout=self.timeout)
        metadata = {
            "url": self.file_url,
            "expiry": (datetime.now() + timedelta(hours=self.expire_hours)).strftime(
                self.expiry_time_format
            ),
            "etag": self.new_etag,
            "sha256": self.new_sha256,
        }
        Path(self.meta_filepath).parent.mkdir(parents=True, exist_ok=True)
        with open(self.meta_filepath, "w+") as f:
            json.dump(metadata, f)

    def check_if_expire_date_need_update(self):
        """Return whether only the metadata expiry timestamp should be refreshed.

        This helper is typically called after :meth:`check_if_file_need_update`
        has fetched remote state. It returns ``True`` when remote content is
        unchanged and therefore the local file can be kept while extending the
        metadata ``expiry`` value.

        Match conditions (either is sufficient):

        - SHA-256 path: ``self.new_sha256`` is available and equals
          ``self.meta_sha256``.
        - ETag fallback path: ``self.new_etag`` is available and equals
          ``self.meta_etag``.

        :return:
            ``True`` if content identity is unchanged and expiry metadata
            should be updated, otherwise ``False``.
        :rtype: bool
        """
        # if we have checked the etag and it is the same as before
        # we need to update the expiry date
        return (
            self.new_sha256 is not None and self.meta_sha256 == self.new_sha256
        ) or (self.new_etag is not None and self.new_etag == self.meta_etag)
