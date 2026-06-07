import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from zelda_music_downloader import (
    create_directory,
    download_file,
    get_album_urls,
    process_album_page,
    sanitize_filename,
)


@pytest.mark.parametrize(
    "filename,expected",
    [
        ("normal_file.mp3", "normal_file.mp3"),
        ("file<with>bad:chars.mp3", "filewithbadchars.mp3"),
        ('file"with"quotes.mp3', "filewithquotes.mp3"),
        ("file/with/slashes.mp3", "filewithslashes.mp3"),
        ("file\\with\\backslashes.mp3", "filewithbackslashes.mp3"),
        ("file|with|pipes.mp3", "filewithpipes.mp3"),
        ("file?with?questions.mp3", "filewithquestions.mp3"),
        ("file*with*stars.mp3", "filewithstars.mp3"),
        ("", ""),
        ("already clean.mp3", "already clean.mp3"),
    ],
)
def test_sanitize_filename(filename, expected):
    assert sanitize_filename(filename) == expected


def test_create_directory_creates_new():
    with tempfile.TemporaryDirectory() as tmp:
        new_dir = os.path.join(tmp, "subdir")
        assert not os.path.exists(new_dir)
        create_directory(new_dir)
        assert os.path.isdir(new_dir)


def test_create_directory_existing_is_noop():
    with tempfile.TemporaryDirectory() as tmp:
        create_directory(tmp)
        assert os.path.isdir(tmp)


def _mock_response(status_code=200, chunks=None):
    response = MagicMock()
    response.status_code = status_code
    response.iter_content.return_value = chunks or [b"data"]
    return response


def test_download_file_success():
    with tempfile.TemporaryDirectory() as tmp:
        filepath = os.path.join(tmp, "track.mp3")
        with patch("zelda_music_downloader.requests.get") as mock_get:
            mock_get.return_value = _mock_response(200, [b"chunk1", b"chunk2"])
            result = download_file("http://example.com/track.mp3", filepath)
        assert result is True
        assert open(filepath, "rb").read() == b"chunk1chunk2"


def test_download_file_non_200_returns_false():
    with tempfile.TemporaryDirectory() as tmp:
        filepath = os.path.join(tmp, "track.mp3")
        with patch("zelda_music_downloader.requests.get") as mock_get:
            mock_get.return_value = _mock_response(404)
            result = download_file("http://example.com/track.mp3", filepath)
        assert result is False
        assert not os.path.exists(filepath)


def test_download_file_request_exception_returns_false():
    with tempfile.TemporaryDirectory() as tmp:
        filepath = os.path.join(tmp, "track.mp3")
        with patch(
            "zelda_music_downloader.requests.get", side_effect=Exception("timeout")
        ):
            result = download_file("http://example.com/track.mp3", filepath)
        assert result is False


def test_download_file_skips_empty_chunks():
    with tempfile.TemporaryDirectory() as tmp:
        filepath = os.path.join(tmp, "track.mp3")
        with patch("zelda_music_downloader.requests.get") as mock_get:
            mock_get.return_value = _mock_response(200, [b"real", b"", b"data"])
            download_file("http://example.com/track.mp3", filepath)
        assert open(filepath, "rb").read() == b"realdata"


def _mock_html_response(html):
    response = MagicMock()
    response.text = html
    return response


_BASE_URL = "https://zeldauniverse.net/media/music/"

_ALBUM_PAGE_HTML = """
<html><body>
  <a href="https://zeldauniverse.net/media/music/">Music</a>
  <a href="https://zeldauniverse.net/media/music/ocarina-of-time/">Ocarina of Time</a>
  <a href="https://zeldauniverse.net/media/music/majoras-mask/">Majora's Mask</a>
  <a href="https://zeldauniverse.net/about/">About</a>
</body></html>
"""


def test_get_album_urls_returns_album_links():
    with patch("zelda_music_downloader.requests.get") as mock_get:
        mock_get.return_value = _mock_html_response(_ALBUM_PAGE_HTML)
        urls = get_album_urls()
    assert "https://zeldauniverse.net/media/music/ocarina-of-time/" in urls
    assert "https://zeldauniverse.net/media/music/majoras-mask/" in urls


def test_get_album_urls_excludes_base_url():
    with patch("zelda_music_downloader.requests.get") as mock_get:
        mock_get.return_value = _mock_html_response(_ALBUM_PAGE_HTML)
        urls = get_album_urls()
    assert _BASE_URL not in urls


def test_get_album_urls_excludes_unrelated_links():
    with patch("zelda_music_downloader.requests.get") as mock_get:
        mock_get.return_value = _mock_html_response(_ALBUM_PAGE_HTML)
        urls = get_album_urls()
    assert "https://zeldauniverse.net/about/" not in urls


_TRACK_PAGE_HTML = """
<html><body>
  <a href="https://zeldauniverse.s3.amazonaws.com/oot/01%20Title%20Theme.mp3">Title Theme</a>
  <a href="https://zeldauniverse.s3.amazonaws.com/oot/02%20Kokiri%20Forest.mp3">Kokiri Forest</a>
  <a href="https://other.example.com/music/track.mp3">External</a>
  <a href="https://zeldauniverse.net/media/music/ocarina-of-time/">Back</a>
</body></html>
"""


def test_process_album_page_returns_mp3_links():
    with patch("zelda_music_downloader.requests.get") as mock_get:
        mock_get.return_value = _mock_html_response(_TRACK_PAGE_HTML)
        links = process_album_page(
            "https://zeldauniverse.net/media/music/ocarina-of-time/"
        )
    urls = [url for url, _ in links]
    assert "https://zeldauniverse.s3.amazonaws.com/oot/01%20Title%20Theme.mp3" in urls
    assert "https://zeldauniverse.s3.amazonaws.com/oot/02%20Kokiri%20Forest.mp3" in urls


def test_process_album_page_decodes_filenames():
    with patch("zelda_music_downloader.requests.get") as mock_get:
        mock_get.return_value = _mock_html_response(_TRACK_PAGE_HTML)
        links = process_album_page(
            "https://zeldauniverse.net/media/music/ocarina-of-time/"
        )
    filenames = [name for _, name in links]
    assert "01 Title Theme.mp3" in filenames
    assert "02 Kokiri Forest.mp3" in filenames


def test_process_album_page_excludes_other_domains():
    with patch("zelda_music_downloader.requests.get") as mock_get:
        mock_get.return_value = _mock_html_response(_TRACK_PAGE_HTML)
        links = process_album_page(
            "https://zeldauniverse.net/media/music/ocarina-of-time/"
        )
    urls = [url for url, _ in links]
    assert "https://other.example.com/music/track.mp3" not in urls


def test_process_album_page_excludes_non_mp3():
    with patch("zelda_music_downloader.requests.get") as mock_get:
        mock_get.return_value = _mock_html_response(_TRACK_PAGE_HTML)
        links = process_album_page(
            "https://zeldauniverse.net/media/music/ocarina-of-time/"
        )
    urls = [url for url, _ in links]
    assert "https://zeldauniverse.net/media/music/ocarina-of-time/" not in urls
