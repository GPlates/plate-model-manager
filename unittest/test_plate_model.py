#!/usr/bin/env python

import os
import sys
import unittest

from common import TEMP_TEST_DIR, get_test_logger, is_test_installed_module
from plate_model_manager.utils.enums import ReferenceFrame

if not is_test_installed_module():
    sys.path.insert(0, f"{os.path.dirname(__file__)}/../src")

import plate_model_manager
from plate_model_manager import PlateModelManager

plate_model_manager.disable_stdout_logging()

if __name__ == "__main__":
    logger_name = "test_plate_model_main"
else:
    logger_name = __name__

logger = get_test_logger(logger_name)
logger.info(plate_model_manager.__file__)


class PlateModelTestCase(unittest.TestCase):
    def setUp(self):
        model_manager = PlateModelManager()

        # test remote models.json with URL
        # model_manager = plate_model.PlateModelManager(
        #    "https://www.earthbyte.org/webdav/ftp/gplately/models.json"
        # )
        self.model_name = "Muller2019"
        self.model = model_manager.get_model(self.model_name)
        if self.model is None:
            raise Exception("The self.model is None. This should not happen!")
        self.model.set_data_dir(TEMP_TEST_DIR)

    def test_get(self):
        logger.info("test_get ...")
        if self.model is None:
            raise Exception("The self.model is None. This should not happen!")
        layers = self.model.get_avail_layers()
        self.assertTrue(len(layers) > 0)
        logger.info(layers)

        rotation_files = self.model.get_rotation_model()
        self.assertTrue(len(rotation_files) > 0)
        logger.info(rotation_files)
        for f in rotation_files:
            self.assertTrue(os.path.isfile(f))

        coastlines_files = self.model.get_layer("Coastlines")
        if coastlines_files is None:
            self.assertTrue(False)
        else:
            self.assertTrue(len(coastlines_files) > 0)
            logger.info(coastlines_files)
            for f in coastlines_files:
                self.assertTrue(os.path.isfile(f))

        cob_files = self.model.get_COBs()
        if cob_files is None:
            self.assertTrue(False)
        else:
            self.assertTrue(len(cob_files) > 0)
            logger.info(cob_files)
            for f in cob_files:
                self.assertTrue(os.path.isfile(f))

        topology_files = self.model.get_topologies()
        if topology_files is None:
            self.assertTrue(False)
        else:
            self.assertTrue(len(topology_files) > 0)
            logger.info(topology_files)
            for f in topology_files:
                self.assertTrue(os.path.isfile(f))

        data_dir = self.model.get_data_dir()
        self.assertEqual(TEMP_TEST_DIR, data_dir)
        logger.info(data_dir)
        self.assertTrue(os.path.isdir(data_dir))

        filepath = self.model.get_raster("AgeGrids", 10)
        self.assertTrue(len(filepath) > 0)
        logger.info(filepath)
        self.assertTrue(os.path.isfile(filepath))

        filepaths = self.model.get_rasters("AgeGrids", [10, 11, 12, 13, 14])
        self.assertEqual(len(filepaths), 5)
        logger.info(filepaths)
        for f in filepaths:
            self.assertTrue(os.path.isfile(f))

    def test_download(self):
        logger.info("test_download ...")
        if self.model is None:
            raise Exception("The self.model is None. This should not happen!")

        self.model.download_all_layers()

        self.model.download_time_dependent_rasters("AgeGrids", times=[1, 2])

    @unittest.skipIf(
        int(os.getenv("PMM_TEST_LEVEL", 0)) < 1,
        "this will download a large volume of data",
    )
    def test_download_all(self):
        if self.model is None:
            raise Exception("The self.model is None. This should not happen!")
        self.model.download_all()

    def test_get_rotation_model_for_pmag_reference_frame(self):
        """Test getting rotation files for pmag reference frame."""
        logger.info("test_get_rotation_model_for_pmag_reference_frame ...")
        model_manager = PlateModelManager()
        model = model_manager.get_model("zahirovic2022", data_dir=TEMP_TEST_DIR)
        if model is None:
            raise Exception("Cannot get zahirovic2022 model!")

        rotation_files, anchor_pid = model.get_rotation_model(
            reference_frame=ReferenceFrame.PmagReferenceFrame
        )
        self.assertTrue(len(rotation_files) > 0)
        self.assertTrue(
            anchor_pid == 701701
        )  # this is the anchor plate in the Pmag reference frame for zahirovic2022
        logger.info(rotation_files)
        for f in rotation_files:
            self.assertTrue(os.path.isfile(f))


if __name__ == "__main__":
    # use the following code to run a list of tests
    # suite = unittest.TestSuite()
    # suite.addTest(PlateModelTestCase("test_get"))
    # runner = unittest.TextTestRunner()
    # runner.run(suite)

    # use the following code to run all tests in this file
    runner = unittest.TextTestRunner()
    runner.run(unittest.TestLoader().loadTestsFromTestCase(PlateModelTestCase))
