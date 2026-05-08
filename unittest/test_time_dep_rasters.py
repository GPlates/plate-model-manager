#!/usr/bin/env python3

import os
import shutil
import sys
import unittest

from common import TEMP_TEST_DIR, get_test_logger, is_test_installed_module
from plate_model_manager.utils.enums import GenerationMethod, ReferenceFrame

if not is_test_installed_module():
    sys.path.insert(0, f"{os.path.dirname(__file__)}/../src")

import plate_model_manager
from plate_model_manager import PlateModelManager

# plate_model_manager.disable_stdout_logging()

if __name__ == "__main__":
    logger_name = "test_time_dep_rasters_main"
else:
    logger_name = __name__

logger = get_test_logger(logger_name)
logger.info(plate_model_manager.__file__)


class TimeDepRastersTestCase(unittest.TestCase):
    def setUp(self):
        self.model_manager = PlateModelManager(
            f"{os.path.dirname(__file__)}/models_test.json"
        )

        # test remote models.json with URL
        # self.model_manager = plate_model.PlateModelManager(
        #    "https://www.earthbyte.org/webdav/ftp/gplately/models.json"
        # )
        self.model_name = "matthews2016_mantle_ref"
        self.model = self.model_manager.get_model(self.model_name)
        if self.model is not None:
            self.model.set_data_dir(TEMP_TEST_DIR)
        if os.path.isdir(f"{TEMP_TEST_DIR}/matthews2016_mantle_ref/Rasters"):
            shutil.rmtree(f"{TEMP_TEST_DIR}/matthews2016_mantle_ref/Rasters")

    def test(self):
        logger.info("test ...")

        if self.model is None:
            raise Exception("The self.model is None. This should not happen!")

        filepath = self.model.get_raster("AgeGrids", 10)
        self.assertTrue(len(filepath) > 0)
        logger.info(filepath)
        self.assertTrue(os.path.isfile(filepath))

        filepaths = self.model.get_rasters("AgeGrids", [10.0, 11.0, 12, 13, 14])
        self.assertEqual(len(filepaths), 5)
        logger.info(filepaths)
        for f in filepaths:
            self.assertTrue(os.path.isfile(f))

        self.model.download_time_dependent_rasters("Coastlines", times=[1, 2])

        filepaths = self.model.get_rasters("Topologies", list(range(10)))
        self.assertEqual(len(filepaths), 10)
        logger.info(filepaths)
        for f in filepaths:
            self.assertTrue(os.path.isfile(f))

    def test_agegrids(self):
        logger.info("test age grids ...")

        m = self.model_manager.get_model("alfonso2024", data_dir=TEMP_TEST_DIR)
        m.get_raster("AgeGrids", 100)

        m = self.model_manager.get_model("muller2022", data_dir=TEMP_TEST_DIR)
        m.get_raster("AgeGrids", 100)
        m.get_raster("AgeGridsPMAG", 100)

        m = self.model_manager.get_model("zahirovic2022", data_dir=TEMP_TEST_DIR)
        m.get_raster("AgegridsUsingIsochronsMantleFrame", 100)
        m.get_raster("AgegridsUsingIsochronsPMAG", 100)
        m.get_raster("AgegridsUsingTopologiesMantleFrame", 100)
        m.get_raster("AgegridsUsingTopologiesPMAG", 100)
        m.get_raster("SpreadingRateUsingTopologiesMantleFrame", 100)
        m.get_raster("SpreadingRateUsingTopologiesPMAG", 100)

        m = self.model_manager.get_model("clennett2020", data_dir=TEMP_TEST_DIR)
        m.get_raster("AgeGrids", 100)
        m.get_raster("SpreadingRate", 100)

        m = self.model_manager.get_model("muller2019", data_dir=TEMP_TEST_DIR)
        m.get_raster("AgeGrids", 100)
        m.get_raster("SedimentThickness", 100)

        m = self.model_manager.get_model("matthews2016", data_dir=TEMP_TEST_DIR)
        m.get_raster("AgeGrids", 100)

        m = self.model_manager.get_model("muller2016", data_dir=TEMP_TEST_DIR)
        m.get_raster("AgeGrids", 100)

        m = self.model_manager.get_model("zahirovic2016", data_dir=TEMP_TEST_DIR)
        m.get_raster("AgeGrids", 100)

        m = self.model_manager.get_model("seton2012", data_dir=TEMP_TEST_DIR)
        m.get_raster("AgeGrids", 100)

    def test_get_rasters_with_ref_frame_and_generated_from_parameters(self):
        m = self.model_manager.get_model("zahirovic2022", data_dir=TEMP_TEST_DIR)
        times = [100, 101]
        filepaths = m.get_rasters(
            "Agegrids",
            times,
            reference_frame=ReferenceFrame.MantleReferenceFrame,
            generated_from=GenerationMethod.Isochrons,
        )

        self.assertEqual(len(filepaths), len(times))
        for filepath in filepaths:
            self.assertTrue(os.path.isfile(filepath), msg=f"Missing file: {filepath}")

        raster_dir = (
            f"{TEMP_TEST_DIR}/zahirovic2022/Rasters/"
            f"Agegrids{GenerationMethod.Isochrons.value}"
            f"{ReferenceFrame.MantleReferenceFrame.value}"
        )
        self.assertTrue(os.path.isdir(raster_dir), msg=f"Missing dir: {raster_dir}")

        downloaded_files = [
            f
            for f in os.listdir(raster_dir)
            if os.path.isfile(os.path.join(raster_dir, f))
        ]
        self.assertGreaterEqual(len(downloaded_files), len(times))


if __name__ == "__main__":
    # use the following code to run a list of tests
    # suite = unittest.TestSuite()
    # suite.addTest(TimeDepRastersTestCase("test"))
    # runner = unittest.TextTestRunner()
    # runner.run(suite)

    # use the following code to run all tests in this file
    runner = unittest.TextTestRunner()
    runner.run(unittest.TestLoader().loadTestsFromTestCase(TimeDepRastersTestCase))
