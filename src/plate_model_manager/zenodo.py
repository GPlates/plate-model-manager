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
from typing import Dict, List

import requests


class ZenodoRecord:
    """Helper for querying all versions of a Zenodo concept record.

    The class fetches all versions for a given ``conceptrecid`` from the Zenodo
    records API and exposes convenience methods for version lookup and file
    metadata extraction.
    """

    def __init__(self, conceptrecid):
        """Initialize a record client for a Zenodo concept record id.

        :param conceptrecid:
            Zenodo concept record id shared by all versions of the record.
        """
        self.conceptrecid = conceptrecid
        self._record_url = f"https://zenodo.org/api/records?q=conceptrecid:{conceptrecid}&all_versions=true"
        r = requests.get(self._record_url)
        self.sub_records = r.json()["hits"]["hits"]

    def get_all_versions(self) -> List[Dict]:
        """Return all version records returned by the Zenodo API query."""
        return self.sub_records

    def get_all_version_ids(self) -> List[str]:
        """Return the list of record ids for all available versions."""
        return [record["id"] for record in self.get_all_versions()]

    def get_version(self, id: int) -> Dict:
        """Return a specific version record by its record id.

        :param id:
            Zenodo record id of the target version.
        :raises Exception:
            If no record with the given id is found.
        """
        for record in self.get_all_versions():
            if record["id"] == id:
                return record

        raise Exception(
            f"Unable to get version({id}). Check {self._record_url} to find out what is going on."
        )

    def get_latest_version(self) -> Dict:
        """Return the record marked as the latest version.

        :raises Exception:
            If no record is marked as latest in the API response.
        """
        for record in self.sub_records:
            if record["metadata"]["relations"]["version"][0]["is_last"] == True:
                return record

        raise Exception(
            f"Unable to find the latest version. Check {self._record_url} to find out what is going on."
        )

    def get_latest_version_id(self) -> int:
        """Return the Zenodo record id of the latest version."""
        return self.get_latest_version()["id"]

    def get_file_links(self, id: int) -> List[str]:
        """Return download links for all files in a version.

        :param id:
            Zenodo record id of the target version.
        """
        record = self.get_version(id)
        return [file["links"]["self"] for file in record["files"]]

    def get_filenames(self, id: int) -> List[str]:
        """Return file names for all files in a version.

        :param id:
            Zenodo record id of the target version.
        """
        record = self.get_version(id)
        return [file["key"] for file in record["files"]]
