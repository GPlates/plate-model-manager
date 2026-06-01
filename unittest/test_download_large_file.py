#!/usr/bin/env python
import glob
import os
import sys
import time
import unittest

sys.path.insert(0, f"{os.path.dirname(__file__)}/../src")
from common import (
    LARGE_DATA_TEST_LEVEL,
    TEMP_TEST_DIR,
    get_test_logger,
    skip_unless_test_level,
)

from plate_model_manager import network_aiohttp, network_requests

if __name__ == "__main__":
    logger_name = "test_download_large_file_main"
else:
    logger_name = __name__

logger = get_test_logger(logger_name)
test_url = "https://repo.gplates.org/webdav/pmm/present-day-rasters/agegrid.tiff.gz"
auto_unzip = True

# concurrent download from www.earthbyte.org does not work because of Cloud provider's network traffic control
# use "http://212.183.159.230/100MB.zip" to test. you can see the performance improvement
# the performance improvement depends on the server/network's configuration


@skip_unless_test_level(
    LARGE_DATA_TEST_LEVEL,
    "set PMM_TEST_LEVEL>=2 to run large download tests",
)
class DownloadLargeFileTestCase(unittest.TestCase):
    def setUp(self):
        pass

    def test_download_directly(self):
        """Download the large file directly with requests"""
        st = time.time()
        spt = time.process_time()

        print("Start download directly ...")

        network_requests.fetch_file(
            test_url, f"{TEMP_TEST_DIR}/download-directly", auto_unzip=auto_unzip
        )

        self.assertTrue(
            os.path.isfile(
                f"{TEMP_TEST_DIR}/download-directly/agegrid.tiff",
            )
        )
        files = glob.glob(f"{TEMP_TEST_DIR}/download-directly/*")
        self.assertTrue(len(files) > 0)

        et = time.time()
        ept = time.process_time()

        print(f"time: {et - st}")
        print(f"process time: {ept - spt}")

        print("End download directly ...")

    def test_requests(self):
        """requests + ThreadPoolExecutor + asyncio"""
        st = time.time()
        spt = time.process_time()

        print("Start download with requests+executor ...")

        network_requests.fetch_large_file(
            test_url,
            f"{TEMP_TEST_DIR}/download-with-requests-executor",
            auto_unzip=auto_unzip,
        )

        self.assertTrue(
            os.path.isfile(
                f"{TEMP_TEST_DIR}/download-with-requests-executor/agegrid.tiff",
            )
        )
        files = glob.glob(f"{TEMP_TEST_DIR}/download-with-requests-executor/*")
        self.assertTrue(len(files) > 0)

        et = time.time()
        ept = time.process_time()

        print(f"time: {et - st}")
        print(f"process time: {ept - spt}")

        print("End download with requests+executor ...")

    def test_aiohttp(self):
        """Download with aiohttp+asyncio"""
        st = time.time()
        spt = time.process_time()

        print("Start download with aiohttp ...")

        network_aiohttp.fetch_large_file(
            test_url, f"{TEMP_TEST_DIR}/download-with-aiohttp", auto_unzip=auto_unzip
        )

        self.assertTrue(
            os.path.isfile(
                f"{TEMP_TEST_DIR}/download-with-aiohttp/agegrid.tiff",
            )
        )
        files = glob.glob(f"{TEMP_TEST_DIR}/download-with-aiohttp/*")
        self.assertTrue(len(files) > 0)

        et = time.time()
        ept = time.process_time()

        print(f"time: {et - st}")
        print(f"process time: {ept - spt}")

        print("End download with aiohttp ...")


if __name__ == "__main__":
    # use the following code to run a list of tests
    # suite = unittest.TestSuite()
    # suite.addTest(DownloadLargeFileTestCase("test_aiohttp"))
    # runner = unittest.TextTestRunner()
    # runner.run(suite)

    # use the following code to run all tests in this file
    runner = unittest.TextTestRunner()
    runner.run(unittest.TestLoader().loadTestsFromTestCase(DownloadLargeFileTestCase))
