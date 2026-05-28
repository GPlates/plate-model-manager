#!/usr/bin/env python3
"""Unit tests for multiprocessing support with PlateModelManager and PlateModel.

This module tests:

1. **Pickling** – that ``PlateModel`` and ``PlateModelManager`` survive a
   ``pickle.dumps`` / ``pickle.loads`` round-trip.
2. **Standard multiprocessing** – that both objects can be sent to
   ``multiprocessing.Pool`` workers (arguments are always pickled when
   travelling through the inter-process queue, even on fork-based platforms).
3. **joblib** – that both objects work with ``joblib.Parallel`` workers
   (tests are skipped automatically when joblib is not installed).
4. **Best-practice pattern** – download model files once in the main process
   with ``PlateModel`` / ``PlateModelManager``, then pass *only file paths*
   to worker processes so workers never need to pickle a model object at all.
"""

import multiprocessing
import os
import pickle
import sys
import unittest

try:
    import joblib

    HAS_JOBLIB = True
except ImportError:
    HAS_JOBLIB = False

from common import TEMP_TEST_DIR, get_test_logger, is_test_installed_module

if not is_test_installed_module():
    sys.path.insert(0, os.path.abspath(f"{os.path.dirname(__file__)}/../src"))

import plate_model_manager
from plate_model_manager import PlateModel, PlateModelManager

plate_model_manager.disable_stdout_logging()

if __name__ == "__main__":
    logger_name = "test_multiprocessing_main"
else:
    logger_name = __name__

logger = get_test_logger(logger_name)

_DIR = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------------------
# Module-level worker functions
#
# Worker functions MUST be defined at module level (not as lambdas or nested
# functions) so that they can be serialised by the standard ``pickle`` module
# when using ``multiprocessing`` with the "spawn" or "forkserver" start
# methods (and on Windows, which always uses "spawn").
# ---------------------------------------------------------------------------


def _worker_get_model_name(plate_model):
    """Return the ``model_name`` attribute of a ``PlateModel`` received by a worker."""
    return plate_model.model_name


def _worker_get_available_models(plate_model_manager_obj):
    """Return the list of available model names from a ``PlateModelManager`` received by a worker."""
    return plate_model_manager_obj.get_available_model_names()


def _worker_check_files_exist(file_paths):
    """Return a list of booleans indicating whether each path refers to an existing file."""
    return [os.path.isfile(f) for f in file_paths]


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _make_model_manager():
    return PlateModelManager()


def _make_model(model_manager, data_dir=TEMP_TEST_DIR):
    model = model_manager.get_model("Muller2019")
    if model is None:
        raise Exception("Muller2019 model not found in config")
    model.set_data_dir(data_dir)
    return model


# ---------------------------------------------------------------------------
# Test cases
# ---------------------------------------------------------------------------


class TestPickling(unittest.TestCase):
    """Verify that ``PlateModel`` and ``PlateModelManager`` survive pickle round-trips."""

    def setUp(self):
        self.model_manager = _make_model_manager()
        self.model = _make_model(self.model_manager)

    # ------------------------------------------------------------------
    # PlateModel
    # ------------------------------------------------------------------

    def test_plate_model_pickle_roundtrip(self):
        """``PlateModel`` can be serialised and deserialised with ``pickle``."""
        data = pickle.dumps(self.model)
        restored = pickle.loads(data)

        self.assertEqual(self.model.model_name, restored.model_name)
        self.assertEqual(self.model.get_data_dir(), restored.get_data_dir())
        self.assertEqual(self.model.get_big_time(), restored.get_big_time())
        self.assertEqual(self.model.get_avail_layers(), restored.get_avail_layers())
        logger.info(
            "PlateModel pickle round-trip OK: model_name=%s", restored.model_name
        )

    def test_plate_model_readonly_pickle_roundtrip(self):
        """``PlateModel`` in *readonly* mode can be serialised and deserialised."""
        # Ensure files are present so that readonly mode can be initialised.
        self.model.download_all_layers()

        readonly_model = PlateModel("Muller2019", data_dir=TEMP_TEST_DIR, readonly=True)

        data = pickle.dumps(readonly_model)
        restored = pickle.loads(data)

        self.assertEqual(readonly_model.model_name, restored.model_name)
        self.assertTrue(restored.readonly)
        logger.info(
            "Readonly PlateModel pickle round-trip OK: model_name=%s",
            restored.model_name,
        )

    # ------------------------------------------------------------------
    # PlateModelManager
    # ------------------------------------------------------------------

    def test_plate_model_manager_pickle_roundtrip(self):
        """``PlateModelManager`` can be serialised and deserialised with ``pickle``."""
        data = pickle.dumps(self.model_manager)
        restored = pickle.loads(data)

        self.assertEqual(
            self.model_manager.get_available_model_names(),
            restored.get_available_model_names(),
        )
        self.assertEqual(self.model_manager.model_manifest, restored.model_manifest)
        logger.info(
            "PlateModelManager pickle round-trip OK: %d models",
            len(restored.get_available_model_names()),
        )


