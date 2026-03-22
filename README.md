# PyautoMusicDownload

Download and organize Spotify playlists or albums using **spotdl**, following **Plex music folder conventions**.

*Forked from [Agnibha007/PyautoMusicDownload](https://github.com/Agnibha007/PyautoMusicDownload)*

## Requirements

* **Python 3.10 - 3.13** (Note: 3.14+ is currently unsupported by dependencies)
* **FFmpeg** (For conversion and tagging)
* **yt-dlp** (Handled via requirements.txt)

## Installation & Setup

### Option 1: Virtual Environment (.venv)

#### Windows
```powershell
# Create environment
py -3.12 -m venv .venv

# Activate environment
.\.venv\Scripts\activate

# Install requirements
pip install -r requirements.txt
```

#### Linux / macOS
```bash
# Create environment
python3 -m venv .venv

# Activate environment
source .venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

### Option 2: Using pipx
If you prefer a global standalone installation of the dependencies:

```bash
# Install the specific spotdl fork globally
pipx install git+https://github.com/TzurSoffer/spotify-downloader.git

# Ensure yt-dlp is available
pipx inject spotdl yt-dlp
```

## Usage

1. **Activate your environment** (if using .venv).
- For linux:
```bash
.venv\Scripts\activate
```
- For windows
```bash
.venv\Scripts\Activate.ps1
```
2. **Run the script**:
   ```bash
   python main.py
   ```
3. **Paste Link**: Provide a Spotify playlist, album, or track URL when prompted.

**Note for Windows users:** Always run `chcp 65001` in your terminal before execution to ensure Unicode support for Japanese or accented titles.

## Features

* **Plex-compatible structure**: `Artist/Album/XX - Title.ext`
* **Metadata fallback**: Automatically switches to direct download if metadata parsing fails.
* **Smart Sync**: Detects existing files to skip duplicates.
* **Unicode & Path Safety**: Handles special characters and Windows-reserved symbols.

## Output Structure

```text
Music/
└── Artist/
    └── Album/
        ├── 01 - Title.mp3
        └── 02 - Title.mp3
```

Reference: [Plex Music Media Preparation](https://support.plex.tv/articles/200265296-adding-music-media-from-folders/)

## License

MIT
