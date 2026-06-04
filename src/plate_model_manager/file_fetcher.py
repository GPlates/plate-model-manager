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
import abc
import asyncio
import io
import os
from pathlib import Path
from typing import Union

from .utils import misc, network, unzip


class FileFetcher(metaclass=abc.ABCMeta):
    @classmethod
    def __subclasshook__(cls, subclass):
        return (
            hasattr(subclass, "fetch_file")
            and callable(subclass.fetch_file)
            and hasattr(subclass, "fetch_files")
            and callable(subclass.fetch_files)
            or hasattr(subclass, "fetch_large_file")
            and callable(subclass.fetch_large_file)
            or NotImplemented
        )

    @abc.abstractmethod
    def fetch_file(
        self,
        url: str,
        filepath: str,
        filename: Union[str, None] = None,
        etag: Union[str, None] = None,
        auto_unzip: bool = True,
    ):
        """download a file from "url" and save to "filepath"
        You can give a new "filename" for the file.
        If "etag" is given, check if etag has changed. If not changed, do not download again.

        :param url: the url to download file from
        :param filepath: location to keep the file
        :param filename: new file name (optional)
        :param etag: old etag. if the old etag is the same with the one on server, do not download again.
        :param auto_unzip: bool flag to indicate if unzip .zip file automatically

        :returns: new etag

        """

        raise NotImplementedError

    @abc.abstractmethod
    def fetch_files(
        self,
        urls,
        filepaths,
        filenames=[],
        etags=[],
        auto_unzip: bool = True,
    ):
        """fetch multiple files concurrently

        :param urls: the urls to download files from
        :param filepaths: location(s) to keep the files. This can be one path for all files or one path for each file.
        :param filenames: new file names (optional)
        :param etags: old etags. if the old etag is the same with the one on server, do not download again.
        :param auto_unzip: bool flag to indicate if unzip .zip file automatically

        """
        raise NotImplementedError

    @abc.abstractmethod
    def _run_fetch_large_file(self, loop, url, filesize, data):
        raise NotImplementedError

    def fetch_large_file(
        self,
        url: str,
        filepath: str,
        filename: Union[str, None],
        filesize: Union[int, None] = None,
        etag: Union[str, None] = None,
        auto_unzip: bool = True,
        check_etag: bool = True,
        timeout=(None, None),
    ):
        """use multi-thread to fetch a large file.
            LOOK HERE!!!
            Be careful when use this function. You cannot get partial content if the content is gzip encoded.
            So the file might be larger than the one download directly.
            It is useful when downloading large .zip file.
            Warning: this could be slower than single thread download.
            Some firewall sequences these requests to shape network traffic and defeat the purpose of this function completely.

            check the etag and get content-length before calling this function

        :param url: the file url
        :param filepath: location to keep the file
        :param filename: the output filename specified by caller. ignored if auto unzip compressed data.
        :param filesize: the size of file (in bytes)
        :param etag: old etag. if the old etag is the same with the one on server, do not download again.
        :param auto_unzip: bool flag to indicate if unzip .zip file automatically

        :returns: new etag

        """
        if filesize is None or check_etag:
            headers = network.get_headers(url, timeout=timeout)
            file_size = network.get_content_length(headers)
            new_etag = network.get_etag(headers)
            # if the etags are the same, do not download again
            if etag and etag == new_etag:
                return etag
        else:
            # if the caller has provided file size and checked etag
            file_size = filesize
            new_etag = etag

        # create folder to keep the file
        if os.path.isfile(filepath):
            raise Exception(
                f"The 'filepath' is in fact a file. The 'filepath' should be a folder path(non-exist is fine). {filepath}"
            )
        Path(filepath).mkdir(parents=True, exist_ok=True)

        # set up concurrent functions
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        data = [io.BytesIO()]

        try:
            self._run_fetch_large_file(loop, url, file_size, data)

        except RuntimeError:
            import nest_asyncio

            nest_asyncio.apply()
            self._run_fetch_large_file(loop, url, file_size, data)
        except Exception as e:
            misc.print_error("Failed to fetch large file!")
            raise Exception("Failed to fetch large file!") from e
        finally:
            loop.close()

        data[0].seek(0)

        if not filename:
            filename = url.split("/")[-1]  # use the filename in the url
        # save the file
        if auto_unzip:
            try:
                unzip.save_compressed_data(url, data[0], filepath)
            except Exception as ex:
                # print(ex)
                # print("failed to save zip. try save directly")
                data[0].seek(0)
                self._save_file(filepath, filename, data[0].read())
        else:
            self._save_file(filepath, filename, data[0].read())

        return new_etag

    def _save_file(self, filepath, filename, data):
        """helper function to save file to hard drive"""

        output_dir = Path(filepath)
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / filename
        if output_file.is_file():
            print(f"Warning: overwriting {filename}")
        with open(output_file, "wb+") as of:
            of.write(data)
