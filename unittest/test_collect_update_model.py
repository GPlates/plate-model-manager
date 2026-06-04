#
#    Copyright (C) 2024-2026 The University of Sydney, Australia
#
#    This program is free software; you can redistribute it and/or modify it under
#    the terms of the GNU General Public License, version 2, as published by
#    the Free Software Foundation.
#
#    This program is distributed in the hope that it will be useful, but WITHOUT
#    ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
#    FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
#    for more details.
#
#    You should have received a copy of the GNU General Public License along
#    with this program; if not, write to Free Software Foundation, Inc.,
#    51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#
import hashlib
import importlib
import json
import os
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

from plate_model_manager.utils import collect_update_model


class CollectUpdateModelTestCase(unittest.TestCase):
    """Test suite for collect_update_model module."""

    def test_env_defaults_are_read(self):
        """Test that environment variables are correctly read for default values."""
        with mock.patch.dict(
            os.environ,
            {
                "DEFAULT_REMOTE_TARGET": "user@example:/path",
                "DEFAULT_IDENTITY_FILE": "/tmp/id.pem",
            },
            clear=False,
        ):
            module = importlib.reload(collect_update_model)
            self.assertEqual(module.DEFAULT_REMOTE_TARGET, "user@example:/path")
            self.assertEqual(module.DEFAULT_IDENTITY_FILE, "/tmp/id.pem")
        importlib.reload(collect_update_model)

    def test_load_model_data_sources_from_local_file(self):
        """Test loading model data sources from a local JSON file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cfg = Path(tmpdir) / "sources.json"
            cfg.write_text(
                json.dumps(
                    {
                        "demo": {
                            "Rotations": ["*.rot"],
                            "Layers": {"StaticPolygons": ["*.gpml"]},
                        }
                    }
                )
            )
            models = collect_update_model._load_model_data_sources(str(cfg))
            self.assertIn("demo", models)
            self.assertEqual(models["demo"]["Rotations"], ["*.rot"])

    def test_load_model_data_sources_from_remote_url(self):
        """Test loading model data sources from a remote URL."""
        response = mock.Mock()
        response.json.return_value = {
            "demo": {
                "Rotations": ["*.rot"],
                "Layers": {"StaticPolygons": ["*.gpml"]},
            }
        }
        response.raise_for_status.return_value = None
        with mock.patch(
            "plate_model_manager.utils.collect_update_model.requests.get",
            return_value=response,
        ):
            models = collect_update_model._load_model_data_sources(
                "https://example.org/sources.json"
            )
            self.assertIn("demo", models)
            self.assertEqual(models["demo"]["Rotations"], ["*.rot"])

    def test_zip_files_creates_zip_archive(self):
        """Test that _zip_files creates a zip archive with specified files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            file1 = Path(tmpdir) / "file1.txt"
            file2 = Path(tmpdir) / "file2.txt"
            file1.write_text("content1")
            file2.write_text("content2")

            # Create zip
            zip_path = Path(tmpdir) / "test.zip"
            collect_update_model._zip_files([file1, file2], zip_path, "test_folder")

            # Verify zip contents
            self.assertTrue(zip_path.exists())
            with zipfile.ZipFile(zip_path, "r") as zf:
                names = zf.namelist()
                self.assertIn("test_folder/file1.txt", names)
                self.assertIn("test_folder/file2.txt", names)

    def test_zip_files_raises_on_empty_list(self):
        """Test that _zip_files raises an exception when given empty file list."""
        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = Path(tmpdir) / "test.zip"
            with self.assertRaises(Exception) as context:
                collect_update_model._zip_files([], zip_path, "test")
            self.assertIn("zip nothing", str(context.exception).lower())

    def test_zip_folder_creates_zip_with_folder_contents(self):
        """Test that _zip_folder creates a zip with all folder contents."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test folder structure
            folder = Path(tmpdir) / "source"
            folder.mkdir()
            (folder / "file1.txt").write_text("content1")
            subfolder = folder / "sub"
            subfolder.mkdir()
            (subfolder / "file2.txt").write_text("content2")

            # Create zip
            zip_path = Path(tmpdir) / "test.zip"
            collect_update_model._zip_folder(folder, zip_path, "test_folder")

            # Verify zip contents
            self.assertTrue(zip_path.exists())
            with zipfile.ZipFile(zip_path, "r") as zf:
                names = zf.namelist()
                self.assertIn("test_folder/file1.txt", names)
                self.assertIn("test_folder/sub/file2.txt", names)

    def test_add_folder_to_zip_appends_to_existing_zip(self):
        """Test that _add_folder_to_zip appends folder contents to existing zip."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create initial zip
            zip_path = Path(tmpdir) / "test.zip"
            initial_file = Path(tmpdir) / "initial.txt"
            initial_file.write_text("initial")
            collect_update_model._zip_files([initial_file], zip_path, "initial")

            # Create folder to add
            folder = Path(tmpdir) / "add_folder"
            folder.mkdir()
            (folder / "new_file.txt").write_text("new content")

            # Add folder to zip
            collect_update_model._add_folder_to_zip(folder, zip_path)

            # Verify both old and new contents
            with zipfile.ZipFile(zip_path, "r") as zf:
                names = zf.namelist()
                self.assertIn("initial/initial.txt", names)
                self.assertTrue(any("new_file.txt" in name for name in names))

    def test_create_hex_hash_sidecar_files(self):
        """Test that SHA256 hash sidecar files are created for zip files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a test zip file
            zip_path = Path(tmpdir) / "test.zip"
            test_content = b"test content for hashing"
            with zipfile.ZipFile(zip_path, "w") as zf:
                zf.writestr("test.txt", test_content)

            # Calculate expected hash
            with open(zip_path, "rb") as f:
                expected_hash = hashlib.sha256(f.read()).hexdigest()

            # Create sidecar files
            collect_update_model.create_hex_hash_sidecar_files(tmpdir)

            # Verify sidecar file exists
            sidecar_path = Path(f"{zip_path}.{expected_hash}")
            self.assertTrue(sidecar_path.exists())

    def test_create_hex_hash_sidecar_files_handles_multiple_zips(self):
        """Test that hash sidecar files are created for multiple zip files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create multiple zip files
            for i in range(3):
                zip_path = Path(tmpdir) / f"test{i}.zip"
                with zipfile.ZipFile(zip_path, "w") as zf:
                    zf.writestr(f"file{i}.txt", f"content{i}")

            # Create sidecar files
            collect_update_model.create_hex_hash_sidecar_files(tmpdir)

            # Count sidecar files (should be 3)
            all_files = list(Path(tmpdir).iterdir())
            zip_files = [f for f in all_files if f.suffix == ".zip"]
            self.assertEqual(len(zip_files), 3)

            # Each zip should have a corresponding sidecar file
            for zip_file in zip_files:
                sidecar_files = [
                    f
                    for f in all_files
                    if str(f).startswith(str(zip_file) + ".") and f != zip_file
                ]
                self.assertGreater(len(sidecar_files), 0)

    def test_upload_model_raises_on_no_files(self):
        """Test that upload_model raises RuntimeError when no files exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            model_dir = Path(tmpdir) / "empty_model"
            model_dir.mkdir()

            with self.assertRaises(RuntimeError) as context:
                collect_update_model.upload_model(
                    model_dir,
                    "user@host:/path",
                    "/tmp/key.pem",
                )
            self.assertIn("No files found", str(context.exception))

    def test_upload_model_raises_on_invalid_remote_target(self):
        """Test that upload_model raises on invalid remote target format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            model_dir = Path(tmpdir) / "model"
            model_dir.mkdir()
            (model_dir / "test.zip").write_text("content")

            with self.assertRaises(AssertionError) as context:
                collect_update_model.upload_model(
                    model_dir,
                    "invalid-format",  # Missing ':'
                    "/tmp/key.pem",
                )
            self.assertIn("Invalid remote target format", str(context.exception))

    @mock.patch("plate_model_manager.utils.collect_update_model.subprocess.run")
    def test_upload_model_tests_ssh_connection(self, mock_run):
        """Test that upload_model tests SSH connection before uploading."""
        with tempfile.TemporaryDirectory() as tmpdir:
            model_dir = Path(tmpdir) / "model"
            model_dir.mkdir()
            (model_dir / "test.zip").write_text("content")

            collect_update_model.upload_model(
                model_dir,
                "user@host:/remote/path",
                "/tmp/key.pem",
            )

            # Check that subprocess.run was called (SSH test + remote commands + scp)
            self.assertGreater(mock_run.call_count, 0)

            # First call should be SSH connection test
            first_call = mock_run.call_args_list[0][0][0]
            self.assertIn("ssh", first_call)
            self.assertIn("echo", first_call)

    def test_collect_model_raises_on_missing_model(self):
        """Test that collect_model raises ValueError for unknown model."""
        with tempfile.TemporaryDirectory() as tmpdir:
            source_file = Path(tmpdir) / "sources.json"
            source_file.write_text(json.dumps({"known_model": {}}))

            with self.assertRaises(ValueError) as context:
                collect_update_model.collect_model(
                    "unknown_model",
                    tmpdir,
                    str(source_file),
                )
            self.assertIn("not in the data source", str(context.exception))

    def test_collect_model_validates_required_fields(self):
        """Test that collect_model validates required fields in model config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            source_file = Path(tmpdir) / "sources.json"
            # Model missing required 'Rotations' field
            source_file.write_text(
                json.dumps({"testmodel": {"Layers": {"StaticPolygons": ["*.gpml"]}}})
            )

            with mock.patch("builtins.input", return_value="n"):
                with self.assertRaises(ValueError) as context:
                    collect_update_model.collect_model(
                        "testmodel",
                        tmpdir,
                        str(source_file),
                    )
                self.assertIn("Rotations", str(context.exception))


if __name__ == "__main__":
    unittest.main()
