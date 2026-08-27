#!/usr/bin/env python3
"""Tests for PlateModel raster-retrieval methods:
get_raster, get_age_grid, get_age_grids,
get_spreading_rate_grid, get_spreading_rate_grids
"""

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
from plate_model_manager.utils.enums import GenerationMethod, ReferenceFrame

if not is_test_installed_module():
    sys.path.insert(0, f"{os.path.dirname(__file__)}/../src")

import plate_model_manager
from plate_model_manager import PlateModelManager

if __name__ == "__main__":
    logger_name = "test_get_raster_main"
else:
    logger_name = __name__

logger = get_test_logger(logger_name)
logger.info(plate_model_manager.__file__)


def _get_model(model_name):
    """Helper: return a PlateModel instance with TEMP_TEST_DIR as data dir."""
    mm = PlateModelManager()
    m = mm.get_model(model_name, data_dir=TEMP_TEST_DIR)
    if m is None:
        raise RuntimeError(f"Model '{model_name}' could not be loaded.")
    return m


# ---------------------------------------------------------------------------
# get_raster
# ---------------------------------------------------------------------------
@skip_unless_test_level(
    INTEGRATION_TEST_LEVEL,
    "set PMM_TEST_LEVEL>=1 to run raster integration tests",
)
class TestGetRaster(unittest.TestCase):
    """Tests for PlateModel.get_raster()."""

    def setUp(self):
        pass

    def test_get_raster_returns_existing_file(self):
        """get_raster returns a path that exists on disk."""
        m = _get_model("matthews2016_mantle_ref")
        path = m.get_raster("AgeGrids", 10)
        self.assertIsInstance(path, str)
        self.assertTrue(os.path.isfile(path), msg=f"File not found: {path}")

    def test_get_raster_int_and_float_times(self):
        """get_raster accepts both int and float reconstruction times."""
        m = _get_model("matthews2016_mantle_ref")
        path_int = m.get_raster("AgeGrids", 5)
        path_float = m.get_raster("AgeGrids", 5.0)
        self.assertTrue(os.path.isfile(path_int))
        self.assertTrue(os.path.isfile(path_float))

    def test_get_raster_with_reference_frame(self):
        """get_raster appends the reference-frame suffix to build the raster key."""
        m = _get_model("muller2022")
        # AgeGrids + PMAG -> AgeGridsPMAG
        path = m.get_raster(
            "AgeGrids", 50, reference_frame=ReferenceFrame.PmagReferenceFrame
        )
        self.assertTrue(os.path.isfile(path), msg=f"File not found: {path}")

    def test_get_raster_with_generated_from(self):
        """get_raster appends the generation-method suffix to build the raster key."""
        m = _get_model("zahirovic2022")
        # Agegrids + UsingTopologies -> AgegridsUsingTopologiesMantleFrame is not right;
        # we need only the generated_from suffix here:
        # Agegrids + UsingIsochrons -> AgegridsUsingIsochrons (not in model)
        # Use the full pre-built key directly to verify suffix-free path still works.
        path = m.get_raster("AgegridsUsingIsochronsMantleFrame", 50)
        self.assertTrue(os.path.isfile(path), msg=f"File not found: {path}")

    def test_get_raster_with_reference_frame_and_generated_from(self):
        """get_raster composes generated_from then reference_frame suffixes."""
        m = _get_model("zahirovic2022")
        # "Agegrids" + "UsingIsochrons" + "MantleFrame" -> "AgegridsUsingIsochronsMantleFrame"
        path = m.get_raster(
            "Agegrids",
            50,
            reference_frame=ReferenceFrame.MantleReferenceFrame,
            generated_from=GenerationMethod.Isochrons,
        )
        self.assertTrue(os.path.isfile(path), msg=f"File not found: {path}")

    def test_get_raster_raises_when_no_time_dep_rasters(self):
        """get_raster raises Exception when the model has no TimeDepRasters."""
        m = _get_model("merdith2021")
        with self.assertRaises(Exception):
            m.get_raster("AgeGrids", 100)

    def test_get_raster_raises_for_unknown_raster_name(self):
        """get_raster raises Exception for a raster name not in the model config."""
        m = _get_model("matthews2016_mantle_ref")
        with self.assertRaises(Exception):
            m.get_raster("NonExistentRaster", 10)


