#!/usr/bin/env python3

import os
import unittest
from unittest import mock

from common import (
    INTEGRATION_TEST_LEVEL,
    LARGE_DATA_TEST_LEVEL,
    get_test_level,
    skip_unless_test_level,
)


class TestLevelHelpersTestCase(unittest.TestCase):
    def test_get_test_level_defaults_to_zero(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertEqual(get_test_level(), 0)

    def test_get_test_level_ignores_invalid_values(self):
        with mock.patch.dict(os.environ, {"PMM_TEST_LEVEL": "not-a-number"}):
            self.assertEqual(get_test_level(), 0)

    def test_skip_unless_test_level_skips_below_threshold(self):
        with mock.patch.dict(
            os.environ, {"PMM_TEST_LEVEL": str(INTEGRATION_TEST_LEVEL - 1)}
        ):
            @skip_unless_test_level(INTEGRATION_TEST_LEVEL, "integration test")
            class SampleTestCase(unittest.TestCase):
                def test_example(self):
                    self.fail("test should have been skipped")

            result = unittest.TestResult()
            SampleTestCase("test_example").run(result)

        self.assertEqual(len(result.skipped), 1)
        self.assertEqual(result.testsRun, 1)

    def test_skip_unless_test_level_runs_at_threshold(self):
        with mock.patch.dict(os.environ, {"PMM_TEST_LEVEL": str(LARGE_DATA_TEST_LEVEL)}):
            @skip_unless_test_level(LARGE_DATA_TEST_LEVEL, "large download test")
            class SampleTestCase(unittest.TestCase):
                def test_example(self):
                    self.assertTrue(True)

            result = unittest.TestResult()
            SampleTestCase("test_example").run(result)

        self.assertEqual(result.skipped, [])
        self.assertEqual(result.failures, [])
        self.assertEqual(result.errors, [])
        self.assertEqual(result.testsRun, 1)


if __name__ == "__main__":
    unittest.main()
