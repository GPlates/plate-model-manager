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
    logger_name = "test_concurrent_download_main"
else:
    logger_name = __name__

logger = get_test_logger(logger_name)

test_urls = [
    "https://repo.gplates.org/webdav/pmm/present-day-rasters/topo15-3601x1801.nc.gz",
    "https://repo.gplates.org/webdav/pmm/matthews2016/Coastlines.zip",
    "https://repo.gplates.org/webdav/pmm/matthews2016/StaticPolygons.zip",
    "https://repo.gplates.org/webdav/pmm/matthews2016/Rotations.zip",
    "https://repo.gplates.org/webdav/pmm/matthews2016_mantle_ref/Coastlines.zip",
    "https://repo.gplates.org/webdav/pmm/matthews2016_mantle_ref/StaticPolygons.zip",
    "https://repo.gplates.org/webdav/pmm/matthews2016_mantle_ref/Rotations.zip",
    "https://repo.gplates.org/webdav/pmm/matthews2016_pmag_ref/Coastlines.zip",
    "https://repo.gplates.org/webdav/pmm/matthews2016_pmag_ref/StaticPolygons.zip",
    "https://repo.gplates.org/webdav/pmm/matthews2016_pmag_ref/Rotations.zip",
    "https://repo.gplates.org/webdav/pmm/merdith2021/Coastlines.zip",
    "https://repo.gplates.org/webdav/pmm/merdith2021/StaticPolygons.zip",
    "https://repo.gplates.org/webdav/pmm/merdith2021/Rotations.zip",
    "https://repo.gplates.org/webdav/pmm/muller2016/Coastlines.zip",
    "https://repo.gplates.org/webdav/pmm/muller2016/StaticPolygons.zip",
    "https://repo.gplates.org/webdav/pmm/muller2016/Rotations.zip",
    "https://repo.gplates.org/webdav/pmm/muller2019/Coastlines.zip",
    "https://repo.gplates.org/webdav/pmm/muller2019/StaticPolygons.zip",
    "https://repo.gplates.org/webdav/pmm/muller2019/Rotations.zip",
    "https://repo.gplates.org/webdav/pmm/muller2022/Coastlines.zip",
    "https://repo.gplates.org/webdav/pmm/muller2022/StaticPolygons.zip",
    "https://repo.gplates.org/webdav/pmm/muller2022/Rotations.zip",
    "https://repo.gplates.org/webdav/pmm/seton2012/Coastlines.zip",
    "https://repo.gplates.org/webdav/pmm/seton2012/StaticPolygons.zip",
    "https://repo.gplates.org/webdav/pmm/seton2012/Rotations.zip",
    "https://repo.gplates.org/webdav/pmm/models.json",
    "https://repo.gplates.org/webdav/pmm/present_day_rasters.json",
]
test_urls += [
    f"https://www.earthbyte.org/webdav/ftp/Data_Collections/Zahirovic_etal_2016_ESR_AgeGrid/jpegs/EarthByte_Zahirovic_etal_2016_ESR_r888_AgeGrid-{i}.jpg"
    for i in range(20)
]

auto_unzip = True


@skip_unless_test_level(
    LARGE_DATA_TEST_LEVEL,
    "set PMM_TEST_LEVEL>=2 to run large download stress tests",
)
class ConcurrentDownloadTestCase(unittest.TestCase):
    def setUp(self):
        pass

    def test_with_for_loop(self):
        """requests + "for loop" """
        st = time.time()
        spt = time.process_time()

        print("Start test_with_for_loop ... ")

        count = 0
        for url in test_urls:
            network_requests.fetch_file(
                url,
                f"{TEMP_TEST_DIR}/download-with-for-loop/{str(count)}",
                auto_unzip=auto_unzip,
            )
            count += 1

        f_list = glob.glob(f"{TEMP_TEST_DIR}/download-with-for-loop/*")
        self.assertTrue(len(f_list) == len(test_urls))

        et = time.time()
        ept = time.process_time()

        print(f"time: {et - st}")
        print(f"process time: {ept - spt}")

        print("End test_with_for_loop ... ")

    def test_concurrent_aiohttp(self):
        """asyncio + aiohttp"""
        st = time.time()
        spt = time.process_time()
        paths = [
            f"{TEMP_TEST_DIR}/download-concurrently-with-aiohttp/{str(i)}"
            for i in range(len(test_urls))
        ]

        print("Start test_concurrent_aiohttp ... ")

        network_aiohttp.fetch_files(
            test_urls,
            paths,
            auto_unzip=auto_unzip,
        )

        f_list = glob.glob(f"{TEMP_TEST_DIR}/download-concurrently-with-aiohttp/*")
        self.assertTrue(len(f_list) == len(test_urls))

        et = time.time()
        ept = time.process_time()

        print(f"time: {et - st}")
        print(f"process time: {ept - spt}")

        print("End test_concurrent_aiohttp ... ")

    def test_concurrent_executor(self):
        """requests + ThreadPoolExecutor + asyncio"""
        st = time.time()
        spt = time.process_time()

        paths = [
            f"{TEMP_TEST_DIR}/download-concurrently-with-executor/{i}"
            for i in range(len(test_urls))
        ]

        print("Start test_concurrent_executor ... ")

        network_requests.fetch_files(
            test_urls,
            paths,
            auto_unzip=auto_unzip,
        )

        f_list = glob.glob(f"{TEMP_TEST_DIR}/download-concurrently-with-executor/*")
        self.assertTrue(len(f_list) == len(test_urls))

        et = time.time()
        ept = time.process_time()

        print(f"time: {et - st}")
        print(f"process time: {ept - spt}")

        print("End test_concurrent_executor ... ")


if __name__ == "__main__":
    # use the following code to run a list of tests
    # suite = unittest.TestSuite()
    # suite.addTest(ConcurrentDownloadTestCase("test_concurrent_executor"))
    # runner = unittest.TextTestRunner()
    # runner.run(suite)

    # use the following code to run all tests in this file
    runner = unittest.TextTestRunner()
    runner.run(unittest.TestLoader().loadTestsFromTestCase(ConcurrentDownloadTestCase))
