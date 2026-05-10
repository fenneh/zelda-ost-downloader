import pytest

from zelda_music_downloader import sanitize_filename


@pytest.mark.parametrize(
    "input,expected",
    [
        ("clean_name.mp3", "clean_name.mp3"),
        ("file<name>.mp3", "filename.mp3"),
        ('file"name".mp3', "filename.mp3"),
        ("file:name.mp3", "filename.mp3"),
        ("file/name.mp3", "filename.mp3"),
        ("file\\name.mp3", "filename.mp3"),
        ("file|name.mp3", "filename.mp3"),
        ("file?name.mp3", "filename.mp3"),
        ("file*name.mp3", "filename.mp3"),
        ("a<>:\"/\\|?*b.mp3", "ab.mp3"),
        ("", ""),
    ],
)
def test_sanitize_filename(input, expected):
    assert sanitize_filename(input) == expected
