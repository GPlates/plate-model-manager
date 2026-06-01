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

from plate_model_manager import PresentDayRasterManager
from plate_model_manager.present_day_rasters import RasterNameNotFound

if __name__ == "__main__":
    logger_name = "test_present_day_raster_main"
else:
    logger_name = __name__

logger = get_test_logger(logger_name)


@skip_unless_test_level(
    INTEGRATION_TEST_LEVEL,
    "set PMM_TEST_LEVEL>=1 to run present-day raster integration tests",
)
class RasterTestCase(unittest.TestCase):
    def setUp(self):
        self.manager = PresentDayRasterManager("../config/present_day_rasters.json")
        # self.manager = PresentDayRasterManager("")
        self.manager.set_data_dir(TEMP_TEST_DIR)

    def test_present_day_raster(self):
        rasters = self.manager.list_present_day_rasters()
        self.assertTrue(len(rasters) > 0)
        logger.info(rasters)
        raster_file = self.manager.get_raster("topography")
        self.assertTrue(os.path.isfile(raster_file))
        raster_file = self.manager.get_raster("etopo1_grd")
        self.assertTrue(os.path.isfile(raster_file))
        raster_file = self.manager.get_raster("etopo1_tif")
        self.assertTrue(os.path.isfile(raster_file))

    def test_wms(self):
        self.assertTrue(self.manager.is_wms("vgg"))
        self.assertFalse(self.manager.is_wms("agegrid"))
        self.assertRaises(RasterNameNotFound, self.manager.is_wms, "no-such-raster")
        print(self.manager.get_raster("vgg", width=3600, height=1600))
        print(
            self.manager.get_raster(
                "vgg", width=1000, height=1000, bbox=[-10, -10, 10, 10]
            )
        )


if __name__ == "__main__":
    # use the following code to run a list of tests
    # suite = unittest.TestSuite()
    # suite.addTest(RasterTestCase("test_present_day_raster"))
    # runner = unittest.TextTestRunner()
    # runner.run(suite)

    # use the following code to run all tests in this file
    runner = unittest.TextTestRunner()
    runner.run(unittest.TestLoader().loadTestsFromTestCase(RasterTestCase))
