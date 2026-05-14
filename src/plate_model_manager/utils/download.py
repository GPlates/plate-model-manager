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
    """class for managing single file download"""

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
        """FileDownloader constructor

        :param file_url: the url to the file
        :param metadata_file: the path to the metadata file
        :param dst_dir: the destination to save the file
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
        """check if the file need an update(download/re-download the files)
        return true if "need update", otherwise false

        1. check if the metadata file exists
        2. check if the file urls match
        3. check expire date
        4. check etag
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
                        logger.debug("The file expired. Check etag.")
                        need_check_etag = True  # expired, need to check etag to decide
                    else:
                        # layer file has not expired yet, no need to check update
                        return False
                except ValueError:
                    need_check_etag = (
                        True  # invalid expiry date, need to check etag to decide
                    )
            else:
                need_check_etag = (
                    True  # no expiry date in metafile, need to check etag to make sure
                )

            if need_check_etag:
                self.meta_sha256 = meta.get("sha256")
                self.new_sha256 = network.get_sha256(self.file_url, timeout=self.timeout)

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
        """download a file from "file_url", save the file in "dst_dir" and update the metadata file

        :param file_url: the url to the file
        :param metadata_file: the path to the metadata file
        :param dst_dir: the destination to save the file

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
        """update metadata file"""
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
        Path("/".join(self.meta_filepath.split("/")[:-1])).mkdir(
            parents=True, exist_ok=True
        )
        with open(self.meta_filepath, "w+") as f:
            json.dump(metadata, f)

    def check_if_expire_date_need_update(self):
        # if we have checked the etag and it is the same as before
        # we need to update the expiry date
        return self.new_etag is not None and self.new_etag == self.meta_etag
