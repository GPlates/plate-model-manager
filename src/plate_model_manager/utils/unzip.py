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
import bz2
import gzip
import lzma
import os
import shutil
import sys
import tarfile
import zipfile

from . import misc


def save_compressed_data(url, data, dst_path):
    """extract files from compressed data

    :param url: URL
    :param data: bytes-like object
    :param dst_path: location to save the files
    """
    # print(f"save_compressed_data:{url}")
    # .zip
    if url.endswith(".zip"):
        if not zipfile.is_zipfile(data):
            misc.print_warning(
                f"The {url} seems a zip file. But it is in fact not. Will not decompress the file."
            )
            raise Exception("Bad compressed data!")
        else:
            with zipfile.ZipFile(data) as z:
                z.extractall(dst_path)
                z.close()
    # .tar.gz or .tgz
    elif url.endswith(".tar.gz") or url.endswith(".tgz"):
        if sys.version_info[1] > 8 and (not tarfile.is_tarfile(data)):
            misc.print_warning(
                f"The {url} seems a tar gzip file. But it is in fact not. Will not decompress the file."
            )
            raise Exception("Bad compressed data!")
        else:
            data.seek(0)
            with tarfile.open(fileobj=data, mode="r:gz") as tar:
                tar.extractall(path=dst_path)
                tar.close()
    # .gz
    elif url.endswith(".gz"):
        fn = url.split("/")[-1][:-3]
        if not fn:
            raise Exception(
                f"The url ends with .gz. But unable to extract the file name. Check the URL {url}"
            )
        try:
            with open(f"{dst_path}/{fn}", "wb+") as f_out:
                with gzip.GzipFile(fileobj=data) as f_in:
                    shutil.copyfileobj(f_in, f_out)
                    f_in.close()
                f_out.close()
        except:
            os.remove(f"{dst_path}/{fn}")
            misc.print_warning(
                f"The {url} seems a gzip file. But it is in fact not. Will not decompress the file."
            )
            raise Exception("Bad compressed data!")
    # .tar.bz2 or .tbz2
    elif url.endswith(".tar.bz2") or url.endswith(".tbz2"):
        if sys.version_info[1] > 8 and (not tarfile.is_tarfile(data)):
            misc.print_warning(
                f"The {url} seems a tar bz2 file. But it is in fact not. Will not decompress the file."
            )
            raise Exception("Bad compressed data!")
        else:
            data.seek(0)
            with tarfile.open(fileobj=data, mode="r:bz2") as tar:
                tar.extractall(path=dst_path)
                tar.close()
    # .bz2
    elif url.endswith(".bz2"):
        fn = url.split("/")[-1][:-4]
        if not fn:
            raise Exception(
                f"The url ends with .bz2. But unable to extract the file name. Check the URL {url}"
            )
        try:
            with open(f"{dst_path}/{fn}", "wb+") as f_out:
                data = bz2.decompress(data.read())
                f_out.write(data)
                f_out.close()
        except:
            os.remove(f"{dst_path}/{fn}")
            misc.print_warning(
                f"The {url} seems a bz2 file. But it is in fact not. Will not decompress the file."
            )
            raise Exception("Bad compressed data!")
    # .lzma
    elif url.endswith(".lzma"):
        fn = url.split("/")[-1][:-5]
        if not fn:
            raise Exception(
                f"The url ends with .lzma. But unable to extract the file name. Check the URL {url}"
            )
        try:
            with open(f"{dst_path}/{fn}", "wb+") as f_out:
                data = lzma.decompress(data.read())
                f_out.write(data)
                f_out.close()
        except:
            os.remove(f"{dst_path}/{fn}")
            misc.print_warning(
                f"The {url} seems a lzma file. But it is in fact not. Will not decompress the file."
            )
            raise Exception("Bad compressed data!")
    # .tar.xz or .txz
    elif url.endswith(".tar.xz") or url.endswith(".txz"):
        if sys.version_info[1] > 8 and (not tarfile.is_tarfile(data)):
            misc.print_warning(
                f"The {url} seems a tar xz file. But it is in fact not. Will not decompress the file."
            )
            raise Exception("Bad compressed data!")
        else:
            data.seek(0)
            with tarfile.open(fileobj=data, mode="r:xz") as tar:
                tar.extractall(path=dst_path)
                tar.close()
    # .xz
    elif url.endswith(".xz"):
        fn = url.split("/")[-1][:-3]
        if not fn:
            raise Exception(
                f"The url ends with .xz. But unable to extract the file name. Check the URL {url}"
            )
        try:
            with open(f"{dst_path}/{fn}", "wb+") as f_out:
                data = lzma.decompress(data.read())
                f_out.write(data)
                f_out.close()
        except:
            os.remove(f"{dst_path}/{fn}")
            misc.print_warning(
                f"The {url} seems a xz file. But it is in fact not. Will not decompress the file."
            )
            raise Exception("Bad compressed data!")
    else:
        raise Exception("Unrecognized zip data!")
