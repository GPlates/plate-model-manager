import string
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from urllib.parse import unquote
from urllib.parse import urlparse

import requests

from . import misc


class _HrefParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hrefs = []

    def handle_starttag(self, tag, attrs):
        for attr_name, attr_value in attrs:
            if attr_name == "href" and attr_value:
                self.hrefs.append(attr_value)


SHA256_HEX_LENGTH = 64


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
    """return the sha256 hash from the sidecar file name in a WebDAV/XML or HTML directory listing.

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

    links = []
    try:
        root = ET.fromstring(r.text)
        for elem in root.iter():
            if elem.tag.endswith("href") and elem.text:
                links.append(elem.text)
    except ET.ParseError:
        pass

    if not links:
        parser = _HrefParser()
        parser.feed(r.text)
        links = parser.hrefs

    for link in links:
        link_name = unquote(link).split("/")[-1]
        expected_prefix = f"{filename}."
        if not link_name.startswith(expected_prefix):
            continue
        hash_string = link_name[len(expected_prefix) :]
        if len(hash_string) == SHA256_HEX_LENGTH and all(
            c in string.hexdigits for c in hash_string
        ):
            return hash_string.lower()

    return None
