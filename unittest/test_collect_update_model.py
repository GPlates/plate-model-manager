import importlib
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from plate_model_manager.utils import collect_update_model


class CollectUpdateModelTestCase(unittest.TestCase):
    def test_env_defaults_are_read(self):
        with mock.patch.dict(
            os.environ,
            {
                "DEFAULT_UPLOAD_TARGET": "user@example",
                "DEFAULT_IDENTITY_FILE": "/tmp/id.pem",
                "DEFAULT_REMOTE_PATH": "/tmp/remote",
            },
            clear=False,
        ):
            module = importlib.reload(collect_update_model)
            self.assertEqual(module.DEFAULT_UPLOAD_TARGET, "user@example")
            self.assertEqual(module.DEFAULT_IDENTITY_FILE, "/tmp/id.pem")
            self.assertEqual(module.DEFAULT_REMOTE_PATH, "/tmp/remote")
        importlib.reload(collect_update_model)

    def test_load_collect_models_from_local_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cfg = Path(tmpdir) / "sources.json"
            cfg.write_text(json.dumps({"models": {"demo": "helpers/collect_demo.py"}}))
            models = collect_update_model.load_collect_models(str(cfg))
            self.assertEqual(models["demo"], "helpers/collect_demo.py")

    def test_load_collect_models_from_remote_url(self):
        response = mock.Mock()
        response.json.return_value = {"models": {"demo": "helpers/collect_demo.py"}}
        response.raise_for_status.return_value = None
        with mock.patch("plate_model_manager.utils.collect_update_model.requests.get", return_value=response):
            models = collect_update_model.load_collect_models("https://example.org/sources.json")
            self.assertEqual(models["demo"], "helpers/collect_demo.py")

    def test_collect_model_files_runs_script_and_upload(self):
        with mock.patch(
            "plate_model_manager.utils.collect_update_model.load_collect_models",
            return_value={"rodinia": "helpers/collect_rodinia.py"},
        ), mock.patch(
            "plate_model_manager.utils.collect_update_model.subprocess.run"
        ) as run_mock, mock.patch(
            "plate_model_manager.utils.collect_update_model.upload_model_folder"
        ) as upload_mock:
            collect_update_model.collect_model_files(
                "rodinia",
                "/tmp/target",
                "/tmp/sources.json",
                upload=True,
                upload_target="u@h",
                identity_file="/tmp/key",
            )

            run_mock.assert_called_once()
            upload_mock.assert_called_once_with(
                Path("/tmp/target/rodinia"),
                "u@h",
                "/tmp/key",
                f"{collect_update_model.DEFAULT_REMOTE_PATH}/rodinia",
            )


if __name__ == "__main__":
    unittest.main()
