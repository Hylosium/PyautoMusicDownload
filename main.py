import os
import json
import subprocess
import time
import re
import shutil
import unicodedata

# BASE PATH = folder where this script is located
BASE_FOLDER = os.path.dirname(os.path.abspath(__file__))

# Desired output structure (spotdl template):
# /{artist}/{album}/{track-number} - {title}.{output-ext}
# (old: /{playlist-name}/{title}.{output-ext})
OUTPUT_TEMPLATE = "{artist}/{album}/{track-number} - {title}.{output-ext}"

# Where to store single-track downloads (root folder)
SINGLES_FOLDER_NAME = "Singles"

# Audio extensions to consider
AUDIO_EXTS = (".mp3", ".wav", ".m4a", ".flac", ".opus", ".ogg")


def _norm(s: str) -> str:
    # Normalizes unicode to reduce false "missing" with Japanese/accents
    return unicodedata.normalize("NFKC", s).casefold().strip()


# -------------------------------------------------
# CLEAN SPOTIFY URL + EXTRACT PLAYLIST / TRACK ID
# -------------------------------------------------
def extract_spotify_id(link: str) -> str:
    clean = link.split("?")[0].rstrip("/")

    # Support /playlist/<id>, /album/<id>, /track/<id>
    for kind in ("playlist", "album", "track"):
        needle = f"{kind}/"
        if needle in clean:
            return clean.split(needle, 1)[1].split("/", 1)[0]

    # Fallback: last path segment
    return clean.split("/")[-1]


def clean_spotify_url(url: str) -> str:
    # consistently remove all params (?si= etc.)
    return url.split("?")[0]


def safe_filename(name) -> str:
    # Windows-safe filename (no <>:"/\|?* and no control chars)
    # Accept None / non-strings (single-track case)
    if not name:
        name = "spotify"
    else:
        name = str(name)

    name = re.sub(r'[<>:"/\\|?*\x00-\x1F]', "_", name)
    name = re.sub(r"\s+", " ", name).strip()
    return name[:180] or "spotify"


# -------------------------------------------------
# FETCH METADATA USING SPOTDL
# -------------------------------------------------
def fetch_metadata(spotify_url: str, spotify_id: str) -> str:
    metadata_file = os.path.join(BASE_FOLDER, f"{safe_filename(spotify_id)}.spotdl")

    print("\nFetching playlist metadata…")

    clean_url = clean_spotify_url(spotify_url)
    command = f'spotdl save "{clean_url}" --save-file "{metadata_file}"'

    subprocess.run(command, shell=True)

    time.sleep(0.5)

    if not os.path.exists(metadata_file):
        print("Metadata file not created.")
        raise SystemExit(1)

    return metadata_file


# -------------------------------------------------
# READ TRACKS FROM .spotdl FILE
# -------------------------------------------------
def load_playlist(path: str):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # list_name exists for playlists, but is None / missing for single-track URLs
    playlist_name = None
    if data and isinstance(data, list) and isinstance(data[0], dict):
        playlist_name = data[0].get("list_name")

    is_playlist = bool(playlist_name)

    tracks = []
    for track in data:
        title = track.get("name") or "Unknown Title"
        artist = (track.get("artists") or ["Unknown Artist"])[0]

        album = track.get("album_name") or track.get("album") or "Unknown Album"

        track_number = track.get("track_number") or track.get("track-number") or 0
        try:
            track_number = int(track_number)
        except Exception:
            track_number = 0

        tracks.append({
            "raw": f"{_norm(title)} {_norm(artist)}",
            "title": title,
            "artist": artist,
            "album": album,
            "track_number": track_number,
        })

    return playlist_name, tracks, is_playlist


# -------------------------------------------------
# CHECK LOCAL FILES
# -------------------------------------------------
def get_local_tracks(folder):
    files = []
    for root, _, filenames in os.walk(folder):
        for f in filenames:
            if f.lower().endswith(AUDIO_EXTS):
                files.append(os.path.splitext(f)[0].lower())
    return files


def _safe_name(s: str) -> str:
    s = s.strip()
    s = re.sub(r'[<>:"/\\|?*\x00-\x1F]', "_", s)
    s = re.sub(r"\s+", " ", s)
    s = _norm(s)
    return s[:180].strip() or "Unknown"


def _list_root_audio_files(folder):
    files = []
    for f in os.listdir(folder):
        p = os.path.join(folder, f)
        if os.path.isfile(p) and f.lower().endswith(AUDIO_EXTS):
            files.append(p)
    return files


