#!/usr/bin/env python3

import json
import os
import sys
import unittest

from common import TEMP_TEST_DIR, get_test_logger, is_test_installed_module

if not is_test_installed_module():
    sys.path.insert(0, f"{os.path.dirname(__file__)}/../src")

import plate_model_manager
from plate_model_manager import PlateModelManager
from plate_model_manager.exceptions import InvalidConfigFile

# plate_model_manager.disable_stdout_logging()

if __name__ == "__main__":
    logger_name = "test_pmm_server_main"
else:
    logger_name = __name__

logger = get_test_logger(logger_name)

logger.info(plate_model_manager.__file__)


def get_real_model_name(name, model_config):
    if name not in model_config:
        return None
    else:
        if isinstance(model_config[name], str):
            return get_real_model_name(model_config[name][1:], model_config)
        else:
            return name


class PMMServerTestCase(unittest.TestCase):
    def setUp(self):
        with open(f"{os.path.dirname(__file__)}/models_test.json", "r") as f:
            self.model_cfg = json.load(f)

    def test_server(self):
        pm_manager = PlateModelManager()
        model_names = pm_manager.get_available_model_names()
        model_names.append("vars")
        names = [n for n in self.model_cfg]
        for mn in self.model_cfg:
            self.assertTrue(
                mn in model_names, f"The model name {mn} is not in {model_names}."
            )
        self.assertEqual(len(names), len(model_names))
        self.assertEqual(set(model_names), set(names))
        for name in model_names:
            print(f"testing {name}")
            if name == "vars":
                continue
            model = pm_manager.get_model(name, data_dir=TEMP_TEST_DIR)
            if not model:
                raise Exception(f"Unable to get model ({name}).")
            layer_names = [
                n
                for n in self.model_cfg[get_real_model_name(name, self.model_cfg)][
                    "Layers"
                ]
            ]
            self.assertEqual(
                layer_names,
                model.get_avail_layers(),
            )
            # make sure rotation files
            rm = model.get_rotation_model()
            self.assertTrue(len(rm))
            for f in rm:
                self.assertTrue(os.path.isfile(f))
            # make sure other layer files
            for layer in layer_names:
                files = model.get_layer(layer)
                self.assertTrue(files is not None)
                if files is not None:
                    self.assertTrue(len(files) > 0)
                    for f in files:
                        self.assertTrue(os.path.isfile(f))

    def test_model_in_server(self):
        pm_manager = PlateModelManager()
        model_names = pm_manager.get_available_model_names()
        self.assertIn("alfonso2024".lower(), model_names)
        self.assertIn("Muller2022".lower(), model_names)
        self.assertIn("Muller2019".lower(), model_names)
        self.assertIn("Muller2016".lower(), model_names)
        self.assertIn("merdith2021".lower(), model_names)
        self.assertIn("matthews2016".lower(), model_names)
        self.assertIn("clennett2020".lower(), model_names)


if __name__ == "__main__":
    # use the following code to run a list of tests
    # suite = unittest.TestSuite()
    # suite.addTest(PMMServerTestCase("test_server"))
    # runner = unittest.TextTestRunner()
    # runner.run(suite)

    # use the following code to run all tests in this file
    runner = unittest.TextTestRunner()
    runner.run(unittest.TestLoader().loadTestsFromTestCase(PMMServerTestCase))