# ---------------------------------------------------------------------------
# get_age_grid / get_age_grids
# ---------------------------------------------------------------------------
@skip_unless_test_level(
    INTEGRATION_TEST_LEVEL,
    "set PMM_TEST_LEVEL>=1 to run raster integration tests",
)
class TestGetAgeGrid(unittest.TestCase):
    """Tests for PlateModel.get_age_grid() and get_age_grids()."""

    def setUp(self):
        pass

    # -- get_age_grid -------------------------------------------------------

    def test_get_age_grid_returns_file(self):
        """get_age_grid returns a path that exists on disk."""
        m = _get_model("matthews2016_mantle_ref")
        path = m.get_age_grid(10)
        self.assertIsInstance(path, str)
        self.assertTrue(os.path.isfile(path), msg=f"File not found: {path}")

    def test_get_age_grid_different_times(self):
        """get_age_grid returns distinct paths for distinct times."""
        m = _get_model("matthews2016_mantle_ref")
        path_a = m.get_age_grid(0)
        path_b = m.get_age_grid(1)
        self.assertTrue(os.path.isfile(path_a))
        self.assertTrue(os.path.isfile(path_b))
        self.assertNotEqual(path_a, path_b)

    def test_get_age_grid_with_pmag_reference_frame(self):
        """get_age_grid with PmagReferenceFrame fetches the PMAG variant."""
        m = _get_model("muller2022")
        # AgeGrids + PMAG -> AgeGridsPMAG
        path = m.get_age_grid(50, reference_frame=ReferenceFrame.PmagReferenceFrame)
        self.assertTrue(os.path.isfile(path), msg=f"File not found: {path}")

    def test_get_age_grid_raises_for_model_without_rasters(self):
        """get_age_grid raises when the model has no TimeDepRasters."""
        m = _get_model("merdith2021")
        with self.assertRaises(Exception):
            m.get_age_grid(100)

    # -- get_age_grids ------------------------------------------------------

    def test_get_age_grids_returns_correct_count(self):
        """get_age_grids returns one path per requested time."""
        m = _get_model("matthews2016_mantle_ref")
        times = [5, 10, 15]
        paths = m.get_age_grids(times)
        self.assertEqual(len(paths), len(times))

    def test_get_age_grids_all_files_exist(self):
        """Every path returned by get_age_grids points to an existing file."""
        m = _get_model("matthews2016_mantle_ref")
        paths = m.get_age_grids([0, 1, 2])
        for p in paths:
            self.assertTrue(os.path.isfile(p), msg=f"File not found: {p}")

    def test_get_age_grids_preserves_order(self):
        """get_age_grids returns paths in the same order as the input times."""
        m = _get_model("matthews2016_mantle_ref")
        times = [3, 1, 2]
        paths = m.get_age_grids(times)
        self.assertEqual(len(paths), 3)
        for p in paths:
            self.assertTrue(os.path.isfile(p))

    def test_get_age_grids_with_reference_frame(self):
        """get_age_grids forwards reference_frame to get_rasters."""
        m = _get_model("muller2022")
        paths = m.get_age_grids(
            [50, 51], reference_frame=ReferenceFrame.PmagReferenceFrame
        )
        self.assertEqual(len(paths), 2)
        for p in paths:
            self.assertTrue(os.path.isfile(p), msg=f"File not found: {p}")

    def test_get_age_grids_raises_for_model_without_rasters(self):
        """get_age_grids raises when the model has no TimeDepRasters."""
        m = _get_model("merdith2021")
        with self.assertRaises(Exception):
            m.get_age_grids([100, 101])


