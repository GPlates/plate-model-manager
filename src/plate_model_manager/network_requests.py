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
import io
import os
from pathlib import Path
from typing import List, Union

import requests

from plate_model_manager.exceptions import FailedToDownloadFile

from .file_fetcher import FileFetcher
from .utils import unzip

# This file contains the code to download file(s) from url(s) using "requests" + "asyncio"
# Download files concurrently can improve the performance significantly.
# Download partial content of a large file concurrently may/maynot work depending on the server configuration.


class RequestsFetcher(FileFetcher):
    def __init__(self):
        pass

    def fetch_file(
        self,
        url: str,
        filepath: str,
        filename: Union[str, None] = None,
        etag: Union[str, None] = None,
        auto_unzip: bool = True,
        timeout=(None, None),
    ):
        """download a file from "url" and save to "filepath"
            You can give a new "filename" for the file.
            If "etag" is given, check if etag has changed. If not changed, do not download again.

        :param url: the url to download file from
        :param filepath: location to keep the file
        :param etag: old etag. if the old etag is the same with the one on server, do not download again.
        :param auto_unzip: bool flag to indicate if unzip .zip file automatically

        """
        if isinstance(etag, str) or isinstance(etag, bytes):
            headers = {"If-None-Match": etag}
        else:
            headers = {}

        if os.path.isfile(filepath):
            raise Exception(
                f"The 'filepath' is in fact a file. The 'filepath' should be a folder path(non-exist is fine). {filepath}"
            )
        Path(filepath).mkdir(parents=True, exist_ok=True)

        r = requests.get(url, allow_redirects=True, headers=headers, timeout=timeout)
        # print(r.headers)

        if r.status_code == 304:
            # print(url)
            print(
                "The file has not been changed since it was downloaded last time. Do nothing and return."
            )
        elif r.status_code == 200:
            if filename is None:
                filename = url.split("/")[-1]  # use the filename in the url
            if auto_unzip:
                try:
                    unzip.save_compressed_data(url, io.BytesIO(r.content), filepath)
                except Exception as ex:
                    # print(ex)
                    self._save_file(filepath, filename, r.content)
            else:
                self._save_file(filepath, filename, r.content)
        else:
            raise FailedToDownloadFile(
                f"HTTP request failed with code {r.status_code}. {url}"
            )
        new_etag = r.headers.get("ETag")
        if new_etag:
            # remove the content-encoding awareness thing
            new_etag = new_etag.replace("-gzip", "")

        return new_etag

    def _fetch_range(
        self, url, index: int, chunk_size: int, data: List, timeout=(None, None)
    ):
        """get patial content of a file from the server
        Be careful, some server does not support this function.
        And some firewall sequences these requests to shape network traffic and defeat the purpose
        of this function completely. So it might slower than download directly.

        """
        # print(index)
        # st = time.time()
        headers = {
            "Range": f"bytes={index*chunk_size}-{(index+1)*chunk_size-1}",
            "Accept-Encoding": "identity",
        }

        r = requests.get(url, headers=headers, timeout=timeout)
        if r.status_code == 206:
            data[index].write(r.content)
        else:
            raise FailedToDownloadFile(
                f"Failed to fetch range from {url} at index {index}"
            )
        # et = time.time()
        # print(f"{index} -- time: {et - st}")

    def _run_fetch_large_file(self, loop, url, filesize, data, timeout=(None, None)):
        """run async function"""
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=15)
        run = functools.partial(loop.run_in_executor, executor)
        loop.run_until_complete(
            self._fetch_large_file(run, url, filesize, data, timeout=timeout)
        )

    async def _fetch_large_file(
        self,
        run,
        url,
        file_size: int,
        data: List,
        chunk_size=10 * 1000 * 1000,
        timeout=(None, None),
    ):
        """async implementation of fetch_large_file"""

        num_chunks = file_size // chunk_size + 1
        data_array = [io.BytesIO() for i in range(num_chunks)]
        tasks = [
            run(self._fetch_range, url, i, chunk_size, data_array, timeout)
            for i in range(num_chunks)
        ]

        await asyncio.wait(tasks)

        for i in range(num_chunks):
            data_array[i].seek(0)
            data[0].write(data_array[i].read())

    async def _async_fetch_files(
        self,
        run,
        urls,
        filepaths: Union[list, str],
        etags=[],
        auto_unzip: bool = True,
        timeout=(None, None),
    ):
        """async implementation of fetch_files function"""
        tasks = []
        for idx, url in enumerate(urls):
            # get filepath
            if isinstance(filepaths, str):
                filepath = filepaths
            elif isinstance(filepaths, list) and len(filepaths) > idx:
                filepath = filepaths[idx]
            else:
                raise Exception(
                    "The 'filepaths' should be either one string or a list of strings. And the length of the list should be the same with the length of urls. "
                )

            # get etag
            if len(etags) > idx:
                etag = etags[idx]
            else:
                etag = None

            filename = None
            tasks.append(
                run(self.fetch_file, url, filepath, filename, etag, auto_unzip, timeout)
            )
        # print(tasks)
        await asyncio.wait(tasks)

    def fetch_files(
        self,
        urls,
        filepaths: Union[list, str],
        filenames=[],
        etags=[],
        auto_unzip: bool = True,
        timeout=(None, None),
    ):
        """fetch multiple files concurrently

        :param urls: the urls to download files from
        :param filepaths: location(s) to keep the files. This can be one path for all files or one path for each file.
        :param etags: old etags. if the old etag is the same with the one on server, do not download again.
        :param auto_unzip: bool flag to indicate if unzip .zip file automatically

        """

        # set up concurrent functions
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=15)
        loop = asyncio.new_event_loop()
        run = functools.partial(loop.run_in_executor, executor)

        asyncio.set_event_loop(loop)

        try:
            loop.run_until_complete(
                self._async_fetch_files(
                    run,
                    urls,
                    filepaths,
                    etags=etags,
                    auto_unzip=auto_unzip,
                    timeout=timeout,
                )
            )
        except RuntimeError:
            import nest_asyncio

            nest_asyncio.apply()
            loop.run_until_complete(
                self._async_fetch_files(
                    run,
                    urls,
                    filepaths,
                    etags=etags,
                    auto_unzip=auto_unzip,
                    timeout=timeout,
                )
            )
        finally:
            loop.close()


def fetch_file(
    url: str,
    filepath: str,
    filename: Union[str, None] = None,
    etag: Union[str, None] = None,
    auto_unzip: bool = True,
    timeout=(None, None),
):
    fetcher = RequestsFetcher()
    return fetcher.fetch_file(
        url,
        filepath,
        filename=filename,
        etag=etag,
        auto_unzip=auto_unzip,
        timeout=timeout,
    )


def fetch_files(
    urls,
    filepaths: Union[list, str],
    etags=[],
    auto_unzip: bool = True,
    timeout=(None, None),
):
    fetcher = RequestsFetcher()
    return fetcher.fetch_files(
        urls, filepaths, etags=etags, auto_unzip=auto_unzip, timeout=timeout
    )


def fetch_large_file(
    url: str,
    filepath: str,
    filename: Union[str, None] = None,
    filesize: Union[int, None] = None,
    etag: Union[str, None] = None,
    auto_unzip: bool = True,
    check_etag: bool = True,
    timeout=(None, None),
):
    fetcher = RequestsFetcher()
    return fetcher.fetch_large_file(
        url,
        filepath,
        filename=filename,
        filesize=filesize,
        etag=etag,
        auto_unzip=auto_unzip,
        check_etag=check_etag,
        timeout=timeout,
    )
