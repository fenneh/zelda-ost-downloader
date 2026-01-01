# zelda-ost-downloader

Downloads Zelda music from Zelda Universe's music archive. Available in Python and PowerShell.

## Features

- Downloads all albums from Zelda Universe
- Organizes music into album folders
- Skips existing files for resumable downloads
- Shows download progress

## Python

```bash
pip install -r requirements.txt
python zelda_music_downloader.py
```

## PowerShell

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\zelda_music_downloader.ps1
```

## Output

Creates a `zelda_music` directory with subdirectories for each album.

## Legal

For personal use only. Music belongs to Nintendo and respective copyright holders.