def _find_best_match_in_root(track, root_files):
    title = _norm(track["title"])
    artist = _norm(track["artist"])
    raw = _norm(track["raw"])

    best_fp = None
    best_score = 0

    for fp in root_files:
        base = _norm(os.path.splitext(os.path.basename(fp))[0])
        score = 0
        if title and title in base:
            score += 2
        if artist and artist in base:
            score += 2
        if raw and raw in base:
            score += 3

        if score > best_score:
            best_score = score
            best_fp = fp

    return best_fp if best_score > 0 else None


def organize_root_tracks(playlist_folder, playlist_tracks):
    root_files = _list_root_audio_files(playlist_folder)
    if not root_files:
        return

    print(f"\nFound {len(root_files)} unorganized file(s) in playlist root. Organizing...")

    moved = 0

    for t in playlist_tracks:
        match = _find_best_match_in_root(t, root_files)
        if not match:
            continue

        ext = os.path.splitext(match)[1]

        artist_dir = _safe_name(t["artist"])
        album_dir = _safe_name(t["album"])

        tn = t["track_number"]
        tn_str = f"{tn:02d}" if tn > 0 else "01"

        filename = _safe_name(f"{tn_str} - {t['title']}") + ext

        dest_dir = os.path.join(playlist_folder, artist_dir, album_dir)
        os.makedirs(dest_dir, exist_ok=True)

        dest_path = os.path.join(dest_dir, filename)

        if os.path.exists(dest_path):
            root_files.remove(match)
            continue

        shutil.move(match, dest_path)
        root_files.remove(match)
        moved += 1
        print(f" - {os.path.basename(match)} -> {dest_path}")

    if root_files:
        print("\nUnmatched root files:")
        for fp in root_files:
            print(f" - {os.path.basename(fp)}")

    print(f"\nOrganized {moved} file(s).")


def track_exists(track, playlist_folder):
    artist_dir = _safe_name(track["artist"])
    album_dir = _safe_name(track["album"])
    base_dir = os.path.join(playlist_folder, artist_dir, album_dir)
    if not os.path.isdir(base_dir):
        return False

    tn = track.get("track_number", 0) or 0
    title_n = _norm(track["title"])

    # Fast path: track-number prefix match in album folder
    if tn > 0:
        tn_str = f"{tn:02d}"
        try:
            for f in os.listdir(base_dir):
                if f.lower().endswith(AUDIO_EXTS) and _norm(f).startswith(_norm(tn_str + " - ")):
                    return True
        except Exception:
            pass

    # Fallback: title match anywhere in filename within album folder
    for root, _, files in os.walk(base_dir):
        for f in files:
            if f.lower().endswith(AUDIO_EXTS) and title_n in _norm(f):
                return True

    return False


# -------------------------------------------------
# DOWNLOAD SINGLE SONG (title + artist)
# -------------------------------------------------
def download_song(title, artist, folder):
    print(f"\nDownloading: {title} – {artist}")

    output_path = os.path.join(folder, OUTPUT_TEMPLATE)

    subprocess.run([
        "spotdl",
        f"{title} {artist}",
        "--output",
        output_path
    ], shell=True)


# -------------------------------------------------
# SYNC PLAYLIST: FIND MISSING SONGS + DOWNLOAD
# -------------------------------------------------
def sync_playlist(playlist_tracks, folder):
    missing = []

    for song in playlist_tracks:
        if not track_exists(song, folder):
            missing.append(song)

    print("\n=== Missing Songs ===")
    for s in missing:
        print(f" - {s['title']} – {s['artist']}")

    for s in missing:
        download_song(s["title"], s["artist"], folder)


# -------------------------------------------------
# MAIN SCRIPT
# -------------------------------------------------
if __name__ == "__main__":
    playlist_url = input("Paste Spotify playlist link: ").strip()

    spotify_id = extract_spotify_id(playlist_url)
    metadata_file = fetch_metadata(playlist_url, spotify_id)

    playlist_name, playlist_tracks, is_playlist = load_playlist(metadata_file)

    # Root folder:
    # - Playlists: <PlaylistName>/
    # - Single tracks: Singles/
    if is_playlist:
        playlist_folder = os.path.join(BASE_FOLDER, safe_filename(playlist_name))
    else:
        playlist_folder = os.path.join(BASE_FOLDER, SINGLES_FOLDER_NAME)

    if not os.path.exists(playlist_folder):
        print(f"\nCreating folder: {playlist_folder}")
        os.makedirs(playlist_folder)

    organize_root_tracks(playlist_folder, playlist_tracks)
    sync_playlist(playlist_tracks, playlist_folder)

    print("\n=== PLAYLIST SYNC COMPLETE ===")