class TestMultiprocessing(unittest.TestCase):
    """Verify that ``PlateModel`` and ``PlateModelManager`` work inside ``multiprocessing.Pool`` workers.

    ``Pool.apply`` / ``Pool.map`` always pickle their arguments via an
    inter-process queue, so these tests exercise the full pickle / unpickle
    cycle even on Linux where the default pool start method is "fork".
    """

    def setUp(self):
        self.model_manager = _make_model_manager()
        self.model = _make_model(self.model_manager)

    # ------------------------------------------------------------------
    # PlateModel
    # ------------------------------------------------------------------

    def test_plate_model_in_worker(self):
        """``PlateModel`` can be pickled and passed to a ``multiprocessing.Pool`` worker."""
        with multiprocessing.Pool(1) as pool:
            result = pool.apply(_worker_get_model_name, (self.model,))

        self.assertEqual(result, self.model.model_name)
        logger.info("PlateModel in worker OK: model_name=%s", result)

    # ------------------------------------------------------------------
    # PlateModelManager
    # ------------------------------------------------------------------

    def test_plate_model_manager_in_worker(self):
        """``PlateModelManager`` can be pickled and passed to a ``multiprocessing.Pool`` worker."""
        with multiprocessing.Pool(1) as pool:
            result = pool.apply(_worker_get_available_models, (self.model_manager,))

        self.assertEqual(result, self.model_manager.get_available_model_names())
        logger.info("PlateModelManager in worker OK: %d models available", len(result))

    # ------------------------------------------------------------------
    # Best-practice pattern
    # ------------------------------------------------------------------

    def test_best_practice_file_paths_in_workers(self):
        """Best practice: download files in the main process, pass only file paths to workers.

        This is the recommended approach for using plate model data in a
        multiprocessing program:

        1. Use ``PlateModel`` / ``PlateModelManager`` **in the main process**
           to download model files.
        2. Retrieve the local file paths (``get_rotation_model``,
           ``get_layer``, …).
        3. Pass **only the file paths** to worker processes – no
           ``PlateModel`` or ``PlateModelManager`` objects cross the process
           boundary.

        Workers can then read the files directly using whatever tools they
        need (e.g. ``pygplates``) without needing internet access or any
        plate model management objects.
        """
        # Step 1: download/locate model files in the main process.
        rotation_files = self.model.get_rotation_model()
        coastlines_files = self.model.get_layer("Coastlines")

        self.assertIsNotNone(rotation_files)
        self.assertGreater(len(rotation_files), 0)

        # Step 2: pass only file paths to workers.
        with multiprocessing.Pool(2) as pool:
            rotation_ok = pool.apply(_worker_check_files_exist, (rotation_files,))
            if coastlines_files:
                coastlines_ok = pool.apply(
                    _worker_check_files_exist, (coastlines_files,)
                )

        self.assertTrue(
            all(rotation_ok),
            "Some rotation files were not found inside the worker process",
        )
        if coastlines_files:
            self.assertTrue(
                all(coastlines_ok),
                "Some coastline files were not found inside the worker process",
            )
        logger.info(
            "Best practice (multiprocessing + file paths): %d rotation files "
            "verified in worker processes",
            len(rotation_files),
        )


@unittest.skipUnless(HAS_JOBLIB, "joblib is not installed – skipping joblib tests")
class TestJoblib(unittest.TestCase):
    """Verify that ``PlateModel`` and ``PlateModelManager`` work with ``joblib.Parallel`` workers.

    ``joblib`` uses the *loky* backend by default, which spawns fresh worker
    processes and serialises arguments with *cloudpickle* (a superset of
    standard ``pickle``).  These tests confirm compatibility with that
    serialisation path.
    """

    def setUp(self):
        self.model_manager = _make_model_manager()
        self.model = _make_model(self.model_manager)

    # ------------------------------------------------------------------
    # PlateModel
    # ------------------------------------------------------------------

    def test_plate_model_with_joblib(self):
        """``PlateModel`` can be serialised and passed to ``joblib.Parallel`` workers."""
        results = joblib.Parallel(n_jobs=1)(
            joblib.delayed(_worker_get_model_name)(self.model) for _ in range(3)
        )

        for result in results:
            self.assertEqual(result, self.model.model_name)
        logger.info("PlateModel with joblib OK: model_name=%s", results[0])

    # ------------------------------------------------------------------
    # PlateModelManager
    # ------------------------------------------------------------------

    def test_plate_model_manager_with_joblib(self):
        """``PlateModelManager`` can be serialised and passed to ``joblib.Parallel`` workers."""
        expected = self.model_manager.get_available_model_names()

        results = joblib.Parallel(n_jobs=1)(
            joblib.delayed(_worker_get_available_models)(self.model_manager)
            for _ in range(3)
        )

        for result in results:
            self.assertEqual(result, expected)
        logger.info("PlateModelManager with joblib OK: %d models", len(results[0]))

    # ------------------------------------------------------------------
    # Best-practice pattern
    # ------------------------------------------------------------------

    def test_best_practice_file_paths_with_joblib(self):
        """Best practice with joblib: pass only file paths to parallel workers.

        Download model files in the main process using ``PlateModel``, then
        distribute individual file paths across ``joblib`` workers.  Each
        worker verifies that its assigned path exists – no plate model object
        crosses the process boundary.
        """
        rotation_files = self.model.get_rotation_model()

        self.assertIsNotNone(rotation_files)
        self.assertGreater(len(rotation_files), 0)

        # Process each file path in a separate joblib worker.
        results = joblib.Parallel(n_jobs=2)(
            joblib.delayed(os.path.isfile)(f) for f in rotation_files
        )

        self.assertTrue(
            all(results),
            "Some rotation files were not found inside joblib worker processes",
        )
        logger.info(
            "Best practice (joblib + file paths): %d rotation files verified "
            "in parallel workers",
            len(rotation_files),
        )


if __name__ == "__main__":
    runner = unittest.TextTestRunner(verbosity=2)
    suite = unittest.TestSuite()
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestPickling))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestMultiprocessing))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestJoblib))
    runner.run(suite)
