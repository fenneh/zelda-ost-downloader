import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from zelda_music_downloader import create_directory, download_file, sanitize_filename


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
    response.iter_content.return_value = chunks or [b"audio", b"data"]
    return response


def test_download_file_success():
    with tempfile.TemporaryDirectory() as tmp:
        dest = os.path.join(tmp, "track.mp3")
        with patch("zelda_music_downloader.requests.get", return_value=_mock_response()):
            result = download_file("http://example.com/track.mp3", dest)
        assert result is True
        assert open(dest, "rb").read() == b"audiodata"


def test_download_file_non_200():
    with tempfile.TemporaryDirectory() as tmp:
        dest = os.path.join(tmp, "track.mp3")
        with patch("zelda_music_downloader.requests.get", return_value=_mock_response(404)):
            result = download_file("http://example.com/track.mp3", dest)
        assert result is False
        assert not os.path.exists(dest)


def test_download_file_exception():
    with tempfile.TemporaryDirectory() as tmp:
        dest = os.path.join(tmp, "track.mp3")
        with patch("zelda_music_downloader.requests.get", side_effect=ConnectionError("timeout")):
            result = download_file("http://example.com/track.mp3", dest)
        assert result is False
