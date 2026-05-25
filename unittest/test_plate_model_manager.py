#!/usr/bin/env python
import os
import shutil
import sys
import tempfile
import unittest

from plate_model_manager.utils.enums import ReferenceFrame

sys.path.insert(0, f"{os.path.dirname(__file__)}/../src")
from common import TEMP_TEST_DIR, get_test_logger

from plate_model_manager import PlateModel, PlateModelManager
from plate_model_manager.exceptions import InvalidConfigFile, ServerUnavailable
from plate_model_manager.plate_model import README_FILENAME

if __name__ == "__main__":
    logger_name = "test_plate_model_manager_main"
else:
    logger_name = __name__

logger = get_test_logger(logger_name)


class PlateModelManagerestCase(unittest.TestCase):
    def setUp(self):
        pass

    def test_plate_model_manager(self):
        model_manager = PlateModelManager(
            f"{os.path.dirname(__file__)}/../config/models_v2.json"
        )
        model_names = model_manager.get_available_model_names()
        self.assertTrue(len(model_names) > 0)
        logger.info(model_names)

        model = model_manager.get_model("Muller2019")
        self.assertIsInstance(model, PlateModel)
        no_good = model_manager.get_model("no-good-model")
        self.assertIsNone(no_good)

        # test remote models.json with URL
        model_manager = PlateModelManager(
            "https://repo.gplates.org/webdav/pmm/config/models_v2.json"
        )
        model_names = model_manager.get_available_model_names()
        model_names = model_manager.get_available_model_names()
        self.assertTrue(len(model_names) > 0)
        logger.info(model_names)

        model = model_manager.get_model("Muller2019")
        self.assertIsInstance(model, PlateModel)
        no_good = model_manager.get_model("no-good-model")
        self.assertIsNone(no_good)

        model_manager = PlateModelManager(
            f"{os.path.dirname(__file__)}/../config/models_v2.json"
        )

        model = model_manager.get_model(
            "matthews2016", reference_frame=ReferenceFrame.PmagReferenceFrame
        )
        self.assertIsInstance(model, PlateModel)
        rotation_files = model.get_rotation_model()
        self.assertIsInstance(rotation_files, tuple)
        self.assertTrue(len(rotation_files) == 2)

        model = model_manager.get_model(
            "zahirovic2022", reference_frame=ReferenceFrame.PmagReferenceFrame
        )
        self.assertIsInstance(model, PlateModel)
        rotation_files = model.get_rotation_model()
        self.assertIsInstance(rotation_files, tuple)
        self.assertTrue(len(rotation_files) == 2)

        model = model_manager.get_model(
            "matthews2016", reference_frame=ReferenceFrame.MantleReferenceFrame
        )
        self.assertIsInstance(model, PlateModel)
        rotation_files = model.get_rotation_model()
        self.assertIsInstance(rotation_files, list)
        self.assertTrue(len(rotation_files) > 0)

        model = model_manager.get_model(
            "zahirovic2022", reference_frame=ReferenceFrame.MantleReferenceFrame
        )
        self.assertIsInstance(model, PlateModel)
        rotation_files = model.get_rotation_model()
        self.assertIsInstance(rotation_files, list)
        self.assertTrue(len(rotation_files) > 0)

        model = model_manager.get_model(
            "Muller2025", reference_frame=ReferenceFrame.MantleReferenceFrame
        )
        self.assertIsInstance(model, PlateModel)
        rotation_files = model.get_rotation_model()
        self.assertIsInstance(rotation_files, list)
        self.assertTrue(len(rotation_files) > 0)

        model = model_manager.get_model(
            "Muller2025", reference_frame=ReferenceFrame.PmagReferenceFrame
        )
        self.assertIsNone(model)

    def test_scotese_and_wright2018_present_in_local_config(self):
        model_manager = PlateModelManager(
            f"{os.path.dirname(__file__)}/../config/models_v2.json"
        )
        model_names = model_manager.get_available_model_names()
        self.assertIn("scotese_and_wright2018", model_names)

    def test_plate_model_manager_timeout(self):
        with self.assertRaises(InvalidConfigFile):
            PlateModelManager(
                "https://repo.gplates.org/webdav/pmm/xxx.json", timeout=(5, 5)
            )

        with self.assertRaises(ServerUnavailable):
            PlateModelManager(
                "https://100.11.12.10/webdav/pmm/model.json", timeout=(5, 5)
            )


class ReadmeCreationTestCase(unittest.TestCase):
    """Tests that readme.txt is created in the model folder when create_model_dir() is called."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="pmm_test_readme_")
        self.model_cfg = {
            "BigTime": 250,
            "SmallTime": 0,
            "Rotations": "https://example.com/Rotations.zip",
            "Layers": {
                "Coastlines": "https://example.com/Coastlines.zip",
                "StaticPolygons": "https://example.com/StaticPolygons.zip",
            },
            "TimeDepRasters": {
                "AgeGrids": "https://example.com/AgeGrid_{:.0f}.nc",
            },
            "Description": "A test plate model description.",
            "URL": "https://doi.org/10.5281/zenodo.0000000",
            "Version": "10.5281/zenodo.0000001",
        }
        self.model_name = "test_readme_model"

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_readme_created_in_model_dir(self):
        """readme.txt should be created when create_model_dir() is called."""
        model = PlateModel(
            self.model_name, model_cfg=self.model_cfg, data_dir=self.test_dir
        )
        model_dir = model.create_model_dir()

        readme_path = os.path.join(model_dir, README_FILENAME)
        self.assertTrue(
            os.path.isfile(readme_path),
            f"readme.txt was not created at {readme_path}",
        )

    def test_readme_contains_model_info(self):
        """readme.txt should contain key model information."""
        model = PlateModel(
            self.model_name, model_cfg=self.model_cfg, data_dir=self.test_dir
        )
        model_dir = model.create_model_dir()

        readme_path = os.path.join(model_dir, README_FILENAME)
        with open(readme_path, encoding="utf-8") as f:
            content = f.read()

        self.assertIn(self.model_name, content)
        self.assertIn("A test plate model description.", content)
        self.assertIn("https://doi.org/10.5281/zenodo.0000000", content)
        self.assertIn("250", content)
        self.assertIn("Coastlines", content)
        self.assertIn("AgeGrids", content)


if __name__ == "__main__":
    # use the following code to run a list of tests
    # suite = unittest.TestSuite()
    # suite.addTest(PlateModelManagerestCase("test_plate_model_manager"))
    # runner = unittest.TextTestRunner()
    # runner.run(suite)

    # use the following code to run all tests in this file
    runner = unittest.TextTestRunner()
    runner.run(unittest.TestLoader().loadTestsFromTestCase(PlateModelManagerestCase))
