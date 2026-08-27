#!/usr/bin/env python3

import json
import os
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

from common import is_test_installed_module

if not is_test_installed_module():
    sys.path.insert(0, f"{os.path.dirname(__file__)}/../src")

from plate_model_manager import PlateModel
from plate_model_manager.exceptions import LayerNotFoundInModel


class LayerMetadataTestCase(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="pmm-layer-metadata-")
        self.model = PlateModel(
            "TestModel",
            model_cfg={"Layers": {"Coastlines": "https://example.com/coast.zip"}},
            data_dir=self.temp_dir,
            timeout=(5, 5),
        )

    def tearDown(self):
        if hasattr(self, "model"):
            try:
                self.model.executor.shutdown(wait=False)
            except Exception:
                pass
            try:
                self.model.loop.close()
            except Exception:
                pass
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_get_layer_metadata_returns_dict(self):
        layer_dir = os.path.join(self.temp_dir, "Coastlines")
        os.makedirs(layer_dir, exist_ok=True)
        expected_metadata = {
            "url": "https://example.com/coast.zip",
            "etag": "example-etag",
            "expiry": "2099/01/01, 00:00:00",
        }

        metadata_path = os.path.join(layer_dir, ".metadata.json")
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(expected_metadata, f)

        with patch.object(self.model, "_download_layer_files", return_value=layer_dir):
            metadata = self.model.get_layer_metadata("Coastlines")

        self.assertEqual(expected_metadata, metadata)

    def test_get_layer_metadata_returns_none_for_missing_layer_when_requested(self):
        with patch.object(
            self.model,
            "_download_layer_files",
            side_effect=LayerNotFoundInModel("missing layer"),
        ):
            metadata = self.model.get_layer_metadata(
                "MissingLayer", return_none_if_not_exist=True
            )

        self.assertIsNone(metadata)

    def test_get_layer_metadata_raises_for_missing_layer_by_default(self):
        with patch.object(
            self.model,
            "_download_layer_files",
            side_effect=LayerNotFoundInModel("missing layer"),
        ):
            with self.assertRaises(LayerNotFoundInModel):
                self.model.get_layer_metadata("MissingLayer")

    def test_get_layer_metadata_raises_when_metadata_file_missing(self):
        layer_dir = os.path.join(self.temp_dir, "Coastlines")
        os.makedirs(layer_dir, exist_ok=True)

        with patch.object(self.model, "_download_layer_files", return_value=layer_dir):
            with self.assertRaisesRegex(Exception, "Layer metadata file not found"):
                self.model.get_layer_metadata("Coastlines")


if __name__ == "__main__":
    runner = unittest.TextTestRunner()
    runner.run(unittest.TestLoader().loadTestsFromTestCase(LayerMetadataTestCase))
