import os
import json
import subprocess
import time
import re
import shutil
import unicodedata
import sys

# --- ENVIRONMENT & UNICODE CONFIG ---
# Force UTF-8 for system environment and stdout to prevent 'charmap' errors on Windows
os.environ["PYTHONIOENCODING"] = "utf-8"
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

BASE_FOLDER = os.path.dirname(os.path.abspath(__file__))
OUTPUT_TEMPLATE = "{artist}/{album}/{track-number} - {title}.{output-ext}"
SINGLES_FOLDER_NAME = "Singles"
AUDIO_EXTS = (".mp3", ".wav", ".m4a", ".flac", ".opus", ".ogg")

# --- UTILS ---
def _norm(s: str) -> str:
    """Normalize unicode strings to NFKC and lowercase for reliable comparison."""
    return unicodedata.normalize("NFKC", s).casefold().strip()

def safe_filename(name) -> str:
    """Sanitize strings to be valid Windows filenames."""
    if not name: return "unknown"
    name = re.sub(r'[<>:"/\\|?*\x00-\x1F]', "_", str(name))
    return re.sub(r"\s+", " ", name).strip()[:180] or "unknown"

def extract_spotify_id(link: str) -> str:
    """Extract the ID from a Spotify URL or return a fallback label."""
    clean = link.split("?")[0].rstrip("/")
    for kind in ("playlist", "album", "track"):
        if f"{kind}/" in clean:
            return clean.split(f"{kind}/", 1)[1].split("/", 1)[0]
    return "direct_link"

# --- CORE LOGIC ---
def track_exists(track, folder):
    """
    Check if the track already exists locally.
    Looks into the artist/album subfolders based on the OUTPUT_TEMPLATE.
    """
    artist_dir = safe_filename(track["artist"])
    album_dir = safe_filename(track["album"])
    search_path = os.path.join(folder, artist_dir, album_dir)
    
    if not os.path.isdir(search_path):
        return False

    title_norm = _norm(track["title"])
    for root, _, files in os.walk(search_path):
        for f in files:
            if f.lower().endswith(AUDIO_EXTS) and title_norm in _norm(f):
                return True
    return False

def fetch_metadata(spotify_url: str, spotify_id: str):
    """Run 'spotdl save' to generate a metadata JSON file."""
    metadata_file = os.path.join(BASE_FOLDER, f"{spotify_id}.spotdl")
    cookie_path = os.path.join(BASE_FOLDER, "cookies.txt")
    
    cmd = ["spotdl", "save", spotify_url, "--save-file", metadata_file]
    if os.path.exists(cookie_path):
        cmd.extend(["--cookie-file", cookie_path])

    # Run and replace unicode errors in stderr to prevent script crashes
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='utf-8', errors='replace')
    return metadata_file if os.path.exists(metadata_file) else None

def download_call(query, folder):
    """Execute the actual spotdl download command."""
    output_path = os.path.join(folder, OUTPUT_TEMPLATE)
    subprocess.run(["spotdl", "download", query, "--output", output_path], shell=True)

def load_playlist(path: str):
    """Parse the .spotdl JSON file and extract track information."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list) or not data: return None, [], False
        
        p_name = data[0].get("list_name")
        tracks = []
        for t in data:
            tracks.append({
                "title": t.get("name", "Unknown"),
                "artist": (t.get("artists") or ["Unknown Artist"])[0],
                "album": t.get("album_name") or t.get("album") or "Unknown Album",
                "url": t.get("url", "")
            })
        return p_name, tracks, bool(p_name)
    except Exception:
        return None, [], False

# --- MAIN EXECUTION ---
if __name__ == "__main__":
    url = input("Spotify Link: ").strip()
    if not url: sys.exit()

    sid = extract_spotify_id(url)
    print(f"\n[1/3] Processing ID: {sid}")
    
    m_file = fetch_metadata(url, sid)
    p_name, tracks, is_p = load_playlist(m_file) if m_file else (None, [], False)

    if tracks:
        # Case: Metadata was successfully parsed
        folder = os.path.join(BASE_FOLDER, safe_filename(p_name) if is_p else SINGLES_FOLDER_NAME)
        os.makedirs(folder, exist_ok=True)
        
        print(f"[2/3] Syncing {len(tracks)} tracks in: {os.path.basename(folder)}")
        
        for i, t in enumerate(tracks, 1):
            if track_exists(t, folder):
                print(f"  - [{i}/{len(tracks)}] Skipping (Exists): {t['title']}")
            else:
                print(f"  - [{i}/{len(tracks)}] Downloading: {t['title']}...")
                download_call(t['url'] if t['url'] else f"{t['title']} {t['artist']}", folder)
    else:
        # Case: Metadata failed or returned 0 tracks, fallback to direct download
        print("[2/3] Metadata fetch failed or empty. Falling back to direct download...")
        folder = os.path.join(BASE_FOLDER, SINGLES_FOLDER_NAME)
        os.makedirs(folder, exist_ok=True)
        download_call(url, folder)

    # Cleanup temporary .spotdl file
    if m_file and os.path.exists(m_file):
        os.remove(m_file)

    print("\n[3/3] === PROCESS COMPLETE ===")
