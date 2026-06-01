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
import io
import os
from pathlib import Path
from typing import List, Union

import aiohttp

from .file_fetcher import FileFetcher
from .utils import unzip

# This file contains experimental code to download files concurrently using aiohttp.
# Later, I realized that "requests"+"ThreadPoolExecutor" works as well.
# I do not want to introduce a new dependency when "requests" works.
# So, keep this file just for record keeping in case we need aiohttp in the future.


class AiohttpFetcher(FileFetcher):
    def __init__(self):
        pass

    def fetch_file(
        self,
        url: str,
        filepath: str,
        filename: Union[str, None] = None,
        etag: Union[str, None] = None,
        auto_unzip: bool = True,
    ):
        """Download a single file.

        Args:
            url: URL to download.
            filepath: Folder where the file should be saved.
            filename: Optional override name for the downloaded file.
            etag: Optional cached ETag used to skip unchanged downloads.
            auto_unzip: If ``True``, automatically extract downloaded ``.zip``
                files when possible.

        Returns:
            The new ETag value returned by the server, if any.
        """

        async def f():
            async with aiohttp.ClientSession() as session:
                await self._fetch_file(
                    session,
                    url,
                    filepath,
                    filename=filename,
                    etag=etag,
                    auto_unzip=auto_unzip,
                )
            await asyncio.sleep(
                0.250
            )  # https://docs.aiohttp.org/en/stable/client_advanced.html#graceful-shutdown

        asyncio.run(f())

    async def _fetch_file(
        self,
        session,
        url: str,
        filepath: str,
        filename: Union[str, None] = None,
        etag: Union[str, None] = None,
        auto_unzip: bool = True,
    ):
        """Async implementation behind :meth:`fetch_file`.

        Args:
            session: Active ``aiohttp`` client session.
            url: URL to download.
            filepath: Folder where the file should be saved.
            filename: Optional override name for the downloaded file.
            etag: Optional cached ETag used to skip unchanged downloads.
            auto_unzip: If ``True``, automatically extract downloaded ``.zip``
                files when possible.

        Returns:
            The new ETag value returned by the server, if any.
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

        async with session.get(url, headers=headers) as r:
            content = await r.content.read()
            # r = requests.get(url, allow_redirects=True, headers=headers)
            # print(r.headers)

            if r.status == 304:
                # print(url)
                print(
                    "The file has not been changed since it was downloaded last time. Do nothing and return."
                )
            elif r.status == 200:
                if not filename:
                    filename = url.split("/")[-1]  # use the filename in the url
                if auto_unzip:
                    try:
                        unzip.save_compressed_data(url, io.BytesIO(content), filepath)
                    except Exception as ex:
                        # print(ex)
                        self._save_file(filepath, filename, content)
                else:
                    self._save_file(filepath, filename, content)
            else:
                raise Exception(f"HTTP request failed with code {r.status_code}.")
            new_etag = r.headers.get("ETag")
            if new_etag:
                # remove the content-encoding awareness thing
                new_etag = new_etag.replace("-gzip", "")

            return new_etag

    async def _fetch_range(
        self, session, url: str, index: int, chunk_size: int, data: List
    ):
        """Fetch one byte range for a large file download.

        Args:
            session: Active ``aiohttp`` client session.
            url: URL to download.
            index: Zero-based chunk index.
            chunk_size: Size of each chunk in bytes.
            data: List of in-memory buffers receiving each chunk.

        Raises:
            Exception: If the server does not return HTTP 206 for the range
                request.
        """
        # print(index)
        # st = time.time()
        headers = {
            "Range": f"bytes={index*chunk_size}-{(index+1)*chunk_size-1}",
            "Accept-Encoding": "identity",
        }

        # r = requests.get(url, headers=headers)
        async with session.get(url, headers=headers) as r:
            if r.status == 206:
                c = await r.content.read()
                data[index].write(c)
            else:
                raise Exception(f"Failed to fetch range from {url} at index {index}")
        # et = time.time()
        # print(f"{index} -- time: {et - st}")

    async def _fetch_large_file(
        self, url: str, file_size: int, data: List, chunk_size=10 * 1000 * 1000
    ):
        """Download a large file using concurrent range requests.

        Args:
            url: URL to download.
            file_size: Total file size in bytes.
            data: Output buffer list whose first element receives the content.
            chunk_size: Size of each concurrent range request in bytes.
        """
        async with aiohttp.ClientSession() as session:
            num_chunks = file_size // chunk_size + 1
            data_array = [io.BytesIO() for i in range(num_chunks)]
            tasks = [
                asyncio.ensure_future(
                    self._fetch_range(session, url, i, chunk_size, data_array)
                )
                for i in range(num_chunks)
            ]

            await asyncio.wait(tasks)

            for i in range(num_chunks):
                data_array[i].seek(0)
                data[0].write(data_array[i].read())

    def _run_fetch_large_file(self, loop, url, filesize, data):
        """Run the large-file coroutine on the given event loop."""
        loop.run_until_complete(self._fetch_large_file(url, filesize, data))

    def fetch_files(
        self,
        urls,
        filepaths,
        filenames=[],
        etags=[],
        auto_unzip: bool = True,
    ):
        """Download multiple files concurrently.

        Args:
            urls: URLs to download.
            filepaths: Output location(s). This can be a single folder used for
                every URL, or a list of per-file destinations matching ``urls``.
            filenames: Optional override names for the downloaded files.
            etags: Optional cached ETag values used to skip unchanged files.
            auto_unzip: If ``True``, automatically extract downloaded ``.zip``
                files when possible.

        Returns:
            A list of the new ETag values returned by the server.
        """

        async def f():
            async with aiohttp.ClientSession() as session:
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

                    if len(filenames) > idx:
                        filename = filenames[idx]
                    else:
                        filename = None

                    tasks.append(
                        asyncio.ensure_future(
                            self._fetch_file(
                                session,
                                url,
                                filepath,
                                filename,
                                etag=etag,
                                auto_unzip=auto_unzip,
                            )
                        )
                    )

                return await asyncio.gather(*tasks)

        # set up concurrent functions
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        new_etags = []
        try:
            new_etags = loop.run_until_complete(f())
        except RuntimeError:
            import nest_asyncio

            nest_asyncio.apply()
            new_etags = loop.run_until_complete(f())
        finally:
            loop.close()
        return new_etags


def fetch_file(
    url: str,
    filepath: str,
    filename: Union[str, None] = None,
    etag: Union[str, None] = None,
    auto_unzip: bool = True,
):
    fetcher = AiohttpFetcher()
    return fetcher.fetch_file(
        url, filepath, filename=filename, etag=etag, auto_unzip=auto_unzip
    )


def fetch_files(
    urls,
    filepaths,
    etags=[],
    auto_unzip: bool = True,
    filenames=[],
):
    fetcher = AiohttpFetcher()
    return fetcher.fetch_files(
        urls, filepaths, etags=etags, auto_unzip=auto_unzip, filenames=filenames
    )


def fetch_large_file(
    url: str,
    filepath: str,
    filename: Union[str, None] = None,
    filesize: Union[int, None] = None,
    etag: Union[str, None] = None,
    auto_unzip: bool = True,
    check_etag: bool = True,
):
    fetcher = AiohttpFetcher()
    return fetcher.fetch_large_file(
        url,
        filepath,
        filename=filename,
        filesize=filesize,
        etag=etag,
        auto_unzip=auto_unzip,
        check_etag=check_etag,
    )
