import re
from pathlib import Path
from urllib.parse import unquote

import requests
from bs4 import BeautifulSoup


def create_directory(path):
    Path(path).mkdir(parents=True, exist_ok=True)


def sanitize_filename(filename):
    """Remove invalid characters from filename"""
    return re.sub(r'[<>:"/\\|?*]', "", filename)


def download_file(url, filepath):
    """Download file from url to filepath"""
    try:
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            with open(filepath, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            return True
        return False
    except Exception as e:
        print(f"Error downloading {url}: {str(e)}")
        return False


def get_album_urls():
    """Get list of album URLs from main music page"""
    base_url = "https://zeldauniverse.net/media/music/"
    response = requests.get(base_url)
    soup = BeautifulSoup(response.text, "html.parser")

    album_links = []
    for link in soup.find_all("a", href=True):
        href = link["href"]
        if "/media/music/" in href and href != base_url:
            album_links.append(href)

    return album_links


def process_album_page(album_url):
    """Process single album page and return list of MP3 URLs"""
    response = requests.get(album_url)
    soup = BeautifulSoup(response.text, "html.parser")

    mp3_links = []
    for link in soup.find_all("a", href=True):
        href = link["href"]
        if href.endswith(".mp3") and "zeldauniverse.s3.amazonaws.com" in href:
            mp3_links.append((href, unquote(href.split("/")[-1])))

    return mp3_links


def main():
    base_dir = Path("zelda_music")
    create_directory(base_dir)

    album_urls = get_album_urls()
    print(f"Found {len(album_urls)} albums")

    for album_url in album_urls:
        album_name = album_url.rstrip("/").split("/")[-1].replace("-", " ").title()
        print(f"\nProcessing album: {album_name}")

        album_dir = base_dir / sanitize_filename(album_name)
        create_directory(album_dir)

        mp3_links = process_album_page(album_url)
        print(f"Found {len(mp3_links)} tracks")

        for mp3_url, filename in mp3_links:
            filepath = album_dir / sanitize_filename(filename)

            if not filepath.exists():
                print(f"Downloading: {filename}")
                if download_file(mp3_url, filepath):
                    print(f"Successfully downloaded: {filename}")
                else:
                    print(f"Failed to download: {filename}")
            else:
                print(f"Skipping existing file: {filename}")


if __name__ == "__main__":
    main()
