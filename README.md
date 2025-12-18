Forked from the original https://github.com/Agnibha007/PyautoMusicDownload

# PyautoMusicDownload

Download and organize Spotify playlists or albums using **spotdl**, following **Plex music folder conventions**.

## Requirements

* Python 3.9+
* ffmpeg

Install **spotdl** (choose one):

```bash
pip install spotdl
```

or (recommended)

```bash
pipx install spotdl
```

## Usage

```bash
python main.py
```

Paste a Spotify **playlist or album** link when prompted.

The script will:

* Fetch metadata
* Organize existing files
* Download only missing tracks

## Output Structure (Plex-compatible)

```
Artist/
└── Album/
    ├── 01 - Title.ext
```

Follows Plex guidelines:
[https://support.plex.tv/articles/200265296-adding-music-media-from-folders/](https://support.plex.tv/articles/200265296-adding-music-media-from-folders/)

## Added Features

* Automatic Artist/Album/Track structure
* Reorganizes previously downloaded files
* Avoids duplicate downloads
* Unicode-safe (Japanese titles, accents)
* Windows-safe filenames

## Notes

* Audio format is handled by spotdl
* Duplicate detection is automatic

## License

MIT
