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
else:
    print("testing installed PMM package")

import plate_model_manager
from plate_model_manager import PlateModelManager
from plate_model_manager.exceptions import (
    FailedToDownloadFile,
    InvalidConfigFile,
    LayerNotFoundInModel,
)

# plate_model_manager.disable_stdout_logging()

if __name__ == "__main__":
    logger_name = "test_basic_main"
else:
    logger_name = __name__

logger = get_test_logger(logger_name)

logger.info(plate_model_manager.__file__)


@skip_unless_test_level(
    INTEGRATION_TEST_LEVEL,
    "set PMM_TEST_LEVEL>=1 to run integration tests that download model data",
)
class BasicTestCase(unittest.TestCase):
    def setUp(self):
        pass

    def test_basic(self):
        with self.assertRaises(InvalidConfigFile):
            pm_manager = PlateModelManager(123, timeout=(5, 5))  # type: ignore
        with self.assertRaises(InvalidConfigFile):
            pm_manager = PlateModelManager("123", timeout=(5, 5))

        # 1
        pm_manager = PlateModelManager(timeout=(5, 5))
        model = pm_manager.get_model("Muller2019", data_dir=TEMP_TEST_DIR)
        self.assertIsNotNone(model)
        self.assertTrue(model.get_rotation_model())

        # 2
        pm_manager = PlateModelManager()
        model = pm_manager.get_model()
        self.assertIsNotNone(model)
        self.assertTrue(model.get_rotation_model())
        self.assertIsNone(model.get_layer("xx", return_none_if_not_exist=True))
        model = pm_manager.get_model("alfonso2024", data_dir=TEMP_TEST_DIR)
        self.assertIsNotNone(model)
        self.assertTrue(len(model.get_layer("Terranes")) == 10)

        # 3
        pm_manager = PlateModelManager(
            model_manifest=f"{os.path.dirname(__file__)}/models_test.json"
        )
        model = pm_manager.get_model("test-model", data_dir=TEMP_TEST_DIR)
        self.assertIsNotNone(model)
        self.assertTrue(model.get_rotation_model())
        with self.assertRaises(LayerNotFoundInModel):
            model.get_layer("xxx")
        with self.assertRaises(FailedToDownloadFile):
            # COBs layer pointing to a file that does not exist, so it should raise FailedToDownloadFile
            model.get_layer("COBs")


if __name__ == "__main__":
    # use the following code to run a list of tests
    # suite = unittest.TestSuite()
    # suite.addTest(BasicTestCase("test_basic"))
    # runner = unittest.TextTestRunner()
    # runner.run(suite)

    # use the following code to run all tests in this file
    runner = unittest.TextTestRunner()
    runner.run(unittest.TestLoader().loadTestsFromTestCase(BasicTestCase))
