import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "helpers"))

import utils  # noqa: E402


class HelperCollectorArgsTestCase(unittest.TestCase):
    def setUp(self):
        utils._REGISTERED_UPLOAD_PATHS.clear()

    def test_parse_collector_args_defaults(self):
        args = utils.parse_collector_args("desc", "demo", argv=[])
        self.assertEqual(args.target_dir, ".")
        self.assertFalse(args.upload)
        self.assertEqual(args.remote_path, f"{utils.DEFAULT_REMOTE_PATH}/demo")

    def test_parse_collector_args_invalid_remote_path(self):
        with self.assertRaises(SystemExit):
            utils.parse_collector_args(
                "desc", "demo", argv=["--remote-path", "/tmp/not-demo"]
            )

    def test_get_model_path_registers_upload_once(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            argv = ["collect_demo.py", tmpdir, "--upload"]
            with mock.patch.object(utils.atexit, "register") as register_mock:
                model_path = utils.get_model_path(argv, "demo")
                self.assertEqual(model_path, f"{tmpdir}/demo")
                self.assertTrue(Path(model_path).is_dir())
                register_mock.assert_called_once_with(
                    utils.upload_model_folder,
                    model_path,
                    utils.DEFAULT_UPLOAD_TARGET,
                    utils.DEFAULT_IDENTITY_FILE,
                    f"{utils.DEFAULT_REMOTE_PATH}/demo",
                )

                utils.get_model_path(argv, "demo")
                register_mock.assert_called_once()


if __name__ == "__main__":
    unittest.main()
