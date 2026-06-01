#!/usr/bin/env python
import glob
import os
import shutil
import sys
import time
import unittest

from common import (
    INTEGRATION_TEST_LEVEL,
    LARGE_DATA_TEST_LEVEL,
    TEMP_TEST_DIR,
    get_test_logger,
    is_test_installed_module,
    skip_unless_test_level,
)

if not is_test_installed_module():
    sys.path.insert(0, f"{os.path.dirname(__file__)}/../src")

import plate_model_manager
from plate_model_manager.utils import download

# plate_model_manager.disable_stdout_logging()


if __name__ == "__main__":
    logger_name = "test_download_file_main"
else:
    logger_name = __name__

logger = get_test_logger(logger_name)
logger.info(plate_model_manager.__file__)


@skip_unless_test_level(
    INTEGRATION_TEST_LEVEL,
    "set PMM_TEST_LEVEL>=1 to run downloader integration tests",
)
class DownloadFileTestCase(unittest.TestCase):
    def setUp(self):
        pass

    def test_download_file(self):
        """test download files and auto unzip"""
        files = {
            "test_bz2": "https://repo.gplates.org/webdav/pmm/present-day-rasters/test/models.json.bz2",
            "test_lzma": "https://repo.gplates.org/webdav/pmm/present-day-rasters/test/models.json.lzma",
            "test_xz": "https://repo.gplates.org/webdav/pmm/present-day-rasters/test/models.json.xz",
            "test_gz": "https://repo.gplates.org/webdav/pmm/present-day-rasters/test/models.json.gz",
            "test_tar_gz": "https://repo.gplates.org/webdav/pmm/present-day-rasters/test/test.tar.gz",
            "test_tgz": "https://repo.gplates.org/webdav/pmm/present-day-rasters/test/test.tgz",
            "test_tar_bz2": "https://repo.gplates.org/webdav/pmm/present-day-rasters/test/test.tar.bz2",
            "test_tar_xz": "https://repo.gplates.org/webdav/pmm/present-day-rasters/test/test.tar.xz",
            "test_tbz2": "https://repo.gplates.org/webdav/pmm/present-day-rasters/test/test.tbz2",
            "test_txz": "https://repo.gplates.org/webdav/pmm/present-day-rasters/test/test.txz",
            "test_zip": "https://repo.gplates.org/webdav/pmm/present-day-rasters/test/test.zip",
            "test_bad_zip": "https://repo.gplates.org/webdav/pmm/present-day-rasters/test/test-bad.zip",
            "test_bad_tar_gz": "https://repo.gplates.org/webdav/pmm/present-day-rasters/test/test-bad.tar.gz",
            "test_bad_xz": "https://repo.gplates.org/webdav/pmm/present-day-rasters/test/test-bad.xz",
            "test_bad_bz2": "https://repo.gplates.org/webdav/pmm/present-day-rasters/test/test-bad.bz2",
        }
        local_files = {
            "test_bz2": "models.json",
            "test_lzma": "models.json",
            "test_xz": "models.json",
            "test_gz": "models.json",
            "test_tar_gz": "models.json.bak",
            "test_tgz": "models.json.bak",
            "test_tar_bz2": "models.json.bak",
            "test_tar_xz": "models.json.bak",
            "test_tbz2": "models.json.bak",
            "test_txz": "models.json.bak",
            "test_zip": "models.json",
            "test_bad_zip": "test-bad.zip",
            "test_bad_tar_gz": "test-bad.tar.gz",
            "test_bad_xz": "test-bad.xz",
            "test_bad_bz2": "test-bad.bz2",
        }
        for client in [
            download.HttpClient.AIOHTTP,
            download.HttpClient.REQUESTS,
        ]:
            for file in files:
                if os.path.isdir(f"{TEMP_TEST_DIR}/test-download-file/{client}/{file}"):
                    shutil.rmtree(f"{TEMP_TEST_DIR}/test-download-file/{client}/{file}")

                downloader = download.FileDownloader(
                    files[file],
                    f"{TEMP_TEST_DIR}/test-download-file/{client}/{file}/.metadata.json",
                    f"{TEMP_TEST_DIR}/test-download-file/{client}/{file}",
                    http_client=client,
                )

                # only re-download when necessary
                if downloader.check_if_file_need_update():
                    downloader.download_file_and_update_metadata()
                else:
                    logger.info(
                        f"The local file is still good. No need to download {files[file]} again!"
                    )

                file_list = glob.glob(
                    f"{TEMP_TEST_DIR}/test-download-file/{client}/{file}/*"
                )

                self.assertTrue(len(file_list) == 1)
                self.assertTrue(
                    os.path.isfile(
                        f"{TEMP_TEST_DIR}/test-download-file/{client}/{file}/.metadata.json"
                    )
                )

                #os.system(
                #    f"ls -rtlha {TEMP_TEST_DIR}/test-download-file/{client}/{file}"
                #)

                self.assertTrue(
                    os.path.isfile(
                        f"{TEMP_TEST_DIR}/test-download-file/{client}/{file}/{local_files[file]}"
                    )
                )

                self.assertFalse(downloader.check_if_file_need_update())

    def test_download_file_rename_1(self):
        """download a file and save the file with a caller-specified file name"""
        for client in [download.HttpClient.AIOHTTP, download.HttpClient.REQUESTS]:
            output_filename = f"{TEMP_TEST_DIR}/test-download-file/xxxx.json"
            metafile = f"{TEMP_TEST_DIR}/test-download-file/.metadata.json"
            if os.path.isfile(output_filename):
                os.remove(output_filename)
            if os.path.isfile(metafile):
                os.remove(metafile)
            file_url = "https://repo.gplates.org/webdav/pmm/models.json"
            downloader = download.FileDownloader(
                file_url,
                metafile,
                f"{TEMP_TEST_DIR}/test-download-file/",
                filename="xxxx.json",
                http_client=client,
            )
            if downloader.check_if_file_need_update():
                downloader.download_file_and_update_metadata()
            else:
                logger.info(
                    f"The local file is still good. No need to download {file_url} again!"
                )

            self.assertFalse(downloader.check_if_file_need_update())
            self.assertTrue(os.path.isfile(output_filename))
            self.assertTrue(os.path.isfile(metafile))

    def test_download_file_rename_2(self):
        """download a file, turn off auto unzip and save the file with a caller-specified file name"""
        for client in [download.HttpClient.AIOHTTP, download.HttpClient.REQUESTS]:
            output_filename = f"{TEMP_TEST_DIR}/test-download-file/qqqq.json.bz2"
            metafile = f"{TEMP_TEST_DIR}/test-download-file/.metadata.json"
            if os.path.isfile(output_filename):
                os.remove(output_filename)
            if os.path.isfile(metafile):
                os.remove(metafile)
            file_url = "https://repo.gplates.org/webdav/pmm/present-day-rasters/test/models.json.bz2"
            downloader = download.FileDownloader(
                file_url,
                metafile,
                f"{TEMP_TEST_DIR}/test-download-file/",
                filename="qqqq.json.bz2",
                auto_unzip=False,
                http_client=client,
            )
            if downloader.check_if_file_need_update():
                downloader.download_file_and_update_metadata()
            else:
                logger.info(
                    f"The local file is still good. No need to download {file_url} again!"
                )

            self.assertFalse(downloader.check_if_file_need_update())
            self.assertTrue(os.path.isfile(output_filename))
            self.assertTrue(os.path.isfile(metafile))

    def test_download_file_rename_3(self):
        """download a file with a user specified file name, but since the auto unzip is on,
        the user-specified file name will be ignored."""
        for client in [download.HttpClient.AIOHTTP, download.HttpClient.REQUESTS]:
            output_filename = f"{TEMP_TEST_DIR}/test-download-file/models.json"
            metafile = f"{TEMP_TEST_DIR}/test-download-file/.metadata.json"
            if os.path.isfile(output_filename):
                os.remove(output_filename)
            if os.path.isfile(metafile):
                os.remove(metafile)
            file_url = "https://repo.gplates.org/webdav/pmm/present-day-rasters/test/models.json.bz2"
            downloader = download.FileDownloader(
                file_url,
                metafile,
                f"{TEMP_TEST_DIR}/test-download-file/",
                filename="qqqq.json",  # auto_unzip, this filename will be ignored.
                http_client=client,
            )
            if downloader.check_if_file_need_update():
                downloader.download_file_and_update_metadata()
            else:
                logger.info(
                    f"The local file is still good. No need to download {file_url} again!"
                )

            self.assertFalse(downloader.check_if_file_need_update())
            self.assertTrue(os.path.isfile(output_filename))
            self.assertTrue(os.path.isfile(metafile))

    @skip_unless_test_level(
        LARGE_DATA_TEST_LEVEL,
        "set PMM_TEST_LEVEL>=2 to run large download tests",
    )
    def test_download_large_file(self):
        """download a large file, use the file name in the url and unzip automatically"""
        for client in [download.HttpClient.AIOHTTP, download.HttpClient.REQUESTS]:
            output_filename = f"{TEMP_TEST_DIR}/test-download-file/agegrid.tiff"
            metafile = f"{TEMP_TEST_DIR}/test-download-file/.metadata.json"
            if os.path.isfile(output_filename):
                os.remove(output_filename)
            if os.path.isfile(metafile):
                os.remove(metafile)
            file_url = "https://repo.gplates.org/webdav/pmm/present-day-rasters/agegrid.tiff.gz"
            downloader = download.FileDownloader(
                file_url,
                metafile,
                f"{TEMP_TEST_DIR}/test-download-file/",
                large_file_hint=True,
                http_client=client,
            )
            if downloader.check_if_file_need_update():
                downloader.download_file_and_update_metadata()
            else:
                logger.info(
                    f"The local file is still good. No need to download {file_url} again!"
                )

            self.assertFalse(downloader.check_if_file_need_update())
            self.assertTrue(os.path.isfile(output_filename))
            self.assertTrue(os.path.isfile(metafile))

    @skip_unless_test_level(
        LARGE_DATA_TEST_LEVEL,
        "set PMM_TEST_LEVEL>=2 to run large download tests",
    )
    def test_download_large_file_rename(self):
        """download a large file and save with a caller specified file name"""
        for client in [download.HttpClient.AIOHTTP, download.HttpClient.REQUESTS]:
            output_filename = (
                f"{TEMP_TEST_DIR}/test-download-file/renamed-agegrid.tiff.gz"
            )
            metafile = f"{TEMP_TEST_DIR}/test-download-file/.metadata.json"
            if os.path.isfile(output_filename):
                os.remove(output_filename)
            if os.path.isfile(metafile):
                os.remove(metafile)
            file_url = "https://repo.gplates.org/webdav/pmm/present-day-rasters/agegrid.tiff.gz"
            downloader = download.FileDownloader(
                file_url,
                metafile,
                f"{TEMP_TEST_DIR}/test-download-file/",
                filename="renamed-agegrid.tiff.gz",
                large_file_hint=True,
                auto_unzip=False,
                http_client=client,
            )
            if downloader.check_if_file_need_update():
                downloader.download_file_and_update_metadata()
            else:
                logger.info(
                    f"The local file is still good. No need to download {file_url} again!"
                )

            self.assertFalse(downloader.check_if_file_need_update())
            self.assertTrue(os.path.isfile(output_filename))
            self.assertTrue(os.path.isfile(metafile))


if __name__ == "__main__":
    # use the following code to run a list of tests
    # suite = unittest.TestSuite()
    # suite.addTest(DownloadFileTestCase("test_download_file"))
    # runner = unittest.TextTestRunner()
    # runner.run(suite)

    # use the following code to run all tests in this file
    runner = unittest.TextTestRunner()
    runner.run(unittest.TestLoader().loadTestsFromTestCase(DownloadFileTestCase))
