#!/usr/bin/env python
import json
import os
import sys
import tempfile
import unittest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from common import is_test_installed_module

if not is_test_installed_module():
    sys.path.insert(0, f"{os.path.dirname(__file__)}/../src")

from plate_model_manager.utils.download import FileDownloader
from plate_model_manager.utils.network import get_sha256


class DownloadFileSha256TestCase(unittest.TestCase):
    def test_update_metadata_writes_sha256(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            meta_filepath = f"{tmpdir}/.metadata.json"
            downloader = FileDownloader(
                "https://repo.gplates.org/webdav/pmm/muller2025/Rotations.zip",
                meta_filepath,
                tmpdir,
            )
            downloader.new_etag = "test-etag"

            with patch(
                "plate_model_manager.utils.download.network.get_sha256",
                return_value="a7d126e6f1de27fffeda9734bb06fec4873805bf0bbbcd6a2719e9dca253608d",
            ):
                downloader.update_metadata()

            with open(meta_filepath, "r") as f:
                metadata = json.load(f)

            self.assertEqual(
                metadata["sha256"],
                "a7d126e6f1de27fffeda9734bb06fec4873805bf0bbbcd6a2719e9dca253608d",
            )
            self.assertEqual(metadata["etag"], "test-etag")

    def test_check_update_prefers_sha256(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            meta_filepath = f"{tmpdir}/.metadata.json"
            with open(meta_filepath, "w") as f:
                json.dump(
                    {
                        "url": "https://repo.gplates.org/webdav/pmm/muller2025/Rotations.zip",
                        "expiry": (
                            datetime.now() - timedelta(hours=1)
                        ).strftime("%Y/%m/%d, %H:%M:%S"),
                        "etag": "old-etag",
                        "sha256": "a7d126e6f1de27fffeda9734bb06fec4873805bf0bbbcd6a2719e9dca253608d",
                    },
                    f,
                )

            downloader = FileDownloader(
                "https://repo.gplates.org/webdav/pmm/muller2025/Rotations.zip",
                meta_filepath,
                tmpdir,
            )

            with (
                patch(
                    "plate_model_manager.utils.download.network.get_sha256",
                    return_value="a7d126e6f1de27fffeda9734bb06fec4873805bf0bbbcd6a2719e9dca253608d",
                ),
                patch(
                    "plate_model_manager.utils.download.network.get_headers",
                    side_effect=AssertionError("etag check should not be called"),
                ),
            ):
                self.assertFalse(downloader.check_if_file_need_update())

    def test_get_sha256_from_webdav_xml_listing(self):
        with patch("plate_model_manager.utils.network.requests.get") as mock_get:
            mock_get.return_value = Mock(
                ok=True,
                text="""<?xml version="1.0"?>
<d:multistatus xmlns:d="DAV:">
  <d:response>
    <d:href>/webdav/pmm/muller2025/Rotations.zip.a7d126e6f1de27fffeda9734bb06fec4873805bf0bbbcd6a2719e9dca253608d</d:href>
  </d:response>
</d:multistatus>""",
            )

            sha256 = get_sha256(
                "https://repo.gplates.org/webdav/pmm/muller2025/Rotations.zip"
            )
            self.assertEqual(
                sha256,
                "a7d126e6f1de27fffeda9734bb06fec4873805bf0bbbcd6a2719e9dca253608d",
            )

    def test_get_sha256_from_html_listing(self):
        with patch("plate_model_manager.utils.network.requests.get") as mock_get:
            mock_get.return_value = Mock(
                ok=True,
                text='<a href="Rotations.zip.a7d126e6f1de27fffeda9734bb06fec4873805bf0bbbcd6a2719e9dca253608d">hash</a>',
            )

            sha256 = get_sha256(
                "https://repo.gplates.org/webdav/pmm/muller2025/Rotations.zip"
            )
            self.assertEqual(
                sha256,
                "a7d126e6f1de27fffeda9734bb06fec4873805bf0bbbcd6a2719e9dca253608d",
            )

    def test_check_update_falls_back_to_etag_when_sha256_unavailable(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            meta_filepath = f"{tmpdir}/.metadata.json"
            with open(meta_filepath, "w") as f:
                json.dump(
                    {
                        "url": "https://repo.gplates.org/webdav/pmm/muller2025/Rotations.zip",
                        "expiry": (
                            datetime.now() - timedelta(hours=1)
                        ).strftime("%Y/%m/%d, %H:%M:%S"),
                        "etag": "same-etag",
                        "sha256": "old-sha256",
                    },
                    f,
                )

            downloader = FileDownloader(
                "https://repo.gplates.org/webdav/pmm/muller2025/Rotations.zip",
                meta_filepath,
                tmpdir,
            )

            with (
                patch(
                    "plate_model_manager.utils.download.network.get_sha256",
                    return_value=None,
                ),
                patch(
                    "plate_model_manager.utils.download.network.get_headers",
                    return_value={"ETag": "same-etag", "Content-Length": "1"},
                ),
            ):
                self.assertFalse(downloader.check_if_file_need_update())


if __name__ == "__main__":
    runner = unittest.TextTestRunner()
    runner.run(unittest.TestLoader().loadTestsFromTestCase(DownloadFileSha256TestCase))
