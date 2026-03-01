#!/usr/bin/env python3

import os
import csv
import time
import requests
import pandas as pd
from urllib.parse import quote
from tqdm import tqdm

# This script downloads TMDB posters (original size) for movies listed in a CSV.
# It prefers a numeric TMDB id column (tmdbId, tmdb_id, tmdb, id, movieId, movie_id).
# If no id is found it will try to search TMDB by title (title or name column).
# Usage:
# 1) Install dependencies: pip install requests pandas tqdm
# 2) Place your movies CSV (movies.csv) in the same directory or update MOVIES_CSV
# 3) Provide your TMDB API key as an environment variable:
#      export TMDB_API_KEY="<your_key>"
#    or create a local file .streamlit/secrets.toml with the line:
#      TMDB_API_KEY="<your_key>"
# 4) Run: python download_posters.py

TMDB_API_KEY = os.environ.get("TMDB_API_KEY")
MOVIES_CSV = "movies.csv"
OUTPUT_DIR = os.path.join("assets", "posters")
MAPPING_CSV = os.path.join(OUTPUT_DIR, "poster_mapping.csv")
SLEEP_BETWEEN = 0.25  # seconds between API calls

os.makedirs(OUTPUT_DIR, exist_ok=True)

# Try to read key from .streamlit/secrets.toml if not in env
if not TMDB_API_KEY:
    try:
        if os.path.exists('.streamlit/secrets.toml'):
            with open('.streamlit/secrets.toml', 'r', encoding='utf-8') as f:
                for line in f:
                    if 'TMDB_API_KEY' in line and '=' in line:
                        # naive parsing: TMDB_API_KEY = "KEY"
                        parts = line.split('=', 1)
                        if len(parts) > 1:
                            key = parts[1].strip().strip('"').strip("'")
                            if key:
                                TMDB_API_KEY = key
                                break
    except Exception:
        pass

if not TMDB_API_KEY:
    raise SystemExit("TMDB_API_KEY not found. Set env var TMDB_API_KEY or create .streamlit/secrets.toml")

session = requests.Session()
session.headers.update({"User-Agent": "movie-poster-downloader/1.0"})

def search_tmdb_by_title(title):
    url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={quote(title)}"
    r = session.get(url, timeout=15)
    if r.status_code != 200:
        return None
    data = r.json()
    results = data.get("results") or []
    if not results:
        return None
    return str(results[0]["id"])

def get_movie_details(tmdb_id):
    url = f"https://api.themoviedb.org/3/movie/{tmdb_id}?api_key={TMDB_API_KEY}"
    r = session.get(url, timeout=15)
    if r.status_code != 200:
        return None
    return r.json()

def download_image(url, path):
    try:
        r = session.get(url, stream=True, timeout=30)
        if r.status_code == 200:
            with open(path, "wb") as f:
                for chunk in r.iter_content(1024 * 16):
                    f.write(chunk)
            return True
    except Exception as e:
        print("Download error:", e)
    return False

def main():
    df = pd.read_csv(MOVIES_CSV)
    mapping_rows = []
    for idx, row in tqdm(df.iterrows(), total=len(df)):
        tmdb_id = None
        title = None
        for col in ("tmdbId", "tmdb_id", "tmdb", "id", "movieId", "movie_id"):
            if col in df.columns:
                val = row.get(col)
                if pd.notna(val):
                    try:
                        tmdb_id = str(int(float(val)))
                        break
                    except Exception:
                        pass
        if not tmdb_id:
            for col in ("title", "name"):
                if col in df.columns:
                    val = row.get(col)
                    if pd.notna(val):
                        title = str(val).strip()
                        if title and title.lower() != "nan":
                            tmdb_id = search_tmdb_by_title(title)
                            time.sleep(SLEEP_BETWEEN)
                            break

        if not tmdb_id:
            mapping_rows.append({
                "index": idx,
                "title": title or "",
                "tmdb_id": "",
                "poster_url": "",
                "local_path": "",
                "status": "no_tmdb_id"
            })
            continue

        details = get_movie_details(tmdb_id)
        time.sleep(SLEEP_BETWEEN)
        if not details:
            mapping_rows.append({
                "index": idx,
                "title": title or "",
                "tmdb_id": tmdb_id,
                "poster_url": "",
                "local_path": "",
                "status": "no_details"
            })
            continue

        poster_path = details.get("poster_path")
        if not poster_path:
            mapping_rows.append({
                "index": idx,
                "title": details.get("title", ""),
                "tmdb_id": tmdb_id,
                "poster_url": "",
                "local_path": "",
                "status": "no_poster"
            })
            continue

        poster_url = f"https://image.tmdb.org/t/p/original{poster_path}"
        ext = os.path.splitext(poster_path)[1] or ".jpg"
        out_file = os.path.join(OUTPUT_DIR, f"{tmdb_id}{ext}")

        success = download_image(poster_url, out_file)
        mapping_rows.append({
            "index": idx,
            "title": details.get("title", ""),
            "tmdb_id": tmdb_id,
            "poster_url": poster_url,
            "local_path": out_file if success else "",
            "status": "ok" if success else "download_failed"
        })

    # save mapping
    os.makedirs(os.path.dirname(MAPPING_CSV), exist_ok=True)
    with open(MAPPING_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["index", "title", "tmdb_id", "poster_url", "local_path", "status"])
        writer.writeheader()
        for r in mapping_rows:
            writer.writerow(r)

    print("Done. Mapping saved to", MAPPING_CSV)

if __name__ == '__main__':
    main()
