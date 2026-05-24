import os
import tempfile

import pytest

from zelda_music_downloader import create_directory, sanitize_filename


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
