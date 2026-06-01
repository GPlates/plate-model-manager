#!/usr/bin/env python3

import os
import sys
import unittest

from common import (
    INTEGRATION_TEST_LEVEL,
    TEMP_TEST_DIR,
    get_test_logger,
    is_test_installed_module,
    skip_unless_test_level,
)

if not is_test_installed_module():
    sys.path.insert(0, f"{os.path.dirname(__file__)}/../src")

import plate_model_manager
from plate_model_manager import PlateModelManager
from plate_model_manager.exceptions import InvalidConfigFile
from plate_model_manager.zenodo import ZenodoRecord

plate_model_manager.disable_stdout_logging()

if __name__ == "__main__":
    logger_name = "test_zenodo_main"
else:
    logger_name = __name__

logger = get_test_logger(logger_name)

logger.info(plate_model_manager.__file__)


@skip_unless_test_level(
    INTEGRATION_TEST_LEVEL,
    "set PMM_TEST_LEVEL>=1 to run Zenodo integration tests",
)
class ZenodoTestCase(unittest.TestCase):
    def setUp(self):
        pass

    def test_zenodo(self):
        logger.info(
            """Testing record ID: 3854459. 
                    https://zenodo.org/records/3854549
                    You can cite all versions by using the DOI 10.5281/zenodo.3854459. 
                    This DOI represents all versions, and will always resolve to the latest one."""
        )
        record = ZenodoRecord(3854459)

        all_version_ids = record.get_all_version_ids()
        logger.info(
            f"""All version IDs: {record.get_all_version_ids()}.
                    At least the IDs should contain two version IDs 3854460 and 3854549."""
        )
        self.assertTrue(3854460 in all_version_ids and 3854549 in all_version_ids)

        latest_id = record.get_latest_version_id()
        logger.info(f"The latest version ID is: {latest_id}.")
        self.assertTrue(latest_id)

        filenames = record.get_filenames(latest_id)
        logger.info(f"The file names in the latest version: {filenames}")

        file_links = record.get_file_links(latest_id)
        logger.info(f"The file links in the latest version: {file_links}")

        filenames = record.get_filenames(3854460)
        logger.info(f"The file names in version 3854460: {filenames}")
        self.assertTrue(len(filenames) == 2)

        file_links = record.get_file_links(3854460)
        logger.info(f"The file links in version 3854460: {file_links}")
        self.assertTrue(len(file_links) == 2)


if __name__ == "__main__":
    # use the following code to run a list of tests
    # suite = unittest.TestSuite()
    # suite.addTest(ZenodoTestCase("test_zenodo"))
    # runner = unittest.TextTestRunner()
    # runner.run(suite)

    # use the following code to run all tests in this file
    runner = unittest.TextTestRunner()
    runner.run(unittest.TestLoader().loadTestsFromTestCase(ZenodoTestCase))