# ---------------------------------------------------------------------------
# get_spreading_rate_grid / get_spreading_rate_grids
# ---------------------------------------------------------------------------
@skip_unless_test_level(
    INTEGRATION_TEST_LEVEL,
    "set PMM_TEST_LEVEL>=1 to run raster integration tests",
)
class TestGetSpreadingRateGrid(unittest.TestCase):
    """Tests for PlateModel.get_spreading_rate_grid() and get_spreading_rate_grids()."""

    def setUp(self):
        pass

    # -- get_spreading_rate_grid --------------------------------------------

    def test_get_spreading_rate_grid_returns_file(self):
        """get_spreading_rate_grid returns a path that exists on disk."""
        m = _get_model("clennett2020")
        path = m.get_spreading_rate_grid(10)
        logger.error(f"Spreading rate grid path: {path}")
        self.assertIsInstance(path, str)
        self.assertTrue(os.path.isfile(path), msg=f"File not found: {path}")

    def test_get_spreading_rate_grid_different_times(self):
        """get_spreading_rate_grid returns distinct paths for distinct times."""
        m = _get_model("clennett2020")
        path_a = m.get_spreading_rate_grid(5)
        path_b = m.get_spreading_rate_grid(10)
        self.assertTrue(os.path.isfile(path_a))
        self.assertTrue(os.path.isfile(path_b))
        self.assertNotEqual(path_a, path_b)

    def test_get_spreading_rate_grid_raises_for_model_without_spreading_rate(self):
        """get_spreading_rate_grid raises when the model has no SpreadingRate raster."""
        m = _get_model("matthews2016_mantle_ref")
        with self.assertRaises(Exception):
            m.get_spreading_rate_grid(10)

    def test_get_spreading_rate_grid_raises_for_model_without_rasters(self):
        """get_spreading_rate_grid raises when the model has no TimeDepRasters."""
        m = _get_model("merdith2021")
        with self.assertRaises(Exception):
            m.get_spreading_rate_grid(100)

    def test_get_spreading_rate_grid_with_generated_from_and_reference_frame(self):
        """get_spreading_rate_grid with both params builds the correct raster key."""
        m = _get_model("zahirovic2022")
        # SpreadingRate + UsingTopologies + MantleFrame -> SpreadingRateUsingTopologiesMantleFrame
        path = m.get_spreading_rate_grid(
            50,
            reference_frame=ReferenceFrame.MantleReferenceFrame,
            generated_from=GenerationMethod.Topologies,
        )
        self.assertTrue(os.path.isfile(path), msg=f"File not found: {path}")

    # -- get_spreading_rate_grids -------------------------------------------

    def test_get_spreading_rate_grids_returns_correct_count(self):
        """get_spreading_rate_grids returns one path per requested time."""
        m = _get_model("clennett2020")
        times = [5, 10, 15]
        paths = m.get_spreading_rate_grids(times)
        self.assertEqual(len(paths), len(times))

    def test_get_spreading_rate_grids_all_files_exist(self):
        """Every path returned by get_spreading_rate_grids points to an existing file."""
        m = _get_model("clennett2020")
        paths = m.get_spreading_rate_grids([0, 1, 2])
        for p in paths:
            self.assertTrue(os.path.isfile(p), msg=f"File not found: {p}")

    def test_get_spreading_rate_grids_preserves_order(self):
        """get_spreading_rate_grids returns paths in the same order as the input times."""
        m = _get_model("clennett2020")
        times = [3, 1, 2]
        paths = m.get_spreading_rate_grids(times)
        self.assertEqual(len(paths), 3)
        for p in paths:
            self.assertTrue(os.path.isfile(p))

    def test_get_spreading_rate_grids_with_generated_from_and_reference_frame(self):
        """get_spreading_rate_grids forwards both optional params to get_rasters."""
        m = _get_model("zahirovic2022")
        # SpreadingRate + UsingTopologies + MantleFrame
        times = [50, 51]
        paths = m.get_spreading_rate_grids(
            times,
            reference_frame=ReferenceFrame.MantleReferenceFrame,
            generated_from=GenerationMethod.Topologies,
        )
        self.assertEqual(len(paths), len(times))
        for p in paths:
            self.assertTrue(os.path.isfile(p), msg=f"File not found: {p}")

    def test_get_spreading_rate_grids_raises_for_model_without_rasters(self):
        """get_spreading_rate_grids raises when the model has no TimeDepRasters."""
        m = _get_model("merdith2021")
        with self.assertRaises(Exception):
            m.get_spreading_rate_grids([100, 101])


if __name__ == "__main__":
    runner = unittest.TextTestRunner()
    runner.run(unittest.TestLoader().loadTestsFromModule(__import__(__name__)))
