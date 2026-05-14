import re
from urllib.parse import urlparse

import requests

from . import misc


def get_headers(url, timeout=(None, None)):
    headers = {"Accept-Encoding": "identity"}
    r = requests.head(url, headers=headers, timeout=timeout)
    return r.headers


def get_content_length(headers):
    file_size = headers.get("Content-Length")
    try:
        return int(file_size)
    except:
        misc.print_warning("Unable to get the size of the content.")
        return None


def get_etag(headers):
    """return the etag in the headers. The return could be none if the server does not support etag.

    :param headers: call get_headers(url) to get headers

    """
    new_etag = headers.get("ETag")
    if new_etag:
        # remove the content-encoding awareness thing if present
        new_etag = new_etag.replace("-gzip", "")

    return new_etag


def get_sha256(url, timeout=(None, None)):
    """return the sha256 hash from the sidecar file name in a WebDAV directory listing.

    :param timeout: a (connect_timeout, read_timeout) tuple for requests.get().
        None keeps requests' default behavior for that timeout component.
    """
    parsed_url = urlparse(url)
    filename = parsed_url.path.split("/")[-1]
    if not filename:
        return None

    directory_url = url.rsplit("/", 1)[0] + "/"
    r = requests.get(directory_url, timeout=timeout)
    if not r.ok:
        return None

    match = re.search(rf"{re.escape(filename)}\.([0-9a-fA-F]{{64}})", r.text)
    if not match:
        return None

    return match.group(1).lower()
