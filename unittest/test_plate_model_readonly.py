#!/usr/bin/env python
import os
import sys
import unittest

sys.path.insert(0, f"{os.path.dirname(__file__)}/../src")
from common import (
    INTEGRATION_TEST_LEVEL,
    TEMP_TEST_DIR,
    get_test_logger,
    skip_unless_test_level,
)

from plate_model_manager import PlateModel, PlateModelManager

if __name__ == "__main__":
    logger_name = "test_plate_model_readonly_main"
else:
    logger_name = __name__

logger = get_test_logger(logger_name)


@skip_unless_test_level(
    INTEGRATION_TEST_LEVEL,
    "set PMM_TEST_LEVEL>=1 to run readonly integration tests",
)
class PlateModelReadonlyTestCase(unittest.TestCase):
    def setUp(self):
        model_manager = PlateModelManager()
        self.model_name = "Muller2019"
        self.data_dir = TEMP_TEST_DIR
        model = model_manager.get_model(self.model_name)
        if model is not None:
            model.set_data_dir(self.data_dir)

    def test_readonly_plate_model(self):
        model = PlateModel(self.model_name, data_dir=self.data_dir, readonly=True)

        layers = model.get_avail_layers()
        self.assertTrue(len(layers) > 0)
        logger.info(layers)

        rotation_files = model.get_rotation_model()
        self.assertTrue(len(rotation_files) > 0)
        logger.info(rotation_files)

        coastlines_files = model.get_layer("Coastlines")
        if coastlines_files is None:
            self.assertTrue(False)
        else:
            self.assertTrue(len(coastlines_files) > 0)
            logger.info(coastlines_files)
            for f in coastlines_files:
                self.assertTrue(os.path.isfile(f))

        cob_files = model.get_COBs()
        if cob_files is None:
            self.assertTrue(False)
        else:
            self.assertTrue(len(cob_files) > 0)
            logger.info(cob_files)
            for f in cob_files:
                self.assertTrue(os.path.isfile(f))

        topology_files = model.get_topologies()
        if topology_files is None:
            self.assertTrue(False)
        else:
            self.assertTrue(len(topology_files) > 0)
            logger.info(topology_files)
            for f in topology_files:
                self.assertTrue(os.path.isfile(f))

        data_dir = model.get_data_dir()
        self.assertEqual(TEMP_TEST_DIR, data_dir)
        logger.info(data_dir)
        self.assertTrue(os.path.isdir(data_dir))


if __name__ == "__main__":
    # use the following code to run a list of tests
    # suite = unittest.TestSuite()
    # suite.addTest(PlateModelReadonlyTestCase("test_readonly_plate_model"))
    # runner = unittest.TextTestRunner()
    # runner.run(suite)

    # use the following code to run all tests in this file
    runner = unittest.TextTestRunner()
    runner.run(unittest.TestLoader().loadTestsFromTestCase(PlateModelReadonlyTestCase))
